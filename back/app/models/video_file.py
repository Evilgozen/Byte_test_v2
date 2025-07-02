from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class VideoFile(Base):
    __tablename__ = "video_files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # 文件大小（字节）
    duration = Column(Float, nullable=True)  # 视频时长（秒）
    width = Column(Integer, nullable=True)  # 视频宽度
    height = Column(Integer, nullable=True)  # 视频高度
    fps = Column(Float, nullable=True)  # 帧率
    format = Column(String(50), nullable=True)  # 视频格式
    description = Column(Text, nullable=True)  # 描述
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    frames = relationship("VideoFrame", back_populates="video_file")
    
    def __repr__(self):
        return f"<VideoFile(id={self.id}, filename='{self.filename}')>"