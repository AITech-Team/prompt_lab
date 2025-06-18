from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from app.routers import models, templates, prompts, responses, test, history, evaluate, auth, prompt_optimize
from app.database import init_db
from app.websocket import manager
import logging
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="Prompt Lab API",
    description="提示词实验室API",
    version="1.0.0"
)

# 配置CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# 从环境变量中获取额外的允许源
extra_origins = os.getenv("ALLOWED_ORIGINS", "")
if extra_origins:
    origins.extend(extra_origins.split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 只允许指定的源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.websocket("/ws/templates")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # 等待客户端消息，但我们主要用于服务器推送
            data = await websocket.receive_text()
            logger.debug(f"Received message from client: {data}")
    except:
        manager.disconnect(websocket)

# 注册路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(prompt_optimize.router, prefix="/api/v1", tags=["prompt_optimize"])
app.include_router(models.router, prefix="/api/models", tags=["models"])
app.include_router(templates.router, prefix="/api/templates", tags=["templates"])
app.include_router(prompts.router, prefix="/api/prompts", tags=["prompts"])
app.include_router(responses.router, prefix="/api/responses", tags=["responses"])
app.include_router(test.router, prefix="/api/test", tags=["test"])
app.include_router(history.router, prefix="/api/history", tags=["history"])
app.include_router(evaluate.router, prefix="/api/evaluate", tags=["evaluate"])

# 初始化数据库
@app.on_event("startup")
async def startup_event():
    """
    应用启动时的初始化操作
    """
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

@app.get("/")
async def root():
    """
    根路由
    """
    return {"message": "Welcome to Prompt Lab API"} 