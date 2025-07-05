from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os

from app.db.database import get_db
from app.services.file_service import FileService
from app.models.video_frame import VideoFrame
from app.schemas.file_schemas import (
    VideoFileResponse, 
    VideoFileUpdate, 
    VideoFrameResponse,
    FrameExtractionRequest,
    FrameExtractionServiceRequest,
    FrameExtractionResponse
)

router = APIRouter(prefix="/files", tags=["文件管理"])

@router.post("/upload", response_model=VideoFileResponse, summary="上传视频文件")
async def upload_video_file(
    file: UploadFile = File(..., description="视频文件"),
    db: Session = Depends(get_db)
):
    """上传视频文件"""
    file_service = FileService(db)
    try:
        video_file = await file_service.upload_video_file(file)
        return video_file
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[VideoFileResponse], summary="获取视频文件列表")
def get_video_files(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    db: Session = Depends(get_db)
):
    """获取视频文件列表"""
    file_service = FileService(db)
    return file_service.get_video_files(skip=skip, limit=limit)

@router.get("/{file_id}", response_model=VideoFileResponse, summary="获取视频文件详情")
def get_video_file(
    file_id: int,
    db: Session = Depends(get_db)
):
    """获取视频文件详情"""
    file_service = FileService(db)
    video_file = file_service.get_video_file(file_id)
    if not video_file:
        raise HTTPException(status_code=404, detail="视频文件不存在")
    return video_file

@router.put("/{file_id}", response_model=VideoFileResponse, summary="更新视频文件信息")
def update_video_file(
    file_id: int,
    file_update: VideoFileUpdate,
    db: Session = Depends(get_db)
):
    """更新视频文件信息"""
    file_service = FileService(db)
    video_file = file_service.update_video_file(file_id, file_update)
    if not video_file:
        raise HTTPException(status_code=404, detail="视频文件不存在")
    return video_file

@router.delete("/{file_id}", summary="删除视频文件")
def delete_video_file(
    file_id: int,
    db: Session = Depends(get_db)
):
    """删除视频文件"""
    file_service = FileService(db)
    success = file_service.delete_video_file(file_id)
    if not success:
        raise HTTPException(status_code=404, detail="视频文件不存在")
    return {"message": "视频文件删除成功"}

@router.get("/{file_id}/download", summary="下载视频文件")
def download_video_file(
    file_id: int,
    db: Session = Depends(get_db)
):
    """下载视频文件"""
    file_service = FileService(db)
    video_file = file_service.get_video_file(file_id)
    if not video_file:
        raise HTTPException(status_code=404, detail="视频文件不存在")
    
    if not os.path.exists(video_file.file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        path=video_file.file_path,
        filename=video_file.original_filename,
        media_type='application/octet-stream'
    )

@router.post("/{file_id}/extract-frames", response_model=FrameExtractionResponse, summary="提取视频帧")
def extract_video_frames(
    file_id: int,
    request: FrameExtractionRequest,
    db: Session = Depends(get_db)
):
    """提取视频帧"""
    file_service = FileService(db)
    
    # 创建内部服务请求对象
    service_request = FrameExtractionServiceRequest(
        video_file_id=file_id,
        interval=request.interval,
        max_frames=request.max_frames,
        extraction_method=request.extraction_method,
        frames_per_second=request.frames_per_second
    )
    
    try:
        extracted_frames = file_service.extract_frames(service_request)
        return FrameExtractionResponse(
            video_file_id=file_id,
            total_frames=len(extracted_frames),
            extracted_frames=extracted_frames,
            message=f"成功提取 {len(extracted_frames)} 帧"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{file_id}/frames", response_model=List[VideoFrameResponse], summary="获取视频帧列表")
def get_video_frames(
    file_id: int,
    db: Session = Depends(get_db)
):
    """获取视频帧列表"""
    file_service = FileService(db)
    
    # 检查视频文件是否存在
    video_file = file_service.get_video_file(file_id)
    if not video_file:
        raise HTTPException(status_code=404, detail="视频文件不存在")
    
    frames = file_service.get_video_frames(file_id)
    return frames

@router.get("/frames/{frame_id}/image", summary="获取帧图片")
def get_frame_image(
    frame_id: int,
    db: Session = Depends(get_db)
):
    """获取帧图片"""
    frame = db.query(VideoFrame).filter(VideoFrame.id == frame_id).first()
    if not frame:
        raise HTTPException(status_code=404, detail="帧不存在")
    
    if not os.path.exists(frame.frame_path):
        raise HTTPException(status_code=404, detail="帧图片文件不存在")
    
    return FileResponse(
        path=frame.frame_path,
        media_type='image/jpeg'
    )

@router.delete("/{file_id}/frames", summary="删除视频对应的所有分割帧")
def delete_video_frames(
    file_id: int,
    db: Session = Depends(get_db)
):
    """删除视频对应的所有分割帧"""
    file_service = FileService(db)
    
    # 检查视频文件是否存在
    video_file = file_service.get_video_file(file_id)
    if not video_file:
        raise HTTPException(status_code=404, detail="视频文件不存在")
    
    try:
        deleted_count = file_service.delete_video_frames(file_id)
        return {
            "message": f"成功删除 {deleted_count} 个视频帧",
            "video_file_id": file_id,
            "deleted_frames_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))