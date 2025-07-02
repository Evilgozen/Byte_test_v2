from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class VideoFrame(Base):
    __tablename__ = "video_frames"
    
    id = Column(Integer, primary_key=True, index=True)
    video_file_id = Column(Integer, ForeignKey("video_files.id"), nullable=False)
    frame_number = Column(Integer, nullable=False)  # 帧序号
    timestamp = Column(Float, nullable=False)  # 时间戳（秒）
    frame_path = Column(String(500), nullable=False)  # 帧图片路径
    width = Column(Integer, nullable=True)  # 帧宽度
    height = Column(Integer, nullable=True)  # 帧高度
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    video_file = relationship("VideoFile", back_populates="frames")
    behavior_descriptions = relationship("FrameBehaviorDescription", back_populates="frame")
    
    def __repr__(self):
        return f"<VideoFrame(id={self.id}, frame_number={self.frame_number})>"

class FrameBehaviorDescription(Base):
    __tablename__ = "frame_behavior_descriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    frame_id = Column(Integer, ForeignKey("video_frames.id"), nullable=False)
    description = Column(Text, nullable=False)  # AI生成的行为描述
    confidence = Column(Float, nullable=True)  # 置信度
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    frame = relationship("VideoFrame", back_populates="behavior_descriptions")
    
    def __repr__(self):
        return f"<FrameBehaviorDescription(id={self.id}, frame_id={self.frame_id})>"