#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试相似度阈值功能

这个脚本用于测试VideoRAGService中新增的相似度阈值功能，
确保只返回相似度足够高的结果，避免返回不相关的答案。
"""

import os
import sys
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.video_rag_service import VideoRAGService
from app.database import get_db

def test_similarity_threshold():
    """测试相似度阈值功能"""
    print("=== 测试相似度阈值功能 ===")
    
    # 获取数据库连接
    db = next(get_db())
    
    try:
        # 初始化RAG服务
        rag_service = VideoRAGService(db)
        
        # 测试查询
        test_query = "应用启动"
        
        print(f"\n测试查询: '{test_query}'")
        print("-" * 50)
        
        # 测试不同的相似度阈值
        thresholds = [0.5, 0.7, 0.8, 0.9]
        
        for threshold in thresholds:
            print(f"\n相似度阈值: {threshold}")
            
            result = rag_service.query_similar_stages(
                query=test_query,
                k=5,
                similarity_threshold=threshold
            )
            
            if result["success"]:
                print(f"找到 {result['total_results']} 个结果")
                
                for i, res in enumerate(result["results"], 1):
                    similarity_score = res.get("similarity_score", "未知")
                    print(f"  {i}. 视频ID: {res['video_id']}, "
                          f"阶段: {res['stage_name']}, "
                          f"相似度: {similarity_score:.3f}" if isinstance(similarity_score, float) else f"相似度: {similarity_score}")
            else:
                print(f"查询失败: {result.get('message', '未知错误')}")
        
        # 测试生成对比报告的相似度阈值
        print("\n=== 测试对比报告的相似度阈值 ===")
        
        report_result = rag_service.generate_comparison_report(
            query=test_query,
            similarity_threshold=0.7
        )
        
        if report_result["success"]:
            print(f"报告生成成功，使用了 {report_result['source_count']} 个相似结果")
            print(f"报告内容预览: {report_result['report'][:200]}...")
        else:
            print(f"报告生成失败: {report_result.get('message', '未知错误')}")
            
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

def test_edge_cases():
    """测试边界情况"""
    print("\n=== 测试边界情况 ===")
    
    db = next(get_db())
    
    try:
        rag_service = VideoRAGService(db)
        
        # 测试极高阈值（应该返回很少或没有结果）
        print("\n测试极高相似度阈值 (0.99):")
        result = rag_service.query_similar_stages(
            query="应用启动",
            k=5,
            similarity_threshold=0.99
        )
        
        if result["success"]:
            print(f"高阈值结果数量: {result['total_results']}")
        else:
            print(f"查询失败: {result.get('message')}")
        
        # 测试极低阈值（应该返回更多结果）
        print("\n测试极低相似度阈值 (0.1):")
        result = rag_service.query_similar_stages(
            query="应用启动",
            k=5,
            similarity_threshold=0.1
        )
        
        if result["success"]:
            print(f"低阈值结果数量: {result['total_results']}")
        else:
            print(f"查询失败: {result.get('message')}")
            
    except Exception as e:
        print(f"边界测试中发生错误: {e}")
    
    finally:
        db.close()

if __name__ == "__main__":
    print("开始测试相似度阈值功能...")
    
    # 基本功能测试
    test_similarity_threshold()
    
    # 边界情况测试
    test_edge_cases()
    
    print("\n测试完成！")
    print("\n功能说明:")
    print("- 相似度阈值功能已添加到 query_similar_stages 和 generate_comparison_report 方法")
    print("- 默认阈值设置为 0.7，可以通过参数自定义")
    print("- 只有相似度大于等于阈值的结果才会被返回")
    print("- API端点已更新，支持 similarity_threshold 参数")
    print("- 这有助于避免返回不相关的低质量匹配结果")