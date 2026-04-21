import requests
import json
import time

# 导入日志模块
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import get_logger
from utils.monitor import get_metrics_collector

logger = get_logger()
metrics = get_metrics_collector()


class BailianAPI:
    def __init__(self, api_key, api_url):
        self.api_key = api_key
        # 确保API URL正确
        if api_url:
            if api_url.endswith('/'):
                self.api_url = api_url.rstrip('/')
            else:
                self.api_url = api_url
        else:
            # 默认API URL
            self.api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        
        # 确保API密钥存在
        if not api_key:
            self.api_key = "your_api_key_here"
            logger.warning("API key not set, please configure BAILIAN_API_KEY in config/.env")
        else:
            logger.info("BailianAPI initialized with provided API key")
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def generate(self, prompt, model_name, temperature=0.7, max_tokens=1000, system_message=None):
        """调用阿里云百炼API生成文本"""
        # 构建完整的API URL
        api_url = f"{self.api_url}/chat/completions"
        
        messages = []
        
        # 添加系统消息（如果有）
        if system_message:
            messages.append({
                "role": "system",
                "content": system_message
            })
        
        # 添加用户消息
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        logger.debug(f"API call to {api_url}, model: {model_name}, prompt length: {len(prompt)}")
        start_time = time.time()
        
        try:
            response = requests.post(
                api_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=30
            )
            response_time = time.time() - start_time
            
            response.raise_for_status()
            result = response.json()
            
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # 记录API调用指标
            metrics.record_api_call(api_url, response.status_code, response_time, success=True)
            logger.info(f"API call successful in {response_time:.2f}s, response length: {len(content)}")
            
            return content
            
        except requests.RequestException as e:
            response_time = time.time() - start_time
            error_msg = f"API调用失败: {e}"
            
            # 记录失败指标
            status_code = e.response.status_code if hasattr(e, 'response') and e.response else 0
            metrics.record_api_call(api_url, status_code, response_time, success=False)
            logger.error(error_msg, api_url=api_url, error=str(e), response_time=response_time)
            
            return "API调用失败，请稍后重试"
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f"API调用发生意外错误: {e}"
            logger.error(error_msg, api_url=api_url, error=str(e), response_time=response_time)
            return "API调用失败，请稍后重试"
    
    def generate_with_context(self, query, context, model_name, temperature=0.7, max_tokens=1000):
        """带上下文的文本生成"""
        # 系统消息 - 控制回答风格
        system_message = "你是景明，星露谷镇鹈鹕村的导游，请使用热情活泼的语言回答问题，保持轻松愉快的语气，就像星露谷游戏的风格一样。回答过程中请尽量避免用户感知到这是一个游戏，你要假扮自己确实是存在于游戏之中的角色。回答要具体、实用，并且与上下文相关。"
        
        prompt = f"基于以下上下文回答问题：\\n\\n{context}\\n\\n问题：{query}\\n\\n回答："
        
        logger.debug(f"Generating response with context, query: '{query[:50]}...', context length: {len(context)}")
        
        return self.generate(prompt, model_name, temperature, max_tokens, system_message)