import requests
import json

# 测试阶段匹配API
def test_stage_matching():
    base_url = "http://127.0.0.1:8000"
    
    # 测试数据
    test_cases = [
        {
            "user_input": "应用启动",
            "video_id": 1
        },
        {
            "user_input": "登录过程",
            "video_id": 1
        },
        {
            "user_input": "页面加载",
            "video_id": 1
        },
        {
            "user_input": "用户交互",
            "video_id": 1
        }
    ]
    
    print("=== 阶段匹配API测试 ===")
    
    # 1. 测试获取视频阶段摘要
    print("\n1. 测试获取视频阶段摘要")
    try:
        response = requests.get(f"{base_url}/stage-matching/video/1/stages-summary")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"成功获取阶段摘要: {data['total_stages']}个阶段")
            for stage in data.get('stages_summary', []):
                print(f"  - {stage['stage_name']}: {stage['start_time']:.2f}s - {stage['end_time']:.2f}s")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 2. 测试单个阶段匹配
    print("\n2. 测试单个阶段匹配")
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: '{test_case['user_input']}'")
        try:
            response = requests.post(
                f"{base_url}/stage-matching/match",
                json=test_case,
                headers={"Content-Type": "application/json"}
            )
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"匹配成功: 找到 {data['total_matches']} 个匹配阶段")
                print(f"分析摘要: {data['analysis_summary']}")
                
                for match in data['matched_stages']:
                    print(f"  - {match['stage_name']} (相似度: {match['similarity_score']:.2f})")
                    print(f"    匹配原因: {match['match_reason']}")
            else:
                print(f"错误: {response.text}")
        except Exception as e:
            print(f"请求失败: {e}")
    
    # 3. 测试批量阶段匹配
    print("\n3. 测试批量阶段匹配")
    try:
        batch_requests = test_cases[:2]  # 只测试前两个
        response = requests.post(
            f"{base_url}/stage-matching/batch-match",
            json=batch_requests,
            headers={"Content-Type": "application/json"}
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"批量匹配成功: 处理了 {data['total_requests']} 个请求")
            for i, result in enumerate(data['results'], 1):
                print(f"  请求 {i}: {result['user_input']} -> {result['total_matches']} 个匹配")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_stage_matching()