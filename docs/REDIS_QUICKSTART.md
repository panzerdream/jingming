# Redis 记忆系统快速开始指南

## 1. 环境准备

### 1.1 安装 Redis

#### macOS
```bash
# 使用 Homebrew
brew install redis
brew services start redis
```

#### Linux
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis

# CentOS/RHEL
sudo yum install redis
sudo systemctl start redis
```

#### Docker
```bash
docker run -d -p 6379:6379 --name redis-memory redis:latest
```

### 1.2 验证 Redis 运行
```bash
redis-cli ping
# 应该返回：PONG
```

### 1.3 安装 Python 依赖
```bash
cd /Users/xuyao/Documents/01_codes/Agent/agent-rag
source venv/bin/activate
pip install -r requirements.txt
```

---

## 2. 配置

### 2.1 编辑配置文件
编辑 [config/.env](file:///Users/xuyao/Documents/01_codes/Agent/agent-rag/config/.env) 文件：

```env
# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_SESSION_TTL=1800        # 30 分钟
REDIS_MEMORY_TTL=604800       # 7 天

# 长期记忆配置
LONG_TERM_MEMORY_ENABLED=true
LONG_TERM_MEMORY_THRESHOLD=0.7
LONG_TERM_MEMORY_TOP_K=3
```

---

## 3. 运行测试

### 3.1 运行集成测试
```bash
python tests/test_redis_integration.py
```

### 3.2 预期输出
```
============================================================
Redis 集成测试
============================================================

=== 测试 Redis 连接 ===
✓ Redis 连接成功
  - 主机：localhost:6379
  - 内存使用：1.2M
  - 会话数量：0

=== 测试会话管理 ===
✓ 会话创建成功：test_session_1234567890
✓ 会话获取成功
  - 用户 ID: test_user_123
  - 创建时间：1234567890
  - 消息数量：0
✓ 添加了 3 条消息
✓ 获取到 3 条消息
  - [user]: 你好，我想问一下谢恩在哪里...
  - [assistant]: 谢恩通常在鹈鹕镇的酒吧工作...
  - [user]: 他喜欢什么？...
✓ 消息历史字符串长度：123
✓ 会话已删除：test_session_1234567890
✓ 确认会话已删除

=== 测试增强对话管理器 ===
✓ 会话创建成功：sess_abc123
✓ 添加了 4 条消息
✓ 获取到 4 条消息
✓ 上下文构建成功，长度：256
  上下文预览：对话历史：
user: 星露谷是什么游戏？
assistant: 星露谷物语是一款农场模拟角色扮演游戏
...
✓ 统计信息:
  - Redis 可用：True
  - 向量存储可用：True
  - 短期记忆最大消息数：20
✓ 会话已删除

=== 测试重要性评分计算 ===
✓ 查询：'谢恩在哪里' -> 评分：0.80
✓ 查询：'你好' -> 评分：0.50
✓ 查询：'那他会喜欢什么礼物' -> 评分：0.70
✓ 查询：'然后呢' -> 评分：0.60

============================================================
测试总结
============================================================
✓ 通过：Redis 连接
✓ 通过：会话管理
✓ 通过：增强对话管理器
✓ 通过：重要性评分

总计：4/4 测试通过

🎉 所有测试通过！
```

---

## 4. 使用示例

### 4.1 在代码中使用

#### 示例 1：基础会话管理
```python
from conversation.enhanced_conversation_manager import get_enhanced_conversation_manager

# 获取管理器实例
conv_mgr = get_enhanced_conversation_manager(vector_store_manager)

# 创建会话
session_id = conv_mgr.create_session("user_123")
print(f"会话 ID: {session_id}")

# 添加消息
conv_mgr.add_message(session_id, "user", "星露谷是什么游戏？")
conv_mgr.add_message(session_id, "assistant", "星露谷物语是一款农场模拟角色扮演游戏")

# 获取历史消息
messages = conv_mgr.get_messages(session_id)
for msg in messages:
    print(f"{msg['role']}: {msg['content']}")

# 构建上下文（用于 LLM 查询）
context = conv_mgr.get_context(session_id, "这个游戏有哪些 NPC", retrieved_docs=[])
print(f"上下文：{context}")

# 删除会话
conv_mgr.delete_session(session_id)
```

#### 示例 2：直接使用 Redis 管理器
```python
from utils.redis_manager import init_redis_manager, get_redis_manager

# 初始化 Redis
redis_mgr = init_redis_manager(
    host='localhost',
    port=6379,
    session_ttl=1800
)

# 创建会话
redis_mgr.create_session("my_session", "user_456")

# 添加消息
redis_mgr.add_message("my_session", "user", "你好")
redis_mgr.add_message("my_session", "assistant", "你好！有什么可以帮助你的吗？")

# 获取消息
messages = redis_mgr.get_messages("my_session", limit=10)
print(f"消息数量：{len(messages)}")

# 获取统计信息
stats = redis_mgr.get_stats()
print(f"Redis 内存使用：{stats['used_memory']}")
print(f"会话数量：{stats['session_count']}")
```

#### 示例 3：长期记忆
```python
from conversation.enhanced_conversation_manager import EnhancedConversationManager

# 创建管理器（需要 vector_store_manager）
conv_mgr = EnhancedConversationManager(vector_store_manager)

# 保存重要对话到长期记忆
success = conv_mgr.save_to_long_term_memory(
    session_id="sess_123",
    query="谢恩在哪里",
    response="谢恩在鹈鹕镇的酒吧工作，每天下午 4 点上班",
    importance_score=0.8  # 可选，不传会自动计算
)

if success:
    print("已保存到长期记忆")

# 检索长期记忆
memories = conv_mgr.search_long_term_memory(
    session_id="sess_123",
    query="谢恩的工作",
    k=3
)

for memory in memories:
    print(f"记忆：{memory.page_content}")
```

---

## 5. 集成到现有系统

### 5.1 更新后端 API

编辑 `backend/main.py`，添加 session_id 支持：

```python
from conversation.enhanced_conversation_manager import get_enhanced_conversation_manager

# 创建增强对话管理器
conv_mgr = get_enhanced_conversation_manager(agent.vector_store_manager)

@app.post("/api/query")
async def query(request: QueryRequest):
    """处理用户查询（支持 session_id）"""
    
    # 如果没有 session_id，创建新会话
    session_id = request.session_id or conv_mgr.create_session(request.user_id or "anonymous")
    
    # 获取短期记忆
    short_term_history = conv_mgr.get_messages_string(session_id, limit=10)
    
    # 检索长期记忆
    long_term_memories = conv_mgr.search_long_term_memory(session_id, request.query)
    
    # 检索知识库文档
    retrieved_docs = agent.vector_store_manager.search(request.query, k=5)
    
    # 构建增强的上下文
    context = conv_mgr.get_context(session_id, request.query, retrieved_docs)
    
    # 生成回复
    response = agent.bailian_api.generate_with_context(
        request.query, context, agent.model_name,
        temperature=agent.temperature,
        max_tokens=agent.max_response_tokens
    )
    
    # 保存对话到 Redis
    conv_mgr.add_message(session_id, "user", request.query)
    conv_mgr.add_message(session_id, "assistant", response)
    
    # 评估重要性，保存到长期记忆
    conv_mgr.save_to_long_term_memory(session_id, request.query, response)
    
    return {
        "response": response,
        "session_id": session_id,
        "message_count": len(conv_mgr.get_messages(session_id))
    }

@app.post("/api/session/create")
async def create_session(request: CreateSessionRequest):
    """创建新会话"""
    session_id = conv_mgr.create_session(request.user_id)
    return {"session_id": session_id}

@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """获取会话信息"""
    session = conv_mgr.get_session(session_id)
    if session:
        return session
    raise HTTPException(status_code=404, detail="会话不存在")

@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    conv_mgr.delete_session(session_id)
    return {"message": "会话已删除"}

@app.get("/api/session/{session_id}/messages")
async def get_messages(session_id: str, limit: int = 20):
    """获取会话消息"""
    messages = conv_mgr.get_messages(session_id, limit)
    return {"messages": messages}
```

### 5.2 前端集成

在 `frontend/src/App.vue` 中添加 session_id 管理：

```javascript
export default {
  data() {
    return {
      sessionId: localStorage.getItem('sessionId') || null,
      messages: [],
      query: ''
    }
  },
  
  async created() {
    // 如果没有 session_id，创建新会话
    if (!this.sessionId) {
      await this.createSession()
    }
  },
  
  methods: {
    async createSession() {
      const response = await fetch('/api/session/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'user_' + Date.now() })
      })
      const data = await response.json()
      this.sessionId = data.session_id
      localStorage.setItem('sessionId', this.sessionId)
    },
    
    async sendMessage() {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: this.sessionId,
          query: this.query
        })
      })
      const data = await response.json()
      this.messages.push({ role: 'user', content: this.query })
      this.messages.push({ role: 'assistant', content: data.response })
      this.query = ''
    },
    
    async clearHistory() {
      await fetch(`/api/session/${this.sessionId}/clear`, {
        method: 'POST'
      })
      this.messages = []
    }
  }
}
```

---

## 6. 监控和维护

### 6.1 查看 Redis 状态
```bash
redis-cli info
```

### 6.2 查看会话数量
```bash
redis-cli keys "session:*" | wc -l
```

### 6.3 清理过期会话
Redis 会自动清理过期的会话（基于 TTL），无需手动清理。

### 6.4 备份 Redis 数据
```bash
# 保存 RDB 快照
redis-cli BGSAVE

# 备份文件位置（默认）
/var/lib/redis/dump.rdb
```

---

## 7. 故障排查

### 问题 1：Redis 连接失败
```
✗ Redis 连接错误：Error 111 connecting to localhost:6379. Connection refused.
```

**解决方案**：
```bash
# 检查 Redis 是否运行
redis-cli ping

# 如果没有运行，启动 Redis
# macOS
brew services start redis

# Linux
sudo systemctl start redis
```

### 问题 2：依赖未安装
```
ModuleNotFoundError: No module named 'redis'
```

**解决方案**：
```bash
source venv/bin/activate
pip install redis hiredis
```

### 问题 3：TTL 不生效
检查配置中的 TTL 值是否正确：
```bash
redis-cli
> CONFIG GET "*ttl*"
```

---

## 8. 性能优化建议

### 8.1 Redis 配置优化
编辑 `/etc/redis/redis.conf`：

```conf
# 最大内存限制
maxmemory 256mb

# 内存淘汰策略
maxmemory-policy allkeys-lru

# 持久化（可选）
save 900 1
save 300 10
save 60 10000
```

### 8.2 连接池优化
```python
# 在 redis_manager.py 中调整连接池大小
self.pool = redis.ConnectionPool(
    # ...
    max_connections=100  # 增加连接数
)
```

### 8.3 批量操作
使用 pipeline 减少网络往返：
```python
pipe = redis_mgr.client.pipeline()
for i in range(100):
    pipe.rpush(f"session:{sid}:messages", f"message_{i}")
pipe.execute()
```

---

## 9. 下一步

- [ ] 完成长期记忆存储逻辑
- [ ] 添加会话管理 API
- [ ] 前端支持会话切换
- [ ] 实现记忆分类
- [ ] 添加记忆可视化

---

## 10. 相关文档

- [设计文档](REDIS_MEMORY_DESIGN.md) - 详细的架构设计
- [实现总结](REDIS_IMPLEMENTATION_SUMMARY.md) - 完整的功能说明
- [测试脚本](../tests/test_redis_integration.py) - 集成测试代码

---

祝你使用愉快！如有问题，请查看日志或联系开发团队。
