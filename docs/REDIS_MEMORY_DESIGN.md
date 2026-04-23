# Redis 记忆系统设计文档

## 1. 需求分析

### 1.1 短期上下文（Redis）
- **目标**：维护用户会话的短期对话历史
- **特点**：
  - 快速读写（毫秒级响应）
  - 自动过期（TTL 机制）
  - 会话隔离（每个用户独立会话）
  - 支持多轮对话

### 1.2 长期记忆（向量数据库）
- **目标**：存储重要对话记录，支持语义检索
- **特点**：
  - 持久化存储
  - 语义相似度检索
  - 选择性存储（重要对话）
  - 跨会话记忆

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    用户请求                              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI 后端 (backend/main.py)              │
│  - Session ID 管理                                       │
│  - 请求路由                                              │
└────────────┬────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│         EnhancedConversationManager                      │
│  (src/conversation/enhanced_conversation_manager.py)    │
└────────────┬────────────────────────────────────────────┘
             │
      ┌──────┴──────┐
      │             │
      ▼             ▼
┌──────────┐   ┌──────────────┐
│  Redis   │   │ VectorStore  │
│ (短期)   │   │  (长期)      │
└──────────┘   └──────────────┘
```

### 2.2 Redis 数据结构设计

#### 2.2.1 会话存储
```
Key: session:{session_id}
Type: Hash
Fields:
  - user_id: 用户 ID
  - created_at: 创建时间戳
  - updated_at: 最后更新时间戳
  - message_count: 消息数量
TTL: 30 分钟（可配置）
```

#### 2.2.2 对话历史存储
```
Key: session:{session_id}:messages
Type: List
Value: JSON 字符串
  [
    {"role": "user", "content": "...", "timestamp": 1234567890},
    {"role": "assistant", "content": "...", "timestamp": 1234567891}
  ]
TTL: 30 分钟（与会话同步）
```

#### 2.2.3 长期记忆索引
```
Key: session:{session_id}:memory_index
Type: Set
Value: 向量存储中的 document_id 集合
用途：快速定位该会话的长期记忆
```

### 2.3 向量存储设计

#### 长期记忆文档结构
```python
{
    "page_content": "用户询问了关于谢恩的信息，回答了他的位置和喜好",
    "metadata": {
        "session_id": "sess_123",
        "user_id": "user_456",
        "timestamp": 1234567890,
        "query": "谢恩在哪里",
        "response": "谢恩通常在鹈鹕镇的酒吧工作...",
        "importance_score": 0.8,  # 重要性评分
        "category": "npc_info"  # 分类：npc_info, location, event 等
    }
}
```

## 3. 核心功能设计

### 3.1 EnhancedConversationManager

#### 类结构
```python
class EnhancedConversationManager:
    def __init__(self, redis_config, vector_store_manager):
        self.redis_client = redis.Redis(**redis_config)
        self.vector_store = vector_store_manager
        self.session_ttl = 1800  # 30 分钟
        self.memory_ttl = 86400 * 7  # 7 天
        
    # 会话管理
    def create_session(self, session_id, user_id)
    def get_session(self, session_id)
    def delete_session(self, session_id)
    
    # 消息管理
    def add_message(self, session_id, role, content)
    def get_messages(self, session_id, limit=10)
    def clear_messages(self, session_id)
    
    # 长期记忆
    def save_to_long_term_memory(self, session_id, query, response, importance_score)
    def search_long_term_memory(self, session_id, query, k=3)
    def get_context(self, session_id, query, retrieved_docs)
```

### 3.2 工作流程

#### 3.2.1 查询处理流程
```
1. 接收查询（包含 session_id）
   ↓
2. 从 Redis 获取最近 N 轮对话
   ↓
3. 从向量存储检索相关长期记忆
   ↓
4. 组合：检索文档 + 短期对话 + 长期记忆
   ↓
5. 调用 LLM 生成回复
   ↓
6. 保存对话到 Redis
   ↓
7. 评估重要性，决定是否存入长期记忆
```

#### 3.2.2 长期记忆存储策略
```python
# 重要性评分规则
def calculate_importance(query, response):
    score = 0.5  # 基础分
    
    # 规则 1: 包含事实性信息 +0.2
    if contains_factual_info(response):
        score += 0.2
    
    # 规则 2: 用户追问 +0.1
    if is_followup_question(query):
        score += 0.1
    
    # 规则 3: 包含数字/日期 +0.1
    if contains_numbers_or_dates(response):
        score += 0.1
    
    # 规则 4: 回复长度适中 +0.1
    if 50 < len(response) < 300:
        score += 0.1
    
    return min(score, 1.0)

# 存储决策
if importance_score > 0.7:
    save_to_long_term_memory()
```

## 4. API 设计

### 4.1 后端 API 扩展

#### 新增端点
```python
# 会话管理
POST /api/session/create      # 创建新会话
DELETE /api/session/{id}      # 删除会话
GET /api/session/{id}         # 获取会话信息

# 消息历史
GET /api/session/{id}/messages  # 获取消息历史
POST /api/session/{id}/clear    # 清空消息

# 长期记忆
GET /api/session/{id}/memory    # 查看长期记忆
POST /api/session/{id}/memory   # 手动添加到长期记忆
```

### 4.2 请求/响应格式

#### 创建会话
```json
// POST /api/session/create
Request:
{
  "user_id": "user_123"
}

Response:
{
  "session_id": "sess_abc123",
  "created_at": 1234567890,
  "expires_at": 1234569690
}
```

#### 查询（带 session_id）
```json
// POST /api/query
Request:
{
  "session_id": "sess_abc123",
  "query": "谢恩在哪里"
}

Response:
{
  "response": "谢恩通常在鹈鹕镇的酒吧工作...",
  "session_id": "sess_abc123",
  "message_count": 5,
  "memory_retrieved": true
}
```

## 5. 配置设计

### 5.1 Redis 配置
```env
# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_SESSION_TTL=1800
REDIS_MEMORY_TTL=604800
```

### 5.2 长期记忆配置
```env
# 长期记忆配置
LONG_TERM_MEMORY_ENABLED=true
LONG_TERM_MEMORY_THRESHOLD=0.7  # 重要性阈值
LONG_TERM_MEMORY_TOP_K=3
```

## 6. 实现计划

### Phase 1: 基础 Redis 集成
- [ ] 安装 redis 依赖
- [ ] 创建 RedisConnectionManager
- [ ] 实现会话管理基础功能
- [ ] 实现消息存储功能

### Phase 2: 长期记忆集成
- [ ] 扩展 VectorStoreManager
- [ ] 实现长期记忆存储逻辑
- [ ] 实现长期记忆检索逻辑
- [ ] 实现重要性评分算法

### Phase 3: EnhancedConversationManager
- [ ] 创建新类（保持向后兼容）
- [ ] 集成 Redis 和向量存储
- [ ] 实现 get_context 增强版本
- [ ] 添加日志和监控

### Phase 4: API 和测试
- [ ] 更新后端 API
- [ ] 添加 session_id 管理
- [ ] 编写单元测试
- [ ] 性能测试和优化

## 7. 依赖更新

### requirements.txt 新增
```txt
# Redis 支持
redis>=4.5.0
hiredis>=2.2.0  # 可选，性能优化

# 长期记忆增强
chromadb>=0.4.0  # 或使用现有的 FAISS
```

## 8. 性能考虑

### 8.1 Redis 优化
- 使用连接池
- 批量操作（pipeline）
- 合理设置 TTL
- 使用 Lua 脚本减少网络往返

### 8.2 向量存储优化
- 定期清理过期记忆
- 使用 HNSW 索引加速检索
- 缓存热门查询结果

### 8.3 内存管理
- 限制每个会话的消息数量（最近 20 轮）
- 限制长期记忆总数（每个会话最多 100 条）
- 定期清理无用会话

## 9. 监控和日志

### 9.1 关键指标
- Redis 连接数
- 会话创建/删除速率
- 平均响应时间
- 长期记忆检索命中率
- 内存使用量

### 9.2 日志记录
- 会话生命周期事件
- 长期记忆存储事件
- 错误和异常
- 性能指标

## 10. 向后兼容性

### 10.1 保持现有 API
- 现有的 `/api/query` 和 `/api/clear` 继续工作
- 如果不提供 session_id，使用默认会话

### 10.2 渐进式迁移
- 默认使用旧的 ConversationManager
- 通过配置启用 EnhancedConversationManager
- 逐步迁移到新架构
