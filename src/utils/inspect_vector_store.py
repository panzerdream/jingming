import os
from vector_store.vector_store import VectorStoreManager
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../config/.env'))

def inspect_vector_store():
    """查看向量存储的内容"""
    # 获取配置
    vector_store_path = os.getenv('VECTOR_STORE_PATH', 'data/vector_db')
    bailian_api_key = os.getenv('BAILIAN_API_KEY')
    
    # 初始化向量存储管理器
    vector_store_manager = VectorStoreManager(vector_store_path, api_key=bailian_api_key)
    
    # 加载向量存储
    vector_store = vector_store_manager.load_vector_store()
    
    if vector_store:
        print("=== 向量存储信息 ===")
        print(f"向量存储路径: {