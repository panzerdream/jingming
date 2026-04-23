import os
import sys
import time
from dotenv import load_dotenv

# 添加当前目录到路径
sys.path.append(os.path.dirname(__file__))

from document_processing.markdown_processor import MarkdownProcessor
from vector_store.vector_store import VectorStoreManager
from api.bailian_api import OptimizedBailianAPI
from conversation.conversation_manager import ConversationManager
from conversation.enhanced_conversation_manager import EnhancedConversationManager
from tools.enhanced_tool_manager import get_tool_manager, should_use_tool, parse_tool_call, run_tool
from utils.logger import get_logger
from utils.monitor import get_metrics_collector, start_monitoring, get_system_summary, export_metrics

# GraphRAG 相关导入
try:
    from graph.graph_builder import KnowledgeGraphBuilder
    from graph.graph_retriever import GraphRetriever
    GRAPHRAG_AVAILABLE = True
except ImportError:
    GRAPHRAG_AVAILABLE = False
    KnowledgeGraphBuilder = None
    GraphRetriever = None

# 加载环境变量
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../config/.env'))

# 获取日志记录器
logger = get_logger()
metrics = get_metrics_collector()


class OptimizedAgentRAG:
    """优化版的AgentRAG系统"""
    
    def __init__(self):
        # 加载配置
        self.bailian_api_key = os.getenv('BAILIAN_API_KEY')
        self.bailian_api_url = os.getenv('BAILIAN_API_URL')
        
        # 使用绝对路径
        base_dir = os.path.dirname(os.path.dirname(__file__))
        self.vector_store_path = os.getenv('VECTOR_STORE_PATH', os.path.join(base_dir, 'data', 'vector_db'))
        self.knowledge_base_path = os.getenv('KNOWLEDGE_BASE_PATH', os.path.join(base_dir, 'data', 'knowledge'))
        
        self.model_name = os.getenv('MODEL_NAME', 'qwen-turbo')
        self.top_k = int(os.getenv('TOP_K', 5))
        self.chunk_size = int(os.getenv('CHUNK_SIZE', 1000))
        self.chunk_overlap = int(os.getenv('CHUNK_OVERLAP', 200))
        
        # 优化参数
        self.api_timeout = int(os.getenv('API_TIMEOUT', 30))  # 增加超时时间到 30 秒
        self.max_response_tokens = int(os.getenv('MAX_RESPONSE_TOKENS', 300))
        self.temperature = float(os.getenv('TEMPERATURE', 0.3))
        
        # GraphRAG 配置
        self.use_graphrag = os.getenv('USE_GRAPHRAG', 'true').lower() == 'true' and GRAPHRAG_AVAILABLE
        self.graph_k = int(os.getenv('GRAPH_TOP_K', 5))
        
        # Redis 和长期记忆配置
        self.use_enhanced_conversation = os.getenv('USE_ENHANCED_CONVERSATION', 'true').lower() == 'true'
        
        logger.info("Initializing OptimizedAgentRAG system", 
                   model_name=self.model_name, 
                   api_timeout=self.api_timeout,
                   max_tokens=self.max_response_tokens,
                   temperature=self.temperature,
                   use_graphrag=self.use_graphrag,
                   use_enhanced_conversation=self.use_enhanced_conversation)
        
        # 初始化模块
        self.markdown_processor = MarkdownProcessor(self.knowledge_base_path)
        self.vector_store_manager = VectorStoreManager(
            self.vector_store_path,
            api_key=self.bailian_api_key
        )
        
        # 使用优化版的 API
        self.bailian_api = OptimizedBailianAPI(self.bailian_api_key, self.bailian_api_url)
        
        # 初始化对话管理器（使用增强版或标准版）
        if self.use_enhanced_conversation:
            logger.info("Initializing EnhancedConversationManager with Redis support...")
            self.conversation_manager = EnhancedConversationManager(
                vector_store_manager=self.vector_store_manager
            )
        else:
            logger.info("Initializing standard ConversationManager...")
            self.conversation_manager = ConversationManager()
        
        self.tool_manager = get_tool_manager()
        
        # 初始化 GraphRAG（如果启用）
        if self.use_graphrag:
            logger.info("Initializing GraphRAG...")
            try:
                self.graph_builder = KnowledgeGraphBuilder()
                self.graph_builder.build_from_directory(self.knowledge_base_path)
                self.graph_retriever = GraphRetriever(self.graph_builder)
                logger.info(f"GraphRAG initialized: {self.graph_builder.get_stats()}")
            except Exception as e:
                logger.error(f"Failed to initialize GraphRAG: {e}")
                self.use_graphrag = False
                self.graph_builder = None
                self.graph_retriever = None
        else:
            self.graph_builder = None
            self.graph_retriever = None
        
        # 加载或创建向量存储
        self._initialize_vector_store()
        
        # 启动监控
        start_monitoring(interval=60)
        logger.info("System monitoring started")
    
    def _initialize_vector_store(self):
        """初始化向量存储"""
        if not os.path.exists(self.vector_store_path) or not os.listdir(self.vector_store_path):
            logger.info("Creating new vector store...")
            
            # 处理知识库文档
            documents = self.markdown_processor.process_all_documents()
            
            if documents:
                # 创建向量存储
                self.vector_store_manager.create_vector_store(
                    documents,
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap
                )
                logger.info(f"Vector store created with {len(documents)} documents")
            else:
                logger.warning("No documents found in knowledge base")
        else:
            logger.info("Loading existing vector store...")
            self.vector_store_manager.load_vector_store()
            logger.info("Vector store loaded successfully")
    
    def process_query(self, query, session_id=None):
        """优化版的查询处理（集成 GraphRAG 和 Redis 会话管理）
        
        Args:
            query: 用户查询
            session_id: 会话 ID（可选，用于 Redis 会话管理）
            
        Returns:
            str: AI 回复
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing query: {query[:50]}...")
            
            # 如果没有 session_id 且使用增强对话管理器，创建新会话
            actual_session_id = session_id
            if self.use_enhanced_conversation and isinstance(self.conversation_manager, EnhancedConversationManager):
                if not actual_session_id:
                    actual_session_id = self.conversation_manager.create_session()
                    logger.info(f"Created new session: {actual_session_id}")
            
            # 1. 向量检索
            retrieved_docs = self.vector_store_manager.search(query, k=self.top_k)
            logger.info(f"Retrieved {len(retrieved_docs)} relevant documents")
            
            # 2. GraphRAG 检索（如果启用）
            graph_results = None
            if self.use_graphrag and self.graph_retriever:
                try:
                    graph_results = self.graph_retriever.retrieve_related_entities(
                        query, k=self.graph_k
                    )
                    logger.info(f"GraphRAG retrieved {len(graph_results)} entities")
                except Exception as e:
                    logger.error(f"GraphRAG retrieval failed: {e}")
                    graph_results = None
            
            # 3. 构建增强的上下文（使用会话 ID）
            if actual_session_id and isinstance(self.conversation_manager, EnhancedConversationManager):
                context = self.conversation_manager.get_context(
                    actual_session_id, query, retrieved_docs
                )
            else:
                context = self._build_enhanced_context(query, retrieved_docs, graph_results)
            
            # 检查是否需要使用工具
            if should_use_tool(query):
                logger.info("Tool usage detected")
                # 解析工具调用
                tool_name, tool_params = parse_tool_call(query)
                if tool_name:
                    # 运行工具
                    tool_result = run_tool(tool_name, tool_params)
                    # 生成回复（结合工具结果）
                    response = self._generate_response_with_tool(query, context, tool_result)
                else:
                    # 生成回复（使用优化参数）
                    response = self.bailian_api.generate_with_context(
                        query, context, self.model_name,
                        temperature=self.temperature,
                        max_tokens=self.max_response_tokens
                    )
            else:
                # 生成回复（使用优化参数）
                response = self.bailian_api.generate_with_context(
                    query, context, self.model_name,
                    temperature=self.temperature,
                    max_tokens=self.max_response_tokens
                )
            
            # 计算处理时间
            processing_time = time.time() - start_time
            
            # 添加到会话历史（使用 session_id）
            if actual_session_id and isinstance(self.conversation_manager, EnhancedConversationManager):
                self.conversation_manager.add_message(actual_session_id, "user", query)
                self.conversation_manager.add_message(actual_session_id, "assistant", response)
                
                # 评估重要性，保存到长期记忆
                self.conversation_manager.save_to_long_term_memory(
                    actual_session_id, query, response
                )
            else:
                # 使用标准对话管理器
                self.conversation_manager.add_message("user", query)
                self.conversation_manager.add_message("assistant", response)
            
            # 记录指标
            metrics.record_query(query, processing_time, success=True)
            logger.log_query(query, response, retrieved_docs, processing_time)
            
            logger.info(f"Query processed in {processing_time:.2f}s")
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"处理查询时发生错误: {e}", query=query, error=str(e))
            metrics.record_query(query, processing_time, success=False)
            
            # 返回友好的错误信息
            return f"抱歉，处理您的查询时出现了问题。错误: {str(e)[:100]}"
    
    def _build_enhanced_context(self, query, vector_results, graph_results=None):
        """构建增强的上下文（结合向量检索和图检索结果）"""
        context_parts = []
        
        # 1. 添加向量检索结果
        if vector_results:
            docs_context = "\n".join([doc.page_content for doc in vector_results])
            context_parts.append(f"相关信息：\n{docs_context}")
        
        # 2. 添加 GraphRAG 检索结果
        if graph_results and len(graph_results) > 0:
            entity_info = []
            for entity in graph_results:
                name = entity.get('name', 'Unknown')
                entity_type = entity.get('type', 'unknown')
                attributes = entity.get('attributes', {})
                
                # 格式化属性
                attr_str = ", ".join([f"{k}: {v}" for k, v in list(attributes.items())[:3]])
                entity_info.append(f"- {name} ({entity_type}): {attr_str}")
            
            if entity_info:
                context_parts.append(f"相关实体：\n" + "\n".join(entity_info))
            
            # 尝试获取关系路径
            if len(graph_results) >= 2:
                try:
                    source_name = graph_results[0].get('name')
                    target_name = graph_results[1].get('name')
                    
                    if source_name and target_name:
                        path = self.graph_retriever.retrieve_relation_path(source_name, target_name)
                        if path and path.get('length', 0) > 0:
                            path_str = " → ".join([node['name'] for node in path['nodes']])
                            context_parts.append(f"关系路径：{path_str}")
                except Exception as e:
                    logger.debug(f"Failed to get relation path: {e}")
        
        # 3. 组合上下文
        context = "\n\n".join(context_parts)
        
        logger.debug(f"Enhanced context built: {len(context)} chars, {len(vector_results) if vector_results else 0} docs, {len(graph_results) if graph_results else 0} entities")
        return context
    
    def _generate_response_with_tool(self, query: str, context: str, tool_result: str) -> str:
        """结合工具结果生成回复（优化版）"""
        try:
            # 构建包含工具结果的上下文
            enhanced_context = f"{context}\n\n工具执行结果:\n{tool_result}"
            
            # 生成回复（使用优化参数）
            response = self.bailian_api.generate_with_context(
                query, enhanced_context, self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_response_tokens
            )
            
            # 在回复中注明使用了工具
            if "工具" not in response and "搜索" not in response and "计算" not in response:
                response = f"（基于工具查询）{response}"
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate response with tool: {e}")
            # 如果生成失败，返回工具结果
            return f"工具执行结果：{tool_result}"
    
    def clear_conversation(self):
        """清空会话历史"""
        self.conversation_manager.clear_history()
        logger.info("Conversation history cleared")
    
    def add_document(self, file_path):
        """添加文档到知识库"""
        try:
            import shutil
            
            # 复制文件到知识库目录
            filename = os.path.basename(file_path)
            dest_path = os.path.join(self.knowledge_base_path, filename)
            shutil.copy2(file_path, dest_path)
            
            # 处理新文档
            documents = self.markdown_processor.process_document(dest_path)
            
            if documents:
                # 添加到向量存储
                self.vector_store_manager.add_documents(documents)
                logger.info(f"Document added successfully: {filename}")
                return True
            else:
                logger.warning(f"No content extracted from document: {filename}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return False
    
    def get_system_status(self):
        """获取系统状态"""
        try:
            summary = get_system_summary()
            return summary
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {"error": str(e)}
    
    def export_metrics(self, filepath="metrics.json"):
        """导出指标"""
        return export_metrics(filepath)
    
    def get_graph_stats(self):
        """获取知识图谱统计信息"""
        if self.graph_builder:
            return self.graph_builder.get_stats()
        return {"available": False}
    
    def get_entity_info(self, entity_name: str):
        """获取实体详细信息"""
        if self.graph_retriever:
            return self.graph_retriever.get_entity_info(entity_name)
        return None
    
    def create_session(self, user_id: str = None):
        """创建新会话（仅当使用 EnhancedConversationManager 时）"""
        if isinstance(self.conversation_manager, EnhancedConversationManager):
            return self.conversation_manager.create_session(user_id)
        else:
            logger.warning("Standard ConversationManager does not support session management")
            return None
    
    def get_session_messages(self, session_id: str, limit: int = 20):
        """获取会话消息历史（仅当使用 EnhancedConversationManager 时）"""
        if isinstance(self.conversation_manager, EnhancedConversationManager):
            return self.conversation_manager.get_messages(session_id, limit)
        else:
            logger.warning("Standard ConversationManager does not support session management")
            return []
    
    def clear_session(self, session_id: str = None):
        """清空会话（支持指定 session_id 或全局清空）"""
        if session_id and isinstance(self.conversation_manager, EnhancedConversationManager):
            return self.conversation_manager.clear_messages(session_id)
        else:
            # 清空全局会话（标准行为）
            self.conversation_manager.clear_history()
            logger.info("Global conversation history cleared")
            return True
    
    def get_conversation_stats(self):
        """获取会话统计信息"""
        if isinstance(self.conversation_manager, EnhancedConversationManager):
            return self.conversation_manager.get_stats()
        return {
            "type": "standard",
            "available": True
        }
    
    def find_relation_path(self, source_name: str, target_name: str):
        """查找两个实体之间的关系路径"""
        if self.graph_retriever:
            return self.graph_retriever.retrieve_relation_path(source_name, target_name)
        return None


# 保持向后兼容
AgentRAG = OptimizedAgentRAG