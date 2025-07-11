# RAG问题快速修复指南

## 🚨 当前问题

您遇到的错误：
```
"Expected where to have exactly one operator, got {'video_id': 2, 'stage_index': 0, 'product_name': '飞书'} in query."
```

**原因**：Chroma向量数据库的filter语法要求使用特定的操作符格式。

## ✅ 已修复的问题

我已经修复了以下文件中的filter语法：
- `app/services/video_rag_service.py` - 所有查询方法的filter语法
- 使用正确的 `{"$and": [...]}` 和 `{"$eq": value}` 格式

## 🔧 立即解决步骤

### 1. 重启服务
```bash
# 停止当前服务
# 重新启动服务以加载修复后的代码
python main.py
```

### 2. 检查向量数据库状态
```bash
# 运行诊断工具
python fix_rag_issues.py --diagnose

# 检查数据库内容
python check_vector_db.py
```

### 3. 测试修复效果
```bash
# 测试新的API调用
curl -X POST "http://127.0.0.1:8000/video-analysis/ssim-analysis/2?product_name=飞书&frame_interval=6&ssim_threshold=0.75"

# 测试查询功能
curl -X POST "http://127.0.0.1:8000/video-analysis/rag/query-similar-stages?query=进入普通图片聊天群&product_name=飞书&k=5"
```

## 🔍 如果问题仍然存在

### 选项1：重置向量数据库
```bash
# 完全重置Chroma数据库
python fix_rag_issues.py --reset

# 重新分析视频
curl -X POST "http://127.0.0.1:8000/video-analysis/ssim-analysis/2?product_name=飞书&frame_interval=6&ssim_threshold=0.75"
```

### 选项2：手动测试存储
```bash
# 运行手动存储测试
python fix_rag_issues.py --test-storage
```

### 选项3：检查环境配置
确保 `.env` 文件包含：
```env
ARK_API_KEY=6e0538ce-25b8-4f61-9342-505879befdda
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
CHROMA_PERSIST_DIRECTORY=./chroma_db
CHROMA_COLLECTION_NAME=video_analysis
```

## 📊 验证修复结果

### 成功的响应应该是：
```json
{
  "success": true,
  "message": "SSIM视频分析完成",
  "data": {
    "rag_storage": {
      "success": true,
      "stored_stages": 3,
      "message": "成功存储 3 个阶段到向量数据库"
    }
  }
}
```

### 查询应该返回：
```json
{
  "success": true,
  "message": "相似阶段查询完成",
  "data": {
    "total_results": 1,
    "results": [
      {
        "video_id": 2,
        "stage_name": "...",
        "product_name": "飞书"
      }
    ]
  }
}
```

## 🆘 如果仍有问题

1. **检查日志**：查看服务器控制台输出的详细错误信息
2. **运行完整诊断**：`python fix_rag_issues.py`
3. **检查依赖**：确保所有包都已正确安装
4. **重新安装依赖**：`pip install -r requirements.txt`

## 📞 调试命令速查

```bash
# 快速诊断
python fix_rag_issues.py --diagnose

# 查看数据
python check_vector_db.py

# 测试存储
python fix_rag_issues.py --test-storage

# 重置数据库
python fix_rag_issues.py --reset

# 测试集成
python test_rag_integration.py
```

---

**注意**：修复后的代码使用了正确的Chroma filter语法，应该能解决您遇到的问题。如果问题持续存在，请运行诊断工具获取更详细的信息。