from datetime import datetime, timedelta
from typing import Optional
import jwt
from sqlalchemy.orm import Session
from ..models import User
from ..config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_HOURS

class AuthService:
    def __init__(self, db: Session):
        self.db = db
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """验证用户凭据"""
        user = self.db.query(User).filter(
            User.username == username,
            User.is_active == True
        ).first()
        
        if user and User.verify_password(password, user.password_hash):
            # 更新最后登录时间
            user.last_login_at = datetime.utcnow()
            self.db.commit()
            return user
        return None
    
    def create_user(self, username: str, password: str, display_name: str = None, email: str = None) -> User:
        """创建新用户"""
        # 检查用户名是否已存在
        existing_user = self.db.query(User).filter(User.username == username).first()
        if existing_user:
            raise ValueError("用户名已存在")
        
        # 检查邮箱是否已存在（如果提供了邮箱）
        if email:
            existing_email = self.db.query(User).filter(User.email == email).first()
            if existing_email:
                raise ValueError("邮箱已存在")
        
        # 创建新用户
        user = User(
            username=username,
            password_hash=User.hash_password(password),
            display_name=display_name or username,
            email=email or "",
            role="user",
            is_active=True
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def generate_token(self, user: User) -> str:
        """生成JWT token"""
        payload = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    def verify_token(self, token: str) -> Optional[dict]:
        """验证JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return self.db.query(User).filter(User.id == user_id, User.is_active == True).first()
    
    def check_username_available(self, username: str) -> bool:
        """检查用户名是否可用"""
        existing_user = self.db.query(User).filter(User.username == username).first()
        return existing_user is None
