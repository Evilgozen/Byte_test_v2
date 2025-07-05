import cv2
import os
import numpy as np
from typing import List, Tuple, Optional
from abc import ABC, abstractmethod

class FrameExtractionStrategy(ABC):
    """帧提取策略抽象基类"""
    
    @abstractmethod
    def extract_frame_indices(self, total_frames: int, fps: float, **kwargs) -> List[int]:
        """提取帧索引"""
        pass

class UniformExtractionStrategy(FrameExtractionStrategy):
    """均匀提取策略"""
    
    def extract_frame_indices(self, total_frames: int, fps: float, 
                            interval: float = 1.0, 
                            max_frames: Optional[int] = None,
                            frames_per_second: Optional[float] = None,
                            **kwargs) -> List[int]:
        """按固定间隔均匀提取帧"""
        if frames_per_second:
            # 如果指定了每秒帧数，计算间隔
            interval_frames = max(1, int(fps / frames_per_second))
        else:
            # 使用时间间隔
            interval_frames = max(1, int(fps * interval))
        
        indices = list(range(0, total_frames, interval_frames))
        
        if max_frames and len(indices) > max_frames:
            indices = indices[:max_frames]
            
        return indices

class KeyframeExtractionStrategy(FrameExtractionStrategy):
    """关键帧提取策略（基于场景变化检测）"""
    
    def extract_frame_indices(self, total_frames: int, fps: float,
                            max_frames: Optional[int] = None,
                            threshold: float = 0.3,
                            **kwargs) -> List[int]:
        """基于场景变化检测提取关键帧"""
        # 这里返回一个基础的关键帧提取逻辑
        # 实际实现需要在extract_frames方法中进行图像分析
        
        # 先按较小间隔采样，然后在实际提取时进行场景变化检测
        sample_interval = max(1, int(fps * 0.5))  # 每0.5秒采样一次
        candidate_indices = list(range(0, total_frames, sample_interval))
        
        if max_frames and len(candidate_indices) > max_frames:
            # 如果候选帧太多，先均匀采样
            step = len(candidate_indices) // max_frames
            candidate_indices = candidate_indices[::step]
            
        return candidate_indices

class SmartExtractionStrategy(FrameExtractionStrategy):
    """智能提取策略（结合均匀采样和关键帧检测）"""
    
    def extract_frame_indices(self, total_frames: int, fps: float,
                            max_frames: Optional[int] = None,
                            **kwargs) -> List[int]:
        """智能提取：结合均匀采样和关键帧检测"""
        # 首先进行均匀采样
        uniform_strategy = UniformExtractionStrategy()
        uniform_indices = uniform_strategy.extract_frame_indices(
            total_frames, fps, interval=2.0, max_frames=max_frames
        )
        
        # 然后添加一些关键帧候选
        keyframe_strategy = KeyframeExtractionStrategy()
        keyframe_indices = keyframe_strategy.extract_frame_indices(
            total_frames, fps, max_frames=max_frames//2 if max_frames else None
        )
        
        # 合并并去重
        all_indices = sorted(set(uniform_indices + keyframe_indices))
        
        if max_frames and len(all_indices) > max_frames:
            all_indices = all_indices[:max_frames]
            
        return all_indices

class VideoFrameExtractor:
    """视频帧提取器"""
    
    def __init__(self):
        self.strategies = {
            "uniform": UniformExtractionStrategy(),
            "keyframe": KeyframeExtractionStrategy(),
            "smart": SmartExtractionStrategy()
        }
    
    def extract_frames(self, video_path: str, output_dir: str, 
                      extraction_method: str = "uniform",
                      **extraction_params) -> List[Tuple[int, float, str]]:
        """提取视频帧
        
        Args:
            video_path: 视频文件路径
            output_dir: 输出目录
            extraction_method: 提取方法
            **extraction_params: 提取参数
            
        Returns:
            List[Tuple[frame_number, timestamp, frame_path]]: 提取的帧信息
        """
        if extraction_method not in self.strategies:
            raise ValueError(f"不支持的提取方法: {extraction_method}")
        
        # 打开视频
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # 获取提取策略
            strategy = self.strategies[extraction_method]
            frame_indices = strategy.extract_frame_indices(
                total_frames, fps, **extraction_params
            )
            
            extracted_frames = []
            
            if extraction_method == "keyframe":
                # 关键帧提取需要特殊处理
                extracted_frames = self._extract_keyframes(
                    cap, frame_indices, fps, output_dir, 
                    extraction_params.get('threshold', 0.3)
                )
            else:
                # 普通提取
                extracted_frames = self._extract_uniform_frames(
                    cap, frame_indices, fps, output_dir
                )
            
            return extracted_frames
            
        finally:
            cap.release()
    
    def _extract_uniform_frames(self, cap: cv2.VideoCapture, 
                               frame_indices: List[int], 
                               fps: float, 
                               output_dir: str) -> List[Tuple[int, float, str]]:
        """提取均匀分布的帧"""
        extracted_frames = []
        
        for frame_idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            
            if ret:
                timestamp = frame_idx / fps
                frame_filename = f"frame_{frame_idx:06d}.jpg"
                frame_path = os.path.join(output_dir, frame_filename)
                
                cv2.imwrite(frame_path, frame)
                extracted_frames.append((frame_idx, timestamp, frame_path))
        
        return extracted_frames
    
    def _extract_keyframes(self, cap: cv2.VideoCapture, 
                          candidate_indices: List[int], 
                          fps: float, 
                          output_dir: str,
                          threshold: float = 0.3) -> List[Tuple[int, float, str]]:
        """基于场景变化检测提取关键帧"""
        extracted_frames = []
        prev_hist = None
        
        for frame_idx in candidate_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            
            if not ret:
                continue
            
            # 计算直方图
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            
            # 如果是第一帧或者与前一帧差异较大，则保存
            if prev_hist is None:
                is_keyframe = True
            else:
                # 计算直方图相关性
                correlation = cv2.compareHist(hist, prev_hist, cv2.HISTCMP_CORREL)
                is_keyframe = correlation < (1 - threshold)
            
            if is_keyframe:
                timestamp = frame_idx / fps
                frame_filename = f"keyframe_{frame_idx:06d}.jpg"
                frame_path = os.path.join(output_dir, frame_filename)
                
                cv2.imwrite(frame_path, frame)
                extracted_frames.append((frame_idx, timestamp, frame_path))
                prev_hist = hist
        
        return extracted_frames
    
    def calculate_frame_difference(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        """计算两帧之间的差异"""
        # 转换为灰度图
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        # 计算结构相似性
        from skimage.metrics import structural_similarity as ssim
        similarity = ssim(gray1, gray2)
        
        return 1 - similarity  # 返回差异值