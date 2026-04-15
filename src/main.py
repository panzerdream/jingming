import os
import sys
from dotenv import load_dotenv

# 添加当前目录到路径
sys.path.append(os.path.dirname(__file__))

from document_processing.markdown_processor import MarkdownProcessor
from vector_store.vector_store import VectorStoreManager
from api.bailian_api import BailianAPI
from conversation.conversation_manager import ConversationManager
from tools.tool_manager import ToolManager

# 加载环境变量
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../config/.env'))

class AgentRAG:
    def __init__(self):
        # 加载配置
        self.bailian_api_key = os.getenv('BAILIAN_API_KEY')
        self.bailian_api_url = os.getenv('BAILIAN_API_URL')
        self.vector_store_path = os.getenv('VECTOR_STORE_PATH', 'data/vector_db')
        self.knowledge_base_path = os.getenv('KNOWLEDGE_BASE_PATH', 'data/knowledge')
        self.model_name = os.getenv('MODEL_NAME', 'qwen-turbo')
        self.top_k = int(os.getenv('TOP_K', 5))
        self.chunk_size = int(os.getenv('CHUNK_SIZE', 1000))
        self.chunk_overlap = int(os.getenv('CHUNK_OVERLAP', 200))
        
        # 初始化模块
        self.markdown_processor = MarkdownProcessor(self.knowledge_base_path)
        self.vector_store_manager = VectorStoreManager(
            self.vector_store_path,
            api_key=self.bailian_api_key
        )
        self.bailian_api = BailianAPI(self.bailian_api_key, self.bailian_api_url)
        self.conversation_manager = ConversationManager()
        self.tool_manager = ToolManager()
        
        # 初始化向量存储
        self._init_vector_store()
    
    def _init_vector_store(self):
        """初始化向量存储"""
        # 检查向量存储文件是否存在
        index_path = os.path.join(self.vector_store_path, "index.faiss")
        if not os.path.exists(index_path):
            print("初始化向量存储...")
            # 确保向量存储目录存在
            os.makedirs(self.vector_store_path, exist_ok=True)
            # 处理markdown文件
            chunks = self.markdown_processor.process(self.chunk_size, self.chunk_overlap)
            if chunks:
                # 创建向量存储
                self.vector_store_manager.create_vector_store(chunks)
                print(f"向量存储创建成功，包含 {len(chunks)} 个文档块")
            else:
                print("知识库中没有markdown文件")
        else:
            print("加载已有的向量存储...")
            self.vector_store_manager.load_vector_store()
    
    def process_query(self, query):
        """处理用户查询"""
        # 检索相关文档
        retrieved_docs = self.vector_store_manager.search(query, k=self.top_k)
        
        # 构建上下文
        context = self.conversation_manager.get_context(query, retrieved_docs)
        
        # 检查是否需要使用工具
        if self._should_use_tool(query):
            # 确定使用哪个工具
            tool_name, tool_input = self._parse_tool_call(query)
            if tool_name:
                # 运行工具
                tool_result = self.tool_manager.run_tool(tool_name, tool_input)
                # 生成回复
                response = f"工具执行结果：{tool_result}"
            else:
                # 生成回复
                response = self.bailian_api.generate_with_context(query, context, self.model_name)
        else:
            # 生成回复
            response = self.bailian_api.generate_with_context(query, context, self.model_name)
        
        # 添加到会话历史
        self.conversation_manager.add_message("user", query)
        self.conversation_manager.add_message("assistant", response)
        
        return response
    
    def _should_use_tool(self, query):
        """判断是否需要使用工具"""
        # 简单的判断逻辑，实际项目中可以使用更复杂的意图识别
        tool_keywords = ["搜索", "计算", "查找", "查询"]
        return any(keyword in query for keyword in tool_keywords)
    
    def _parse_tool_call(self, query):
        """解析工具调用"""
        # 简单的解析逻辑，实际项目中可以使用更复杂的自然语言解析
        if "搜索" in query:
            # 提取搜索关键词
            search_query = query.replace("搜索", "").strip()
            return "Search", search_query
        elif "计算" in query:
            # 提取计算表达式
            expression = query.replace("计算", "").strip()
            return "Calculator", expression
        return None, None
    
    def clear_conversation(self):
        """清空会话历史"""
        self.conversation_manager.clear_history()
        print("会话历史已清空")
    
    def add_document(self, file_path):
        """添加文档到知识库"""
        # 复制文件到知识库目录
        import shutil
        dest_path = os.path.join(self.knowledge_base_path, os.path.basename(file_path))
        shutil.copy(file_path, dest_path)
        
        # 处理新文档
        chunks = self.markdown_processor.process(self.chunk_size, self.chunk_overlap)
        if chunks:
            # 添加到向量存储
            self.vector_store_manager.add_documents(chunks)
            print(f"文档添加成功，包含 {len(chunks)} 个文档块")
        else:
            print("文档处理失败")

def main():
    print("Agent RAG系统启动中...")
    agent = AgentRAG()
    print("系统启动完成，开始对话（输入'退出'结束对话，输入'清空'清空会话历史）")
    
    while True:
        user_input = input("用户：")
        
        if user_input == "退出":
            print("对话结束，再见！")
            break
        elif user_input == "清空":
            agent.clear_conversation()
            continue
        
        response = agent.process_query(user_input)
        print(f"Agent：{response}")

if __name__ == "__main__":
    main()