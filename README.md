# Agent RAG系统

基于LangChain和阿里云百炼API的知识库聊天机器人系统。

## 项目简介

本项目使用RAG（Retrieval-Augmented Generation）技术，将markdown文件转换为向量数据库，结合阿里云百炼API生成高质量的回答。系统具备自然语言理解、工具使用能力、记忆和学习、自主决策等核心功能。

## 技术栈

- **编程语言**：Python 3.8+
- **核心框架**：LangChain
- **向量存储**：FAISS（本地）
- **文本处理**：Markdown解析器
- **API服务**：阿里云百炼API

## 项目结构

```
agent-rag/
├── docs/                  # 文档
├── src/                   # 源代码
│   ├── document_processing/  # 文档处理模块
│   ├── vector_store/         # 向量存储模块
│   ├── retrieval/            # 检索模块
│   ├── conversation/         # 对话管理模块
│   ├── tools/                # 工具使用模块
│   ├── api/                  # API集成模块
│   └── main.py               # 主入口
├── config/                # 配置文件
├── data/                  # 数据目录
│   ├── knowledge/           # 知识库文件
│   └── vector_db/           # 向量数据库
├── tests/                 # 测试文件
├── requirements.txt       # 依赖声明
└── README.md              # 项目说明
```

## 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置

在`config/`目录下创建`.env`文件，配置阿里云百炼API的相关参数：

```env
# 阿里云百炼API配置
BAILIAN_API_KEY=your_api_key
BAILIAN_API_URL=your_api_url

# 向量存储配置
VECTOR_STORE_PATH=data/vector_db

# 知识库配置
KNOWLEDGE_BASE_PATH=data/knowledge
```

### 3. 准备知识库

将markdown文件放入`data/knowledge/`目录。

### 4. 运行系统

```bash
# 启动系统
python src/main.py
```

## 功能模块

### 文档处理
- 解析markdown文件
- 文本分块处理
- 元数据提取

### 向量存储
- 文本向量化
- 向量存储管理
- 索引优化

### 检索功能
- 相似性搜索
- 结果排序
- 上下文构建

### 对话管理
- 会话历史管理
- 意图识别
- 回复生成

### 工具使用
- 工具注册与管理
- 工具调用执行
- 结果处理

### 阿里云百炼API集成
- API调用封装
- 模型参数配置
- 响应处理

## 扩展性

系统采用模块化设计，支持以下扩展：

- 添加新的工具和功能
- 集成其他语言模型
- 添加重排序功能
- 支持更多文档格式

## 测试

```bash
# 运行测试
pytest tests/
```

## 部署

### 本地部署
适合开发和测试环境。

### 容器化部署
使用Docker容器部署：

```bash
# 构建镜像
docker build -t agent-rag .

# 运行容器
docker run -p 8000:8000 agent-rag
```

### 云端部署
可部署到云服务器或云函数平台。

## 注意事项

- 阿里云百炼API可能有调用频率限制，请合理使用
- 向量存储性能会随着知识库增大而下降，需定期优化
- 可通过调整提示词和参数提高模型响应质量
- 建议添加错误处理和日志记录以提高系统稳定性