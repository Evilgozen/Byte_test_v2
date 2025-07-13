import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""
    
    # 基础配置
    app_name: str = "Video Analysis API"
    app_version: str = "1.0.0"
    debug: bool = True
    environment: str = "development"
    
    # 数据库配置
    database_url: str = "sqlite:///./video_analysis.db"
    
    # 文件存储配置
    upload_dir: str = "uploads"
    thumbnail_dir: str = "thumbnails"
    max_file_size: int = 1073741824  # 1GB
    allowed_file_types: List[str] = ["mp4", "avi", "mov", "mkv", "wmv", "flv", "webm"]
    
    # AI配置
    openai_api_key: str = "your_openai_api_key_here"
    openai_model: str = "gpt-4-vision-preview"
    openai_max_tokens: int = 1000
    openai_temperature: float = 0.7
    
    # 豆包AI配置
    ark_api_key: str = "6e0538ce-25b8-4f61-9342-505879befdda"
    ark_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    ark_model: str = "doubao-1-5-vision-pro-250328"
    ark_embedding_model: str = "doubao-embedding"
    
    # RAG配置
    chroma_persist_directory: str = "./chroma_db"
    chroma_collection_name: str = "video_analysis"
    rag_chunk_size: int = 1000
    rag_chunk_overlap: int = 200
    rag_top_k: int = 5
    
    # 安全配置
    secret_key: str = "your_secret_key_here_change_in_production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS配置
    allowed_hosts: List[str] = ["*"]
    
    # 飞书应用配置
    # 飞书配置已删除
    
    # Redis配置
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    log_rotation: str = "10 MB"
    log_retention: str = "30 days"
    
    # 视频处理配置
    ffmpeg_path: str = "ffmpeg"
    max_frame_extraction: int = 1000
    default_thumbnail_size: str = "200,150"
    video_quality_threshold: int = 720
    
    # 分析配置
    default_ai_model: str = "openai"
    analysis_timeout: int = 300
    max_concurrent_analyses: int = 5
    retry_attempts: int = 3
    
    # 缓存配置
    cache_ttl: int = 3600
    cache_max_size: int = 1000
    
    # 性能配置
    worker_processes: int = 4
    worker_connections: int = 1000
    keep_alive: int = 2
    
    # 监控配置
    health_check_interval: int = 30
    metrics_enabled: bool = True
    
    # 文件清理配置
    cleanup_interval: int = 24
    temp_file_retention: int = 7
    old_analysis_retention: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 创建全局配置实例
settings = Settings()