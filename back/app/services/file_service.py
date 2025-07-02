import os
import cv2
import shutil
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from app.models.video_file import VideoFile
from app.models.video_frame import VideoFrame
from app.schemas.file_schemas import VideoFileCreate, VideoFileUpdate, FrameExtractionRequest

class FileService:
    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = "static/files"
        self.frames_dir = "static/cut_files"
        
        # 确保目录存在
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.frames_dir, exist_ok=True)
    
    async def upload_video_file(self, file: UploadFile) -> VideoFile:
        """上传视频文件"""
        # 检查文件类型
        if not file.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="只支持视频文件")
        
        # 生成唯一文件名
        import uuid
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(self.upload_dir, unique_filename)
        
        # 保存文件
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
        
        # 获取文件信息
        file_size = os.path.getsize(file_path)
        video_info = self._get_video_info(file_path)
        
        # 创建数据库记录
        video_file_data = VideoFileCreate(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            **video_info
        )
        
        db_video_file = VideoFile(**video_file_data.dict())
        self.db.add(db_video_file)
        self.db.commit()
        self.db.refresh(db_video_file)
        
        return db_video_file
    
    def get_video_file(self, file_id: int) -> Optional[VideoFile]:
        """获取视频文件信息"""
        return self.db.query(VideoFile).filter(VideoFile.id == file_id).first()
    
    def get_video_files(self, skip: int = 0, limit: int = 100) -> List[VideoFile]:
        """获取视频文件列表"""
        return self.db.query(VideoFile).offset(skip).limit(limit).all()
    
    def update_video_file(self, file_id: int, file_update: VideoFileUpdate) -> Optional[VideoFile]:
        """更新视频文件信息"""
        db_video_file = self.get_video_file(file_id)
        if not db_video_file:
            return None
        
        update_data = file_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_video_file, field, value)
        
        self.db.commit()
        self.db.refresh(db_video_file)
        return db_video_file
    
    def delete_video_file(self, file_id: int) -> bool:
        """删除视频文件"""
        db_video_file = self.get_video_file(file_id)
        if not db_video_file:
            return False
        
        # 删除物理文件
        try:
            if os.path.exists(db_video_file.file_path):
                os.remove(db_video_file.file_path)
        except Exception as e:
            print(f"删除文件失败: {e}")
        
        # 删除相关的帧文件
        frames = self.db.query(VideoFrame).filter(VideoFrame.video_file_id == file_id).all()
        for frame in frames:
            try:
                if os.path.exists(frame.frame_path):
                    os.remove(frame.frame_path)
            except Exception as e:
                print(f"删除帧文件失败: {e}")
        
        # 删除数据库记录
        self.db.delete(db_video_file)
        self.db.commit()
        return True
    
    def extract_frames(self, request: FrameExtractionRequest) -> List[VideoFrame]:
        """提取视频帧"""
        video_file = self.get_video_file(request.video_file_id)
        if not video_file:
            raise HTTPException(status_code=404, detail="视频文件不存在")
        
        if not os.path.exists(video_file.file_path):
            raise HTTPException(status_code=404, detail="视频文件路径不存在")
        
        # 创建帧存储目录
        video_frames_dir = os.path.join(self.frames_dir, f"video_{video_file.id}")
        os.makedirs(video_frames_dir, exist_ok=True)
        
        # 使用OpenCV提取帧
        cap = cv2.VideoCapture(video_file.file_path)
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="无法打开视频文件")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        extracted_frames = []
        frame_count = 0
        
        # 计算提取间隔
        interval_frames = int(fps * request.interval) if request.interval else 1
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 按间隔提取帧
                if frame_count % interval_frames == 0:
                    timestamp = frame_count / fps
                    frame_filename = f"frame_{frame_count:06d}.jpg"
                    frame_path = os.path.join(video_frames_dir, frame_filename)
                    
                    # 保存帧图片
                    cv2.imwrite(frame_path, frame)
                    
                    # 创建数据库记录
                    db_frame = VideoFrame(
                        video_file_id=video_file.id,
                        frame_number=frame_count,
                        timestamp=timestamp,
                        frame_path=frame_path,
                        width=frame.shape[1],
                        height=frame.shape[0]
                    )
                    
                    self.db.add(db_frame)
                    extracted_frames.append(db_frame)
                    
                    # 检查最大帧数限制
                    if request.max_frames and len(extracted_frames) >= request.max_frames:
                        break
                
                frame_count += 1
        
        finally:
            cap.release()
        
        self.db.commit()
        return extracted_frames
    
    def get_video_frames(self, video_file_id: int) -> List[VideoFrame]:
        """获取视频的所有帧"""
        return self.db.query(VideoFrame).filter(VideoFrame.video_file_id == video_file_id).all()
    
    def _get_video_info(self, file_path: str) -> dict:
        """获取视频信息"""
        try:
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                return {}
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else None
            
            cap.release()
            
            return {
                "duration": duration,
                "width": width,
                "height": height,
                "fps": fps,
                "format": os.path.splitext(file_path)[1][1:].upper()
            }
        except Exception as e:
            print(f"获取视频信息失败: {e}")
            return {}