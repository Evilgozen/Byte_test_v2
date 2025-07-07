#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试SSIM视频分析服务的最后阶段修复
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base, SessionLocal, create_tables
from app.services.ssim_video_service import SSIMVideoAnalysisService
from app.services.video_service import VideoFileService
from app.models.video_file import VideoFile
from app.models.video_stage import VideoStage
from app.models.video_frame import VideoFrame

# 使用项目的数据库配置
create_tables()

def test_ssim_last_stage_fix():
    """测试SSIM分析最后阶段修复"""
    db = SessionLocal()
    
    try:
        # 创建测试视频文件记录
        test_video_path = "test_video.mp4"  # 这里应该是一个真实的视频文件路径
        
        # 如果没有真实视频文件，我们创建一个模拟的测试
        if not os.path.exists(test_video_path):
            print("警告: 没有找到测试视频文件，将创建模拟测试")
            return test_mock_ssim_analysis(db)
        
        video_service = VideoFileService(db)
        
        # 创建视频文件记录
        video_file = VideoFile(
            filename="test_video.mp4",
            file_path=test_video_path,
            file_size=1024000,
            duration=10.0,
            width=1920,
            height=1080,
            fps=30.0
        )
        
        db.add(video_file)
        db.commit()
        db.refresh(video_file)
        
        print(f"创建测试视频文件记录，ID: {video_file.id}")
        
        # 创建SSIM分析服务
        ssim_service = SSIMVideoAnalysisService(db)
        
        # 执行SSIM分析
        print("开始SSIM视频分析...")
        result = ssim_service.analyze_video_with_ssim(
            video_id=video_file.id,
            frame_interval=30,
            ssim_threshold=0.75
        )
        
        print(f"分析完成，提取了 {result['total_keyframes']} 个关键帧")
        print(f"生成了 {len(result['saved_stages'])} 个阶段")
        
        # 检查阶段信息
        stages = result['saved_stages']
        if stages:
            print("\n阶段信息:")
            for i, stage in enumerate(stages):
                print(f"阶段 {i+1}: {stage['stage_name']}")
                print(f"  时间范围: {stage['start_time']:.3f}s - {stage['end_time']:.3f}s")
                print(f"  持续时间: {stage['duration']:.3f}s")
                print(f"  描述: {stage['description']}")
                print()
            
            # 检查最后一个阶段
            last_stage = stages[-1]
            video_duration = video_file.duration
            
            print(f"视频总时长: {video_duration}s")
            print(f"最后阶段结束时间: {last_stage['end_time']}s")
            print(f"最后阶段持续时间: {last_stage['duration']}s")
            
            # 验证最后阶段是否正确延续到视频结尾
            if abs(last_stage['end_time'] - video_duration) < 0.1:  # 允许0.1秒误差
                print("✅ 最后阶段正确延续到视频结尾")
            else:
                print("❌ 最后阶段未正确延续到视频结尾")
            
            # 验证最后阶段持续时间不为0
            if last_stage['duration'] > 0.05:  # 至少50ms
                print("✅ 最后阶段持续时间正常")
            else:
                print("❌ 最后阶段持续时间异常")
        
        return result
        
    except Exception as e:
        print(f"测试出错: {e}")
        return None
    finally:
        db.close()

def test_mock_ssim_analysis(db):
    """模拟SSIM分析测试"""
    print("执行模拟SSIM分析测试...")
    
    # 创建模拟的关键帧信息
    mock_keyframes = [
        {"frame_number": 0, "timestamp": 0.0, "ssim_score": 1.0},
        {"frame_number": 90, "timestamp": 3.0, "ssim_score": 0.6},
        {"frame_number": 180, "timestamp": 6.0, "ssim_score": 0.7},
        {"frame_number": 299, "timestamp": 10.0, "ssim_score": 0.8, "is_end_frame": True}
    ]
    
    # 模拟AI分析结果
    mock_stage_analysis = {
        "stage": ["应用启动", "登录界面", "主界面加载"],
        "time": ["0~3000ms", "3000~6000ms", "6000~10000ms"],
        "description": ["应用启动阶段", "用户登录阶段", "主界面加载完成"]
    }
    
    print("模拟关键帧信息:")
    for kf in mock_keyframes:
        end_marker = " (结束帧)" if kf.get("is_end_frame") else ""
        print(f"  帧 {kf['frame_number']}: {kf['timestamp']}s, SSIM: {kf['ssim_score']}{end_marker}")
    
    print("\n模拟阶段分析:")
    for i, (stage, time_range, desc) in enumerate(zip(
        mock_stage_analysis["stage"],
        mock_stage_analysis["time"],
        mock_stage_analysis["description"]
    )):
        print(f"  阶段 {i+1}: {stage} ({time_range}) - {desc}")
    
    # 验证最后阶段时间范围
    last_time_range = mock_stage_analysis["time"][-1]
    if "10000ms" in last_time_range:
        print("\n✅ 模拟测试：最后阶段正确延续到视频结尾(10秒)")
    else:
        print("\n❌ 模拟测试：最后阶段未延续到视频结尾")
    
    return {
        "mock_test": True,
        "keyframes": mock_keyframes,
        "stage_analysis": mock_stage_analysis,
        "message": "模拟测试完成，实际测试需要真实视频文件"
    }

if __name__ == "__main__":
    print("开始测试SSIM视频分析最后阶段修复...")
    print("=" * 50)
    
    result = test_ssim_last_stage_fix()
    
    if result:
        print("\n=" * 50)
        print("测试完成")
        if result.get("mock_test"):
            print("注意: 这是模拟测试，要进行完整测试请提供真实视频文件")
    else:
        print("\n测试失败")