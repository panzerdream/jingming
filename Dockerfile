# 后端服务 Dockerfile
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .
COPY backend/requirements.txt backend/

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# 复制源代码
COPY . .

# 设置环境变量
ENV PORT=8000
ENV BAILIAN_API_KEY=your_api_key_here
ENV BAILIAN_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 暴露端口
EXPOSE 8000

# 启动后端服务
CMD ["python", "backend/main.py"]
