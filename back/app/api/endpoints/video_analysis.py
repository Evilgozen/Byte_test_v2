from fastapi import APIRouter

router = APIRouter(prefix="/video-analysis", tags=["视频分析"])

@router.get("/")
def get_analysis_info():
    """获取视频分析信息"""
    return {
        "message": "视频分析模块",
        "features": [
            "视频帧提取",
            "行为描述生成",
            "阶段识别",
            "性能对比"
        ]
    }