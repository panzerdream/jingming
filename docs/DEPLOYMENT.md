# 星露谷助手 RAG 系统部署指南

本指南详细说明如何使用 Docker 部署星露谷助手 RAG 系统，包括环境准备、配置修改、构建运行和常见问题解决。

## 环境准备

### 1. 安装 Docker

确保您的系统已安装 Docker 和 Docker Compose：

- **Windows/macOS**：下载并安装 [Docker Desktop](https://www.docker.com/products/docker-desktop)
- **Linux**：按照 [Docker 官方文档](https://docs.docker.com/engine/install/) 安装 Docker 和 Docker Compose

### 2. 克隆代码库

```bash
git clone <repository-url>
cd agent-rag
```

## 配置修改

### 1. 配置 API 密钥

编辑 `config/.env` 文件，设置您的阿里云百炼 API 密钥：

```env
# 阿里云百炼 API 配置
BAILIAN_API_KEY=your_api_key_here
BAILIAN_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 向量存储配置
VECTOR_STORE_PATH=data/vector_db
KNOWLEDGE_BASE_PATH=data/knowledge

# 模型配置
MODEL_NAME=qwen-turbo

# 检索配置
TOP_K=5
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### 2. 配置 Docker 环境变量

编辑 `docker-compose.yml` 文件，根据需要修改环境变量：

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
      - BAILIAN_API_KEY=your_api_key_here
      - BAILIAN_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
      - VECTOR_STORE_PATH=data/vector_db
      - KNOWLEDGE_BASE_PATH=data/knowledge
    volumes:
      - ./data:/app/data
      - ./config:/app/config

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.frontend
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://backend:8000
    depends_on:
      - backend
```

## 构建和运行

### 1. 构建 Docker 镜像

在项目根目录执行以下命令：

```bash
docker-compose build
```

### 2. 启动服务

```bash
docker-compose up -d
```

### 3. 查看服务状态

```bash
docker-compose ps
```

## 访问服务

- **前端界面**：http://localhost:5173
- **后端 API**：http://localhost:8000

## 停止服务

```bash
docker-compose down
```

## 常见问题解决

### 1. 端口被占用

如果遇到端口被占用的问题，可以修改 `docker-compose.yml` 文件中的端口映射：

```yaml
# 例如，将前端端口改为 3000，后端端口改为 8080
frontend:
  ports:
    - "3000:5173"

backend:
  ports:
    - "8080:8000"
```

同时需要修改前端的环境变量：

```yaml
frontend:
  environment:
    - VITE_API_URL=http://backend:8000  # 注意：这里使用的是容器内部的端口
```

### 2. API 调用失败

- 检查 `config/.env` 文件中的 API 密钥是否正确
- 确保网络连接正常，能够访问阿里云百炼 API
- 检查后端服务日志：
  ```bash
  docker-compose logs backend
  ```

### 3. 向量存储初始化失败

- 检查 `data/knowledge` 目录是否存在 Markdown 文件
- 检查后端服务日志：
  ```bash
  docker-compose logs backend
  ```

### 4. 前端无法连接后端

- 检查 `docker-compose.yml` 文件中的 `VITE_API_URL` 是否正确
- 确保后端服务正在运行
- 检查前端服务日志：
  ```bash
  docker-compose logs frontend
  ```

## 数据持久化

系统会将向量存储和知识库文件存储在 `data` 目录中，确保该目录的权限正确，并且在容器重启后数据不会丢失。

## 部署到生产环境

在生产环境中，建议：

1. 使用环境变量注入敏感信息，而不是硬编码在配置文件中
2. 配置反向代理（如 Nginx）处理 HTTPS 和负载均衡
3. 定期备份 `data` 目录中的数据
4. 监控服务运行状态，设置告警机制

## 版本更新

当代码更新后，需要重新构建和启动服务：

```bash
docker-compose down
docker-compose build
docker-compose up -d
```

---

通过以上步骤，您可以成功部署星露谷助手 RAG 系统，开始与系统进行交互。如果遇到任何问题，请参考常见问题解决部分，或查看服务日志获取详细信息。