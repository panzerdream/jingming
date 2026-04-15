from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os

class MarkdownProcessor:
    def __init__(self, knowledge_base_path):
        self.knowledge_base_path = knowledge_base_path
    
    def load_documents(self):
        """加载知识库中的markdown文件"""
        loader = DirectoryLoader(
            path=self.knowledge_base_path,
            glob="*.md",
            loader_cls=TextLoader
        )
        documents = loader.load()
        return documents
    
    def split_documents(self, documents, chunk_size=500, chunk_overlap=100):
        """将文档分块"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_documents(documents)
        return chunks
    
    def process(self, chunk_size=500, chunk_overlap=100):
        """处理markdown文件并返回分块"""
        documents = self.load_documents()
        chunks = self.split_documents(documents, chunk_size, chunk_overlap)
        return chunks