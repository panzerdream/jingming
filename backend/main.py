from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import sys
import os
import asyncio

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.main import AgentRAG

app = FastAPI()

# 获取端口配置
PORT = int(os.getenv('PORT', 8000))

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局AgentRAG实例
agent = None

# 请求模型
class QueryRequest(BaseModel):
    query: str

# 响应模型
class QueryResponse(BaseModel):
    response: str

@app.on_event("startup")
async def startup_event():
    """启动时初始化AgentRAG"""
    global agent
    try:
        # 切换到项目根目录
        os.chdir(os.path.join(os.path.dirname(__file__), '..'))
        print("正在初始化AgentRAG...")
        print(f"当前工作目录: {os.getcwd()}")
        print(f"config目录是否存在: {os.path.exists('config')}")
        print(f".env文件是否存在: {os.path.exists('config/.env')}")
        agent = AgentRAG()
        print("AgentRAG初始化成功")
    except Exception as e:
        print(f"AgentRAG初始化失败: {e}")
        import traceback
        traceback.print_exc()

@app.post("/api/query")
async def query(request: QueryRequest):
    """处理用户查询（流式输出）"""
    global agent
    if not agent:
        raise HTTPException(status_code=500, detail="AgentRAG未初始化")
    
    try:
        print(f"收到查询请求: {request.query}")
        
        # 生成响应
        response = agent.process_query(request.query)
        print(f"生成响应: {response}")
        
        # 流式输出
        async def generate():
            # 去除MD格式的标点符号
            response_clean = response.replace("#", "").replace("*", "").replace("_", "")
            # 处理换行符，确保前端能正确显示
            response_clean = response_clean.replace("\n", "<br>")
            # 分段输出
            chunks = response_clean.split(" ")
            for i, chunk in enumerate(chunks):
                if i > 0:
                    yield f" {chunk}"
                else:
                    yield chunk
                await asyncio.sleep(0.05)  # 控制输出速度
        
        return StreamingResponse(generate(), media_type="text/plain")
    except Exception as e:
        print(f"处理查询失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"处理查询失败: {str(e)}")

@app.post("/api/clear")
async def clear():
    """清空会话历史"""
    global agent
    if not agent:
        raise HTTPException(status_code=500, detail="AgentRAG未初始化")
    
    try:
        agent.clear_conversation()
        return {"message": "会话历史已清空"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空会话失败: {str(e)}")

@app.get("/")
async def root():
    """根路径"""
    return {"message": "星露谷风格RAG系统后端API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)