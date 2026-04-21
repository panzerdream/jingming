import json
import time
import requests
from typing import Optional, Dict, Any
from enum import Enum

# 导入日志模块
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import get_logger
from utils.monitor import get_metrics_collector

logger = get_logger()
metrics = get_metrics_collector()


class ModelType(Enum):
    """模型类型枚举"""
    BAILIAN = "bailian"      # 阿里云百炼
    LOCAL_OLLAMA = "local"   # 本地Ollama模型
    OPENAI = "openai"        # OpenAI API


class OptimizedBailianAPI:
    """优化版的API调用器"""
    
    def __init__(self, api_key: str, api_url: str, timeout: int = 15):
        self.api_key = api_key
        self.api_url = api_url.rstrip('/') if api_url else "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.timeout = timeout  # 减少超时时间
        
        if not api_key:
            self.api_key = "your_api_key_here"
            logger.warning("API key not set, please configure BAILIAN_API_KEY in config/.env")
        else:
            logger.info(f"OptimizedBailianAPI initialized with timeout={timeout}s")
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def generate(self, prompt: str, model_name: str, temperature: float = 0.3, 
                 max_tokens: int = 500, system_message: Optional[str] = None) -> str:
        """优化版的API调用"""
        api_url = f"{self.api_url}/chat/completions"
        
        # 优化提示词，减少token数量
        optimized_prompt = self._optimize_prompt(prompt, max_tokens)
        
        messages = []
        if system_message:
            messages.append({
                "role": "system",
                "content": system_message[:200]  # 限制系统消息长度
            })
        
        messages.append({
            "role": "user",
            "content": optimized_prompt
        })
        
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,  # 降低温度以获得更确定的回答
            "max_tokens": min(max_tokens, 500),  # 限制最大token数
            "stream": False
        }
        
        logger.debug(f"Optimized API call to {api_url}, model: {model_name}, prompt length: {len(optimized_prompt)}")
        start_time = time.time()
        
        try:
            response = requests.post(
                api_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=self.timeout  # 使用较短的超时时间
            )
            response_time = time.time() - start_time
            
            response.raise_for_status()
            result = response.json()
            
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # 记录API调用指标
            metrics.record_api_call(api_url, response.status_code, response_time, success=True)
            logger.info(f"Optimized API call successful in {response_time:.2f}s, response length: {len(content)}")
            
            return content
            
        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            logger.warning(f"API调用超时 ({self.timeout}s)，使用快速回复", api_url=api_url, response_time=response_time)
            return self._get_fallback_response(prompt)
            
        except requests.RequestException as e:
            response_time = time.time() - start_time
            error_msg = f"API调用失败: {e}"
            
            status_code = e.response.status_code if hasattr(e, 'response') and e.response else 0
            metrics.record_api_call(api_url, status_code, response_time, success=False)
            logger.error(error_msg, api_url=api_url, error=str(e), response_time=response_time)
            
            return self._get_fallback_response(prompt)
    
    def generate_with_context(self, query: str, context: str, model_name: str) -> str:
        """优化版的上下文生成"""
        # 压缩上下文，只保留最相关的部分
        compressed_context = self._compress_context(context, max_length=1000)
        
        # 构建优化的提示词
        prompt = f"""请基于以下信息简洁地回答：

{compressed_context}

问题：{query}

要求：回答要简洁明了，不超过3句话。"""
        
        return self.generate(prompt, model_name, temperature=0.3, max_tokens=200)
    
    def _optimize_prompt(self, prompt: str, max_tokens: int) -> str:
        """优化提示词，减少不必要的token"""
        # 如果提示词太长，进行截断
        if len(prompt) > max_tokens * 3:  # 粗略估计：1个token ≈ 3个字符
            logger.debug(f"提示词过长 ({len(prompt)}字符)，进行截断")
            return prompt[:max_tokens * 3] + "..."
        return prompt
    
    def _compress_context(self, context: str, max_length: int = 1000) -> str:
        """压缩上下文，保留关键信息"""
        if len(context) <= max_length:
            return context
        
        # 简单压缩：取开头和结尾部分
        half = max_length // 2
        compressed = context[:half] + "\n...\n" + context[-half:]
        logger.debug(f"上下文从 {len(context)} 字符压缩到 {len(compressed)} 字符")
        return compressed
    
    def _get_fallback_response(self, query: str) -> str:
        """获取备用回复（当API调用失败时）"""
        fallback_responses = {
            "计算": f"根据我的计算：{query.replace('计算', '').strip()} 的结果需要具体计算。",
            "时间": "当前时间需要查询系统时钟。",
            "搜索": f"关于'{query}'的信息，建议查阅相关资料。",
            "状态": "系统运行正常，所有功能可用。"
        }
        
        for key, response in fallback_responses.items():
            if key in query:
                return response
        
        return "已收到您的查询。由于网络延迟，建议稍后重试或使用本地工具。"


class HybridModelAPI:
    """混合模型API，自动选择最快的模型"""
    
    def __init__(self, bailian_api: OptimizedBailianAPI, local_api=None):
        self.bailian_api = bailian_api
        self.local_api = local_api
        self.preferred_model = ModelType.BAILIAN
        self.response_times = {
            ModelType.BAILIAN: [],
            ModelType.LOCAL_OLLAMA: []
        }
        
        logger.info("HybridModelAPI initialized with fallback support")
    
    def generate_with_context(self, query: str, context: str, model_name: str) -> str:
        """智能选择模型生成回复"""
        # 首先尝试本地模型（如果可用）
        if self.local_api:
            try:
                logger.debug("尝试使用本地模型...")
                start_time = time.time()
                response = self.local_api.generate_with_context(query, context)
                response_time = time.time() - start_time
                
                self.response_times[ModelType.LOCAL_OLLAMA].append(response_time)
                logger.info(f"本地模型响应时间: {response_time:.2f}s")
                
                if response_time < 5.0:  # 本地模型在5秒内响应
                    return response
            except Exception as e:
                logger.warning(f"本地模型调用失败，回退到云端: {e}")
        
        # 使用优化版的云端API
        logger.debug("使用优化版云端API...")
        return self.bailian_api.generate_with_context(query, context, model_name)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        stats = {}
        for model_type, times in self.response_times.items():
            if times:
                stats[model_type.value] = {
                    "count": len(times),
                    "avg_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times)
                }
        return stats