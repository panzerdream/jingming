import os
import sys
import time
import json
from dotenv import load_dotenv

# 添加当前目录到路径
sys.path.append(os.path.dirname(__file__))

from document_processing.markdown_processor import MarkdownProcessor
from vector_store.vector_store import VectorStoreManager
from api.bailian_api import BailianAPI
from conversation.conversation_manager import ConversationManager
from tools.enhanced_tool_manager import get_tool_manager, should_use_tool, parse_tool_call, run_tool
from utils.logger import get_logger
from utils.monitor import get_metrics_collector, start_monitoring, get_system_summary, export_metrics

# 加载环境变量
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../config/.env'))

# 获取日志记录器
logger = get_logger()
metrics = get_metrics_collector()


class AgentRAG:
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
        
        logger.info("Initializing AgentRAG system", 
                   model_name=self.model_name, top_k=self.top_k,
                   chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
        
        # 初始化模块
        self.markdown_processor = MarkdownProcessor(self.knowledge_base_path)
        self.vector_store_manager = VectorStoreManager(
            self.vector_store_path,
            api_key=self.bailian_api_key
        )
        self.bailian_api = BailianAPI(self.bailian_api_key, self.bailian_api_url)
        self.conversation_manager = ConversationManager()
        self.tool_manager = get_tool_manager()
        
        # 初始化向量存储
        self._init_vector_store()
        
        # 启动监控
        start_monitoring(interval=60)
        logger.info("System monitoring started")
    
    def _init_vector_store(self):
        """初始化向量存储"""
        # 检查向量存储文件是否存在
        index_path = os.path.join(self.vector_store_path, "index.faiss")
        if not os.path.exists(index_path):
            logger.info("Initializing vector store...")
            # 确保向量存储目录存在
            os.makedirs(self.vector_store_path, exist_ok=True)
            # 处理markdown文件
            chunks = self.markdown_processor.process(self.chunk_size, self.chunk_overlap)
            if chunks:
                # 创建向量存储
                self.vector_store_manager.create_vector_store(chunks)
                logger.info(f"Vector store created successfully with {len(chunks)} document chunks")
                metrics.record_tool_usage("vector_store_create", success=True)
            else:
                logger.warning("No markdown files in knowledge base")
                metrics.record_error("no_documents_found")
        else:
            logger.info("Loading existing vector store...")
            self.vector_store_manager.load_vector_store()
            logger.info("Vector store loaded successfully")
    
    def process_query(self, query):
        """处理用户查询"""
        start_time = time.time()
        
        try:
            logger.info(f"Processing query: {query[:100]}...")
            
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
                    # 生成回复
                    response = self.bailian_api.generate_with_context(query, context, self.model_name)
            else:
                # 生成回复
                response = self.bailian_api.generate_with_context(query, context, self.model_name)
            
            # 计算处理时间
            processing_time = time.time() - start_time
            
            # 添加到会话历史
            self.conversation_manager.add_message("user", query)
            
            # 对于工具查询，保存简化版本的响应（不包含工具结果标记）
            if should_use_tool(query) and tool_name:
                # 如果是计算工具，保存简化响应
                if "根据计算，结果是" in response:
                    # 提取计算结果部分
                    simplified_response = response
                else:
                    simplified_response = response.replace("（基于工具查询）", "")
            else:
                simplified_response = response
                
            self.conversation_manager.add_message("assistant", simplified_response)
            
            # 记录指标
            metrics.record_query(query, processing_time, success=True)
            logger.log_query(query, response, retrieved_docs, processing_time)
            
            logger.info(f"Query processed in {processing_time:.2f}s")
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"处理查询时发生错误: {str(e)}"
            logger.error(error_msg, query=query, error=str(e))
            metrics.record_query(query, processing_time, success=False)
            metrics.record_error("query_processing_failed")
            return error_msg
    
    def _generate_response_with_tool(self, query: str, context: str, tool_result: str) -> str:
        """结合工具结果生成回复"""
        try:
            # 构建包含工具结果的上下文
            enhanced_context = f"{context}\\n\\n工具执行结果:\\n{tool_result}"
            
            # 生成回复
            response = self.bailian_api.generate_with_context(query, enhanced_context, self.model_name)
            
            # 在回复中注明使用了工具（仅当回复不是计算结果时）
            if "工具" not in response and "搜索" not in response and "计算" not in response and "结果是" not in response:
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
            
            logger.info(f"Adding document: {file_path}")
            
            # 复制文件到知识库目录
            dest_path = os.path.join(self.knowledge_base_path, os.path.basename(file_path))
            shutil.copy(file_path, dest_path)
            
            # 处理新文档
            chunks = self.markdown_processor.process(self.chunk_size, self.chunk_overlap)
            if chunks:
                # 添加到向量存储
                self.vector_store_manager.add_documents(chunks)
                logger.info(f"Document added successfully with {len(chunks)} document chunks")
                metrics.record_tool_usage("vector_store_add_documents", success=True)
                return True
            else:
                logger.warning("Document processing failed")
                metrics.record_error("document_processing_failed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            metrics.record_error("add_document_failed")
            return False
    
    def get_system_status(self):
        """获取系统状态"""
        try:
            status = get_system_summary()
            return json.dumps(status, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return f"获取系统状态失败: {str(e)}"
    
    def export_system_metrics(self, filepath: str = "system_metrics.json"):
        """导出系统指标"""
        try:
            success = export_metrics(filepath)
            if success:
                return f"系统指标已导出到 {filepath}"
            else:
                return "导出系统指标失败"
        except Exception as e:
            logger.error(f"Failed to export system metrics: {e}")
            return f"导出系统指标失败: {str(e)}"


def main():
    print("Agent RAG系统启动中...")
    logger.info("Starting Agent RAG system")
    
    agent = AgentRAG()
    
    print("系统启动完成！")
    print("可用命令：")
    print("  - 输入查询进行对话")
    print("  - 输入'状态'查看系统状态")
    print("  - 输入'工具'查看可用工具")
    print("  - 输入'清空'清空会话历史")
    print("  - 输入'导出'导出系统指标")
    print("  - 输入'退出'结束对话")
    
    while True:
        try:
            user_input = input("\n用户：").strip()
            
            if user_input == "退出":
                print("对话结束，再见！")
                logger.info("User exited the conversation")
                break
            elif user_input == "清空":
                agent.clear_conversation()
                print("会话历史已清空")
                continue
            elif user_input == "状态":
                status = agent.get_system_status()
                print(f"系统状态：\\n{status}")
                continue
            elif user_input == "工具":
                tool_descriptions = get_tool_manager().get_tool_descriptions()
                print(f"可用工具：\\n{tool_descriptions}")
                continue
            elif user_input == "导出":
                result = agent.export_system_metrics()
                print(result)
                continue
            
            response = agent.process_query(user_input)
            print(f"Agent：{response}")
            
        except KeyboardInterrupt:
            print("\\n程序被中断")
            logger.info("Program interrupted by user")
            break
        except Exception as e:
            error_msg = f"处理输入时发生错误: {str(e)}"
            print(error_msg)
            logger.error(error_msg, error=str(e))


if __name__ == "__main__":
    main()