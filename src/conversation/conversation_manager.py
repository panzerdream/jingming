import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import get_logger

logger = get_logger()


class ConversationManager:
    def __init__(self, memory_key="chat_history"):
        self.memory_key = memory_key
        self.history = []
        logger.info("ConversationManager initialized")
    
    def add_message(self, role, content):
        """添加消息到会话历史"""
        try:
            self.history.append({"role": role, "content": content})
            logger.debug(f"Added {role} message: {content[:50]}...")
        except Exception as e:
            logger.error(f"Failed to add message: {e}")
    
    def get_history(self):
        """获取会话历史"""
        try:
            logger.debug(f"Retrieved conversation history with {len(self.history)} messages")
            return self.history
        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return []
    
    def get_history_str(self):
        """获取会话历史字符串"""
        try:
            history_str = ""
            for message in self.history:
                role = message.get("role", "unknown")
                content = message.get("content", "")
                history_str += f"{role}: {content}\n"
            
            logger.debug(f"Formatted history string length: {len(history_str)}")
            return history_str
            
        except Exception as e:
            logger.error(f"Failed to get history string: {e}")
            return ""
    
    def clear_history(self):
        """清空会话历史"""
        try:
            self.history = []
            logger.info("Conversation history cleared")
        except Exception as e:
            logger.error(f"Failed to clear history: {e}")
    
    def get_context(self, query, retrieved_docs):
        """构建上下文"""
        logger.debug(f"Building context for query: {query[:50]}...")
        
        try:
            # 构建检索到的文档上下文
            docs_context = "\n".join([doc.page_content for doc in retrieved_docs])
            
            # 构建会话历史上下文
            history_context = self.get_history_str()
            
            # 组合上下文
            context = f"检索到的相关信息：\n{docs_context}\n"
            if history_context:
                context += f"\n会话历史：\n{history_context}\n"
            
            logger.debug(f"Context built, length: {len(context)}")
            return context
            
        except Exception as e:
            logger.error(f"Failed to build context: {e}")
            return f"检索到的相关信息：\n{''.join([doc.page_content for doc in retrieved_docs])}\n"
