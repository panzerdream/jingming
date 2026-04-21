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
from tools.enhanced_tool_manager import get_tool_manager, should_use_tool, parse_tool_call, run_tool
from utils.logger import get_logger
from utils.monitor import get_metrics_collector, start_monitoring, get_system_summary, export_metrics

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
        self.api_timeout = int(os.getenv('API_TIMEOUT', 30))  # 增加超时时间到30秒
        self.max_response_tokens = int(os.getenv('MAX_RESPONSE_TOKENS', 300))
        self.temperature = float(os.getenv('TEMPERATURE', 0.3))
        
        logger.info("Initializing OptimizedAgentRAG system", 
                   model_name=self.model_name, 
                   api_timeout=self.api_timeout,
                   max_tokens=self.max_response_tokens,
                   temperature=self.temperature)
        
        # 初始化模块
        self.markdown_processor = MarkdownProcessor(self.knowledge_base_path)
        self.vector_store_manager = VectorStoreManager(
            self.vector_store_path,
            api_key=self.bailian_api_key
        )
        
        # 使用优化版的API
        self.bailian_api = OptimizedBailianAPI(self.bailian_api_key, self.bailian_api_url)
        
        self.conversation_manager = ConversationManager()
        self.tool_manager = get_tool_manager()
        
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
    
    def process_query(self, query):
        """优化版的查询处理"""
        start_time = time.time()
        
        try:
            logger.info(f"Processing query: {query[:50]}...")
            
            # 检索相关文档
            retrieved_docs = self.vector_store_manager.search(query, k=self.top_k)
            logger.info(f"Retrieved {len(retrieved_docs)} relevant documents")
            
            # 构建上下文
            context = self.conversation_manager.get_context(query, retrieved_docs)
            
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
            
            # 添加到会话历史
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


# 保持向后兼容
AgentRAG = OptimizedAgentRAG