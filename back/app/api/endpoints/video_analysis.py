from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.db.database import get_db
from app.services.ssim_video_service import SSIMVideoAnalysisService
from app.services.video_service import VideoFileService

router = APIRouter(prefix="/video-analysis", tags=["视频分析"])


@router.post("/ssim-analysis/{video_id}", summary="SSIM视频分析")
def analyze_video_with_ssim(
    video_id: int,
    product_name: str = Query(..., description="产品名称（用于向量存储的元数据）"),
    frame_interval: int = Query(30, ge=1, le=300, description="帧间隔（多少帧检测一次，默认30帧）"),
    ssim_threshold: float = Query(0.75, ge=0.1, le=0.99, description="SSIM阈值（默认0.75）"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    使用SSIM算法分析视频，提取关键帧并生成阶段分析结果
    
    参数:
    - video_id: 视频文件ID
    - frame_interval: 帧间隔，每隔多少帧进行一次SSIM检测（默认30帧）
    - ssim_threshold: SSIM相似度阈值，低于此值认为是关键帧（默认0.75）
    
    返回:
    - 包含关键帧信息和阶段分析结果的字典
    """
    try:
        # 检查视频文件是否存在
        video_service = VideoFileService(db)
        video_file = video_service.get_video_file(video_id)
        if not video_file:
            raise HTTPException(status_code=404, detail=f"视频文件不存在: {video_id}")
        
        # 执行SSIM分析
        ssim_service = SSIMVideoAnalysisService(db)
        result = ssim_service.analyze_video_with_ssim(
            video_id=video_id,
            product_name=product_name,
            frame_interval=frame_interval,
            ssim_threshold=ssim_threshold
        )
        
        return {
            "success": True,
            "message": "SSIM视频分析完成",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析过程中发生错误: {str(e)}")


@router.delete("/analysis/{video_id}", summary="删除视频分析结果")
def delete_video_analysis(
    video_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    删除指定视频的所有分析结果，包括关键帧和阶段信息
    
    参数:
    - video_id: 视频文件ID
    
    返回:
    - 删除操作的结果信息
    """
    try:
        # 检查视频文件是否存在
        video_service = VideoFileService(db)
        video_file = video_service.get_video_file(video_id)
        if not video_file:
            raise HTTPException(status_code=404, detail=f"视频文件不存在: {video_id}")
        
        # 删除分析结果
        ssim_service = SSIMVideoAnalysisService(db)
        result = ssim_service.delete_video_analysis(video_id)
        
        return {
            "success": True,
            "message": "视频分析结果删除成功",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除过程中发生错误: {str(e)}")


@router.get("/video/{video_id}/stages", summary="获取视频阶段信息")
def get_video_stages(
    video_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取指定视频的阶段分析信息
    
    参数:
    - video_id: 视频文件ID
    
    返回:
    - 视频的阶段信息列表
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
        
        stages_data = []
        for stage in stages:
            stages_data.append({
                "id": stage.id,
                "stage_name": stage.stage_name,
                "start_time": stage.start_time,
                "end_time": stage.end_time,
                "duration": stage.duration,
                "description": stage.description,
                "created_at": stage.created_at.isoformat() if stage.created_at else None
            })
        
        return {
            "success": True,
            "video_id": video_id,
            "total_stages": len(stages_data),
            "stages": stages_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取阶段信息时发生错误: {str(e)}")


@router.get("/video/{video_id}/keyframes", summary="获取视频关键帧信息")
def get_video_keyframes(
    video_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取指定视频的关键帧信息
    
    参数:
    - video_id: 视频文件ID
    
    返回:
    - 视频的关键帧信息列表
    """
    try:
        # 检查视频文件是否存在
        video_service = VideoFileService(db)
        video_file = video_service.get_video_file(video_id)
        if not video_file:
            raise HTTPException(status_code=404, detail=f"视频文件不存在: {video_id}")
        
        # 获取关键帧信息
        from app.services.video_service import VideoFrameService
        frame_service = VideoFrameService(db)
        frames = frame_service.get_video_frames(video_id)
        
        frames_data = []
        for frame in frames:
            frames_data.append({
                "id": frame.id,
                "frame_number": frame.frame_number,
                "timestamp": frame.timestamp,
                "frame_path": frame.frame_path,
                "width": frame.width,
                "height": frame.height,
                "created_at": frame.created_at.isoformat() if frame.created_at else None
            })
        
        return {
            "success": True,
            "video_id": video_id,
            "total_frames": len(frames_data),
            "keyframes": frames_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取关键帧信息时发生错误: {str(e)}")


@router.post("/rag/query-similar-stages", summary="查询相似视频阶段")
def query_similar_video_stages(
    query: str = Query(..., description="查询描述"),
    product_name: str = Query(None, description="产品名称过滤（可选）"),
    k: int = Query(5, ge=1, le=20, description="返回结果数量（默认5）"),
    similarity_threshold: float = Query(0.7, ge=0.0, le=1.0, description="相似度阈值（默认0.7）"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    基于RAG查询相似的视频阶段分析
    
    参数:
    - query: 查询描述文本
    - product_name: 产品名称过滤（可选）
    - k: 返回结果数量
    - similarity_threshold: 相似度阈值，只返回相似度大于此值的结果
    
    返回:
    - 相似阶段的分析结果，包含视频ID和阶段ID
    """
    try:
        ssim_service = SSIMVideoAnalysisService(db)
        result = ssim_service.query_similar_video_stages(
            query=query,
            product_name=product_name,
            k=k,
            similarity_threshold=similarity_threshold
        )
        
        return {
            "success": True,
            "message": "相似阶段查询完成",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询过程中发生错误: {str(e)}")


@router.post("/rag/generate-comparison-report", summary="生成阶段对比报告")
def generate_stage_comparison_report(
    query: str = Query(..., description="查询描述"),
    product_name: str = Query(None, description="产品名称过滤（可选）"),
    similarity_threshold: float = Query(0.7, ge=0.0, le=1.0, description="相似度阈值（默认0.7）"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    生成基于RAG的阶段对比分析报告
    
    参数:
    - query: 查询描述文本
    - product_name: 产品名称过滤（可选）
    - similarity_threshold: 相似度阈值，只使用相似度大于此值的结果生成报告
    
    返回:
    - 生成的对比分析报告
    """
    try:
        ssim_service = SSIMVideoAnalysisService(db)
        result = ssim_service.generate_stage_comparison_report(
            query=query,
            product_name=product_name,
            similarity_threshold=similarity_threshold
        )
        
        return {
            "success": True,
            "message": "对比报告生成完成",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"报告生成过程中发生错误: {str(e)}")