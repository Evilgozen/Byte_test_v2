# 视频分析RAG功能使用指南

## 概述

本项目已集成Chroma向量数据库和RAG（检索增强生成）功能，用于视频阶段分析的智能存储、查询和对比。

## 功能特性

### 1. 向量化存储
- 自动将视频阶段分析结果存储到Chroma向量数据库
- 支持产品名称元数据标记
- 防重复存储机制
- 支持批量删除

### 2. 智能查询
- 基于语义相似度的阶段查询
- 支持产品名称过滤
- 返回相关视频ID和阶段ID
- 可配置返回结果数量

### 3. 对比报告生成
- AI驱动的阶段对比分析
- 自动生成详细报告
- 支持跨产品对比

## API接口

### 1. 视频分析（已更新）

```http
POST /video-analysis/ssim-analysis/{video_id}
```

**参数：**
- `video_id`: 视频文件ID
- `product_name`: 产品名称（必填，用于向量存储元数据）
- `frame_interval`: 帧间隔（默认30）
- `ssim_threshold`: SSIM阈值（默认0.75）

**响应示例：**
```json
{
  "success": true,
  "message": "SSIM视频分析完成",
  "data": {
    "video_id": 1,
    "product_name": "产品A",
    "total_keyframes": 5,
    "stage_analysis": [...],
    "rag_storage": {
      "stored_stages": 3,
      "message": "成功存储到向量数据库"
    }
  }
}
```

### 2. 查询相似阶段

```http
POST /video-analysis/rag/query-similar-stages
```

**参数：**
- `query`: 查询描述文本
- `product_name`: 产品名称过滤（可选）
- `k`: 返回结果数量（默认5，最大20）

**响应示例：**
```json
{
  "success": true,
  "message": "相似阶段查询完成",
  "data": {
    "query": "用户登录流程",
    "results": [
      {
        "video_id": 1,
        "stage_id": "stage_1",
        "stage_name": "登录阶段",
        "similarity_score": 0.95,
        "content": "用户进入应用并完成登录操作",
        "metadata": {
          "product_name": "产品A",
          "start_time": "00:00:00",
          "end_time": "00:00:30"
        }
      }
    ]
  }
}
```

### 3. 生成对比报告

```http
POST /video-analysis/rag/generate-comparison-report
```

**参数：**
- `query`: 查询描述文本
- `product_name`: 产品名称过滤（可选）

**响应示例：**
```json
{
  "success": true,
  "message": "对比报告生成完成",
  "data": {
    "query": "分析登录流程的用户体验",
    "report": "基于检索到的相似阶段，生成的详细对比分析报告...",
    "similar_stages": [...]
  }
}
```

## 使用流程

### 1. 视频分析和存储
```bash
# 分析视频并存储到向量数据库
curl -X POST "http://localhost:8000/video-analysis/ssim-analysis/1" \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "产品A",
    "frame_interval": 30,
    "ssim_threshold": 0.75
  }'
```

### 2. 查询相似阶段
```bash
# 查询相似的登录流程
curl -X POST "http://localhost:8000/video-analysis/rag/query-similar-stages" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "用户登录操作流程",
    "product_name": "产品A",
    "k": 5
  }'
```

### 3. 生成对比报告
```bash
# 生成登录流程对比报告
curl -X POST "http://localhost:8000/video-analysis/rag/generate-comparison-report" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "对比不同版本的登录流程用户体验",
    "product_name": "产品A"
  }'
```

## 配置说明

### 环境变量
确保以下环境变量已正确配置：

```bash
# Volcengine Ark配置
ARK_API_KEY=your_ark_api_key
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3

# Chroma配置
CHROMA_PERSIST_DIRECTORY=./chroma_db
```

### 依赖包
```bash
pip install langchain-chroma
pip install langchain-openai
pip install volcengine
```

## 测试

运行集成测试：
```bash
python test_rag_integration.py
```

## 注意事项

1. **产品名称**: 每次分析时必须提供产品名称，用于数据隔离和过滤
2. **重复存储**: 系统会自动检测并防止重复存储相同的分析结果
3. **数据清理**: 删除视频分析时会同时清理向量数据库中的相关数据
4. **性能优化**: 建议根据实际使用情况调整查询参数k值
5. **错误处理**: 所有API都包含完整的错误处理和状态返回

## 故障排除

### 常见问题及解决方案

**1. Filter语法错误**
```
错误: "Expected where to have exactly one operator"
解决: 使用正确的Chroma filter语法
```

**2. 查询结果为空**
- 检查向量数据库中是否有数据：`python check_vector_db.py`
- 确认产品名称匹配
- 验证数据是否正确存储

**3. 存储失败**
- 检查环境变量配置
- 验证Chroma目录权限
- 运行诊断工具：`python fix_rag_issues.py --diagnose`

### 诊断工具

**检查向量数据库内容：**
```bash
# 查看所有存储的数据
python check_vector_db.py

# 清空向量数据库（谨慎使用）
python check_vector_db.py --clear
```

**运行诊断和修复：**
```bash
# 完整诊断
python fix_rag_issues.py

# 仅诊断问题
python fix_rag_issues.py --diagnose

# 测试filter语法
python fix_rag_issues.py --test-filter

# 测试手动存储
python fix_rag_issues.py --test-storage

# 重置数据库
python fix_rag_issues.py --reset
```

### 数据验证步骤

1. **验证存储**：分析视频后检查返回的`rag_storage`字段
2. **验证查询**：使用诊断工具检查数据是否存在
3. **验证filter**：确认查询条件正确
4. **验证环境**：检查所有必需的环境变量

## 扩展功能

### 未来可扩展的功能：
1. 飞书API集成（任务4）
2. 多模态检索（图像+文本）
3. 自定义embedding模型
4. 批量分析和对比
5. 实时查询优化