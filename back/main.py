import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import api_router
from app.db.database import create_tables
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    create_tables()
    print("数据库表创建完成")
    yield
    # 关闭时执行
    print("应用关闭")


# 创建FastAPI应用
app = FastAPI(
    title="视频分析系统API",
    description="用于视频录屏分析、阶段识别和性能对比的API系统",
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 包含API路由
app.include_router(api_router, prefix="")


@app.get("/")
def read_root():
    return {
        "message": "视频分析系统API",
        "version": "1.0.0",
        "docs": "/docs",
        "features": [
            "视频文件管理",
            "视频帧提取和分析",
            "AI行为描述生成",
            "阶段识别和耗时分析",
            "版本对比和竞品对比",
            "性能指标统计"
        ]
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "API服务运行正常"}


if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
