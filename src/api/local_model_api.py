import json
import time
import requests
from typing import Optional, Dict, Any

# 导入日志模块
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import get_logger
from utils.monitor import get_metrics_collector

logger = get_logger()
metrics = get_metrics_collector()


class LocalModelAPI:
    """本地模型API（使用Ollama）"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model_name: str = "qwen3.5:9b"):
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self.headers = {
            "Content-Type": "application/json"
        }
        logger.info(f"LocalModelAPI initialized with model: {model_name}")
    
    def generate(self, prompt: str, model_name: Optional[str] = None, 
                 temperature: float = 0.7, max_tokens: int = 1000, 
                 system_message: Optional[str] = None) -> str:
        """调用本地模型生成文本"""
        model = model_name or self.model_name
        api_url = f"{self.base_url}/api/generate"
        
        # 构建消息
        messages = []
        if system_message:
            messages.append({
                "role": "system",
                "content": system_message
            })
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system_message or "",
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        logger.debug(f"Local API call to {api_url}, model: {model}, prompt length: {len(prompt)}")
        start_time = time.time()
        
        try:
            response = requests.post(
                api_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=60  # 本地调用，设置较长的超时时间
            )
            response_time = time.time() - start_time
            
            response.raise_for_status()
            result = response.json()
            
            content = result.get("response", "")
            
            # 记录API调用指标
            metrics.record_api_call(api_url, response.status_code, response_time, success=True)
            logger.info(f"Local API call successful in {response_time:.2f}s, response length: {len(content)}")
            
            return content
            
        except requests.RequestException as e:
            response_time = time.time() - start_time
            error_msg = f"本地API调用失败: {e}"
            
            # 记录失败指标
            status_code = e.response.status_code if hasattr(e, 'response') and e.response else 0
            metrics.record_api_call(api_url, status_code, response_time, success=False)
            logger.error(error_msg, api_url=api_url, error=str(e), response_time=response_time)
            
            return "本地模型调用失败，请检查Ollama服务是否运行"
    
    def generate_with_context(self, query: str, context: str, model_name: Optional[str] = None) -> str:
        """结合上下文生成回复"""
        # 构建包含上下文的提示
        prompt = f"""基于以下上下文信息回答问题：

{context}

问题：{query}

请根据上下文提供准确、有用的回答。如果上下文信息不足，请说明。"""
        
        return self.generate(prompt, model_name)
    
    def chat_completion(self, messages: list, model_name: Optional[str] = None) -> str:
        """聊天补全接口（兼容OpenAI格式）"""
        model = model_name or self.model_name
        api_url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        
        logger.debug(f"Local chat API call to {api_url}, model: {model}")
        start_time = time.time()
        
        try:
            response = requests.post(
                api_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=60
            )
            response_time = time.time() - start_time
            
            response.raise_for_status()
            result = response.json()
            
            content = result.get("message", {}).get("content", "")
            
            metrics.record_api_call(api_url, response.status_code, response_time, success=True)
            logger.info(f"Local chat API successful in {response_time:.2f}s")
            
            return content
            
        except requests.RequestException as e:
            response_time = time.time() - start_time
            error_msg = f"本地聊天API调用失败: {e}"
            
            status_code = e.response.status_code if hasattr(e, 'response') and e.response else 0
            metrics.record_api_call(api_url, status_code, response_time, success=False)
            logger.error(error_msg, api_url=api_url, error=str(e), response_time=response_time)
            
            return "本地聊天模型调用失败"


def get_local_model_api(base_url: str = "http://localhost:11434", model_name: str = "qwen3.5:9b") -> LocalModelAPI:
    """获取本地模型API实例"""
    return LocalModelAPI(base_url, model_name)