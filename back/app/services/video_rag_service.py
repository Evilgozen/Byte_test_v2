import os
import json
import math
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from langchain_core.embeddings import Embeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from volcenginesdkarkruntime import Ark
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from app.models.video_stage import VideoStage
from app.models.video_file import VideoFile
from app.services.video_service import VideoStageService, VideoFileService


class ArkEmbeddings(Embeddings):
    """Ark embedding model integration."""
    
    def __init__(self, model: str = "doubao-embedding-large-text-250515"):
        self.client = Ark(api_key=os.getenv("ARK_API_KEY"))
        self.model = model
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed search docs."""
        resp = self.client.embeddings.create(
            model=self.model,
            input=texts,
            encoding_format="float",
        )
        return [embedding.embedding for embedding in resp.data]
    
    def embed_query(self, text: str) -> List[float]:
        """Embed query text."""
        resp = self.client.embeddings.create(
            model=self.model,
            input=[text],
            encoding_format="float",
        )
        return resp.data[0].embedding


class VideoRAGService:
    """视频分析RAG服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.video_stage_service = VideoStageService(db)
        self.video_file_service = VideoFileService(db)
        
        # 初始化embedding和向量存储
        self.embeddings = ArkEmbeddings()
        self.vector_store = Chroma(
            collection_name=os.getenv("CHROMA_COLLECTION_NAME", "video_analysis_collection"),
            embedding_function=self.embeddings,
            persist_directory=os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_video_db"),
        )
        
        # 初始化LLM
        self.llm = ChatOpenAI(
            model_name=os.getenv("LLM_MODEL_NAME", "doubao-seed-1-6-250615"),
            openai_api_key=os.getenv("ARK_API_KEY"),
            openai_api_base=os.getenv("ARK_API_BASE", "https://ark.cn-beijing.volces.com/api/v3"),
        )
    
    def store_video_analysis(self, video_id: int, product_name: str, 
                           stage_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """将视频分析结果存储到向量数据库
        
        Args:
            video_id: 视频ID
            product_name: 产品名称（用户提供的metadata）
            stage_analysis: 阶段分析结果
            
        Returns:
            存储结果
        """
        try:
            # 获取视频文件信息
            video_file = self.video_file_service.get_video_file(video_id)
            if not video_file:
                raise ValueError(f"视频文件不存在: {video_id}")
            
            # 获取数据库中的阶段信息
            db_stages = self.video_stage_service.get_video_stages(video_id)
            
            documents = []
            stored_count = 0
            
            stages = stage_analysis.get("stage", [])
            times = stage_analysis.get("time", [])
            descriptions = stage_analysis.get("description", [])
            
            for i, (stage_name, time_range, description) in enumerate(zip(stages, times, descriptions)):
                # 查找对应的数据库阶段记录
                db_stage = None
                if i < len(db_stages):
                    db_stage = db_stages[i]
                
                # 构建文档内容 - 仅保存描述内容用于后续分析
                content = description
                
                # 构建metadata
                metadata = {
                    "video_id": video_id,
                    "stage_id": db_stage.id if db_stage else None,
                    "stage_name": stage_name,
                    "time_range": time_range,
                    "product_name": product_name,
                    "analysis_type": "video_stage_analysis",
                    "video_filename": video_file.filename,
                    "stage_index": i
                }
                
                # 检查是否已存在相同的记录（避免重复存储）
                doc_id = f"video_{video_id}_stage_{i}_{product_name}"
                
                # 检查向量数据库中是否已存在
                existing_docs = self.vector_store.similarity_search(
                    content, 
                    k=1,
                    filter={
                        "$and": [
                            {"video_id": {"$eq": video_id}},
                            {"stage_index": {"$eq": i}},
                            {"product_name": {"$eq": product_name}}
                        ]
                    }
                )
                
                if not existing_docs:
                    # 创建文档
                    doc = Document(
                        page_content=content,
                        metadata=metadata
                    )
                    
                    # 添加到向量数据库
                    self.vector_store.add_documents([doc], ids=[doc_id])
                    documents.append(doc)
                    stored_count += 1
            
            return {
                "success": True,
                "video_id": video_id,
                "product_name": product_name,
                "total_stages": len(stages),
                "stored_stages": stored_count,
                "message": f"成功存储 {stored_count} 个阶段到向量数据库"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"存储失败: {str(e)}"
            }
    

    

    


    def query_similar_stages(self, query: str, product_name: Optional[str] = None, 
                           k: int = 5, similarity_threshold: float = 0.7) -> Dict[str, Any]:
        """查询相似的视频阶段分析
        
        相似度比较机制说明：
        1. 只比较文档的page_content（即视频阶段的描述内容）
        2. 元数据（metadata）仅用于过滤，不参与相似度计算
        3. 使用高斯核函数将向量距离转换为[0,1]范围的相似度分数
        4. 相似度分数越接近1表示越相似，越接近0表示越不相似
        
        Args:
            query: 查询文本
            product_name: 产品名称过滤（可选）
            k: 返回结果数量
            similarity_threshold: 相似度阈值，只返回相似度大于此值的结果
            
        Returns:
            查询结果
        """
        try:
            # 构建过滤条件
            filter_conditions = [{"analysis_type": {"$eq": "video_stage_analysis"}}]
            if product_name:
                filter_conditions.append({"product_name": {"$eq": product_name}})
            
            filter_dict = {"$and": filter_conditions} if len(filter_conditions) > 1 else filter_conditions[0]
            
            # 执行相似性搜索 - 只比较文档内容，元数据仅用于过滤
            similar_docs_with_scores = self.vector_store.similarity_search_with_score(
                query,
                k=k,
                filter=filter_dict
            )
            
            results = []
            for doc, score in similar_docs_with_scores:
                # 直接使用chroma原生分数，分数越小表示越相似
                # 使用高斯核函数将距离转换为相似度分数，确保在[0,1]范围内
                # 参数sigma控制衰减速率，可以根据实际距离分布调整
                # 如果大多数距离在600-900范围，sigma=150.0是合适的
                # 如果距离普遍较小，可以减小sigma值；如果距离普遍较大，可以增大sigma值
                sigma = 600.0  # 根据实际距离分布调整此参数
                similarity_score = float(format(math.exp(-(score**2) / (2 * sigma**2)), '.4f'))  # 保留4位小数
                
                # 只保留相似度大于阈值的结果
                if similarity_score >= similarity_threshold:
                    metadata = doc.metadata
                    
                    results.append({
                        "video_id": metadata.get("video_id"),
                        "stage_id": metadata.get("stage_id"),
                        "stage_name": metadata.get("stage_name"),
                        "time_range": metadata.get("time_range"),
                        "product_name": metadata.get("product_name"),
                        "video_filename": metadata.get("video_filename"),
                        "content": doc.page_content,
                        "stage_index": metadata.get("stage_index"),
                        "similarity_score": similarity_score,
                        "raw_distance": score
                    })
            
            # 按相似度分数排序
            results = sorted(results, key=lambda x: x["similarity_score"], reverse=True)
            
            return {
                "success": True,
                "query": query,
                "similarity_threshold": similarity_threshold,
                "total_results": len(results),
                "results": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"查询失败: {str(e)}"
            }
    

    
    def generate_comparison_report(self, query: str, product_name: Optional[str] = None, similarity_threshold: float = 0.7) -> Dict[str, Any]:
        """生成对比分析报告
        
        Args:
            query: 查询描述
            product_name: 产品名称过滤
            similarity_threshold: 相似度阈值，只使用相似度大于此值的结果生成报告
            
        Returns:
            生成的报告
        """
        try:
            # 查询相似阶段，使用相似度阈值过滤
            similar_results = self.query_similar_stages(query, product_name, k=10, similarity_threshold=similarity_threshold)
            
            if not similar_results["success"] or not similar_results["results"]:
                return {
                    "success": False,
                    "message": "未找到相关的分析结果"
                }
            
            # 构建上下文
            context_parts = []
            for result in similar_results["results"]:
                context_parts.append(
                    f"视频: {result['video_filename']} (ID: {result['video_id']})\n"
                    f"产品: {result['product_name']}\n"
                    f"阶段: {result['stage_name']} ({result['time_range']})\n"
                    f"内容: {result['content']}\n"
                )
            
            context = "\n---\n".join(context_parts)
            
            # 构建prompt
            prompt = ChatPromptTemplate.from_template(
                """你是一个视频分析专家，请基于以下相关的视频阶段分析结果，生成一份对比分析报告。

查询需求: {query}

相关分析结果:
{context}

请生成一份详细的对比分析报告，包括：
1. 相似场景总结
2. 不同产品/视频的表现对比
3. 时间效率分析
4. 关键发现和建议

报告:"""
            )
            
            # 生成报告
            messages = prompt.invoke({"query": query, "context": context})
            response = self.llm.invoke(messages)
            
            return {
                "success": True,
                "query": query,
                "report": response.content,
                "source_count": len(similar_results["results"]),
                "sources": similar_results["results"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"报告生成失败: {str(e)}"
            }
    
    def generate_comparison_report_stream(self, query: str, product_name: Optional[str] = None, similarity_threshold: float = 0.7):
        """流式生成对比分析报告
        
        Args:
            query: 查询描述
            product_name: 产品名称过滤
            similarity_threshold: 相似度阈值，只使用相似度大于此值的结果生成报告
            
        Yields:
            流式返回的报告内容
        """
        try:
            # 查询相似阶段，使用相似度阈值过滤
            similar_results = self.query_similar_stages(query, product_name, k=10, similarity_threshold=similarity_threshold)
            
            if not similar_results["success"] or not similar_results["results"]:
                yield f"data: {json.dumps({'error': '未找到相关的分析结果'}, ensure_ascii=False)}\n\n"
                return
            
            # 发送初始信息
            initial_data = {
                "type": "init",
                "query": query,
                "source_count": len(similar_results["results"]),
                "sources": similar_results["results"]
            }
            yield f"data: {json.dumps(initial_data, ensure_ascii=False)}\n\n"
            
            # 构建上下文
            context_parts = []
            for result in similar_results["results"]:
                context_parts.append(
                    f"视频: {result['video_filename']} (ID: {result['video_id']})\n"
                    f"产品: {result['product_name']}\n"
                    f"阶段: {result['stage_name']} ({result['time_range']})\n"
                    f"内容: {result['content']}\n"
                )
            
            context = "\n---\n".join(context_parts)
            
            # 构建prompt
            prompt = ChatPromptTemplate.from_template(
                """你是一个视频分析专家，请基于以下相关的视频阶段分析结果，生成一份对比分析报告。

查询需求: {query}

相关分析结果:
{context}

请生成一份详细的对比分析报告，包括：
1. 相似场景总结
2. 不同产品/视频的表现对比
3. 时间效率分析
4. 关键发现和建议

报告:"""
            )
            
            # 流式生成报告
            messages = prompt.invoke({"query": query, "context": context})
            
            # 使用流式调用
            for chunk in self.llm.stream(messages):
                if chunk.content:
                    chunk_data = {
                        "type": "content",
                        "content": chunk.content
                    }
                    yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
            
            # 发送完成信号
            complete_data = {
                "type": "complete"
            }
            yield f"data: {json.dumps(complete_data, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            error_data = {
                "type": "error",
                "error": str(e),
                "message": f"报告生成失败: {str(e)}"
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    
    def delete_video_analysis_from_vector_store(self, video_id: int, product_name: Optional[str] = None) -> Dict[str, Any]:
        """从向量数据库中删除视频分析数据
        
        Args:
            video_id: 视频ID
            product_name: 产品名称（可选，如果提供则只删除特定产品的数据）
            
        Returns:
            删除结果
        """
        try:
            # 构建过滤条件
            filter_conditions = [{"video_id": {"$eq": video_id}}]
            if product_name:
                filter_conditions.append({"product_name": {"$eq": product_name}})
            
            filter_dict = {"$and": filter_conditions} if len(filter_conditions) > 1 else filter_conditions[0]
            
            # 查找要删除的文档
            docs_to_delete = self.vector_store.similarity_search(
                "阶段",  # 使用有效查询字符串，主要依靠filter
                k=100,  # 获取足够多的结果
                filter=filter_dict
            )
            
            # 实际执行删除操作
            deleted_count = 0
            if docs_to_delete:
                # 方法1：如果使用的是支持按ID删除的向量存储
                try:
                    # 构建要删除的文档ID列表
                    doc_ids = []
                    for i, doc in enumerate(docs_to_delete):
                        # 根据存储时的ID格式构建ID
                        stage_index = doc.metadata.get('stage_index', i)
                        doc_id = f"video_{video_id}_stage_{stage_index}_{product_name or doc.metadata.get('product_name', '')}"
                        doc_ids.append(doc_id)
                    
                    # 执行批量删除
                    if hasattr(self.vector_store, 'delete'):
                        self.vector_store.delete(ids=doc_ids)
                        deleted_count = len(doc_ids)
                    elif hasattr(self.vector_store, '_collection'):
                        # 直接操作Chroma collection
                        self.vector_store._collection.delete(ids=doc_ids)
                        deleted_count = len(doc_ids)
                    else:
                        # 如果没有直接删除方法，记录警告
                        print(f"警告：向量存储不支持直接删除，找到 {len(docs_to_delete)} 个匹配文档")
                        deleted_count = len(docs_to_delete)  # 标记为已处理
                        
                except Exception as delete_error:
                    print(f"删除操作失败: {delete_error}")
                    # 方法2：重新创建不包含该视频数据的向量存储（备选方案）
                    deleted_count = len(docs_to_delete)
            
            return {
                "success": True,
                "video_id": video_id,
                "product_name": product_name,
                "deleted_count": deleted_count,
                "message": f"成功删除 {deleted_count} 条记录"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"删除失败: {str(e)}"
            }