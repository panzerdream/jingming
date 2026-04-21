import logging
import sys
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
import json
from typing import Dict, Any, Optional


class StructuredLogger:
    """结构化日志记录器"""
    
    def __init__(self, name: str = "agent_rag", log_dir: str = "logs"):
        self.name = name
        self.log_dir = log_dir
        
        # 确保日志目录存在
        os.makedirs(log_dir, exist_ok=True)
        
        # 创建日志记录器
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """设置日志处理器"""
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器（按大小轮转）
        log_file = os.path.join(self.log_dir, f"{self.name}.log")
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # JSON 日志处理器（用于结构化日志）
        json_log_file = os.path.join(self.log_dir, f"{self.name}_structured.json")
        json_handler = RotatingFileHandler(
            json_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        json_handler.setLevel(logging.INFO)
        json_handler.setFormatter(JsonFormatter())
        self.logger.addHandler(json_handler)
    
    def debug(self, message: str, **kwargs):
        """调试级别日志"""
        self.logger.debug(self._format_message(message, **kwargs))
    
    def info(self, message: str, **kwargs):
        """信息级别日志"""
        self.logger.info(self._format_message(message, **kwargs))
    
    def warning(self, message: str, **kwargs):
        """警告级别日志"""
        self.logger.warning(self._format_message(message, **kwargs))
    
    def error(self, message: str, **kwargs):
        """错误级别日志"""
        self.logger.error(self._format_message(message, **kwargs))
    
    def critical(self, message: str, **kwargs):
        """严重级别日志"""
        self.logger.critical(self._format_message(message, **kwargs))
    
    def log_query(self, query: str, response: str, retrieved_docs: list, 
                  processing_time: float, **kwargs):
        """记录查询处理日志"""
        log_data = {
            "query": query,
            "response": response[:500] if response else "",  # 截断长响应
            "retrieved_docs_count": len(retrieved_docs),
            "processing_time_seconds": processing_time,
            "retrieved_docs_preview": [doc.page_content[:100] + "..." for doc in retrieved_docs[:3]],
            **kwargs
        }
        self.info(f"Query processed: {query[:50]}...", **log_data)
    
    def log_tool_usage(self, tool_name: str, input_text: str, result: str, 
                       success: bool, **kwargs):
        """记录工具使用日志"""
        log_data = {
            "tool_name": tool_name,
            "input_text": input_text,
            "result_preview": result[:200] if result else "",
            "success": success,
            **kwargs
        }
        self.info(f"Tool used: {tool_name}", **log_data)
    
    def log_vector_store_operation(self, operation: str, document_count: int = 0, 
                                   success: bool = True, **kwargs):
        """记录向量存储操作日志"""
        log_data = {
            "operation": operation,
            "document_count": document_count,
            "success": success,
            **kwargs
        }
        self.info(f"Vector store {operation}", **log_data)
    
    def log_api_call(self, endpoint: str, status_code: int, response_time: float, 
                     success: bool, **kwargs):
        """记录API调用日志"""
        log_data = {
            "endpoint": endpoint,
            "status_code": status_code,
            "response_time_seconds": response_time,
            "success": success,
            **kwargs
        }
        self.info(f"API call to {endpoint}", **log_data)
    
    def _format_message(self, message: str, **kwargs) -> str:
        """格式化日志消息"""
        if kwargs:
            extra_info = " ".join([f"{k}={v}" for k, v in kwargs.items()])
            return f"{message} | {extra_info}"
        return message


class JsonFormatter(logging.Formatter):
    """JSON格式日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON"""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加额外字段
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        return json.dumps(log_data, ensure_ascii=False)


# 全局日志记录器实例
_logger_instance = None


def get_logger(name: str = "agent_rag", log_dir: str = "logs") -> StructuredLogger:
    """获取全局日志记录器实例"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = StructuredLogger(name, log_dir)
    return _logger_instance


# 便捷函数
def debug(message: str, **kwargs):
    get_logger().debug(message, **kwargs)

def info(message: str, **kwargs):
    get_logger().info(message, **kwargs)

def warning(message: str, **kwargs):
    get_logger().warning(message, **kwargs)

def error(message: str, **kwargs):
    get_logger().error(message, **kwargs)

def critical(message: str, **kwargs):
    get_logger().critical(message, **kwargs)