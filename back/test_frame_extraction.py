#!/usr/bin/env python3
"""
视频帧提取API测试脚本

使用示例:
python test_frame_extraction.py
"""

import requests
import json
import time
from typing import Dict, Any

class FrameExtractionTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_uniform_extraction(self, file_id: int) -> Dict[str, Any]:
        """测试均匀提取"""
        print("\n=== 测试均匀提取 ===")
        
        payload = {
            "interval": 1.0,  # 每秒一帧
            "max_frames": 10,
            "extraction_method": "uniform"
        }
        
        response = self.session.post(
            f"{self.base_url}/files/{file_id}/extract-frames",
            json=payload
        )
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"提取成功: {result['message']}")
            print(f"总帧数: {result['total_frames']}")
            return result
        else:
            print(f"错误: {response.text}")
            return {}
    
    def test_frames_per_second_extraction(self, file_id: int) -> Dict[str, Any]:
        """测试每秒帧数提取"""
        print("\n=== 测试每秒5帧提取 ===")
        
        payload = {
            "frames_per_second": 5.0,  # 每秒5帧
            "max_frames": 20,
            "extraction_method": "uniform"
        }
        
        response = self.session.post(
            f"{self.base_url}/files/{file_id}/extract-frames",
            json=payload
        )
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"提取成功: {result['message']}")
            print(f"总帧数: {result['total_frames']}")
            return result
        else:
            print(f"错误: {response.text}")
            return {}
    
    def test_keyframe_extraction(self, file_id: int) -> Dict[str, Any]:
        """测试关键帧提取"""
        print("\n=== 测试关键帧提取 ===")
        
        payload = {
            "max_frames": 15,
            "extraction_method": "keyframe"
        }
        
        response = self.session.post(
            f"{self.base_url}/files/{file_id}/extract-frames",
            json=payload
        )
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"提取成功: {result['message']}")
            print(f"总帧数: {result['total_frames']}")
            return result
        else:
            print(f"错误: {response.text}")
            return {}
    
    def test_smart_extraction(self, file_id: int) -> Dict[str, Any]:
        """测试智能提取"""
        print("\n=== 测试智能提取 ===")
        
        payload = {
            "max_frames": 12,
            "extraction_method": "smart"
        }
        
        response = self.session.post(
            f"{self.base_url}/files/{file_id}/extract-frames",
            json=payload
        )
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"提取成功: {result['message']}")
            print(f"总帧数: {result['total_frames']}")
            return result
        else:
            print(f"错误: {response.text}")
            return {}
    
    def get_video_files(self) -> Dict[str, Any]:
        """获取视频文件列表"""
        response = self.session.get(f"{self.base_url}/files/")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"获取文件列表失败: {response.text}")
            return []
    
    def get_video_frames(self, file_id: int) -> Dict[str, Any]:
        """获取视频帧列表"""
        response = self.session.get(f"{self.base_url}/files/{file_id}/frames")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"获取帧列表失败: {response.text}")
            return []
    
    def run_all_tests(self, file_id: int = None):
        """运行所有测试"""
        print("开始视频帧提取API测试...")
        
        # 如果没有指定文件ID，尝试获取第一个文件
        if file_id is None:
            files = self.get_video_files()
            if not files:
                print("没有找到视频文件，请先上传视频")
                return
            file_id = files[0]['id']
            print(f"使用文件ID: {file_id} ({files[0]['original_filename']})")
        
        # 测试各种提取方法
        results = {}
        
        # 1. 均匀提取
        results['uniform'] = self.test_uniform_extraction(file_id)
        time.sleep(1)
        
        # 2. 每秒帧数提取
        results['frames_per_second'] = self.test_frames_per_second_extraction(file_id)
        time.sleep(1)
        
        # 3. 关键帧提取
        results['keyframe'] = self.test_keyframe_extraction(file_id)
        time.sleep(1)
        
        # 4. 智能提取
        results['smart'] = self.test_smart_extraction(file_id)
        
        # 获取最终的帧列表
        print("\n=== 获取帧列表 ===")
        frames = self.get_video_frames(file_id)
        print(f"当前视频共有 {len(frames)} 帧")
        
        # 显示一些帧的信息
        if frames:
            print("\n前5帧信息:")
            for i, frame in enumerate(frames[:5]):
                print(f"  帧{i+1}: 帧号={frame['frame_number']}, 时间戳={frame['timestamp']:.2f}s")
        
        print("\n=== 测试完成 ===")
        return results

def main():
    """主函数"""
    tester = FrameExtractionTester()
    
    # 可以指定特定的文件ID进行测试
    # file_id = 2  # 根据实际情况修改
    file_id = None  # 自动选择第一个文件
    
    try:
        results = tester.run_all_tests(file_id)
        print("\n所有测试完成！")
    except Exception as e:
        print(f"测试过程中出现错误: {e}")

if __name__ == "__main__":
    main()