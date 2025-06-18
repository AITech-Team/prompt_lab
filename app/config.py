import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 模型配置
DEFAULT_API_KEY = os.getenv("DEFAULT_API_KEY", "")  # 默认API密钥
DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "modelscope")  # 默认使用 modelscope 作为提供商
DEFAULT_MODEL_NAME = os.getenv("DEFAULT_MODEL_NAME", "Qwen/Qwen3-32B")  # 默认模型名称
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # OpenAI API密钥，仅作为备用

# JWT配置
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "168"))  # 7天