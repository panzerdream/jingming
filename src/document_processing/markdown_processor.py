from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
import time

# 导入日志模块
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import get_logger

logger = get_logger()


class MarkdownProcessor:
    def __init__(self, knowledge_base_path):
        self.knowledge_base_path = knowledge_base_path
        logger.info(f"Initializing MarkdownProcessor with path: {knowledge_base_path}")
    
    def load_documents(self):
        """加载知识库中的markdown文件"""
        logger.info(f"Loading markdown documents from {self.knowledge_base_path}")
        start_time = time.time()
        
        try:
            loader = DirectoryLoader(
                path=self.knowledge_base_path,
                glob="*.md",
                loader_cls=TextLoader
            )
            documents = loader.load()
            
            execution_time = time.time() - start_time
            logger.info(f"Loaded {len(documents)} markdown documents in {execution_time:.2f}s")
            
            return documents
        except Exception as e:
            logger.error(f"Failed to load documents: {e}")
            return []
    
    def split_documents(self, documents, chunk_size=500, chunk_overlap=100):
        """将文档分块"""
        logger.info(f"Splitting {len(documents)} documents (chunk_size={chunk_size}, overlap={chunk_overlap})")
        start_time = time.time()
        
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\\n\\n", "\\n", " ", ""]
            )
            chunks = text_splitter.split_documents(documents)
            
            execution_time = time.time() - start_time
            logger.info(f"Split documents into {len(chunks)} chunks in {execution_time:.2f}s")
            
            return chunks
        except Exception as e:
            logger.error(f"Failed to split documents: {e}")
            return []
    
    def process(self, chunk_size=500, chunk_overlap=100):
        """处理markdown文件并返回分块"""
        logger.info(f"Processing markdown files (chunk_size={chunk_size}, overlap={chunk_overlap})")
        
        documents = self.load_documents()
        if not documents:
            logger.warning("No documents found to process")
            return []
        
        chunks = self.split_documents(documents, chunk_size, chunk_overlap)
        return chunks