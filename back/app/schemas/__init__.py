from .file_schemas import (
    VideoFileBase, VideoFileCreate, VideoFileUpdate, VideoFileResponse,
    VideoFrameBase, VideoFrameCreate, VideoFrameResponse,
    FrameExtractionRequest, FrameExtractionResponse
)

try:
    from .video_schemas import (
        FrameBehaviorDescriptionBase, FrameBehaviorDescriptionCreate, FrameBehaviorDescriptionResponse,
        VideoStageBase, VideoStageCreate, VideoStageResponse,
        StageMetricBase, StageMetricCreate, StageMetricResponse,
        VideoComparisonBase, VideoComparisonCreate, VideoComparisonResponse,
        ComparisonDetailBase, ComparisonDetailCreate, ComparisonDetailResponse,
        StageQueryRequest, StageQueryResponse,
        ComparisonQueryRequest, ComparisonQueryResponse
    )
    __all__ = [
        "VideoFileBase", "VideoFileCreate", "VideoFileUpdate", "VideoFileResponse",
        "VideoFrameBase", "VideoFrameCreate", "VideoFrameResponse",
        "FrameExtractionRequest", "FrameExtractionResponse",
        "FrameBehaviorDescriptionBase", "FrameBehaviorDescriptionCreate", "FrameBehaviorDescriptionResponse",
        "VideoStageBase", "VideoStageCreate", "VideoStageResponse",
        "StageMetricBase", "StageMetricCreate", "StageMetricResponse",
        "VideoComparisonBase", "VideoComparisonCreate", "VideoComparisonResponse",
        "ComparisonDetailBase", "ComparisonDetailCreate", "ComparisonDetailResponse",
        "StageQueryRequest", "StageQueryResponse",
        "ComparisonQueryRequest", "ComparisonQueryResponse"
    ]
except ImportError:
    __all__ = [
        "VideoFileBase", "VideoFileCreate", "VideoFileUpdate", "VideoFileResponse",
        "VideoFrameBase", "VideoFrameCreate", "VideoFrameResponse",
        "FrameExtractionRequest", "FrameExtractionResponse"
    ]