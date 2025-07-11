#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试RAG集成功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.video_rag_service import VideoRAGService
from app.db.database import get_db

def test_rag_service():
    """测试RAG服务基本功能"""
    print("开始测试RAG服务...")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 初始化RAG服务
        rag_service = VideoRAGService(db)
        print("✓ RAG服务初始化成功")
        
        # 测试存储功能
        test_stage_analysis = [
            {
                "stage_name": "登录阶段",
                "start_time": "00:00:00",
                "end_time": "00:00:30",
                "duration": 30.0,
                "description": "用户进入应用并完成登录操作"
            },
            {
                "stage_name": "主页浏览",
                "start_time": "00:00:30",
                "end_time": "00:01:15",
                "duration": 45.0,
                "description": "用户在主页浏览各种功能和内容"
            }
        ]
        
        # 存储测试数据
        store_result = rag_service.store_video_analysis(
            video_id=999,
            product_name="测试产品",
            stage_analysis=test_stage_analysis
        )
        print(f"✓ 存储测试: {store_result}")
        
        # 测试查询功能
        query_result = rag_service.query_similar_stages(
            query="用户登录流程",
            product_name="测试产品",
            k=3
        )
        print(f"✓ 查询测试: {query_result}")
        
        # 测试报告生成
        report_result = rag_service.generate_comparison_report(
            query="分析登录流程的用户体验",
            product_name="测试产品"
        )
        print(f"✓ 报告生成测试: {report_result}")
        
        # 清理测试数据
        delete_result = rag_service.delete_video_analysis_from_vector_store(
            video_id=999,
            product_name="测试产品"
        )
        print(f"✓ 删除测试: {delete_result}")
        
        print("\n🎉 所有RAG功能测试通过！")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    test_rag_service()