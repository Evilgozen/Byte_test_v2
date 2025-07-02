#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API功能的脚本
"""

import requests
import json

# API基础URL
BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_health_check():
    """测试健康检查"""
    try:
        response = requests.get("http://127.0.0.1:8000/health")
        print(f"健康检查: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"健康检查失败: {e}")
        return False

def test_get_files():
    """测试获取文件列表"""
    try:
        response = requests.get(f"{BASE_URL}/files/")
        print(f"获取文件列表: {response.status_code}")
        if response.status_code == 200:
            files = response.json()
            print(f"文件数量: {len(files)}")
            for file in files[:3]:  # 只显示前3个
                print(f"  - {file['original_filename']} (ID: {file['id']})")
        return response.status_code == 200
    except Exception as e:
        print(f"获取文件列表失败: {e}")
        return False

def test_upload_file(file_path):
    """测试文件上传"""
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path, f, 'video/mp4')}
            response = requests.post(f"{BASE_URL}/files/upload", files=files)
        
        print(f"文件上传: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"上传成功: {result['original_filename']} (ID: {result['id']})")
            return result['id']
        else:
            print(f"上传失败: {response.text}")
            return None
    except Exception as e:
        print(f"文件上传失败: {e}")
        return None

def test_extract_frames(file_id):
    """测试帧提取"""
    try:
        data = {
            "video_file_id": file_id,
            "interval": 2.0,  # 每2秒提取一帧
            "max_frames": 10   # 最多10帧
        }
        response = requests.post(
            f"{BASE_URL}/files/{file_id}/extract-frames", 
            json=data
        )
        
        print(f"帧提取: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"提取成功: {result['total_frames']} 帧")
            return True
        else:
            print(f"帧提取失败: {response.text}")
            return False
    except Exception as e:
        print(f"帧提取失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=== API功能测试 ===")
    
    # 1. 健康检查
    print("\n1. 测试健康检查...")
    if not test_health_check():
        print("❌ 服务器未启动或不可访问")
        return
    
    # 2. 获取文件列表
    print("\n2. 测试获取文件列表...")
    test_get_files()
    
    # 3. 文件上传测试（需要提供测试视频文件）
    print("\n3. 测试文件上传...")
    print("请将测试视频文件放在当前目录下，命名为 'test_video.mp4'")
    
    # 4. 帧提取测试
    print("\n4. 如果有视频文件，可以测试帧提取功能")
    
    print("\n=== 测试完成 ===")
    print("\n可用的API端点:")
    print("- GET /api/v1/files/ - 获取文件列表")
    print("- POST /api/v1/files/upload - 上传视频文件")
    print("- GET /api/v1/files/{id} - 获取文件详情")
    print("- PUT /api/v1/files/{id} - 更新文件信息")
    print("- DELETE /api/v1/files/{id} - 删除文件")
    print("- POST /api/v1/files/{id}/extract-frames - 提取视频帧")
    print("- GET /api/v1/files/{id}/frames - 获取帧列表")
    print("- GET /api/v1/files/frames/{frame_id}/image - 获取帧图片")

if __name__ == "__main__":
    main()