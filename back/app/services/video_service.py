from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.video_file import VideoFile
from app.models.video_frame import VideoFrame, FrameBehaviorDescription
from app.models.video_stage import VideoStage, StageMetric, VideoComparison, ComparisonDetail
from app.schemas.video_schemas import (
    FrameBehaviorDescriptionCreate,
    VideoStageCreate,
    StageMetricCreate,
    VideoComparisonCreate,
    ComparisonDetailCreate
)

class VideoFileService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_video_file(self, file_id: int) -> Optional[VideoFile]:
        return self.db.query(VideoFile).filter(VideoFile.id == file_id).first()
    
    def get_video_files(self, skip: int = 0, limit: int = 100) -> List[VideoFile]:
        return self.db.query(VideoFile).offset(skip).limit(limit).all()

class VideoFrameService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_video_frames(self, video_file_id: int) -> List[VideoFrame]:
        return self.db.query(VideoFrame).filter(VideoFrame.video_file_id == video_file_id).all()
    
    def get_frame(self, frame_id: int) -> Optional[VideoFrame]:
        return self.db.query(VideoFrame).filter(VideoFrame.id == frame_id).first()

class FrameBehaviorService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_behavior_description(self, behavior_data: FrameBehaviorDescriptionCreate) -> FrameBehaviorDescription:
        db_behavior = FrameBehaviorDescription(**behavior_data.dict())
        self.db.add(db_behavior)
        self.db.commit()
        self.db.refresh(db_behavior)
        return db_behavior
    
    def get_frame_behaviors(self, frame_id: int) -> List[FrameBehaviorDescription]:
        return self.db.query(FrameBehaviorDescription).filter(FrameBehaviorDescription.frame_id == frame_id).all()

class VideoStageService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_stage(self, stage_data: VideoStageCreate) -> VideoStage:
        db_stage = VideoStage(**stage_data.dict())
        self.db.add(db_stage)
        self.db.commit()
        self.db.refresh(db_stage)
        return db_stage
    
    def get_video_stages(self, video_file_id: int) -> List[VideoStage]:
        return self.db.query(VideoStage).filter(VideoStage.video_file_id == video_file_id).all()
    
    def get_stage(self, stage_id: int) -> Optional[VideoStage]:
        return self.db.query(VideoStage).filter(VideoStage.id == stage_id).first()

class StageMetricService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_metric(self, metric_data: StageMetricCreate) -> StageMetric:
        db_metric = StageMetric(**metric_data.dict())
        self.db.add(db_metric)
        self.db.commit()
        self.db.refresh(db_metric)
        return db_metric
    
    def get_stage_metrics(self, stage_id: int) -> List[StageMetric]:
        return self.db.query(StageMetric).filter(StageMetric.stage_id == stage_id).all()

class VideoComparisonService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_comparison(self, comparison_data: VideoComparisonCreate) -> VideoComparison:
        db_comparison = VideoComparison(**comparison_data.dict())
        self.db.add(db_comparison)
        self.db.commit()
        self.db.refresh(db_comparison)
        return db_comparison
    
    def add_comparison_detail(self, detail_data: ComparisonDetailCreate) -> ComparisonDetail:
        db_detail = ComparisonDetail(**detail_data.dict())
        self.db.add(db_detail)
        self.db.commit()
        self.db.refresh(db_detail)
        return db_detail
    
    def get_comparisons(self, skip: int = 0, limit: int = 100) -> List[VideoComparison]:
        return self.db.query(VideoComparison).offset(skip).limit(limit).all()
    
    def get_comparison(self, comparison_id: int) -> Optional[VideoComparison]:
        return self.db.query(VideoComparison).filter(VideoComparison.id == comparison_id).first()