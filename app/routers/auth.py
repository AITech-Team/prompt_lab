from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

from ..database import get_db
from ..services.auth_service import AuthService
from ..models import User

router = APIRouter(prefix="", tags=["认证"])
security = HTTPBearer()

# 请求模型
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    confirmPassword: str
    displayName: Optional[str] = None
    email: Optional[str] = None

# 响应模型
class UserInfo(BaseModel):
    id: int
    username: str
    displayName: str
    email: str
    createdTime: datetime
    lastLoginTime: Optional[datetime] = None

class LoginResponse(BaseModel):
    token: str
    user: UserInfo

class ApiResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: str

# 依赖注入：获取当前用户
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    payload = auth_service.verify_token(credentials.credentials)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = auth_service.get_user_by_id(payload["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

@router.post("/login", response_model=ApiResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    try:
        if not request.username or not request.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名和密码不能为空"
            )
        
        auth_service = AuthService(db)
        user = auth_service.authenticate_user(request.username, request.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 生成token
        token = auth_service.generate_token(user)
        
        user_info = UserInfo(
            id=user.id,
            username=user.username,
            displayName=user.display_name or user.username,
            email=user.email or "",
            createdTime=user.created_at,
            lastLoginTime=user.last_login_at
        )
        
        response_data = LoginResponse(token=token, user=user_info)
        
        return ApiResponse(
            success=True,
            data=response_data.dict(),
            message="登录成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )

@router.post("/register", response_model=ApiResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册"""
    try:
        # 验证输入
        if not request.username or not request.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名和密码不能为空"
            )
        
        if request.password != request.confirmPassword:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="两次输入的密码不一致"
            )
        
        if len(request.username) < 3 or len(request.username) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名长度必须在3-50个字符之间"
            )
        
        if len(request.password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密码长度至少为6个字符"
            )
        
        auth_service = AuthService(db)
        
        try:
            user = auth_service.create_user(
                username=request.username,
                password=request.password,
                display_name=request.displayName,
                email=request.email
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        
        # 生成token
        token = auth_service.generate_token(user)
        
        user_info = UserInfo(
            id=user.id,
            username=user.username,
            displayName=user.display_name or user.username,
            email=user.email or "",
            createdTime=user.created_at,
            lastLoginTime=user.last_login_at
        )
        
        response_data = LoginResponse(token=token, user=user_info)
        
        return ApiResponse(
            success=True,
            data=response_data.dict(),
            message="注册成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )

@router.get("/check-username/{username}")
async def check_username(username: str, db: Session = Depends(get_db)):
    """检查用户名是否可用"""
    try:
        auth_service = AuthService(db)
        is_available = auth_service.check_username_available(username)
        
        return ApiResponse(
            success=True,
            data={"isAvailable": is_available},
            message="检查完成"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检查用户名失败: {str(e)}"
        )

@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    user_info = UserInfo(
        id=current_user.id,
        username=current_user.username,
        displayName=current_user.display_name or current_user.username,
        email=current_user.email or "",
        createdTime=current_user.created_at,
        lastLoginTime=current_user.last_login_at
    )
    
    return ApiResponse(
        success=True,
        data=user_info.dict(),
        message="获取用户信息成功"
    )
