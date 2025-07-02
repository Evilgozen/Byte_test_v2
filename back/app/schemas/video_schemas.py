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

# Query request/response schemas
class StageQueryRequest(BaseModel):
    video_file_id: int
    stage_name: Optional[str] = None

class StageQueryResponse(BaseModel):
    stages: List[VideoStageResponse]
    total_count: int

class ComparisonQueryRequest(BaseModel):
    comparison_id: Optional[int] = None
    video_file_id: Optional[int] = None

class ComparisonQueryResponse(BaseModel):
    comparisons: List[VideoComparisonResponse]
    total_count: int