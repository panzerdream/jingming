from langchain_community.vectorstores import FAISS
import os

class VectorStoreManager:
    def __init__(self, vector_store_path, api_key=None):
        self.vector_store_path = vector_store_path
        if api_key:
            # 使用阿里云百炼API的嵌入模型
            from langchain_community.embeddings import DashScopeEmbeddings
            self.embeddings = DashScopeEmbeddings(
                model="text-embedding-v1",
                dashscope_api_key=api_key
            )
        else:
            # 使用简易的嵌入模型作为fallback
            from langchain_community.embeddings import FakeEmbeddings
            self.embeddings = FakeEmbeddings(size=768)
        self.vector_store = None
    
    def create_vector_store(self, documents):
        """创建向量存储"""
        self.vector_store = FAISS.from_documents(documents, self.embeddings)
        self.save_vector_store()
        return self.vector_store
    
    def load_vector_store(self):
        """加载向量存储"""
        index_path = os.path.join(self.vector_store_path, "index.faiss")
        if os.path.exists(index_path):
            self.vector_store = FAISS.load_local(
                self.vector_store_path,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
        return self.vector_store
    
    def save_vector_store(self):
        """保存向量存储"""
        if self.vector_store:
            self.vector_store.save_local(self.vector_store_path)
    
    def add_documents(self, documents):
        """添加文档到向量存储"""
        if not self.vector_store:
            self.load_vector_store()
        if self.vector_store:
            self.vector_store.add_documents(documents)
            self.save_vector_store()
        else:
            self.create_vector_store(documents)
    
    def search(self, query, k=5):
        """搜索相关文档"""
        if not self.vector_store:
            self.load_vector_store()
        if self.vector_store:
            results = self.vector_store.similarity_search(query, k=k)
            return results
        return []