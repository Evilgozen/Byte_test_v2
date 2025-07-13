import os
import base64
import cv2
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from skimage.metrics import structural_similarity as ssim
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from app.models.video_file import VideoFile
from app.models.video_frame import VideoFrame
from app.models.video_stage import VideoStage
from app.services.video_service import VideoFileService, VideoStageService
from app.services.video_rag_service import VideoRAGService


class SSIMVideoAnalysisService:
    """基于SSIM的视频分析服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.video_file_service = VideoFileService(db)
        self.video_stage_service = VideoStageService(db)
        self.rag_service = VideoRAGService(db)
        
        # 初始化LangChain ChatOpenAI客户端
        self.llm = ChatOpenAI(
            model_name=os.getenv("ARK_MODEL", "doubao-1-5-vision-pro-250328"),
            openai_api_key=os.getenv("ARK_API_KEY"),
            openai_api_base=os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
        )
    
    def analyze_video_with_ssim(self, video_id: int, product_name: str, 
                               frame_interval: int = 30, ssim_threshold: float = 0.75) -> Dict[str, Any]:
        """使用SSIM分析视频并生成阶段信息
        
        Args:
            video_id: 视频文件ID
            product_name: 产品名称（用于向量存储的metadata）
            frame_interval: 帧间隔（多少帧检测一次）
            ssim_threshold: SSIM阈值
            
        Returns:
            分析结果字典
        """
        # 获取视频文件
        video_file = self.video_file_service.get_video_file(video_id)
        if not video_file:
            raise ValueError(f"视频文件不存在: {video_id}")
        
        if not os.path.exists(video_file.file_path):
            raise ValueError(f"视频文件路径不存在: {video_file.file_path}")
        
        # 提取关键帧
        keyframes_info = self._extract_ssim_keyframes(
            video_file.file_path, frame_interval, ssim_threshold
        )
        
        # 保存关键帧到数据库和文件系统
        saved_frames = self._save_keyframes_to_db(video_id, keyframes_info)
        
        # 使用AI分析关键帧生成阶段信息
        stage_analysis = self._analyze_stages_with_ai(keyframes_info)
        
        # 保存阶段信息到数据库
        saved_stages = self._save_stages_to_db(video_id, stage_analysis)
        
        # 存储到向量数据库
        rag_result = self.rag_service.store_video_analysis(video_id, product_name, stage_analysis)
        
        return {
            "video_id": video_id,
            "product_name": product_name,
            "total_keyframes": len(saved_frames),
            "keyframes": saved_frames,
            "stage_analysis": stage_analysis,
            "saved_stages": saved_stages,
            "rag_storage": rag_result,
            "ssim_threshold": ssim_threshold,
            "frame_interval": frame_interval
        }
    
    def delete_video_analysis(self, video_id: int) -> Dict[str, Any]:
        """删除视频的分析结果
        
        Args:
            video_id: 视频文件ID
            
        Returns:
            删除结果
        """
        # 删除视频帧
        deleted_frames = self.db.query(VideoFrame).filter(
            VideoFrame.video_file_id == video_id
        ).all()
        
        # 删除帧文件
        for frame in deleted_frames:
            if os.path.exists(frame.frame_path):
                os.remove(frame.frame_path)
        
        # 删除数据库记录
        frames_count = self.db.query(VideoFrame).filter(
            VideoFrame.video_file_id == video_id
        ).delete()
        
        stages_count = self.db.query(VideoStage).filter(
            VideoStage.video_file_id == video_id
        ).delete()
        
        self.db.commit()
        
        # 从向量数据库中删除
        rag_delete_result = self.rag_service.delete_video_analysis_from_vector_store(video_id)
        
        return {
            "video_id": video_id,
            "deleted_frames": frames_count,
            "deleted_stages": stages_count,
            "rag_deletion": rag_delete_result,
            "message": f"成功删除视频 {video_id} 的分析结果"
        }
    
    def _extract_ssim_keyframes(self, video_path: str, frame_interval: int, 
                               ssim_threshold: float) -> List[Dict[str, Any]]:
        """使用SSIM提取关键帧"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            video_duration = total_frames / fps  # 视频总时长（秒）
            
            keyframes_info = []
            prev_frame = None
            last_keyframe_index = 0
            
            # 读取第一帧作为参考
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, first_frame = cap.read()
            if ret:
                keyframes_info.append({
                    "frame_number": 0,
                    "timestamp": 0.0,
                    "frame_data": first_frame,
                    "ssim_score": 1.0
                })
                prev_frame = first_frame
                last_keyframe_index = 0
            
            # 按间隔检测关键帧
            for i in range(frame_interval, total_frames, frame_interval):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, current_frame = cap.read()
                
                if ret and prev_frame is not None:
                    # 计算SSIM相似度
                    similarity = self._calculate_ssim(prev_frame, current_frame)
                    
                    # 如果相似度低于阈值，认为是关键帧
                    if similarity < ssim_threshold:
                        timestamp = i / fps
                        keyframes_info.append({
                            "frame_number": i,
                            "timestamp": timestamp,
                            "frame_data": current_frame,
                            "ssim_score": similarity
                        })
                        prev_frame = current_frame
                        last_keyframe_index = i
            
            # 处理最后一个阶段：如果最后一个关键帧不是视频结尾，添加结束帧
            if len(keyframes_info) > 0 and last_keyframe_index < total_frames - frame_interval:
                # 读取最后一帧
                cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
                ret, last_frame = cap.read()
                if ret:
                    # 计算与最后一个关键帧的相似度
                    last_similarity = self._calculate_ssim(prev_frame, last_frame)
                    
                    # 添加视频结束帧作为最后阶段的结束点
                    keyframes_info.append({
                        "frame_number": total_frames - 1,
                        "timestamp": video_duration,
                        "frame_data": last_frame,
                        "ssim_score": last_similarity,
                        "is_end_frame": True  # 标记为结束帧
                    })
            
            return keyframes_info
            
        finally:
            cap.release()
    
    def _calculate_ssim(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        """计算两帧之间的SSIM相似度"""
        # 转换为灰度图
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        # 调整图像大小以提高计算速度
        gray1 = cv2.resize(gray1, (320, 240))
        gray2 = cv2.resize(gray2, (320, 240))
        
        # 计算SSIM
        similarity = ssim(gray1, gray2)
        return similarity
    
    def _encode_image_to_base64(self, image: np.ndarray) -> str:
        """将图片转为Base64编码"""
        _, buffer = cv2.imencode('.jpg', image)
        return base64.b64encode(buffer).decode('utf-8')
    
    def _save_keyframes_to_db(self, video_id: int, keyframes_info: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """保存关键帧到数据库和文件系统"""
        # 创建输出目录
        output_dir = f"static/cut_files/video_{video_id}"
        os.makedirs(output_dir, exist_ok=True)
        
        saved_frames = []
        
        for i, keyframe in enumerate(keyframes_info):
            # 保存帧图片
            frame_filename = f"keyframe_{i+1:02d}_time_{keyframe['timestamp']*1000:.0f}ms.jpg"
            frame_path = os.path.join(output_dir, frame_filename)
            
            cv2.imwrite(frame_path, keyframe['frame_data'])
            
            # 保存到数据库
            db_frame = VideoFrame(
                video_file_id=video_id,
                frame_number=keyframe['frame_number'],
                timestamp=keyframe['timestamp'],
                frame_path=frame_path,
                width=keyframe['frame_data'].shape[1],
                height=keyframe['frame_data'].shape[0]
            )
            
            self.db.add(db_frame)
            self.db.flush()  # 获取ID
            
            saved_frames.append({
                "id": db_frame.id,
                "frame_number": keyframe['frame_number'],
                "timestamp": keyframe['timestamp'],
                "frame_path": frame_path,
                "ssim_score": keyframe['ssim_score']
            })
        
        self.db.commit()
        return saved_frames
    
    def _analyze_stages_with_ai(self, keyframes_info: List[Dict[str, Any]]) -> Dict[str, Any]:
        """使用AI分析关键帧生成阶段信息"""
        if not keyframes_info:
            return {"stages": [], "time": [], "description": []}
        
        # 构建多图像输入的content
        content = []
        
        # 添加所有帧图像
        for i, keyframe in enumerate(keyframes_info):
            frame_base64 = self._encode_image_to_base64(keyframe['frame_data'])
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{frame_base64}"
                }
            })
        
        # 添加文本提示
        frame_times_str = ', '.join([f'{kf["timestamp"]*1000:.0f}ms' for kf in keyframes_info])
        video_end_time = keyframes_info[-1]['timestamp'] * 1000  # 视频结束时间（毫秒）
        
        prompt_text = f"""你是一个QA，你的任务是对给定视频的关键帧进行阶段分析。首先，请仔细阅读以下视频关键帧的时间点：
<frame_times>
{frame_times_str}
</frame_times>

视频总时长: {video_end_time:.0f}ms

接下来，请查看从视频中提取的关键帧：
<video_frames>
上述提供的图像序列
</video_frames>

请参考以下示例格式来分析视频的各个阶段：
<example>
视频总共包括4个阶段
1. 从0~890ms:应用(APP启动、页面打开)启动
2. 从1000ms~3000ms:登录完成
3. 从3500ms~4000ms:打开一个会话(页面)
4. 从3600ms~{video_end_time:.0f}ms:页面内容完成加载（最后阶段延续到视频结尾）
</example>

重要提示：
1. 最后一个阶段必须延续到视频结尾时间({video_end_time:.0f}ms)
2. 每个阶段都应该有明确的开始和结束时间
3. 阶段之间不应该有时间间隙

最后，请严格按照以下JSON格式返回结果，不要添加任何其他文字：
{{
  "stage": ["阶段1", "阶段2", "阶段3"],
  "time": ["开始时间1~结束时间1", "开始时间2~结束时间2", "开始时间3~{video_end_time:.0f}ms"],
  "description": ["阶段1描述", "阶段2描述", "阶段3描述"]
}}"""
        
        content.append({
            "type": "text",
            "text": prompt_text
        })
        
        # 使用LangChain的HumanMessage来处理多图像输入
        message = HumanMessage(content=content)
        
        try:
            response = self.llm.invoke([message])
            
            # 尝试解析JSON响应
            response_text = response.content.strip()
            
            # 如果响应包含代码块，提取JSON部分
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            
            # 解析JSON
            try:
                stage_analysis = json.loads(response_text)
                return stage_analysis
            except json.JSONDecodeError:
                # 如果JSON解析失败，返回默认结构
                return {
                    "stage": ["视频分析"],
                    "time": [f"0~{keyframes_info[-1]['timestamp']*1000:.0f}ms"],
                    "description": ["AI分析失败，使用默认描述"]
                }
                
        except Exception as e:
            print(f"AI分析出错: {e}")
            return {
                "stage": ["视频分析"],
                "time": [f"0~{keyframes_info[-1]['timestamp']*1000:.0f}ms"],
                "description": [f"AI分析出错: {str(e)}"]
            }
    
    def _save_stages_to_db(self, video_id: int, stage_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """保存阶段信息到数据库"""
        saved_stages = []
        
        stages = stage_analysis.get("stage", [])
        times = stage_analysis.get("time", [])
        descriptions = stage_analysis.get("description", [])
        
        # 获取视频文件信息以确定视频总时长
        video_file = self.video_file_service.get_video_file(video_id)
        video_duration = None
        if video_file and os.path.exists(video_file.file_path):
            cap = cv2.VideoCapture(video_file.file_path)
            if cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                video_duration = total_frames / fps
                cap.release()
        
        for i, (stage_name, time_range, description) in enumerate(zip(stages, times, descriptions)):
            # 解析时间范围
            try:
                if "~" in time_range:
                    start_str, end_str = time_range.split("~")
                    start_time = float(start_str.replace("ms", "")) / 1000  # 转换为秒
                    end_time = float(end_str.replace("ms", "")) / 1000
                else:
                    start_time = 0.0
                    end_time = float(time_range.replace("ms", "")) / 1000
            except:
                start_time = 0.0
                end_time = 1.0
            
            # 特殊处理最后一个阶段：确保结束时间不会是0ms持续时间
            if i == len(stages) - 1 and video_duration is not None:
                # 如果是最后一个阶段，确保结束时间是视频总时长
                if end_time <= start_time:
                    end_time = video_duration
                # 确保最后阶段至少延续到视频结尾
                end_time = max(end_time, video_duration)
            
            duration = end_time - start_time
            
            # 确保持续时间不为0或负数
            if duration <= 0:
                duration = 0.1  # 最小持续时间100ms
                end_time = start_time + duration
            
            # 保存到数据库
            db_stage = VideoStage(
                video_file_id=video_id,
                stage_name=stage_name,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                description=description
            )
            
            self.db.add(db_stage)
            self.db.flush()
            
            saved_stages.append({
                "id": db_stage.id,
                "stage_name": stage_name,
                "start_time": start_time,
                "end_time": end_time,
                "duration": duration,
                "description": description
            })
        
        self.db.commit()
        return saved_stages
    
    def query_similar_video_stages(self, query: str, product_name: Optional[str] = None, 
                                  k: int = 5, similarity_threshold: float = 0.7) -> Dict[str, Any]:
        """查询相似的视频阶段分析
        
        Args:
            query: 查询文本
            product_name: 产品名称过滤（可选）
            k: 返回结果数量
            similarity_threshold: 相似度阈值，只返回相似度大于此值的结果
            
        Returns:
            查询结果
        """
        return self.rag_service.query_similar_stages(query, product_name, k, similarity_threshold)
    
    def generate_stage_comparison_report(self, query: str, product_name: Optional[str] = None, 
                                        similarity_threshold: float = 0.7) -> Dict[str, Any]:
        """生成阶段对比分析报告
        
        Args:
            query: 查询描述
            product_name: 产品名称过滤
            similarity_threshold: 相似度阈值，只使用相似度大于此值的结果生成报告
            
        Returns:
            生成的报告
        """
        return self.rag_service.generate_comparison_report(query, product_name, similarity_threshold)
    
    def generate_stage_comparison_report_stream(self, query: str, product_name: Optional[str] = None, 
                                              similarity_threshold: float = 0.7):
        """流式生成阶段对比分析报告
        
        Args:
            query: 查询描述
            product_name: 产品名称过滤
            similarity_threshold: 相似度阈值，只使用相似度大于此值的结果生成报告
            
        Yields:
            流式返回的报告内容
        """
        return self.rag_service.generate_comparison_report_stream(query, product_name, similarity_threshold)