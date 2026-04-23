from langchain_community.vectorstores import FAISS
import os
import time

# 导入日志模块
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import get_logger

logger = get_logger()


class VectorStoreManager:
    def __init__(self, vector_store_path, api_key=None):
        self.vector_store_path = vector_store_path
        logger.info(f"Initializing VectorStoreManager at {vector_store_path}")
        
        if api_key:
            # 使用阿里云百炼API的嵌入模型
            from langchain_community.embeddings import DashScopeEmbeddings
            self.embeddings = DashScopeEmbeddings(
                model="text-embedding-v1",
                dashscope_api_key=api_key
            )
            logger.info("Using DashScope embeddings")
        else:
            # 使用简易的嵌入模型作为fallback
            from langchain_community.embeddings import FakeEmbeddings
            self.embeddings = FakeEmbeddings(size=768)
            logger.warning("Using FakeEmbeddings as fallback (no API key provided)")
        
        self.vector_store = None
        self.bm25_available = False
        self.bm25_index = None
        self.documents = []
        
        # 尝试导入BM25相关依赖
        try:
            import numpy as np
            from rank_bm25 import BM25Okapi
            import jieba
            self.bm25_available = True
            self.np = np
            self.BM25Okapi = BM25Okapi
            self.jieba = jieba
            logger.info("BM25 dependencies loaded successfully")
        except ImportError:
            logger.warning("BM25 dependencies not installed, will use pure vector search")
    
    def create_vector_store(self, documents):
        """创建向量存储"""
        logger.info(f"Creating vector store with {len(documents)} documents")
        start_time = time.time()
        
        try:
            self.vector_store = FAISS.from_documents(documents, self.embeddings)
            self.save_vector_store()
            
            if self.bm25_available:
                self._build_bm25_index(documents)
            
            execution_time = time.time() - start_time
            logger.info(f"Vector store created successfully in {execution_time:.2f}s")
            return self.vector_store
            
        except Exception as e:
            logger.error(f"Failed to create vector store: {e}")
            raise
    
    def load_vector_store(self):
        """加载向量存储"""
        index_path = os.path.join(self.vector_store_path, "index.faiss")
        logger.info(f"Loading vector store from {index_path}")
        
        if os.path.exists(index_path):
            try:
                self.vector_store = FAISS.load_local(
                    self.vector_store_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info("Vector store loaded successfully")
                return self.vector_store
            except Exception as e:
                logger.error(f"Failed to load vector store: {e}")
                raise
        else:
            logger.warning(f"Vector store index not found at {index_path}")
            return None
    
    def save_vector_store(self):
        """保存向量存储"""
        if self.vector_store:
            try:
                self.vector_store.save_local(self.vector_store_path)
                logger.debug(f"Vector store saved to {self.vector_store_path}")
            except Exception as e:
                logger.error(f"Failed to save vector store: {e}")
    
    def add_documents(self, documents):
        """添加文档到向量存储"""
        logger.info(f"Adding {len(documents)} documents to vector store")
        start_time = time.time()
        
        if not self.vector_store:
            self.load_vector_store()
        
        if self.vector_store:
            try:
                self.vector_store.add_documents(documents)
                self.save_vector_store()
                
                if self.bm25_available:
                    self._build_bm25_index(documents)
                
                execution_time = time.time() - start_time
                logger.info(f"Documents added successfully in {execution_time:.2f}s")
                
            except Exception as e:
                logger.error(f"Failed to add documents: {e}")
                raise
        else:
            logger.info("No existing vector store, creating new one")
            self.create_vector_store(documents)
    
    def add_document(self, document):
        """添加单个文档到向量存储
        
        Args:
            document: LangChain Document 对象
            
        Returns:
            bool: 添加成功返回 True
        """
        try:
            logger.info(f"Adding single document to vector store")
            
            if not self.vector_store:
                self.load_vector_store()
            
            if self.vector_store:
                # 使用 add_documents 方法添加单个文档
                self.vector_store.add_documents([document])
                self.save_vector_store()
                
                if self.bm25_available:
                    # 重新构建 BM25 索引
                    self._build_bm25_index(self.documents + [document])
                
                logger.info("Single document added successfully")
                return True
            else:
                # 如果没有现有向量存储，创建新的
                logger.info("No existing vector store, creating new one")
                self.create_vector_store([document])
                return True
                
        except Exception as e:
            logger.error(f"Failed to add single document: {e}")
            return False
    
    def _build_bm25_index(self, documents):
        """构建BM25索引"""
        if not self.bm25_available:
            return
        
        logger.info("Building BM25 index")
        start_time = time.time()
        
        try:
            self.documents = documents
            tokenized_corpus = []
            for doc in documents:
                # 对中文文本进行分词
                tokens = list(self.jieba.cut(doc.page_content))
                tokenized_corpus.append(tokens)
            
            self.bm25_index = self.BM25Okapi(tokenized_corpus)
            
            execution_time = time.time() - start_time
            logger.info(f"BM25 index built with {len(documents)} documents in {execution_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Failed to build BM25 index: {e}")
    
    def _bm25_search(self, query, k=5):
        """BM25搜索"""
        if not self.bm25_available or not self.bm25_index:
            return []
        
        logger.debug(f"BM25 search: '{query[:50]}...' (k={k})")
        start_time = time.time()
        
        try:
            # 对查询进行分词
            tokens = list(self.jieba.cut(query))
            scores = self.bm25_index.get_scores(tokens)
            # 获取Top K结果
            top_indices = self.np.argsort(scores)[::-1][:k]
            results = [self.documents[i] for i in top_indices]
            
            execution_time = time.time() - start_time
            logger.debug(f"BM25 search completed in {execution_time:.3f}s, found {len(results)} results")
            
            return results
            
        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []
    
    def _hybrid_search(self, query, k=5, dense_weight=0.6, bm25_weight=0.4):
        """混合检索"""
        logger.debug(f"Hybrid search: '{query[:50]}...' (k={k})")
        start_time = time.time()
        
        try:
            # 执行向量检索
            dense_results = self.search_dense(query, k=k*2)
            # 执行BM25检索
            bm25_results = self._bm25_search(query, k=k*2)
            
            # 合并结果并去重
            merged_results = {}
            # 为向量检索结果添加分数
            for i, doc in enumerate(dense_results):
                if doc.page_content not in merged_results:
                    merged_results[doc.page_content] = {
                        'doc': doc,
                        'score': (1 - i/(k*2)) * dense_weight
                    }
            # 为BM25检索结果添加分数
            for i, doc in enumerate(bm25_results):
                if doc.page_content in merged_results:
                    merged_results[doc.page_content]['score'] += (1 - i/(k*2)) * bm25_weight
                else:
                    merged_results[doc.page_content] = {
                        'doc': doc,
                        'score': (1 - i/(k*2)) * bm25_weight
                    }
            
            # 按分数排序
            sorted_results = sorted(merged_results.values(), key=lambda x: x['score'], reverse=True)
            # 返回Top K结果
            results = [item['doc'] for item in sorted_results[:k]]
            
            execution_time = time.time() - start_time
            logger.debug(f"Hybrid search completed in {execution_time:.3f}s, found {len(results)} results")
            
            return results
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return self.search_dense(query, k=k)
    
    def search_dense(self, query, k=5):
        """纯向量搜索"""
        logger.debug(f"Dense search: '{query[:50]}...' (k={k})")
        start_time = time.time()
        
        if not self.vector_store:
            self.load_vector_store()
        
        if self.vector_store:
            try:
                results = self.vector_store.similarity_search(query, k=k)
                
                execution_time = time.time() - start_time
                logger.debug(f"Dense search completed in {execution_time:.3f}s, found {len(results)} results")
                
                return results
            except Exception as e:
                logger.error(f"Dense search failed: {e}")
                return []
        return []
    
    def search(self, query, k=5, use_hybrid=True):
        """搜索相关文档"""
        logger.info(f"Searching for: '{query[:100]}...' (k={k}, hybrid={use_hybrid})")
        
        if use_hybrid and self.bm25_available:
            return self._hybrid_search(query, k=k)
        else:
            return self.search_dense(query, k=k)