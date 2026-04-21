<template>
  <div class="app-container">
    <div class="stardew-header">
      <h1>星露谷百事通</h1>
    </div>
    
    <div class="chat-container">
      <div class="chat-messages" ref="chatMessages">
        <div v-for="(message, index) in messages" :key="index" :class="['message', message.sender]">
          <div class="message-content" v-html="message.content"></div>
        </div>
        <div v-if="loading" class="message bot">
          <div class="message-content">
            <div class="loading">
              <div class="loading-dot"></div>
              <div class="loading-dot"></div>
              <div class="loading-dot"></div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="chat-input">
        <input 
          v-model="inputMessage" 
          @keydown.enter.prevent="$event.shiftKey ? null : sendMessage()" 
          placeholder="输入你的问题..."
          :disabled="loading"
        />
        <button @click="sendMessage" :disabled="loading || !inputMessage.trim()">
          发送
        </button>
        <button @click="clearChat" :disabled="loading">
          清空
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      messages: [],
      inputMessage: '',
      loading: false
    }
  },
  mounted() {
    // 添加欢迎消息
    this.messages.push({
      sender: 'bot',
      content: '你好！我是星露谷助手，有什么可以帮你的吗？'
    })
  },
  methods: {
    async sendMessage() {
      if (!this.inputMessage.trim() || this.loading) return
      
      // 添加用户消息
      const userMessage = this.inputMessage.trim()
      this.messages.push({
        sender: 'user',
        content: userMessage
      })
      
      // 清空输入框
      this.inputMessage = ''
      
      // 滚动到底部
      this.scrollToBottom()
      
      // 显示加载状态
      this.loading = true
      
      try {
        // 发送请求到后端（使用相对路径，通过 Vite 代理）
        const response = await fetch('/api/query', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ query: userMessage })
        })
        
        if (!response.ok) {
          throw new Error('API请求失败')
        }
        
        // 处理流式响应
        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        
        // 添加机器人消息占位符
        const botMessageIndex = this.messages.length
        this.messages.push({
          sender: 'bot',
          content: ''
        })
        
        // 逐步接收数据
        let accumulatedContent = ''
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          
          const chunk = decoder.decode(value, { stream: true })
          accumulatedContent += chunk
          
          // 更新机器人消息
          this.messages[botMessageIndex].content = accumulatedContent
          this.scrollToBottom()
        }
        
      } catch (error) {
        console.error('发送消息失败:', error)
        this.messages.push({
          sender: 'bot',
          content: '抱歉，处理你的请求时出错了，请稍后再试。'
        })
      } finally {
        // 隐藏加载状态
        this.loading = false
        // 滚动到底部
        this.scrollToBottom()
      }
    },
    async clearChat() {
      if (this.loading) return
      
      try {
        // 发送请求到后端清空会话（使用相对路径，通过 Vite 代理）
        const response = await fetch('/api/clear', {
          method: 'POST'
        })
        
        if (!response.ok) {
          throw new Error('清空会话失败')
        }
        
        // 清空本地消息
        this.messages = [{
          sender: 'bot',
          content: '会话已清空，有什么可以帮你的吗？'
        }]
      } catch (error) {
        console.error('清空会话失败:', error)
        this.messages.push({
          sender: 'bot',
          content: '抱歉，清空会话时出错了，请稍后再试。'
        })
      }
    },
    scrollToBottom() {
      setTimeout(() => {
        const chatMessages = this.$refs.chatMessages
        if (chatMessages) {
          chatMessages.scrollTop = chatMessages.scrollHeight
        }
      }, 100)
    }
  }
}
</script>

<style scoped>
/* 全局样式 */
* {
  font-family: 'Noto Sans SC', 'Press Start 2P', sans-serif;
  font-weight: normal;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  font-size: 14px;
  line-height: 1.5;
}

.app-container {
  background-color: #8B4513;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  /* 像素风格效果 */
  image-rendering: pixelated;
  image-rendering: crisp-edges;
}

/* 为中文字符添加像素风格 */
.message-content {
  text-rendering: optimizeSpeed;
  -webkit-font-smoothing: none;
  -moz-osx-font-smoothing: grayscale;
}

.stardew-header {
  background-color: #556B2F;
  color: #FFF8DC;
  padding: 15px 30px;
  border: 2px solid #8B4513;
  border-radius: 4px;
  margin-bottom: 20px;
  box-shadow: 0 2px 0 #2F4F4F;
}

.stardew-header h1 {
  font-size: 24px;
  margin: 0;
  text-align: center;
  font-weight: bold;
  font-family: 'Press Start 2P', 'Noto Sans SC', sans-serif;
  text-rendering: optimizeSpeed;
  -webkit-font-smoothing: none;
  -moz-osx-font-smoothing: grayscale;
}

.chat-container {
  width: 100%;
  max-width: 800px;
  background-color: #DEB887;
  border: 4px solid #8B4513;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 0 #2F4F4F;
}

.chat-messages {
  height: 500px;
  overflow-y: auto;
  padding: 20px;
  background-color: #F5DEB3;
  border-bottom: 4px solid #8B4513;
}

.message {
  margin-bottom: 15px;
  max-width: 80%;
  padding: 10px;
  border: 2px solid #8B4513;
  border-radius: 8px;
  box-shadow: 0 2px 0 #2F4F4F;
}

.message.user {
  background-color: #E6E6FA;
  margin-left: auto;
  border-bottom-right-radius: 0;
}

.message.bot {
  background-color: #FFF8DC;
  margin-right: auto;
  border-bottom-left-radius: 0;
}

.message-content {
  font-size: 14px;
  line-height: 1.5;
  word-wrap: break-word;
  text-align: left;
  white-space: normal;
}

.loading {
  display: flex;
  gap: 5px;
}

.loading-dot {
  width: 10px;
  height: 10px;
  background-color: #8B4513;
  border-radius: 50%;
  animation: pulse 1.5s infinite ease-in-out;
}

.loading-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.loading-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  50% {
    transform: scale(1.2);
    opacity: 1;
  }
}

.chat-input {
  display: flex;
  padding: 15px;
  background-color: #DEB887;
  border-top: 4px solid #8B4513;
}

.chat-input input {
  flex: 1;
  padding: 10px;
  border: 2px solid #8B4513;
  border-radius: 4px;
  font-size: 14px;
  background-color: #FFF8DC;
  box-shadow: inset 0 2px 0 #2F4F4F;
}

.chat-input button {
  margin-left: 10px;
  padding: 10px 15px;
  border: 2px solid #8B4513;
  border-radius: 4px;
  font-size: 14px;
  background-color: #556B2F;
  color: #FFF8DC;
  cursor: pointer;
  box-shadow: 0 2px 0 #2F4F4F;
  transition: all 0.2s;
}

.chat-input button:hover:not(:disabled) {
  background-color: #6B8E23;
  transform: translateY(-1px);
  box-shadow: 0 3px 0 #2F4F4F;
}

.chat-input button:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 1px 0 #2F4F4F;
}

.chat-input button:disabled {
  background-color: #A0522D;
  cursor: not-allowed;
  opacity: 0.7;
}

/* 滚动条样式 */
.chat-messages::-webkit-scrollbar {
  width: 12px;
}

.chat-messages::-webkit-scrollbar-track {
  background: #DEB887;
  border-left: 2px solid #8B4513;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #8B4513;
  border: 2px solid #DEB887;
  border-radius: 6px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #A0522D;
}
</style>