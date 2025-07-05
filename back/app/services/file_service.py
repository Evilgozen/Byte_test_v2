import os
import cv2
import shutil
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from app.models.video_file import VideoFile
from app.models.video_frame import VideoFrame
from app.schemas.file_schemas import VideoFileCreate, VideoFileUpdate, FrameExtractionServiceRequest
from app.utils.frame_extractor import VideoFrameExtractor

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
    
    def extract_frames(self, request: FrameExtractionServiceRequest) -> List[VideoFrame]:
        """提取视频帧"""
        video_file = self.get_video_file(request.video_file_id)
        if not video_file:
            raise HTTPException(status_code=404, detail="视频文件不存在")
        
        if not os.path.exists(video_file.file_path):
            raise HTTPException(status_code=404, detail="视频文件路径不存在")
        
        # 创建帧存储目录
        video_frames_dir = os.path.join(self.frames_dir, f"video_{video_file.id}")
        os.makedirs(video_frames_dir, exist_ok=True)
        
        # 清理已存在的帧记录
        existing_frames = self.db.query(VideoFrame).filter(
            VideoFrame.video_file_id == video_file.id
        ).all()
        for frame in existing_frames:
            if os.path.exists(frame.frame_path):
                os.remove(frame.frame_path)
            self.db.delete(frame)
        
        # 使用模块化的帧提取器
        extractor = VideoFrameExtractor()
        
        # 准备提取参数
        extraction_params = {
            'interval': request.interval,
            'max_frames': request.max_frames,
            'frames_per_second': request.frames_per_second,
            'threshold': 0.3  # 关键帧检测阈值
        }
        
        try:
            # 提取帧
            frame_info_list = extractor.extract_frames(
                video_file.file_path,
                video_frames_dir,
                request.extraction_method or "uniform",
                **extraction_params
            )
            
            # 创建数据库记录
            extracted_frames = []
            for frame_number, timestamp, frame_path in frame_info_list:
                # 获取帧尺寸
                frame_img = cv2.imread(frame_path)
                height, width = frame_img.shape[:2] if frame_img is not None else (0, 0)
                
                db_frame = VideoFrame(
                    video_file_id=video_file.id,
                    frame_number=frame_number,
                    timestamp=timestamp,
                    frame_path=frame_path,
                    width=width,
                    height=height
                )
                
                self.db.add(db_frame)
                extracted_frames.append(db_frame)
            
            self.db.commit()
            return extracted_frames
            
        except Exception as e:
            # 清理可能创建的文件
            if os.path.exists(video_frames_dir):
                for file in os.listdir(video_frames_dir):
                    file_path = os.path.join(video_frames_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"帧提取失败: {str(e)}")
    
    def get_video_frames(self, video_file_id: int) -> List[VideoFrame]:
        """获取视频的所有帧"""
        return self.db.query(VideoFrame).filter(VideoFrame.video_file_id == video_file_id).all()
    
    def delete_video_frames(self, video_file_id: int) -> int:
        """删除视频对应的所有分割帧"""
        # 获取所有相关的帧记录
        frames = self.db.query(VideoFrame).filter(VideoFrame.video_file_id == video_file_id).all()
        
        deleted_count = 0
        
        # 删除物理文件和数据库记录
        for frame in frames:
            try:
                # 删除物理文件
                if os.path.exists(frame.frame_path):
                    os.remove(frame.frame_path)
                
                # 删除数据库记录
                self.db.delete(frame)
                deleted_count += 1
                
            except Exception as e:
                print(f"删除帧文件失败: {frame.frame_path}, 错误: {e}")
                # 即使文件删除失败，也删除数据库记录
                self.db.delete(frame)
                deleted_count += 1
        
        # 尝试删除帧目录（如果为空）
        try:
            video_frames_dir = os.path.join(self.frames_dir, f"video_{video_file_id}")
            if os.path.exists(video_frames_dir) and not os.listdir(video_frames_dir):
                os.rmdir(video_frames_dir)
        except Exception as e:
            print(f"删除帧目录失败: {e}")
        
        self.db.commit()
        return deleted_count
    
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