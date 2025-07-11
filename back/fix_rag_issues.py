#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG问题修复脚本
解决向量数据库查询和存储问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.video_rag_service import VideoRAGService
from app.db.database import get_db
import json
import shutil

def diagnose_rag_issues():
    """诊断RAG相关问题"""
    print("=== RAG问题诊断 ===")
    
    # 1. 检查环境变量
    print("\n1. 检查环境变量...")
    required_env_vars = [
        "ARK_API_KEY",
        "ARK_BASE_URL", 
        "CHROMA_PERSIST_DIRECTORY",
        "CHROMA_COLLECTION_NAME"
    ]
    
    for var in required_env_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✓ {var}: {value[:20]}..." if len(value) > 20 else f"  ✓ {var}: {value}")
        else:
            print(f"  ❌ {var}: 未设置")
    
    # 2. 检查Chroma目录
    print("\n2. 检查Chroma存储目录...")
    chroma_dir = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
    if os.path.exists(chroma_dir):
        print(f"  ✓ Chroma目录存在: {chroma_dir}")
        # 列出目录内容
        try:
            files = os.listdir(chroma_dir)
            print(f"  目录内容: {files}")
        except Exception as e:
            print(f"  ❌ 无法读取目录内容: {str(e)}")
    else:
        print(f"  ❌ Chroma目录不存在: {chroma_dir}")
        print(f"  将创建目录...")
        try:
            os.makedirs(chroma_dir, exist_ok=True)
            print(f"  ✓ 目录创建成功")
        except Exception as e:
            print(f"  ❌ 目录创建失败: {str(e)}")
    
    # 3. 测试RAG服务初始化
    print("\n3. 测试RAG服务初始化...")
    db = next(get_db())
    
    try:
        rag_service = VideoRAGService(db)
        print("  ✓ RAG服务初始化成功")
        
        # 4. 测试向量存储连接
        print("\n4. 测试向量存储连接...")
        try:
            # 尝试一个简单的查询
            test_docs = rag_service.vector_store.similarity_search(
                "测试查询",
                k=1
            )
            print(f"  ✓ 向量存储连接正常，返回 {len(test_docs)} 个结果")
        except Exception as e:
            print(f"  ❌ 向量存储连接失败: {str(e)}")
        
        # 5. 测试embedding功能
        print("\n5. 测试embedding功能...")
        try:
            test_text = "这是一个测试文本"
            embeddings = rag_service.embeddings.embed_query(test_text)
            print(f"  ✓ Embedding功能正常，向量维度: {len(embeddings)}")
        except Exception as e:
            print(f"  ❌ Embedding功能失败: {str(e)}")
        
    except Exception as e:
        print(f"  ❌ RAG服务初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

def fix_filter_syntax():
    """修复filter语法问题的测试"""
    print("\n=== Filter语法测试 ===")
    
    db = next(get_db())
    
    try:
        rag_service = VideoRAGService(db)
        
        # 测试不同的filter语法
        test_filters = [
            # 单条件
            {"video_id": {"$eq": 2}},
            
            # 多条件 - 正确语法
            {
                "$and": [
                    {"video_id": {"$eq": 2}},
                    {"product_name": {"$eq": "飞书"}}
                ]
            },
            
            # 简单条件（可能不支持）
            {"analysis_type": {"$eq": "video_stage_analysis"}}
        ]
        
        for i, filter_dict in enumerate(test_filters):
            print(f"\n测试Filter {i+1}: {json.dumps(filter_dict, ensure_ascii=False)}")
            try:
                docs = rag_service.vector_store.similarity_search(
                    "测试",
                    k=5,
                    filter=filter_dict
                )
                print(f"  ✓ 成功，返回 {len(docs)} 个结果")
            except Exception as e:
                print(f"  ❌ 失败: {str(e)}")
    
    except Exception as e:
        print(f"❌ Filter测试失败: {str(e)}")
    
    finally:
        db.close()

def test_manual_storage():
    """手动测试数据存储"""
    print("\n=== 手动存储测试 ===")
    
    db = next(get_db())
    
    try:
        rag_service = VideoRAGService(db)
        
        # 创建测试数据
        test_stage_analysis = {
            "stage": ["测试阶段1", "测试阶段2"],
            "time": ["00:00:00-00:00:30", "00:00:30-00:01:00"],
            "description": ["这是测试阶段1的描述", "这是测试阶段2的描述"]
        }
        
        print("尝试存储测试数据...")
        result = rag_service.store_video_analysis(
            video_id=999,
            product_name="测试产品",
            stage_analysis=test_stage_analysis
        )
        
        print(f"存储结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result["success"]:
            print("\n尝试查询刚存储的数据...")
            query_result = rag_service.query_similar_stages(
                query="测试阶段",
                product_name="测试产品",
                k=5
            )
            print(f"查询结果: {json.dumps(query_result, ensure_ascii=False, indent=2)}")
            
            # 清理测试数据
            print("\n清理测试数据...")
            delete_result = rag_service.delete_video_analysis_from_vector_store(
                video_id=999,
                product_name="测试产品"
            )
            print(f"删除结果: {json.dumps(delete_result, ensure_ascii=False, indent=2)}")
    
    except Exception as e:
        print(f"❌ 手动存储测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

def reset_chroma_database():
    """重置Chroma数据库"""
    print("\n=== 重置Chroma数据库 ===")
    
    confirm = input("确定要重置Chroma数据库吗？这将删除所有向量数据！(输入 'YES' 确认): ")
    if confirm != 'YES':
        print("操作已取消")
        return
    
    chroma_dir = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
    
    try:
        if os.path.exists(chroma_dir):
            shutil.rmtree(chroma_dir)
            print(f"✓ 已删除Chroma目录: {chroma_dir}")
        
        os.makedirs(chroma_dir, exist_ok=True)
        print(f"✓ 已重新创建Chroma目录: {chroma_dir}")
        
        print("✓ Chroma数据库重置完成")
        
    except Exception as e:
        print(f"❌ 重置失败: {str(e)}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG问题修复工具")
    parser.add_argument("--diagnose", action="store_true", help="诊断RAG问题")
    parser.add_argument("--test-filter", action="store_true", help="测试filter语法")
    parser.add_argument("--test-storage", action="store_true", help="测试手动存储")
    parser.add_argument("--reset", action="store_true", help="重置Chroma数据库")
    
    args = parser.parse_args()
    
    if args.diagnose:
        diagnose_rag_issues()
    elif args.test_filter:
        fix_filter_syntax()
    elif args.test_storage:
        test_manual_storage()
    elif args.reset:
        reset_chroma_database()
    else:
        # 默认运行所有诊断
        diagnose_rag_issues()
        fix_filter_syntax()
        test_manual_storage()

if __name__ == "__main__":
    main()