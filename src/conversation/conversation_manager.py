from langchain.memory import ConversationBufferMemory

class ConversationManager:
    def __init__(self, memory_key="chat_history", return_messages=True):
        self.memory = ConversationBufferMemory(
            memory_key=memory_key,
            return_messages=return_messages
        )
    
    def add_message(self, role, content):
        """添加消息到会话历史"""
        if role == "user":
            self.memory.chat_memory.add_user_message(content)
        elif role == "assistant":
            self.memory.chat_memory.add_ai_message(content)
    
    def get_history(self):
        """获取会话历史"""
        return self.memory.load_memory_variables({}).get("chat_history", [])
    
    def get_history_str(self):
        """获取会话历史字符串"""
        history = self.get_history()
        history_str = ""
        for message in history:
            if hasattr(message, "role"):
                history_str += f"{message.role}: {message.content}\n"
            elif hasattr(message, "type"):
                if message.type == "human":
                    history_str += f"user: {message.content}\n"
                elif message.type == "ai":
                    history_str += f"assistant: {message.content}\n"
        return history_str
    
    def clear_history(self):
        """清空会话历史"""
        self.memory.clear()
    
    def get_context(self, query, retrieved_docs):
        """构建上下文"""
        # 构建检索到的文档上下文
        docs_context = "\n".join([doc.page_content for doc in retrieved_docs])
        
        # 构建会话历史上下文
        history_context = self.get_history_str()
        
        # 组合上下文
        context = f"检索到的相关信息：\n{docs_context}\n"
        if history_context:
            context += f"\n会话历史：\n{history_context}\n"
        
        return context