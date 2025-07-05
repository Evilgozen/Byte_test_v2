#!/usr/bin/env python3
"""
启动视频分析API服务器

使用方法:
python start_server.py
"""

import uvicorn
import sys
import os

def main():
    """启动服务器"""
    print("正在启动视频分析API服务器...")
    print("服务器地址: http://127.0.0.1:8000")
    print("API文档: http://127.0.0.1:8000/docs")
    print("健康检查: http://127.0.0.1:8000/health")
    print("按 Ctrl+C 停止服务器")
    print("-" * 50)
    
    try:
        uvicorn.run(
            "main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"启动服务器时出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()