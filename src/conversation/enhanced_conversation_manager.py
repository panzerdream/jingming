"""
增强的对话管理器
集成 Redis（短期记忆）和向量存储（长期记忆）
"""
import time
import uuid
import os
import sys
from typing import Dict, List, Optional, Any

# 导入日志模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import get_logger
from utils.redis_manager import get_redis_manager, RedisManager

logger = get_logger()


class EnhancedConversationManager:
    """增强的对话管理器 - 支持短期和长期记忆"""
    
    def __init__(self, vector_store_manager=None):
        """
        初始化增强的对话管理器
        
        Args:
            vector_store_manager: 向量存储管理器（用于长期记忆）
        """
        self.vector_store = vector_store_manager
        self.redis_manager: Optional[RedisManager] = None
        
        # 尝试初始化 Redis
        try:
            self.redis_manager = get_redis_manager()
            if self.redis_manager:
                logger.info("Redis manager initialized for enhanced conversation management")
            else:
                logger.warning("Redis manager not available, falling back to in-memory storage")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            logger.warning("Will use in-memory storage as fallback")
        
        # 内存存储（Redis 不可用时的 fallback）
        self.memory_storage = {}
        
        # 配置
        self.max_short_term_messages = 20  # 短期记忆最大消息数
        self.long_term_memory_threshold = 0.7  # 长期记忆重要性阈值
        self.long_term_memory_top_k = 3  # 长期记忆检索数量
        
        logger.info("EnhancedConversationManager initialized")
    
    def create_session(self, user_id: str = None) -> str:
        """
        创建新会话
        
        Args:
            user_id: 用户 ID（可选）
            
        Returns:
            str: 会话 ID
        """
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        
        if self.redis_manager:
            self.redis_manager.create_session(session_id, user_id or "anonymous")
        else:
            # Fallback to in-memory
            self.memory_storage[session_id] = {
                "user_id": user_id or "anonymous",
                "created_at": int(time.time()),
                "messages": []
            }
        
        logger.info(f"Session created: {session_id} for user {user_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话信息
        
        Args:
            session_id: 会话 ID
            
        Returns:
            dict: 会话信息，不存在返回 None
        """
        if self.redis_manager:
            return self.redis_manager.get_session(session_id)
        else:
            # Fallback to in-memory
            return self.memory_storage.get(session_id)
    
    def add_message(self, session_id: str, role: str, content: str) -> bool:
        """
        添加消息到会话
        
        Args:
            session_id: 会话 ID
            role: 角色（user/assistant）
            content: 消息内容
            
        Returns:
            bool: 添加成功返回 True
        """
        if self.redis_manager:
            return self.redis_manager.add_message(session_id, role, content)
        else:
            # Fallback to in-memory
            if session_id not in self.memory_storage:
                self.memory_storage[session_id] = {
                    "user_id": "anonymous",
                    "created_at": int(time.time()),
                    "messages": []
                }
            
            messages = self.memory_storage[session_id]["messages"]
            messages.append({
                "role": role,
                "content": content,
                "timestamp": int(time.time())
            })
            
            # 限制消息数量
            if len(messages) > self.max_short_term_messages:
                messages = messages[-self.max_short_term_messages:]
            
            self.memory_storage[session_id]["messages"] = messages
            return True
    
    def get_messages(self, session_id: str, limit: int = None) -> List[Dict[str, str]]:
        """
        获取会话历史消息
        
        Args:
            session_id: 会话 ID
            limit: 获取最近 N 条消息（None 则使用默认值）
            
        Returns:
            list: 消息列表
        """
        if limit is None:
            limit = self.max_short_term_messages
        
        if self.redis_manager:
            return self.redis_manager.get_messages(session_id, limit)
        else:
            # Fallback to in-memory
            if session_id not in self.memory_storage:
                return []
            
            messages = self.memory_storage[session_id]["messages"]
            return messages[-limit:]
    
    def get_messages_string(self, session_id: str, limit: int = 10) -> str:
        """
        获取会话历史消息的字符串格式
        
        Args:
            session_id: 会话 ID
            limit: 获取最近 N 条消息
            
        Returns:
            str: 格式化的历史消息字符串
        """
        messages = self.get_messages(session_id, limit)
        
        if not messages:
            return ""
        
        history_str = ""
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            history_str += f"{role}: {content}\n"
        
        return history_str
    
    def clear_messages(self, session_id: str) -> bool:
        """
        清空会话消息历史
        
        Args:
            session_id: 会话 ID
            
        Returns:
            bool: 清空成功返回 True
        """
        if self.redis_manager:
            return self.redis_manager.clear_messages(session_id)
        else:
            # Fallback to in-memory
            if session_id in self.memory_storage:
                self.memory_storage[session_id]["messages"] = []
                return True
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话 ID
            
        Returns:
            bool: 删除成功返回 True
        """
        if self.redis_manager:
            return self.redis_manager.delete_session(session_id)
        else:
            # Fallback to in-memory
            if session_id in self.memory_storage:
                del self.memory_storage[session_id]
                return True
            return False
    
    def search_long_term_memory(self, session_id: str, query: str, k: int = None) -> List[Any]:
        """
        从长期记忆中检索相关信息
        
        Args:
            session_id: 会话 ID
            query: 查询文本
            k: 检索数量
            
        Returns:
            list: 检索到的记忆
        """
        if not self.vector_store:
            logger.debug("Vector store not available, skipping long-term memory search")
            return []
        
        if k is None:
            k = self.long_term_memory_top_k
        
        try:
            # 从向量存储检索
            results = self.vector_store.search(query, k=k)
            
            logger.debug(f"Retrieved {len(results)} long-term memories for session {session_id}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search long-term memory: {e}")
            return []
    
    def save_to_long_term_memory(self, session_id: str, query: str, response: str, 
                                  importance_score: float = None) -> bool:
        """
        保存重要对话到长期记忆
        
        Args:
            session_id: 会话 ID
            query: 用户查询
            response: AI 回复
            importance_score: 重要性评分（可选，自动计算如果未提供）
            
        Returns:
            bool: 保存成功返回 True
        """
        if not self.vector_store:
            logger.debug("Vector store not available, skipping long-term memory save")
            return False
        
        try:
            # 如果没有提供重要性评分，自动计算
            if importance_score is None:
                importance_score = self._calculate_importance(query, response)
            
            # 如果重要性不够，不保存
            if importance_score < self.long_term_memory_threshold:
                logger.debug(f"Importance score {importance_score} below threshold, skipping")
                return False
            
            # 创建记忆文档
            memory_content = f"用户询问：{query}\nAI 回答：{response}"
            
            # 创建文档对象（LangChain 格式）
            from langchain.schema import Document
            memory_doc = Document(
                page_content=memory_content,
                metadata={
                    "session_id": session_id,
                    "query": query,
                    "response": response,
                    "importance_score": importance_score,
                    "timestamp": int(time.time()),
                    "type": "conversation_memory"
                }
            )
            
            # 添加到向量存储
            logger.info(f"Saving to long-term memory (importance: {importance_score:.2f})")
            
            if self.vector_store:
                # 使用新实现的 add_document 方法
                success = self.vector_store.add_document(memory_doc)
                if success:
                    logger.info("Memory document saved to vector store successfully")
                else:
                    logger.warning("Failed to save memory document to vector store")
            
            # 添加索引到 Redis
            if self.redis_manager:
                # 使用文档内容 hash 作为 ID
                import hashlib
                doc_id = hashlib.md5(memory_content.encode()).hexdigest()
                self.redis_manager.add_memory_index(session_id, doc_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save to long-term memory: {e}")
            return False
    
    def _calculate_importance(self, query: str, response: str) -> float:
        """
        计算对话的重要性评分
        
        Args:
            query: 用户查询
            response: AI 回复
            
        Returns:
            float: 重要性评分（0-1）
        """
        score = 0.5  # 基础分
        
        # 规则 1: 包含事实性信息 +0.2
        factual_keywords = ['是', '在', '有', '叫', '住', '工作', '喜欢', '需要', '可以', '会']
        if any(keyword in response for keyword in factual_keywords):
            score += 0.2
        
        # 规则 2: 回复长度适中 +0.1
        if 30 < len(response) < 300:
            score += 0.1
        
        # 规则 3: 包含数字或具体信息 +0.1
        import re
        if re.search(r'\d+', response):
            score += 0.1
        
        # 规则 4: 用户追问（包含"那"、"然后"等）+0.1
        if query.startswith(('那', '然后', '接着', '还有')):
            score += 0.1
        
        return min(score, 1.0)
    
    def get_context(self, session_id: str, query: str, retrieved_docs: List[Any]) -> str:
        """
        构建增强的上下文（短期记忆 + 长期记忆 + 检索文档）
        
        Args:
            session_id: 会话 ID
            query: 当前查询
            retrieved_docs: 从知识库检索到的文档
            
        Returns:
            str: 组合后的上下文
        """
        # 1. 获取短期记忆（最近对话）
        short_term_history = self.get_messages_string(session_id, self.max_short_term_messages)
        
        # 2. 检索长期记忆
        long_term_memories = self.search_long_term_memory(session_id, query)
        
        # 3. 构建上下文
        context_parts = []
        
        # 3.1 知识库检索文档
        if retrieved_docs:
            docs_context = "\n".join([doc.page_content for doc in retrieved_docs])
            context_parts.append(f"相关信息：\n{docs_context}")
        
        # 3.2 长期记忆
        if long_term_memories:
            memory_context = "\n".join([
                f"记忆：{doc.page_content}" 
                for doc in long_term_memories
            ])
            context_parts.append(f"历史记忆：\n{memory_context}")
        
        # 3.3 短期记忆
        if short_term_history:
            context_parts.append(f"对话历史：\n{short_term_history}")
        
        # 4. 组合上下文
        context = "\n\n".join(context_parts)
        
        logger.debug(f"Context built for session {session_id}: {len(context)} chars")
        return context
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取对话管理器统计信息
        
        Returns:
            dict: 统计信息
        """
        stats = {
            "redis_available": self.redis_manager is not None,
            "vector_store_available": self.vector_store is not None,
            "max_short_term_messages": self.max_short_term_messages,
            "long_term_memory_threshold": self.long_term_memory_threshold
        }
        
        if self.redis_manager:
            redis_stats = self.redis_manager.get_stats()
            stats["redis"] = redis_stats
        
        if not self.redis_manager:
            stats["memory_sessions"] = len(self.memory_storage)
        
        return stats


# 全局增强对话管理器实例
_enhanced_conversation_manager = None


def get_enhanced_conversation_manager(vector_store_manager=None) -> EnhancedConversationManager:
    """获取增强的对话管理器单例"""
    global _enhanced_conversation_manager
    
    if _enhanced_conversation_manager is None:
        _enhanced_conversation_manager = EnhancedConversationManager(vector_store_manager)
    
    return _enhanced_conversation_manager
