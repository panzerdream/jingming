"""
Redis 连接管理器
负责管理 Redis 连接、会话存储和消息历史
"""
import redis
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
from .logger import get_logger

logger = get_logger()


class RedisManager:
    """Redis 连接和会话管理器"""
    
    def __init__(self, host='localhost', port=6379, db=0, password=None,
                 session_ttl=1800, memory_ttl=604800):
        """
        初始化 Redis 连接
        
        Args:
            host: Redis 主机地址
            port: Redis 端口
            db: Redis 数据库编号
            password: Redis 密码（可选）
            session_ttl: 会话过期时间（秒），默认 30 分钟
            memory_ttl: 长期记忆过期时间（秒），默认 7 天
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.session_ttl = session_ttl
        self.memory_ttl = memory_ttl
        
        # 连接池
        self.pool = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,
            max_connections=50
        )
        
        # Redis 客户端
        self.client = redis.Redis(connection_pool=self.pool)
        
        # 测试连接
        try:
            self.client.ping()
            logger.info(f"Redis connection established: {host}:{port}")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
        
        logger.info(f"RedisManager initialized with session_ttl={session_ttl}s, memory_ttl={memory_ttl}s")
    
    def create_session(self, session_id: str, user_id: str) -> bool:
        """
        创建新会话
        
        Args:
            session_id: 会话 ID
            user_id: 用户 ID
            
        Returns:
            bool: 创建成功返回 True
        """
        try:
            session_key = f"session:{session_id}"
            session_data = {
                "user_id": user_id,
                "created_at": str(int(time.time())),
                "updated_at": str(int(time.time())),
                "message_count": "0"
            }
            
            # 使用 pipeline 批量操作
            pipe = self.client.pipeline()
            pipe.hset(session_key, mapping=session_data)
            pipe.expire(session_key, self.session_ttl)
            pipe.execute()
            
            logger.debug(f"Session created: {session_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create session {session_id}: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, str]]:
        """
        获取会话信息
        
        Args:
            session_id: 会话 ID
            
        Returns:
            dict: 会话信息，不存在返回 None
        """
        try:
            session_key = f"session:{session_id}"
            session_data = self.client.hgetall(session_key)
            
            if session_data:
                # 更新最后访问时间
                self.client.hset(session_key, "updated_at", str(int(time.time())))
                # 刷新 TTL
                self.client.expire(session_key, self.session_ttl)
                return session_data
            else:
                logger.debug(f"Session not found: {session_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """
        删除会话及其所有数据
        
        Args:
            session_id: 会话 ID
            
        Returns:
            bool: 删除成功返回 True
        """
        try:
            pipe = self.client.pipeline()
            # 删除会话信息
            pipe.delete(f"session:{session_id}")
            # 删除消息历史
            pipe.delete(f"session:{session_id}:messages")
            # 删除长期记忆索引
            pipe.delete(f"session:{session_id}:memory_index")
            pipe.execute()
            
            logger.info(f"Session deleted: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    def add_message(self, session_id: str, role: str, content: str) -> bool:
        """
        添加消息到会话历史
        
        Args:
            session_id: 会话 ID
            role: 角色（user/assistant）
            content: 消息内容
            
        Returns:
            bool: 添加成功返回 True
        """
        try:
            message_key = f"session:{session_id}:messages"
            message_data = {
                "role": role,
                "content": content,
                "timestamp": str(int(time.time()))
            }
            
            # 添加到列表
            pipe = self.client.pipeline()
            pipe.rpush(message_key, json.dumps(message_data))
            # 限制消息数量（最近 50 条）
            pipe.ltrim(message_key, -50, -1)
            # 刷新 TTL
            pipe.expire(message_key, self.session_ttl)
            # 更新会话的 message_count
            pipe.hincrby(f"session:{session_id}", "message_count", 1)
            pipe.hset(f"session:{session_id}", "updated_at", str(int(time.time())))
            pipe.expire(f"session:{session_id}", self.session_ttl)
            pipe.execute()
            
            logger.debug(f"Message added to session {session_id}: {role}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add message to session {session_id}: {e}")
            return False
    
    def get_messages(self, session_id: str, limit: int = 20) -> List[Dict[str, str]]:
        """
        获取会话历史消息
        
        Args:
            session_id: 会话 ID
            limit: 获取最近 N 条消息
            
        Returns:
            list: 消息列表
        """
        try:
            message_key = f"session:{session_id}:messages"
            messages = self.client.lrange(message_key, -limit, -1)
            
            # 解析 JSON
            result = [json.loads(msg) for msg in messages]
            
            logger.debug(f"Retrieved {len(result)} messages from session {session_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get messages from session {session_id}: {e}")
            return []
    
    def clear_messages(self, session_id: str) -> bool:
        """
        清空会话消息历史
        
        Args:
            session_id: 会话 ID
            
        Returns:
            bool: 清空成功返回 True
        """
        try:
            message_key = f"session:{session_id}:messages"
            self.client.delete(message_key)
            self.client.hset(f"session:{session_id}", "message_count", "0")
            
            logger.info(f"Messages cleared for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear messages for session {session_id}: {e}")
            return False
    
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
    
    def add_memory_index(self, session_id: str, memory_id: str) -> bool:
        """
        添加长期记忆索引
        
        Args:
            session_id: 会话 ID
            memory_id: 向量存储中的文档 ID
            
        Returns:
            bool: 添加成功返回 True
        """
        try:
            index_key = f"session:{session_id}:memory_index"
            self.client.sadd(index_key, memory_id)
            self.client.expire(index_key, self.memory_ttl)
            
            logger.debug(f"Memory index added: {memory_id} for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add memory index: {e}")
            return False
    
    def get_memory_index(self, session_id: str) -> List[str]:
        """
        获取长期记忆索引
        
        Args:
            session_id: 会话 ID
            
        Returns:
            list: 记忆 ID 列表
        """
        try:
            index_key = f"session:{session_id}:memory_index"
            memory_ids = self.client.smembers(index_key)
            
            logger.debug(f"Retrieved {len(memory_ids)} memory indices for session {session_id}")
            return list(memory_ids)
            
        except Exception as e:
            logger.error(f"Failed to get memory index: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取 Redis 统计信息
        
        Returns:
            dict: 统计信息
        """
        try:
            info = self.client.info()
            
            # 获取会话数量
            session_keys = len(self.client.keys("session:*"))
            
            return {
                "connected": True,
                "host": self.host,
                "port": self.port,
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "session_count": session_keys,
                "uptime_seconds": info.get("uptime_in_seconds", 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get Redis stats: {e}")
            return {
                "connected": False,
                "error": str(e)
            }
    
    def close(self):
        """关闭 Redis 连接"""
        try:
            self.client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Failed to close Redis connection: {e}")


# 全局 Redis 管理器实例
_redis_manager = None


def get_redis_manager() -> Optional[RedisManager]:
    """获取 Redis 管理器单例"""
    global _redis_manager
    
    if _redis_manager is None:
        # 从环境变量加载配置
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_db = int(os.getenv('REDIS_DB', 0))
        redis_password = os.getenv('REDIS_PASSWORD') or None
        session_ttl = int(os.getenv('REDIS_SESSION_TTL', 1800))
        memory_ttl = int(os.getenv('REDIS_MEMORY_TTL', 604800))
        
        try:
            _redis_manager = RedisManager(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                session_ttl=session_ttl,
                memory_ttl=memory_ttl
            )
        except Exception as e:
            logger.error(f"Failed to initialize Redis manager: {e}")
            return None
    
    return _redis_manager


def init_redis_manager(host='localhost', port=6379, db=0, password=None,
                       session_ttl=1800, memory_ttl=604800) -> RedisManager:
    """初始化 Redis 管理器"""
    global _redis_manager
    
    _redis_manager = RedisManager(
        host=host,
        port=port,
        db=db,
        password=password,
        session_ttl=session_ttl,
        memory_ttl=memory_ttl
    )
    
    return _redis_manager
