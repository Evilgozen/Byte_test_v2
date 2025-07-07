from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.db.database import get_db
from app.services.stage_matching_service import StageMatchingService
from app.services.video_service import VideoFileService
from app.schemas.video_schemas import StageMatchingRequest, StageMatchingResponse

router = APIRouter(prefix="/stage-matching", tags=["阶段匹配"])


@router.post("/match", summary="阶段匹配分析", response_model=StageMatchingResponse)
def match_stages(
    request: StageMatchingRequest,
    db: Session = Depends(get_db)
) -> StageMatchingResponse:
    """
    使用LangChain和豆包AI进行阶段匹配分析
    
    参数:
    - user_input: 用户输入的查询文本
    - video_id: 视频文件ID
    
    返回:
    - 匹配的阶段信息列表，包含相似度分数和匹配原因
    """
    try:
        # 检查视频文件是否存在
        video_service = VideoFileService(db)
        video_file = video_service.get_video_file(request.video_id)
        if not video_file:
            raise HTTPException(status_code=404, detail=f"视频文件不存在: {request.video_id}")
        
        # 执行阶段匹配分析
        matching_service = StageMatchingService(db)
        result = matching_service.match_stages(request)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"阶段匹配分析过程中发生错误: {str(e)}")


@router.get("/video/{video_id}/stages-summary", summary="获取视频阶段摘要")
def get_video_stages_summary(
    video_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取指定视频的阶段摘要信息，用于用户了解可匹配的阶段
    
    参数:
    - video_id: 视频文件ID
    
    返回:
    - 视频阶段的摘要信息
    """
    try:
        # 检查视频文件是否存在
        video_service = VideoFileService(db)
        video_file = video_service.get_video_file(video_id)
        if not video_file:
            raise HTTPException(status_code=404, detail=f"视频文件不存在: {video_id}")
        
        # 获取阶段信息
        from app.services.video_service import VideoStageService
        stage_service = VideoStageService(db)
        stages = stage_service.get_video_stages(video_id)
        
        if not stages:
            return {
                "success": False,
                "video_id": video_id,
                "message": "该视频暂无阶段信息，请先进行视频分析",
                "total_stages": 0,
                "stages_summary": []
            }
        
        # 构建阶段摘要
        stages_summary = []
        for stage in stages:
            stages_summary.append({
                "id": stage.id,
                "stage_name": stage.stage_name,
                "start_time": stage.start_time,
                "end_time": stage.end_time,
                "duration": stage.duration,
                "description": stage.description or "无描述"
            })
        
        return {
            "success": True,
            "video_id": video_id,
            "total_stages": len(stages_summary),
            "stages_summary": stages_summary,
            "message": "阶段信息获取成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取阶段摘要时发生错误: {str(e)}")


@router.post("/batch-match", summary="批量阶段匹配")
def batch_match_stages(
    requests: list[StageMatchingRequest],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    批量进行阶段匹配分析
    
    参数:
    - requests: 多个阶段匹配请求
    
    返回:
    - 批量匹配结果
    """
    try:
        if len(requests) > 10:
            raise HTTPException(status_code=400, detail="批量请求数量不能超过10个")
        
        matching_service = StageMatchingService(db)
        video_service = VideoFileService(db)
        
        results = []
        for request in requests:
            # 检查视频文件是否存在
            video_file = video_service.get_video_file(request.video_id)
            if not video_file:
                results.append({
                    "success": False,
                    "user_input": request.user_input,
                    "video_id": request.video_id,
                    "error": f"视频文件不存在: {request.video_id}"
                })
                continue
            
            # 执行匹配
            result = matching_service.match_stages(request)
            results.append(result.dict())
        
        return {
            "success": True,
            "total_requests": len(requests),
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量阶段匹配过程中发生错误: {str(e)}")