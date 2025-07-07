from typing import List, Dict, Any
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json
import os
from dotenv import load_dotenv

from app.models.video_stage import VideoStage
from app.services.video_service import VideoStageService
from app.schemas.video_schemas import StageMatchingRequest, StageMatchingResponse, MatchedStage

# 加载环境变量
load_dotenv()

class StageMatchingService:
    def __init__(self, db: Session):
        self.db = db
        self.stage_service = VideoStageService(db)
        
        # 初始化LangChain ChatOpenAI客户端
        self.llm = ChatOpenAI(
            model_name="doubao-seed-1-6-250615",
            openai_api_key="6e0538ce-25b8-4f61-9342-505879befdda",
            openai_api_base="https://ark.cn-beijing.volces.com/api/v3",
        )
    
    def match_stages(self, request: StageMatchingRequest) -> StageMatchingResponse:
        """
        使用LangChain和豆包AI进行阶段匹配分析
        
        Args:
            request: 包含用户输入和视频ID的请求对象
            
        Returns:
            StageMatchingResponse: 匹配结果响应
        """
        try:
            # 获取数据库中的阶段信息
            db_stages = self.stage_service.get_video_stages(request.video_id)
            
            if not db_stages:
                return StageMatchingResponse(
                    success=False,
                    user_input=request.user_input,
                    video_id=request.video_id,
                    matched_stages=[],
                    total_matches=0,
                    analysis_summary="该视频暂无阶段信息，请先进行视频分析。"
                )
            
            # 构建阶段信息字符串
            stages_info = self._format_stages_for_prompt(db_stages)
            
            # 构建prompt
            prompt = self._create_matching_prompt(request.user_input, stages_info)
            
            # 调用LangChain进行分析
            response = self.llm.invoke([prompt])
            
            # 解析AI响应
            analysis_result = self._parse_ai_response(response.content, db_stages)
            
            return StageMatchingResponse(
                success=True,
                user_input=request.user_input,
                video_id=request.video_id,
                matched_stages=analysis_result["matched_stages"],
                total_matches=len(analysis_result["matched_stages"]),
                analysis_summary=analysis_result["summary"]
            )
            
        except Exception as e:
            return StageMatchingResponse(
                success=False,
                user_input=request.user_input,
                video_id=request.video_id,
                matched_stages=[],
                total_matches=0,
                analysis_summary=f"分析过程中发生错误: {str(e)}"
            )
    
    def _format_stages_for_prompt(self, stages: List[VideoStage]) -> str:
        """
        将数据库中的阶段信息格式化为prompt字符串
        """
        stages_text = ""
        for i, stage in enumerate(stages, 1):
            stages_text += f"""
阶段{i}:
- ID: {stage.id}
- 名称: {stage.stage_name}
- 开始时间: {stage.start_time:.2f}秒
- 结束时间: {stage.end_time:.2f}秒
- 持续时间: {stage.duration:.2f}秒
- 描述: {stage.description or '无描述'}

"""
        return stages_text
    
    def _create_matching_prompt(self, user_input: str, stages_info: str) -> HumanMessage:
        """
        创建用于阶段匹配的prompt
        """
        prompt_text = f"""
你是一个专业的视频阶段分析专家。你的任务是根据用户的输入，从给定的视频阶段信息中找到最匹配的阶段。

用户输入: "{user_input}"

视频阶段信息:
{stages_info}

请参考以下示例格式分析视频的各个阶段：

<example>
视频总共包括4个阶段
1. 从0~890ms:应用(APP启动、页面打开)启动
2. 从1000ms~3000ms:登录完成
3. 从3500ms~4000ms:打开一个会话(页面)
4. 从3600ms~4100ms页面内容完成加载
</example>

请分析用户输入与各个阶段的相似度，并按照以下JSON格式返回结果：

{{
  "matched_stages": [
    {{
      "stage_id": 阶段ID,
      "start_time": 开始时间(秒),
      "end_time": 结束时间(秒),
      "similarity_score": 相似度分数(0-1之间的浮点数),
      "match_reason": "匹配原因的详细说明"
    }}
  ],
  "summary": "整体分析总结"
}}

分析要求:
1. 相似度分数应该基于语义相似性、关键词匹配、时间范围等因素综合评估
2. 只返回相似度分数大于0.3的阶段
3. 按相似度分数从高到低排序
4. 匹配原因要具体说明为什么这个阶段与用户输入相关
5. 总结要简洁明了地说明匹配结果
6. 返回结果中必须包含阶段的起始时间和结束时间

请严格按照JSON格式返回，不要添加任何其他文字。
"""
        
        return HumanMessage(content=prompt_text)
    
    def _parse_ai_response(self, ai_response: str, db_stages: List[VideoStage]) -> Dict[str, Any]:
        """
        解析AI响应并构建匹配结果
        """
        try:
            # 尝试解析JSON响应
            response_data = json.loads(ai_response)
            
            matched_stages = []
            stage_dict = {stage.id: stage for stage in db_stages}
            
            for match in response_data.get("matched_stages", []):
                stage_id = match.get("stage_id")
                if stage_id in stage_dict:
                    stage = stage_dict[stage_id]
                    # 使用AI返回的时间信息，如果没有则使用数据库中的时间
                    ai_start_time = match.get("start_time", stage.start_time)
                    ai_end_time = match.get("end_time", stage.end_time)
                    
                    matched_stage = MatchedStage(
                        stage_id=stage.id,
                        stage_name=stage.stage_name,
                        start_time=ai_start_time,
                        end_time=ai_end_time,
                        duration=ai_end_time - ai_start_time,
                        description=stage.description,
                        similarity_score=match.get("similarity_score", 0.0),
                        match_reason=match.get("match_reason", "")
                    )
                    matched_stages.append(matched_stage)
            
            return {
                "matched_stages": matched_stages,
                "summary": response_data.get("summary", "分析完成")
            }
            
        except json.JSONDecodeError:
            # 如果JSON解析失败，返回默认结果
            return {
                "matched_stages": [],
                "summary": f"AI响应解析失败，原始响应: {ai_response[:200]}..."
            }
        except Exception as e:
            return {
                "matched_stages": [],
                "summary": f"响应处理错误: {str(e)}"
            }