// 修复版本：简化响应处理
async sendMessage() {
  if (!this.userInput.trim() || this.loading) return
  
  const userMessage = this.userInput.trim()
  
  // 添加用户消息
  this.messages.push({
    sender: 'user',
    content: userMessage
  })
  
  // 清空输入框
  this.userInput = ''
  
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
    
    // 读取响应文本（非流式）
    const responseText = await response.text()
    
    // 添加机器人消息
    this.messages.push({
      sender: 'bot',
      content: responseText
    })
    
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
}