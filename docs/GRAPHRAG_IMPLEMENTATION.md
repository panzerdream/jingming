# GraphRAG 实现文档

## 1. 已完成的功能

### Phase 1: 基础图构建 ✅

#### 1.1 依赖安装
- ✅ networkx - 图结构和算法
- ✅ graphviz - 图可视化
- ✅ neo4j - 图数据库支持

#### 1.2 实体抽取器 ([src/graph/entity_extractor.py](file:///Users/xuyao/Documents/01_codes/Agent/agent-rag/src/graph/entity_extractor.py))

实现了从 Markdown 知识库中提取实体和关系的功能：

**核心类**：
- `Entity` - 实体数据类
- `Relation` - 关系数据类
- `EntityExtractor` - 实体抽取器

**功能**：
- ✅ 人物实体抽取（从居民详细文档）
  - 提取属性：生日、住址、职业等
  - 提取关系：家庭、朋友、工作地点
- ✅ 物品实体抽取（从物品文档）
  - 分类：农作物、果树、动物产品等
  - 属性：类别、来源
- ✅ 节日实体抽取（从节日文档）
  - 属性：时间、地点、活动
- ✅ 支持从目录批量提取

**支持的关系类型**：
- family - 家庭关系（父母、子女等）
- friend - 朋友关系
- work_at - 工作地点
- live_at - 居住地
- like/love/hate - 喜好关系

---

## 2. 待完成功能

### Phase 1: 图构建器（进行中）⏳

需要实现：
- [ ] KnowledgeGraphBuilder - 图构建器
- [ ] 从实体列表构建 NetworkX 图
- [ ] 添加节点和边
- [ ] 图可视化功能

### Phase 2: 图检索器 ⏳

需要实现：
- [ ] GraphRetriever - 图检索器
- [ ] 实体链接（从查询识别实体）
- [ ] k 跳邻居检索
- [ ] 关系路径检索
- [ ] 混合检索（向量 + 图）

### Phase 3: 集成到主系统 ⏳

需要修改：
- [ ] src/main_optimized.py - 添加图检索流程
- [ ] src/conversation/enhanced_conversation_manager.py - 增强上下文
- [ ] src/api/bailian_api.py - 支持图检索结果

### Phase 4: Neo4j 集成 ⏳

需要实现：
- [ ] Neo4jManager - Neo4j 连接管理
- [ ] 图数据持久化
- [ ] Cypher 查询接口
- [ ] 社区发现和摘要

---

## 3. 架构设计

### 3.1 整体架构

```
知识库 Markdown 文件
    ↓
EntityExtractor (实体抽取)
    ↓
KnowledgeGraphBuilder (图构建)
    ├── NetworkX (内存图)
    └── Neo4j (持久化图，可选)
    ↓
GraphRetriever (图检索)
    ├── 实体链接
    ├── 邻居检索
    └── 关系路径检索
    ↓
HybridRetriever (混合检索)
    ├── Vector Search (FAISS)
    └── Graph Search (NetworkX/Neo4j)
    ↓
EnhancedContext (增强上下文)
    ├── 向量检索结果
    ├── 图检索结果
    └── 关系路径
    ↓
LLM 生成回复
```

### 3.2 数据结构

#### 实体节点
```python
{
    "id": "char_阿比盖尔",
    "name": "阿比盖尔",
    "type": "character",
    "attributes": {
        "生日": "秋季第 14 天",
        "住址": "鹈鹕镇，皮埃尔的杂货店",
        "职业": "学生"
    }
}
```

#### 关系边
```python
{
    "source": "char_阿比盖尔",
    "target": "char_皮埃尔",
    "type": "father",
    "properties": {
        "confidence": 1.0
    }
}
```

---

## 4. 使用示例

### 4.1 实体抽取

```python
from graph.entity_extractor import EntityExtractor

# 创建抽取器
extractor = EntityExtractor()

# 从单个文件提取
entities = extractor.extract_from_markdown(
    "data/knowledge/居民详细/阿比盖尔.md"
)

# 从目录批量提取
all_entities = extractor.extract_from_directory(
    "data/knowledge"
)

print(f"提取了 {len(all_entities)} 个实体")
for entity in all_entities:
    print(f"- {entity.name} ({entity.type})")
    for rel in entity.relations:
        print(f"  └─ {rel['type']}: {rel['target']}")
```

### 4.2 图构建（待实现）

```python
from graph.graph_builder import KnowledgeGraphBuilder

# 创建构建器
builder = KnowledgeGraphBuilder()

# 从实体列表构建图
graph = builder.build_graph(all_entities)

# 可视化
builder.visualize(graph, "knowledge_graph.png")
```

### 4.3 图检索（待实现）

```python
from graph.graph_retriever import GraphRetriever

# 创建检索器
retriever = GraphRetriever(graph)

# 检索相关实体
related = retriever.retrieve_related_entities(
    query="阿比盖尔的朋友",
    k=5
)

# 关系路径检索
path = retriever.retrieve_relation_path(
    source="阿比盖尔",
    target="皮埃尔"
)
```

### 4.4 混合检索（待实现）

```python
# 在 main_optimized.py 中
def process_query(self, query):
    # 1. 向量检索
    vector_results = self.vector_store_manager.search(query, k=5)
    
    # 2. 图检索
    graph_results = self.graph_retriever.hybrid_retrieve(
        query, vector_results, k=10
    )
    
    # 3. 构建增强上下文
    context = self._build_enhanced_context(
        query, vector_results, graph_results
    )
    
    # 4. 生成回复
    return self.bailian_api.generate_with_context(...)
```

---

## 5. 预期效果

### 5.1 关系推理

**查询**: "阿比盖尔的朋友有哪些？"
- **当前**: 从向量检索找到相关文档
- **GraphRAG**: 直接从图中返回山姆、塞巴斯蒂安

### 5.2 多跳查询

**查询**: "塞巴斯蒂安的妹妹的爸爸是谁？"
- **路径**: 塞巴斯蒂安 → 玛鲁（妹妹）→ 德米特里厄斯（爸爸）
- **GraphRAG**: 通过关系路径推理得出答案

### 5.3 复杂查询

**查询**: "皮埃尔家的女儿喜欢什么？"
- **推理**: 皮埃尔 → 阿比盖尔（女儿）→ 紫水晶、巧克力蛋糕
- **GraphRAG**: 多跳关系检索

---

## 6. 下一步计划

### 立即可做
1. 实现 KnowledgeGraphBuilder
2. 实现 GraphRetriever
3. 集成到 main_optimized.py

### 短期计划
1. 添加图可视化
2. 实现关系路径检索
3. A/B 测试检索效果

### 长期计划
1. Neo4j 持久化
2. 社区发现和摘要
3. 图神经网络增强

---

## 7. 文件和目录

### 新增文件
```
src/graph/
├── entity_extractor.py          # 实体抽取器 ✅
├── graph_builder.py             # 图构建器 ⏳
├── graph_retriever.py           # 图检索器 ⏳
├── neo4j_manager.py             # Neo4j 管理 ⏳
└── __init__.py                  # 包初始化
```

### 更新文件
```
src/main_optimized.py            # 集成图检索
src/conversation/enhanced_conversation_manager.py
requirements.txt                 # 添加 graph 相关依赖
```

---

## 8. 测试和验证

### 测试用例
1. 实体抽取准确性
2. 关系提取准确性
3. 图检索召回率
4. 混合检索效果对比
5. 多跳查询成功率

### 评估指标
- 实体抽取 F1 值
- 关系抽取准确率
- 检索召回率@K
- 用户满意度评分

---

## 9. 总结

目前已完成 GraphRAG 的基础实体抽取功能，为后续图构建和检索打下了良好基础。

下一步需要实现图构建器和检索器，最终实现完整的 GraphRAG 功能，显著提升系统的关系推理和多跳查询能力。
