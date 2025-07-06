from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# FrameBehaviorDescription schemas
class FrameBehaviorDescriptionBase(BaseModel):
    description: str
    confidence: Optional[float] = None

class FrameBehaviorDescriptionCreate(FrameBehaviorDescriptionBase):
    frame_id: int

class FrameBehaviorDescriptionResponse(FrameBehaviorDescriptionBase):
    id: int
    frame_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# VideoStage schemas
class VideoStageBase(BaseModel):
    stage_name: str
    start_time: float
    end_time: float
    duration: float
    description: Optional[str] = None

class VideoStageCreate(VideoStageBase):
    video_file_id: int

class VideoStageResponse(VideoStageBase):
    id: int
    video_file_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# StageMetric schemas
class StageMetricBase(BaseModel):
    metric_name: str
    metric_value: float
    unit: Optional[str] = None

class StageMetricCreate(StageMetricBase):
    stage_id: int

class StageMetricResponse(StageMetricBase):
    id: int
    stage_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# VideoComparison schemas
class VideoComparisonBase(BaseModel):
    name: str
    description: Optional[str] = None

class VideoComparisonCreate(VideoComparisonBase):
    pass

class VideoComparisonResponse(VideoComparisonBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ComparisonDetail schemas
class ComparisonDetailBase(BaseModel):
    role: str
    notes: Optional[str] = None

class ComparisonDetailCreate(ComparisonDetailBase):
    comparison_id: int
    video_file_id: int

class ComparisonDetailResponse(ComparisonDetailBase):
    id: int
    comparison_id: int
    video_file_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# SSIM Analysis schemas
class SSIMAnalysisRequest(BaseModel):
    frame_interval: int = 30
    ssim_threshold: float = 0.75

class SSIMAnalysisResponse(BaseModel):
    video_id: int
    total_keyframes: int
    keyframes: List[dict]
    stage_analysis: dict
    saved_stages: List[dict]
    ssim_threshold: float
    frame_interval: int