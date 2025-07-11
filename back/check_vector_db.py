#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量数据库查看工具
用于检查Chroma向量数据库中存储的视频分析数据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.video_rag_service import VideoRAGService
from app.db.database import get_db
import json

def check_vector_database():
    """检查向量数据库中的数据"""
    print("=== 向量数据库数据检查工具 ===")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 初始化RAG服务
        rag_service = VideoRAGService(db)
        print("✓ RAG服务初始化成功")
        
        # 获取所有数据（使用有效查询字符串）
        print("\n1. 检查所有存储的数据...")
        try:
            # 使用一个通用查询词而不是空字符串
            all_docs = rag_service.vector_store.similarity_search(
                "阶段",  # 使用通用查询词
                k=100  # 获取更多结果
            )
            
            if all_docs:
                print(f"✓ 找到 {len(all_docs)} 条记录")
                for i, doc in enumerate(all_docs):
                    print(f"\n记录 {i+1}:")
                    print(f"  内容: {doc.page_content[:100]}...")
                    print(f"  元数据: {json.dumps(doc.metadata, ensure_ascii=False, indent=2)}")
            else:
                print("❌ 向量数据库中没有找到任何数据")
        except Exception as e:
            print(f"❌ 查询所有数据失败: {str(e)}")
        
        # 检查特定产品的数据
        print("\n2. 检查'飞书'产品的数据...")
        try:
            feishu_result = rag_service.query_similar_stages(
                query="任意查询",
                product_name="飞书",
                k=10
            )
            print(f"飞书产品查询结果: {json.dumps(feishu_result, ensure_ascii=False, indent=2)}")
        except Exception as e:
            print(f"❌ 查询飞书数据失败: {str(e)}")
        
        # 检查特定视频ID的数据
        print("\n3. 检查视频ID=2的数据...")
        try:
            # 使用有效查询字符串和filter
            video2_docs = rag_service.vector_store.similarity_search(
                "视频阶段",  # 使用有效查询字符串
                k=50,
                filter={"video_id": {"$eq": 2}}
            )
            
            if video2_docs:
                print(f"✓ 视频ID=2 找到 {len(video2_docs)} 条记录")
                for i, doc in enumerate(video2_docs):
                    print(f"\n视频2记录 {i+1}:")
                    print(f"  内容: {doc.page_content}")
                    print(f"  元数据: {json.dumps(doc.metadata, ensure_ascii=False, indent=2)}")
            else:
                print("❌ 视频ID=2 没有找到数据")
        except Exception as e:
            print(f"❌ 查询视频ID=2数据失败: {str(e)}")
        
        # 测试不同的查询方式
        print("\n4. 测试语义查询...")
        test_queries = [
            "进入普通图片聊天群",
            "登录",
            "聊天",
            "图片"
        ]
        
        for query in test_queries:
            try:
                result = rag_service.query_similar_stages(query, k=3)
                print(f"\n查询 '{query}' 结果:")
                print(f"  成功: {result['success']}")
                print(f"  结果数量: {result.get('total_results', 0)}")
                if result.get('results'):
                    for r in result['results'][:2]:  # 只显示前2个结果
                        print(f"    - {r.get('stage_name', 'N/A')} (视频{r.get('video_id', 'N/A')})")
            except Exception as e:
                print(f"❌ 查询 '{query}' 失败: {str(e)}")
        
        print("\n=== 检查完成 ===")
        
    except Exception as e:
        print(f"❌ 检查过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

def clear_vector_database():
    """清空向量数据库（谨慎使用）"""
    print("=== 清空向量数据库 ===")
    
    confirm = input("确定要清空向量数据库吗？这将删除所有数据！(输入 'YES' 确认): ")
    if confirm != 'YES':
        print("操作已取消")
        return
    
    db = next(get_db())
    
    try:
        rag_service = VideoRAGService(db)
        
        # 删除collection（如果支持的话）
        try:
            # 注意：这个方法可能因Chroma版本而异
            rag_service.vector_store.delete_collection()
            print("✓ 向量数据库已清空")
        except Exception as e:
            print(f"❌ 清空失败: {str(e)}")
            print("提示：可能需要手动删除 chroma_db 目录")
    
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="向量数据库检查工具")
    parser.add_argument("--clear", action="store_true", help="清空向量数据库")
    
    args = parser.parse_args()
    
    if args.clear:
        clear_vector_database()
    else:
        check_vector_database()