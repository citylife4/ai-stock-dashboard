import json
import os
from datetime import datetime
from typing import List
from ..models import AdminActionLog


class AuditService:
    def __init__(self):
        self.log_file = "admin_audit.json"
    
    def log_action(self, action: str, details: str, admin_user: str):
        """Log an admin action."""
        log_entry = AdminActionLog(
            timestamp=datetime.now(),
            action=action,
            details=details,
            admin_user=admin_user
        )
        
        # Load existing logs
        logs = self.get_logs()
        
        # Add new log
        logs.append(log_entry.dict())
        
        # Keep only last 1000 entries
        if len(logs) > 1000:
            logs = logs[-1000:]
        
        # Save logs
        try:
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving audit log: {e}")
    
    def get_logs(self, limit: int = 100) -> List[dict]:
        """Get audit logs."""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    logs = json.load(f)
                    # Return most recent logs first
                    return list(reversed(logs[-limit:]))
        except Exception as e:
            print(f"Error loading audit logs: {e}")
        
        return []