#!/usr/bin/env python3
"""
初始化管理员用户脚本
"""
import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, init_db
# 修改导入语句，从 app.models.py 导入 User 类
from app.models import User

def create_admin_user():
    """创建默认管理员用户"""
    db = SessionLocal()
    try:
        # 初始化数据库表
        init_db()
        
        # 检查是否已存在管理员用户
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("管理员用户已存在")
            return
        
        # 从环境变量获取管理员密码，如果未设置则使用默认密码
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        
        # 创建管理员用户
        admin_user = User(
            username="admin",
            password_hash=User.hash_password(admin_password),
            display_name="管理员",
            email="admin@promptlab.com",
            role="admin",
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        
        print("管理员用户创建成功！")
        print("用户名: admin")
        print(f"密码: {admin_password}")
        if admin_password == "admin123":
            print("警告：正在使用默认密码，请在生产环境中修改默认密码！")
        
    except Exception as e:
        print(f"创建管理员用户失败: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()