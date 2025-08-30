from datetime import datetime
from typing import List, Optional
from bson import ObjectId
import bcrypt
from ..models import (
    User, UserCreate, UserResponse, SubscriptionTier, 
    UserStock, AdminUserResponse, AdminUserUpdate
)
from ..database import get_database
import logging

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self):
        # Don't get database at init time, get it when needed
        pass
    
    @property
    def db(self):
        """Get database connection lazily."""
        return get_database()
    
    async def create_user(self, user_data: UserCreate) -> Optional[User]:
        """Create a new user."""
        if self.db is None:
            return None
            
        try:
            # Hash password
            hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt())
            
            # Get subscription limits
            limits = self._get_subscription_limits(user_data.subscription_tier)
            
            user_doc = {
                "username": user_data.username,
                "email": user_data.email,
                "password_hash": hashed_password,
                "subscription_tier": user_data.subscription_tier.value,
                "max_stocks": limits["max_stocks"],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
                "is_admin": False
            }
            
            result = await self.db.users.insert_one(user_doc)
            
            if result.inserted_id:
                user_doc["id"] = str(result.inserted_id)
                return User(**user_doc)
                
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        if self.db is None:
            return None
            
        try:
            user_doc = await self.db.users.find_one({"email": email})
            if user_doc:
                user_doc["id"] = str(user_doc["_id"])
                return User(**user_doc)
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        if self.db is None:
            return None
            
        try:
            user_doc = await self.db.users.find_one({"_id": ObjectId(user_id)})
            if user_doc:
                user_doc["id"] = str(user_doc["_id"])
                return User(**user_doc)
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    async def verify_password(self, plain_password: str, hashed_password: bytes) -> bool:
        """Verify password against hash."""
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False
    
    async def update_user_subscription(self, user_id: str, subscription_tier: SubscriptionTier, max_stocks: Optional[int] = None) -> bool:
        """Update user subscription tier."""
        if self.db is None:
            return False
            
        try:
            update_data = {
                "subscription_tier": subscription_tier.value,
                "updated_at": datetime.utcnow()
            }
            
            if max_stocks is not None:
                update_data["max_stocks"] = max_stocks
            else:
                limits = self._get_subscription_limits(subscription_tier)
                update_data["max_stocks"] = limits["max_stocks"]
            
            result = await self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating user subscription: {e}")
            return False
    
    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[AdminUserResponse]:
        """Get all users for admin panel."""
        if self.db is None:
            return []
            
        try:
            users = []
            async for user_doc in self.db.users.find().skip(skip).limit(limit):
                # Get stock count for user
                stock_count = await self.db.user_stocks.count_documents({"user_id": str(user_doc["_id"])})
                
                user_response = AdminUserResponse(
                    id=str(user_doc["_id"]),
                    username=user_doc["username"],
                    email=user_doc["email"],
                    subscription_tier=SubscriptionTier(user_doc["subscription_tier"]),
                    max_stocks=user_doc["max_stocks"],
                    created_at=user_doc["created_at"],
                    is_active=user_doc["is_active"],
                    stock_count=stock_count
                )
                users.append(user_response)
                
            return users
            
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    async def update_user_admin(self, user_id: str, update_data: AdminUserUpdate) -> bool:
        """Update user by admin."""
        if self.db is None:
            return False
            
        try:
            update_doc = {"updated_at": datetime.utcnow()}
            
            if update_data.subscription_tier is not None:
                update_doc["subscription_tier"] = update_data.subscription_tier.value
                
            if update_data.max_stocks is not None:
                update_doc["max_stocks"] = update_data.max_stocks
                
            if update_data.is_active is not None:
                update_doc["is_active"] = update_data.is_active
            
            result = await self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_doc}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating user by admin: {e}")
            return False
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user and all associated data."""
        if self.db is None:
            return False
            
        try:
            # First, delete all user's stock tracking data
            await self.db.user_stocks.delete_many({"user_id": user_id})
            
            # Then delete the user
            result = await self.db.users.delete_one({"_id": ObjectId(user_id)})
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False
    
    def _get_subscription_limits(self, tier: SubscriptionTier) -> dict:
        """Get limits for subscription tier."""
        limits = {
            SubscriptionTier.FREE: {"max_stocks": 5},
            SubscriptionTier.PRO: {"max_stocks": 10},
            SubscriptionTier.EXPERT: {"max_stocks": 20}
        }
        return limits.get(tier, limits[SubscriptionTier.FREE])
    
    async def create_admin_user(self, username: str, email: str, password: str) -> Optional[User]:
        """Create admin user with unlimited access."""
        if self.db is None:
            return None
            
        try:
            # Check if admin user already exists
            existing_admin = await self.db.users.find_one({
                "$or": [
                    {"email": email},
                    {"username": username},
                    {"is_admin": True}
                ]
            })
            
            if existing_admin:
                logger.info("Admin user already exists")
                return None
            
            # Hash password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            admin_doc = {
                "username": username,
                "email": email,
                "password_hash": hashed_password,
                "subscription_tier": SubscriptionTier.EXPERT.value,  # Admin gets expert tier
                "max_stocks": 9999,  # Unlimited stocks for admin
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
                "is_admin": True
            }
            
            result = await self.db.users.insert_one(admin_doc)
            
            if result.inserted_id:
                admin_doc["id"] = str(result.inserted_id)
                return User(**admin_doc)
                
        except Exception as e:
            logger.error(f"Error creating admin user: {e}")
            return None
    
    async def ensure_admin_user_exists(self, username: str, email: str, password: str) -> bool:
        """Ensure admin user exists in the database."""
        if self.db is None:
            return False
            
        try:
            # Check if admin user exists with correct email
            admin_exists = await self.db.users.find_one({
                "is_admin": True,
                "email": email,
                "username": username
            })
            
            if not admin_exists:
                # Check if admin exists with wrong email or different username
                old_admin = await self.db.users.find_one({"is_admin": True})
                if old_admin:
                    logger.info(f"Removing old admin user with incorrect email: {old_admin.get('email')}")
                    await self.db.users.delete_one({"_id": old_admin["_id"]})
                
                admin_user = await self.create_admin_user(username, email, password)
                if admin_user:
                    logger.info(f"Created admin user: {username} with email: {email}")
                    return True
                else:
                    logger.error("Failed to create admin user")
                    return False
            else:
                logger.info(f"Admin user already exists: {username}")
                return True
                
        except Exception as e:
            logger.error(f"Error ensuring admin user exists: {e}")
            return False


class UserStockService:
    def __init__(self):
        # Don't get database at init time, get it when needed
        pass
    
    @property
    def db(self):
        """Get database connection lazily."""
        return get_database()
    
    async def add_user_stock(self, user_id: str, symbol: str) -> bool:
        """Add stock to user's tracking list."""
        if self.db is None:
            return False
            
        try:
            # Check if user already tracks this stock
            existing = await self.db.user_stocks.find_one({
                "user_id": user_id,
                "symbol": symbol.upper()
            })
            
            if existing:
                return False  # Already tracking
            
            # Check stock limit
            current_count = await self.db.user_stocks.count_documents({"user_id": user_id})
            user = await UserService().get_user_by_id(user_id)
            
            if not user or current_count >= user.max_stocks:
                return False  # Limit exceeded
            
            user_stock = {
                "user_id": user_id,
                "symbol": symbol.upper(),
                "added_at": datetime.utcnow()
            }
            
            result = await self.db.user_stocks.insert_one(user_stock)
            return result.inserted_id is not None
            
        except Exception as e:
            logger.error(f"Error adding user stock: {e}")
            return False
    
    async def remove_user_stock(self, user_id: str, symbol: str) -> bool:
        """Remove stock from user's tracking list."""
        if self.db is None:
            return False
            
        try:
            result = await self.db.user_stocks.delete_one({
                "user_id": user_id,
                "symbol": symbol.upper()
            })
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error removing user stock: {e}")
            return False
    
    async def get_user_stocks(self, user_id: str) -> List[str]:
        """Get list of stocks tracked by user."""
        if self.db is None:
            return []
            
        try:
            stocks = []
            async for stock_doc in self.db.user_stocks.find({"user_id": user_id}):
                stocks.append(stock_doc["symbol"])
            
            return stocks
            
        except Exception as e:
            logger.error(f"Error getting user stocks: {e}")
            return []
    
    async def get_all_tracked_symbols(self) -> List[str]:
        """Get all unique symbols being tracked by any user."""
        if self.db is None:
            return []
            
        try:
            symbols = await self.db.user_stocks.distinct("symbol")
            return symbols
            
        except Exception as e:
            logger.error(f"Error getting all tracked symbols: {e}")
            return []