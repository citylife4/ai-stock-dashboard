from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..models import User, UserLogin, LoginResponse, UserResponse
from ..config import config
from .user_service import UserService
import logging

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

class AuthService:
    def __init__(self):
        self.secret_key = config.SECRET_KEY
        self.admin_username = config.ADMIN_USERNAME
        self.admin_password_hash = pwd_context.hash(config.ADMIN_PASSWORD)
        self.user_service = UserService()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def authenticate_admin(self, username: str, password: str) -> bool:
        """Authenticate admin credentials."""
        if username != self.admin_username:
            return False
        return self.verify_password(password, self.admin_password_hash)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify a JWT token and return username if valid."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                return None
            return username
        except JWTError:
            return None
    
    # User authentication methods
    def create_user_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token for users."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=config.JWT_EXPIRATION_HOURS)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
        return encoded_jwt
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = await self.user_service.get_user_by_email(email)
        if not user:
            return None
        
        if not user.is_active:
            return None
            
        # Get user document to access password hash
        from ..database import get_database
        db = get_database()
        if db is None:
            return None
            
        try:
            from bson import ObjectId
            user_doc = await db.users.find_one({"_id": ObjectId(user.id)})
            if not user_doc:
                return None
                
            if not await self.user_service.verify_password(password, user_doc["password_hash"]):
                return None
                
            return user
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    async def login(self, login_data: UserLogin) -> Optional[LoginResponse]:
        """Login user and return access token."""
        user = await self.authenticate_user(login_data.email, login_data.password)
        if not user:
            return None
        
        access_token = self.create_user_access_token(data={"sub": user.id})
        
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            subscription_tier=user.subscription_tier,
            max_stocks=user.max_stocks,
            created_at=user.created_at,
            is_active=user.is_active,
            is_admin=getattr(user, 'is_admin', False)
        )
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
        """Get current user from JWT token."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(credentials.credentials, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        
        user = await self.user_service.get_user_by_id(user_id)
        if user is None:
            raise credentials_exception
            
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user"
            )
        
        return user


# Create global instance
auth_service = AuthService()

# Dependency functions for users
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Dependency to get current user."""
    return await auth_service.get_current_user(credentials)

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to get current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user