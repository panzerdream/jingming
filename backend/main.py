from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.main import AgentRAG

app = FastAPI()

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
        agent = AgentRAG()
        print("AgentRAG初始化成功")
    except Exception as e:
        print(f"AgentRAG初始化失败: {e}")

@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """处理用户查询"""
    global agent
    if not agent:
        raise HTTPException(status_code=500, detail="AgentRAG未初始化")
    
    try:
        response = agent.process_query(request.query)
        return QueryResponse(response=response)
    except Exception as e:
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