from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class VideoStage(Base):
    __tablename__ = "video_stages"
    
    id = Column(Integer, primary_key=True, index=True)
    video_file_id = Column(Integer, ForeignKey("video_files.id"), nullable=False)
    stage_name = Column(String(255), nullable=False)  # 阶段名称
    start_time = Column(Float, nullable=False)  # 开始时间（秒）
    end_time = Column(Float, nullable=False)  # 结束时间（秒）
    duration = Column(Float, nullable=False)  # 持续时间（秒）
    description = Column(Text, nullable=True)  # 阶段描述
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    video_file = relationship("VideoFile")
    metrics = relationship("StageMetric", back_populates="stage")
    
    def __repr__(self):
        return f"<VideoStage(id={self.id}, stage_name='{self.stage_name}')>"

class StageMetric(Base):
    __tablename__ = "stage_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    stage_id = Column(Integer, ForeignKey("video_stages.id"), nullable=False)
    metric_name = Column(String(255), nullable=False)  # 指标名称
    metric_value = Column(Float, nullable=False)  # 指标值
    unit = Column(String(50), nullable=True)  # 单位
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    stage = relationship("VideoStage", back_populates="metrics")
    
    def __repr__(self):
        return f"<StageMetric(id={self.id}, metric_name='{self.metric_name}')>"

class VideoComparison(Base):
    __tablename__ = "video_comparisons"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # 对比名称
    description = Column(Text, nullable=True)  # 对比描述
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    details = relationship("ComparisonDetail", back_populates="comparison")
    
    def __repr__(self):
        return f"<VideoComparison(id={self.id}, name='{self.name}')>"

class ComparisonDetail(Base):
    __tablename__ = "comparison_details"
    
    id = Column(Integer, primary_key=True, index=True)
    comparison_id = Column(Integer, ForeignKey("video_comparisons.id"), nullable=False)
    video_file_id = Column(Integer, ForeignKey("video_files.id"), nullable=False)
    role = Column(String(100), nullable=False)  # 角色（如：baseline, competitor）
    notes = Column(Text, nullable=True)  # 备注
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    comparison = relationship("VideoComparison", back_populates="details")
    video_file = relationship("VideoFile")
    
    def __repr__(self):
        return f"<ComparisonDetail(id={self.id}, role='{self.role}')>"