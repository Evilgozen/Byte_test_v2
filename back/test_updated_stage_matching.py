#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试更新后的阶段匹配功能

这个脚本用于测试更新后的stage_matching_service.py，
验证新的prompt格式和返回结果是否包含起始时间、阶段ID、相似度和匹配原因。
"""

import requests
import json

def test_updated_stage_matching():
    base_url = "http://127.0.0.1:8000"
    
    print("=== 测试更新后的阶段匹配功能 ===")
    
    # 1. 首先获取视频阶段摘要
    print("\n1. 获取视频阶段摘要...")
    try:
        response = requests.get(f"{base_url}/stage-matching/video/1/stages-summary")
        if response.status_code == 200:
            summary_data = response.json()
            print(f"✓ 获取成功，共有 {summary_data.get('total_stages', 0)} 个阶段")
            
            if summary_data.get('stages_summary'):
                print("阶段信息:")
                for stage in summary_data['stages_summary']:
                    print(f"  - 阶段{stage['id']}: {stage['stage_name']} ({stage['start_time']:.2f}s - {stage['end_time']:.2f}s)")
            else:
                print("⚠ 该视频暂无阶段信息，请先进行视频分析")
                return
        else:
            print(f"✗ 获取失败: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"✗ 请求异常: {e}")
        return
    
    # 2. 测试阶段匹配
    print("\n2. 测试阶段匹配...")
    test_cases = [
        {
            "user_input": "应用启动",
            "description": "测试应用启动相关的匹配"
        },
        {
            "user_input": "登录过程",
            "description": "测试登录相关的匹配"
        },
        {
            "user_input": "页面加载",
            "description": "测试页面加载相关的匹配"
        },
        {
            "user_input": "打开会话",
            "description": "测试会话相关的匹配"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: {test_case['description']}")
        print(f"用户输入: '{test_case['user_input']}'")
        
        try:
            response = requests.post(
                f"{base_url}/stage-matching/match",
                json={
                    "user_input": test_case['user_input'],
                    "video_id": 1
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ 匹配成功，找到 {result.get('total_matches', 0)} 个匹配阶段")
                print(f"分析摘要: {result.get('analysis_summary', 'N/A')}")
                
                if result.get('matched_stages'):
                    print("匹配结果:")
                    for j, stage in enumerate(result['matched_stages'], 1):
                        print(f"  {j}. 阶段ID: {stage.get('stage_id')}")
                        print(f"     阶段名称: {stage.get('stage_name')}")
                        print(f"     时间范围: {stage.get('start_time', 'N/A'):.2f}s - {stage.get('end_time', 'N/A'):.2f}s")
                        print(f"     相似度: {stage.get('similarity_score', 'N/A'):.3f}")
                        print(f"     匹配原因: {stage.get('match_reason', 'N/A')}")
                        print()
                else:
                    print("  无匹配阶段")
            else:
                print(f"✗ 匹配失败: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"✗ 请求异常: {e}")
    
    # 3. 测试批量匹配
    print("\n3. 测试批量匹配...")
    try:
        batch_requests = [
            {"user_input": "启动阶段", "video_id": 1},
            {"user_input": "加载完成", "video_id": 1}
        ]
        
        response = requests.post(
            f"{base_url}/stage-matching/batch-match",
            json=batch_requests,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ 批量匹配成功，处理了 {result.get('total_requests', 0)} 个请求")
            
            for i, batch_result in enumerate(result.get('results', []), 1):
                print(f"\n批量结果 {i}:")
                print(f"  用户输入: {batch_result.get('user_input')}")
                print(f"  匹配数量: {batch_result.get('total_matches', 0)}")
                if batch_result.get('matched_stages'):
                    for stage in batch_result['matched_stages']:
                        print(f"    - {stage.get('stage_name')} (相似度: {stage.get('similarity_score', 0):.3f})")
        else:
            print(f"✗ 批量匹配失败: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"✗ 批量匹配异常: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_updated_stage_matching()