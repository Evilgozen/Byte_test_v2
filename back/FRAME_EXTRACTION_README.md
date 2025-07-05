# 视频帧提取API修复和优化

## 问题修复

### 原始问题
- **422 Unprocessable Entity错误**: 由于`FrameExtractionRequest`中包含`video_file_id`字段，但该字段应该通过URL路径参数传递，导致参数验证失败。

### 解决方案
1. **分离API请求模型和服务请求模型**:
   - `FrameExtractionRequest`: 用于API接口，不包含`video_file_id`
   - `FrameExtractionServiceRequest`: 用于内部服务，包含完整参数

2. **模块化帧提取逻辑**:
   - 创建了`VideoFrameExtractor`类和多种提取策略
   - 支持均匀提取、关键帧提取、智能提取等多种方法

## 新功能特性

### 1. 多种提取方法

#### 均匀提取 (uniform)
```json
{
  "interval": 1.0,
  "max_frames": 10,
  "extraction_method": "uniform"
}
```

#### 每秒帧数提取
```json
{
  "frames_per_second": 5.0,
  "max_frames": 20,
  "extraction_method": "uniform"
}
```

#### 关键帧提取 (keyframe)
```json
{
  "max_frames": 15,
  "extraction_method": "keyframe"
}
```

#### 智能提取 (smart)
```json
{
  "max_frames": 12,
  "extraction_method": "smart"
}
```

### 2. API接口

**POST** `/files/{file_id}/extract-frames`

**请求参数**:
- `interval` (可选): 提取间隔（秒），默认1.0
- `max_frames` (可选): 最大帧数限制
- `extraction_method` (可选): 提取方法，默认"uniform"
- `frames_per_second` (可选): 每秒提取帧数

**响应格式**:
```json
{
  "video_file_id": 1,
  "total_frames": 10,
  "extracted_frames": [
    {
      "id": 1,
      "video_file_id": 1,
      "frame_number": 0,
      "timestamp": 0.0,
      "frame_path": "static/cut_files/video_1/frame_000000.jpg",
      "width": 1920,
      "height": 1080,
      "created_at": "2024-01-01T00:00:00"
    }
  ],
  "message": "成功提取 10 帧"
}
```

## 使用示例

### 1. 基础均匀提取（每秒1帧）
```bash
curl -X POST "http://localhost:8000/files/1/extract-frames" \
  -H "Content-Type: application/json" \
  -d '{
    "interval": 1.0,
    "max_frames": 10,
    "extraction_method": "uniform"
  }'
```

### 2. 高频率提取（每秒5帧）
```bash
curl -X POST "http://localhost:8000/files/1/extract-frames" \
  -H "Content-Type: application/json" \
  -d '{
    "frames_per_second": 5.0,
    "max_frames": 20,
    "extraction_method": "uniform"
  }'
```

### 3. 关键帧提取
```bash
curl -X POST "http://localhost:8000/files/1/extract-frames" \
  -H "Content-Type: application/json" \
  -d '{
    "max_frames": 15,
    "extraction_method": "keyframe"
  }'
```

### 4. 智能提取
```bash
curl -X POST "http://localhost:8000/files/1/extract-frames" \
  -H "Content-Type: application/json" \
  -d '{
    "max_frames": 12,
    "extraction_method": "smart"
  }'
```

## 测试

运行测试脚本:
```bash
python test_frame_extraction.py
```

该脚本会自动测试所有提取方法并显示结果。

## 技术实现

### 架构设计

```
API Layer (file.py)
    ↓
Service Layer (file_service.py)
    ↓
Utility Layer (frame_extractor.py)
    ↓
Strategy Pattern (提取策略)
```

### 提取策略

1. **UniformExtractionStrategy**: 均匀间隔提取
2. **KeyframeExtractionStrategy**: 基于场景变化检测的关键帧提取
3. **SmartExtractionStrategy**: 结合均匀采样和关键帧检测

### 关键帧检测算法

使用直方图相关性分析:
- 计算连续帧的灰度直方图
- 使用OpenCV的`compareHist`函数计算相关性
- 当相关性低于阈值时，认为是关键帧

## 依赖更新

新增依赖:
- `scikit-image>=0.21.0`: 用于SSIM计算
- `numpy>=1.24.0`: 数值计算

## 错误处理

- 自动清理失败时产生的临时文件
- 详细的错误信息返回
- 数据库事务回滚机制

## 性能优化

- 避免重复提取：每次提取前清理已存在的帧
- 内存优化：逐帧处理，避免一次性加载所有帧
- 文件管理：自动创建和清理目录结构

## 兼容性

- 向后兼容原有API调用方式
- 新参数都是可选的，有合理的默认值
- 支持多种视频格式（通过OpenCV）