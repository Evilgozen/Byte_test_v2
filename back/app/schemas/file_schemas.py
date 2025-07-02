from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# VideoFile schemas
class VideoFileBase(BaseModel):
    filename: str
    original_filename: str
    description: Optional[str] = None

class VideoFileCreate(VideoFileBase):
    file_path: str
    file_size: int
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    format: Optional[str] = None

class VideoFileUpdate(BaseModel):
    filename: Optional[str] = None
    description: Optional[str] = None

class VideoFileResponse(VideoFileBase):
    id: int
    file_path: str
    file_size: int
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    format: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# VideoFrame schemas
class VideoFrameBase(BaseModel):
    frame_number: int
    timestamp: float

class VideoFrameCreate(VideoFrameBase):
    video_file_id: int
    frame_path: str
    width: Optional[int] = None
    height: Optional[int] = None

class VideoFrameResponse(VideoFrameBase):
    id: int
    video_file_id: int
    frame_path: str
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Frame extraction request
class FrameExtractionRequest(BaseModel):
    video_file_id: int
    interval: Optional[float] = 1.0  # 提取间隔（秒）
    max_frames: Optional[int] = None  # 最大帧数

# Frame extraction response
class FrameExtractionResponse(BaseModel):
    video_file_id: int
    total_frames: int
    extracted_frames: List[VideoFrameResponse]
    message: str