import requests
import json
import time

# API基础URL
BASE_URL = "http://127.0.0.1:8000"

def test_ssim_analysis():
    """测试SSIM视频分析功能"""
    print("=== 测试SSIM视频分析功能 ===")
    
    # 1. 获取视频文件列表
    print("\n1. 获取视频文件列表...")
    response = requests.get(f"{BASE_URL}/files/")
    if response.status_code == 200:
        videos = response.json()
        print(f"找到 {len(videos)} 个视频文件")
        if videos:
            video_id = videos[0]['id']
            print(f"使用视频ID: {video_id} ({videos[0]['original_filename']})")
        else:
            print("没有找到视频文件，请先上传视频")
            return
    else:
        print(f"获取视频列表失败: {response.status_code}")
        return
    
    # 2. 执行SSIM分析
    print("\n2. 执行SSIM分析...")
    analysis_params = {
        "frame_interval": 30,  # 每30帧检测一次
        "ssim_threshold": 0.75  # SSIM阈值
    }
    
    print(f"分析参数: {analysis_params}")
    response = requests.post(
        f"{BASE_URL}/video-analysis/ssim-analysis/{video_id}",
        params=analysis_params
    )
    
    if response.status_code == 200:
        result = response.json()
        print("SSIM分析成功!")
        print(f"提取关键帧数量: {result['data']['total_keyframes']}")
        print(f"生成阶段数量: {len(result['data']['saved_stages'])}")
        
        # 显示阶段信息
        print("\n阶段信息:")
        for i, stage in enumerate(result['data']['saved_stages'], 1):
            print(f"  {i}. {stage['stage_name']} ({stage['start_time']:.2f}s - {stage['end_time']:.2f}s)")
            print(f"     描述: {stage['description']}")
        
        # 显示关键帧信息
        print("\n关键帧信息:")
        for i, frame in enumerate(result['data']['keyframes'][:5], 1):  # 只显示前5个
            print(f"  {i}. 帧号: {frame['frame_number']}, 时间: {frame['timestamp']:.2f}s, SSIM: {frame['ssim_score']:.3f}")
        
        if len(result['data']['keyframes']) > 5:
            print(f"  ... 还有 {len(result['data']['keyframes']) - 5} 个关键帧")
            
    else:
        print(f"SSIM分析失败: {response.status_code}")
        print(f"错误信息: {response.text}")
        return
    
    # 3. 获取视频阶段信息
    print("\n3. 获取视频阶段信息...")
    response = requests.get(f"{BASE_URL}/video-analysis/video/{video_id}/stages")
    if response.status_code == 200:
        stages_result = response.json()
        print(f"获取到 {stages_result['total_stages']} 个阶段")
    else:
        print(f"获取阶段信息失败: {response.status_code}")
    
    # 4. 获取视频关键帧信息
    print("\n4. 获取视频关键帧信息...")
    response = requests.get(f"{BASE_URL}/video-analysis/video/{video_id}/keyframes")
    if response.status_code == 200:
        frames_result = response.json()
        print(f"获取到 {frames_result['total_frames']} 个关键帧")
    else:
        print(f"获取关键帧信息失败: {response.status_code}")
    
    # 5. 测试删除分析结果
    print("\n5. 测试删除分析结果...")
    confirm = input("是否要删除分析结果? (y/N): ")
    if confirm.lower() == 'y':
        response = requests.delete(f"{BASE_URL}/video-analysis/analysis/{video_id}")
        if response.status_code == 200:
            delete_result = response.json()
            print("删除成功!")
            print(f"删除了 {delete_result['data']['deleted_frames']} 个关键帧")
            print(f"删除了 {delete_result['data']['deleted_stages']} 个阶段")
        else:
            print(f"删除失败: {response.status_code}")
    else:
        print("跳过删除操作")

def test_api_health():
    """测试API健康状态"""
    print("=== 测试API健康状态 ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("API服务正常运行")
            return True
        else:
            print(f"API服务异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("无法连接到API服务，请确保服务已启动")
        return False

if __name__ == "__main__":
    print("SSIM视频分析功能测试")
    print("=" * 50)
    
    # 检查API服务状态
    if test_api_health():
        print("\n" + "=" * 50)
        test_ssim_analysis()
    else:
        print("\n请先启动API服务: python start_server.py")
    
    print("\n测试完成!")