import requests
import json
import time
from typing import Optional

# 导入日志模块
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import get_logger
from utils.monitor import get_metrics_collector

logger = get_logger()
metrics = get_metrics_collector()


class OptimizedBailianAPI:
    """优化版的阿里云百炼API调用器"""
    
    def __init__(self, api_key: str, api_url: str):
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
            logger.info("OptimizedBailianAPI initialized with performance optimizations")
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def generate(self, prompt: str, model_name: str, temperature: float = 0.3, 
                 max_tokens: int = 500, system_message: Optional[str] = None) -> str:
        """优化版的API调用 - 减少响应时间"""
        # 构建完整的API URL
        api_url = f"{self.api_url}/chat/completions"
        
        # 优化1: 压缩提示词，减少token数量
        optimized_prompt = self._optimize_prompt(prompt, max_tokens)
        
        messages = []
        
        # 优化2: 限制系统消息长度
        if system_message:
            messages.append({
                "role": "system",
                "content": system_message[:200]  # 限制系统消息长度
            })
        
        messages.append({
            "role": "user",
            "content": optimized_prompt
        })
        
        # 优化3: 调整参数以加快响应
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
            # 优化4: 减少超时时间
            response = requests.post(
                api_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=15  # 从30秒减少到15秒
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
            logger.warning(f"API调用超时 (15s)，使用快速回复", api_url=api_url, response_time=response_time)
            return self._get_fallback_response(prompt)
            
        except requests.RequestException as e:
            response_time = time.time() - start_time
            error_msg = f"API调用失败: {e}"
            
            status_code = e.response.status_code if hasattr(e, 'response') and e.response else 0
            metrics.record_api_call(api_url, status_code, response_time, success=False)
            logger.error(error_msg, api_url=api_url, error=str(e), response_time=response_time)
            
            return self._get_fallback_response(prompt)
            
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f"API调用发生意外错误: {e}"
            logger.error(error_msg, api_url=api_url, error=str(e), response_time=response_time)
            return self._get_fallback_response(prompt)
    
    def generate_with_context(self, query: str, context: str, model_name: str, 
                             temperature: float = 0.3, max_tokens: int = 300) -> str:
        """优化版的带上下文文本生成"""
        # 优化5: 压缩上下文，只保留最相关的部分
        compressed_context = self._compress_context(context, max_length=800)
        
        # 优化6: 使用更简洁的系统消息
        system_message = "你是星露谷导游景明。请用1-3句话简洁回答，保持热情但简短。"
        
        # 优化7: 使用更简洁的提示模板
        prompt = f"""信息：
{compressed_context}

问题：{query}

请简洁回答："""
        
        logger.debug(f"Optimized context generation, query: '{query[:30]}...', context length: {len(compressed_context)}")
        
        return self.generate(prompt, model_name, temperature, max_tokens, system_message)
    
    def _optimize_prompt(self, prompt: str, max_tokens: int) -> str:
        """优化提示词，减少不必要的token"""
        # 如果提示词太长，进行截断
        if len(prompt) > max_tokens * 3:  # 粗略估计：1个token ≈ 3个字符
            logger.debug(f"提示词过长 ({len(prompt)}字符)，进行截断")
            return prompt[:max_tokens * 3] + "..."
        return prompt
    
    def _compress_context(self, context: str, max_length: int = 800) -> str:
        """压缩上下文，保留关键信息"""
        if len(context) <= max_length:
            return context
        
        # 简单压缩策略：取开头和结尾部分
        half = max_length // 2
        compressed = context[:half] + "\n...\n" + context[-half:]
        logger.debug(f"上下文从 {len(context)} 字符压缩到 {len(compressed)} 字符")
        return compressed
    
    def _get_fallback_response(self, query: str) -> str:
        """获取备用回复（当API调用失败或超时时）"""
        # 针对常见查询类型的快速回复
        fallback_responses = {
            "计算": f"根据计算：{query.replace('计算', '').strip()} 需要具体运算。",
            "时间": "当前时间需要查询系统时钟。",
            "搜索": f"关于'{query}'的信息，建议查阅星露谷Wiki。",
            "状态": "系统运行正常。",
            "你好": "你好！我是星露谷助手景明。",
            "谢谢": "不客气！随时为您服务。"
        }
        
        # 检查查询是否包含关键词
        query_lower = query.lower()
        for key in fallback_responses:
            if key in query or key in query_lower:
                return fallback_responses[key]
        
        # 通用快速回复
        quick_replies = [
            "已收到您的查询。",
            "正在处理您的请求。",
            "这个问题很有趣！",
            "让我想想...",
            "好的，我了解了。"
        ]
        
        import random
        return random.choice(quick_replies)


# 保持向后兼容的别名
BailianAPI = OptimizedBailianAPI