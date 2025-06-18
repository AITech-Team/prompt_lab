#!/usr/bin/env python3
"""
Prompt Lab 启动脚本
"""
import os
import sys
import subprocess
import time

def check_requirements():
    """检查必要的依赖"""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import jwt
        print("✓ 后端依赖检查通过")
        return True
    except ImportError as e:
        print(f"✗ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def init_database():
    """初始化数据库"""
    try:
        print("正在初始化数据库...")
        subprocess.run([sys.executable, "init_admin.py"], check=True)
        print("✓ 数据库初始化完成")
        return True
    except subprocess.CalledProcessError:
        print("✗ 数据库初始化失败")
        return False

def start_backend():
    """启动后端服务"""
    print("正在启动后端服务...")
    try:
        subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ])
        print("✓ 后端服务启动成功 (http://localhost:8000)")
        return True
    except Exception as e:
        print(f"✗ 后端服务启动失败: {e}")
        return False

def start_frontend():
    """启动前端服务"""
    print("正在启动前端服务...")
    try:
        subprocess.Popen([
            "npm", "start"
        ], shell=True)
        print("✓ 前端服务启动成功 (http://localhost:3000)")
        return True
    except Exception as e:
        print(f"✗ 前端服务启动失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("🚀 Prompt Lab 启动脚本")
    print("=" * 50)
    
    # 检查依赖
    if not check_requirements():
        return
    
    # 初始化数据库
    if not init_database():
        return
    
    # 启动后端
    if not start_backend():
        return
    
    # 等待后端启动
    print("等待后端服务启动...")
    time.sleep(3)
    
    # 启动前端
    if not start_frontend():
        return
    
    print("\n" + "=" * 50)
    print("🎉 Prompt Lab 启动完成！")
    print("前端地址: http://localhost:3000")
    print("后端地址: http://localhost:8000")
    print("API文档: http://localhost:8000/docs")
    print("\n默认管理员账户:")
    print("用户名: admin")
    print("密码: admin123")
    print("=" * 50)
    
    try:
        print("\n按 Ctrl+C 停止服务...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止服务...")

if __name__ == "__main__":
    main()
