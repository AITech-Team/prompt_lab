import os
import openai
import anthropic
import httpx
from volcenginesdkarkruntime import Ark
import re
import json
import logging

# 配置日志
logger = logging.getLogger(__name__)

class ModelAdapter:
    def __init__(self, provider: str, api_key: str, base_url: str = ""):
        self.provider = provider
        self.api_key = api_key.strip() if api_key else ""
        self.base_url = base_url.strip() if base_url else ""
        self._validate_api_key()

    @classmethod
    def get_model_types(cls):
        """返回所有支持的模型类型列表"""
        return [
            'openai', 'anthropic', 'deepseek', 'qwen', 'doubao', 
            'chatglm', 'zhipu', 'wenxin', 'spark', 'modelscope', 'local'
        ]

    def _validate_api_key(self):
        """验证API密钥的有效性"""
        if not self.api_key and self.provider != "local":
            raise ValueError(f"未配置{self.provider}的API密钥")
            
        # 根据不同的模型类型验证API密钥格式
        if self.provider == "openai" and not self.api_key.startswith("sk-"):
            raise ValueError("无效的OpenAI API密钥格式")
        elif self.provider == "anthropic" and not re.match(r"^sk-ant-[a-zA-Z0-9-]+$", self.api_key):
            raise ValueError("无效的Anthropic API密钥格式")
        elif self.provider == "deepseek" and not self.api_key.startswith("sk-"):
            raise ValueError("无效的Deepseek API密钥格式")
        elif self.provider == "qwen" and len(self.api_key) < 10:
            raise ValueError("无效的Qwen API密钥格式")
        elif self.provider == "doubao" and len(self.api_key) < 10:
            raise ValueError("无效的豆包API密钥格式")
        elif self.provider == "chatglm" and len(self.api_key) < 10:
            raise ValueError("无效的ChatGLM API密钥格式")
        elif self.provider == "zhipu" and len(self.api_key) < 10:
            raise ValueError("无效的智谱AI API密钥格式")
        elif self.provider == "wenxin" and len(self.api_key) < 10:
            raise ValueError("无效的文心API密钥格式")
        elif self.provider == "spark" and len(self.api_key) < 10:
            raise ValueError("无效的讯飞星火API密钥格式")
        elif self.provider == "modelscope" and len(self.api_key) < 10:
            raise ValueError("无效的ModelScope API密钥格式")

    def validate_api_key(self) -> bool:
        """验证API密钥是否有效"""
        try:
            self._validate_api_key()
            return True
        except ValueError:
            return False

    def send_prompt(self, prompt: str, variables: dict = None):
        # 替换变量
        if variables:
            for var_name, var_value in variables.items():
                prompt = prompt.replace("{{" + var_name + "}}", str(var_value))

        if self.provider == "openai":
            return self._call_openai(prompt, variables)
        elif self.provider == "anthropic":
            return self._call_anthropic(prompt, variables)
        elif self.provider == "deepseek":
            return self._call_deepseek(prompt, variables)
        elif self.provider == "qwen":
            return self._call_qwen(prompt, variables)
        elif self.provider == "doubao":
            return self._call_doubao(prompt, variables)
        elif self.provider == "chatglm":
            return self._call_chatglm(prompt, variables)
        elif self.provider == "zhipu":
            return self._call_zhipu(prompt, variables)
        elif self.provider == "wenxin":
            return self._call_wenxin(prompt, variables)
        elif self.provider == "spark":
            return self._call_spark(prompt, variables)
        elif self.provider == "modelscope":
            return self._call_modelscope(prompt, variables)
        elif self.provider == "local":
            return self._call_local_llm(prompt, variables)
        else:
            raise NotImplementedError(f"不支持的模型类型: {self.provider}")

    def _call_openai(self, prompt, variables):
        if not self.api_key:
            raise ValueError("未配置OpenAI API密钥")
        # 默认模型为gpt-4，可以通过variables传入自定义模型
        model = variables.get("model", "gpt-4") if variables else "gpt-4"
        logger.info(f"Calling OpenAI with model: {model}")
        client = openai.OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
        return {"model": "openai", "output": response.choices[0].message.content}

    def _call_anthropic(self, prompt, variables):
        if not self.api_key:
            raise ValueError("未配置Anthropic API密钥")
        # 默认模型为claude-3-opus-20240229，可以通过variables传入自定义模型
        model = variables.get("model", "claude-3-opus-20240229") if variables else "claude-3-opus-20240229"
        client = anthropic.Anthropic(api_key=self.api_key)
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return {"model": "anthropic", "output": response.content[0].text if hasattr(response.content[0], 'text') else response.content}

    def _call_deepseek(self, prompt, variables):
        if not self.api_key:
            raise ValueError("未配置Deepseek API密钥")
        # 默认模型为deepseek-chat，可以通过variables传入自定义模型
        model = variables.get("model", "deepseek-chat") if variables else "deepseek-chat"
        base_url = self.base_url or "https://api.deepseek.com/v1"
        logger.info(f"Calling Deepseek with model: {model}, base_url: {base_url}")
        try:
            client = openai.OpenAI(api_key=self.api_key, base_url=base_url)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )
            # 获取响应内容
            content = response.choices[0].message.content
            # 预处理响应内容，移除可能导致格式错误的字符
            content = content.strip()
            content = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', content)  # 移除控制字符
            return {"model": "deepseek", "output": content}
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Deepseek API调用失败: {error_msg}")
            return {"model": "deepseek", "output": f"调用失败: {error_msg}", "error": True}

    def _call_qwen(self, prompt, variables):
        if not self.api_key:
            raise ValueError("未配置Qwen API密钥")
        # 默认模型为qwen-plus，可以通过variables传入自定义模型
        model = variables.get("model", "qwen-plus") if variables else "qwen-plus"
        logger.info(f"Calling Qwen with model: {model}")
        client = openai.OpenAI(api_key=self.api_key, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
        return {"model": "qwen", "output": response.choices[0].message.content}

    def _call_modelscope(self, prompt, variables):
        """调用ModelScope API"""
        if not self.api_key:
            raise ValueError("未配置ModelScope API密钥")
        
        # 使用默认的base_url或提供的url
        base_url = self.base_url or "https://api-inference.modelscope.cn/v1/"
        
        # 获取模型名称，优先使用传入的model参数
        model_name = variables.get("model") if variables else None
        
        # 如果没有传入model参数，则使用默认的Qwen模型
        if not model_name:
            model_name = "Qwen/Qwen3-32B"
        
        # 确保模型名称格式正确，如果是简单名称如"qwen-32b"，则转换为标准格式
        if not "/" in model_name and "qwen" in model_name.lower():
            model_name = f"Qwen/{model_name}"
        
        try:
            logger.info(f"Calling ModelScope with model: {model_name}")
            
            # 创建客户端
            client = openai.OpenAI(
                base_url=base_url,
                api_key=self.api_key
            )
            
            # 构建请求参数
            messages = [{"role": "user", "content": prompt}]
            
            # 如果是评估任务，添加系统提示词
            if "评估" in prompt and "JSON" in prompt:
                system_message = {
                    "role": "system",
                    "content": """你是一个专业的AI回答质量评估专家。你的任务是评估AI回答的质量，并返回JSON格式的评估结果。
请确保你的回答：
1. 只包含JSON格式的评估结果
2. 不要添加任何其他解释或说明
3. 分数必须是1-10的整数
4. 使用简洁的中文描述理由
5. JSON格式必须完全正确，不要包含注释"""
                }
                messages.insert(0, system_message)
            
            # 构建API参数
            api_params = {
                "model": model_name,
                "messages": messages,
                "stream": False,
                "extra_body": {
                    "enable_thinking": False  # 非流式调用时必须设置为false
                }
            }
            
            # 发送请求
            response = client.chat.completions.create(**api_params)
            
            # 检查响应是否为空
            if not response:
                logger.error("ModelScope response is None")
                return {
                    "model": "modelscope",
                    "output": None,
                    "error": "API返回为空"
                }

            # 检查choices是否存在
            if not hasattr(response, 'choices') or not response.choices:
                logger.error("ModelScope response has no choices")
                return {
                    "model": "modelscope",
                    "output": None,
                    "error": "API返回格式错误：缺少choices"
                }

            # 检查第一个choice是否存在
            if len(response.choices) == 0:
                logger.error("ModelScope response choices is empty")
                return {
                    "model": "modelscope",
                    "output": None,
                    "error": "API返回格式错误：choices为空"
                }

            # 检查message是否存在
            first_choice = response.choices[0]
            if not hasattr(first_choice, 'message') or not first_choice.message:
                logger.error("ModelScope response choice has no message")
                return {
                    "model": "modelscope",
                    "output": None,
                    "error": "API返回格式错误：缺少message"
                }

            # 获取content
            content = first_choice.message.content
            if content is None:
                logger.error("ModelScope response message has no content")
                return {
                    "model": "modelscope",
                    "output": None,
                    "error": "API返回格式错误：缺少content"
                }
                
            return {
                "model": "modelscope",
                "output": content
            }
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"ModelScope API调用失败: {error_msg}")
            return {
                "model": "modelscope",
                "output": f"调用失败: {error_msg}",
                "error": True
            }

    def _call_doubao(self, prompt, variables):
        if not self.api_key:
            raise ValueError("未配置豆包API密钥")
        # 默认模型为doubao-1.5-pro-32k，可以通过variables传入自定义模型
        model = variables.get("model", "doubao-1.5-pro-32k") if variables else "doubao-1.5-pro-32k"
        ark_client = Ark(api_key=self.api_key)
        response = ark_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return {"model": "doubao", "output": response.choices[0].message.content}

    def _call_local_llm(self, prompt, variables):
        # TODO: 实现本地LLM调用
        return {"model": "local", "output": "本地LLM调用未实现"}

    def _call_chatglm(self, prompt, variables):
        """调用ChatGLM API"""
        if not self.api_key:
            raise ValueError("未配置ChatGLM API密钥")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 默认API路径包含模型名称，可以通过base_url或variables中的model参数自定义
        model = variables.get("model", "chatglm_turbo") if variables else "chatglm_turbo"
        api_url = self.base_url or f"https://open.bigmodel.cn/api/paas/v3/model-api/{model}/sse-invoke"
        
        data = {
            "prompt": prompt,
            "temperature": 0.7,
            "top_p": 0.7,
            "request_id": f"{model}_" + str(variables.get("request_id", "") if variables else "")
        }
        
        try:
            with httpx.Client() as client:
                response = client.post(api_url, json=data, headers=headers)
                response.raise_for_status()
                result = response.json()
                # 安全地获取嵌套字段
                data = result.get("data")
                if data and isinstance(data, dict):
                    output = data.get("text", "")
                else:
                    output = ""
                return {"model": "chatglm", "output": output}
        except Exception as e:
            raise ValueError(f"调用ChatGLM API失败: {str(e)}")

    def _call_zhipu(self, prompt, variables):
        """调用智谱AI API"""
        if not self.api_key:
            raise ValueError("未配置智谱AI API密钥")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 默认API路径包含模型名称，可以通过base_url或variables中的model参数自定义
        model = variables.get("model", "chatglm_turbo") if variables else "chatglm_turbo"
        api_url = self.base_url or f"https://open.bigmodel.cn/api/paas/v3/model-api/{model}/sse-invoke"
        
        data = {
            "prompt": prompt,
            "temperature": 0.7,
            "top_p": 0.7
        }
        
        try:
            with httpx.Client() as client:
                response = client.post(api_url, json=data, headers=headers)
                response.raise_for_status()
                result = response.json()
                return {"model": "zhipu", "output": result.get("response", "")}
        except Exception as e:
            raise ValueError(f"调用智谱AI API失败: {str(e)}")

    def _call_wenxin(self, prompt, variables):
        """调用百度文心API"""
        if not self.api_key:
            raise ValueError("未配置文心API密钥")
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # 文心API需要access token
        access_token_url = "https://aip.baidubce.com/oauth/2.0/token"
        token_params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key.split(":")[0],
            "client_secret": self.api_key.split(":")[1]
        }
        
        try:
            with httpx.Client() as client:
                token_response = client.post(access_token_url, params=token_params)
                token_response.raise_for_status()
                access_token = token_response.json().get("access_token")
                
                if not access_token:
                    raise ValueError("获取文心API access token失败")
                
                # 默认模型为completions，可以通过variables传入自定义模型
                model = variables.get("model", "completions") if variables else "completions"
                api_url = self.base_url or f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{model}?access_token={access_token}"
                
                data = {
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "top_p": 0.7
                }
                
                response = client.post(api_url, json=data, headers=headers)
                response.raise_for_status()
                result = response.json()
                return {"model": "wenxin", "output": result.get("result", "")}
        except Exception as e:
            raise ValueError(f"调用文心API失败: {str(e)}")

    def _call_spark(self, prompt, variables):
        """调用讯飞星火API"""
        if not self.api_key:
            raise ValueError("未配置讯飞星火API密钥")
        
        from datetime import datetime
        import hmac
        import base64
        import hashlib
        import json
        
        # 讯飞API需要特殊的鉴权
        app_id, api_key, api_secret = self.api_key.split(":")
        
        def create_url():
            # 默认版本为v1.1，可以通过variables传入自定义版本
            version = variables.get("version", "v1.1") if variables else "v1.1"
            # 默认域为chat，可以通过variables传入自定义域
            domain = variables.get("domain", "chat") if variables else "chat"
            url = self.base_url or f"wss://spark-api.xf-yun.com/{version}/{domain}"
            
            # 生成RFC1123格式的时间戳
            now = datetime.now()
            date = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
            
            # 拼接字符串
            signature_origin = f"host: spark-api.xf-yun.com\ndate: {date}\nGET /{version}/{domain} HTTP/1.1"
            
            # 使用hmac-sha256进行加密
            signature_sha = hmac.new(
                api_secret.encode('utf-8'),
                signature_origin.encode('utf-8'),
                digestmod=hashlib.sha256
            ).digest()
            
            signature_sha_base64 = base64.b64encode(signature_sha).decode()
            authorization_origin = f'api_key="{api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
            authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode()
            
            v = {
                "authorization": authorization,
                "date": date,
                "host": "spark-api.xf-yun.com"
            }
            return url + "?" + "&".join([f"{k}={v}" for k, v in v.items()])
        
        try:
            url = create_url()
            headers = {
                "Content-Type": "application/json"
            }
            
            # 默认域为general，可以通过variables传入自定义域
            model_domain = variables.get("model_domain", "general") if variables else "general"
            
            data = {
                "header": {
                    "app_id": app_id
                },
                "parameter": {
                    "chat": {
                        "domain": model_domain,
                        "temperature": 0.7,
                        "top_k": 4
                    }
                },
                "payload": {
                    "message": {
                        "text": [{"role": "user", "content": prompt}]
                    }
                }
            }
            
            with httpx.Client() as client:
                response = client.post(url, json=data, headers=headers)
                response.raise_for_status()
                result = response.json()
                # 安全地获取嵌套字段
                payload = result.get("payload")
                if payload and isinstance(payload, dict):
                    message = payload.get("message")
                    if message and isinstance(message, dict):
                        text_list = message.get("text", [""])
                        if text_list and isinstance(text_list, list) and len(text_list) > 0:
                            output = text_list[0]
                        else:
                            output = ""
                    else:
                        output = ""
                else:
                    output = ""
                return {"model": "spark", "output": output}
        except Exception as e:
            raise ValueError(f"调用讯飞星火API失败: {str(e)}") 