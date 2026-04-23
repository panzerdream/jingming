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
        
        # 更激进的优化参数
        payload = {
            "model": model_name,
            "messages": messages,
            "max_tokens": int(os.getenv("MAX_RESPONSE_TOKENS", "150")),  # 进一步减少
            "temperature": float(os.getenv("TEMPERATURE", "0.2")),  # 进一步降低
            "stream": False
        }
        
        # 更短的超时时间
        timeout = int(os.getenv("API_TIMEOUT", "20"))
        
        logger.debug(f"Optimized API call to {api_url}, model: {model_name}, prompt length: {len(optimized_prompt)}")
        start_time = time.time()
        
        try:
            # 优化4: 减少超时时间
            response = requests.post(
                api_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=timeout  # 使用配置的超时时间
            )
            response_time = time.time() - start_time
            
            # 严格超时检查：即使requests没有抛出异常，如果响应时间超过超时设置，也视为超时
            if response_time > timeout:
                logger.warning(f"API响应时间超过超时设置 ({response_time:.2f}s > {timeout}s)，使用快速回复", 
                             api_url=api_url, response_time=response_time, timeout=timeout)
                metrics.record_api_call(api_url, response.status_code, response_time, success=False)
                return self._get_fallback_response(prompt)
            
            response.raise_for_status()
            result = response.json()
            
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # 记录API调用指标
            metrics.record_api_call(api_url, response.status_code, response_time, success=True)
            logger.info(f"Optimized API call successful in {response_time:.2f}s, response length: {len(content)}")
            
            return content
            
        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            logger.warning(f"API调用超时 ({timeout}s)，使用快速回复", api_url=api_url, response_time=response_time)
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
        # 优化 5: 压缩上下文，但保留更多信息
        compressed_context = self._compress_context(context, max_length=1200)
        
        # 检查是否包含工具结果
        if "工具执行结果:" in compressed_context:
            # 使用工具专用的系统消息
            system_message = "你是星露谷导游景明。用户使用了计算工具，工具执行结果是数字。请直接回答结果，并做简要说明。"
            logger.debug(f"检测到工具结果，使用专用系统消息")
        else:
            # 优化 6: 使用更清晰的系统消息，不暴露检索过程
            system_message = """你是星露谷导游景明，对星露谷物语了如指掌。
- 请直接、自然地回答问题，就像你在和朋友聊天一样
- 不要提及"资料"、"信息"、"检索"、"查询"等词汇
- 不要说"根据提供的信息"、"在我整理的资料中"这类话
- 如果知道答案，就直接回答，好像这是你的知识一样
- 如果不知道，就友好地说不知道
- 回答要完整，控制在 200 字以内，确保话说完"""
            logger.debug(f"未检测到工具结果，使用通用系统消息")
        
        logger.debug(f"压缩后的上下文内容：\n{compressed_context[:500]}...")
        
        # 优化 7: 使用更自然的提示模板，不暴露检索过程
        if "工具执行结果:" in compressed_context:
            # 工具查询的提示模板
            prompt = f"""工具执行结果：
{compressed_context.split('工具执行结果:')[1].strip()}

问题：{query}

回答："""
        else:
            # 普通查询的提示模板 - 自然对话版本
            prompt = f"""参考内容：
{compressed_context}

问题：{query}

回答："""
        
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
        
        # 检查是否包含工具结果
        tool_result_marker = "工具执行结果:"
        if tool_result_marker in context:
            # 优先保留工具结果部分
            marker_index = context.find(tool_result_marker)
            
            # 计算工具结果部分需要保留的长度
            # 工具结果部分通常不长，我们保留标记后的200个字符
            tool_result_section = context[marker_index:marker_index + 300]  # 标记+结果
            
            # 剩余长度用于其他上下文
            remaining_length = max_length - len(tool_result_section) - 20  # 留一些空间给分隔符
            
            if remaining_length > 100:
                # 从开头取一部分上下文
                start_part = context[:remaining_length // 2]
                end_part = context[-remaining_length // 2:] if len(context) > remaining_length // 2 else ""
                
                compressed = f"{start_part}\n...\n{tool_result_section}"
                if end_part:
                    compressed += f"\n...\n{end_part}"
            else:
                # 如果空间不够，只保留工具结果
                compressed = tool_result_section
            
            logger.debug(f"上下文从 {len(context)} 字符压缩到 {len(compressed)} 字符（保留工具结果）")
            return compressed
        
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