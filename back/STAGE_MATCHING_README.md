# 阶段匹配API使用说明

## 概述

阶段匹配API使用LangChain和豆包AI来分析用户输入，并从数据库中存储的视频阶段信息中找到最相似的匹配项。该API能够理解用户的自然语言查询，并返回相关的视频阶段信息。

## API接口

### 1. 阶段匹配分析

**接口地址**: `POST /stage-matching/match`

**请求参数**:
```json
{
  "user_input": "用户输入的查询文本",
  "video_id": 1
}
```

**响应示例**:
```json
{
  "success": true,
  "user_input": "应用启动",
  "video_id": 1,
  "matched_stages": [
    {
      "stage_id": 1,
      "stage_name": "阶段1",
      "start_time": 0.0,
      "end_time": 2.56,
      "duration": 2.56,
      "description": "应用启动和初始化",
      "similarity_score": 0.85,
      "match_reason": "用户输入'应用启动'与阶段描述'应用启动和初始化'高度匹配"
    }
  ],
  "total_matches": 1,
  "analysis_summary": "找到1个与'应用启动'相关的阶段"
}
```

### 2. 获取视频阶段摘要

**接口地址**: `GET /stage-matching/video/{video_id}/stages-summary`

**响应示例**:
```json
{
  "success": true,
  "video_id": 1,
  "total_stages": 4,
  "stages_summary": [
    {
      "id": 1,
      "stage_name": "阶段1",
      "start_time": 0.0,
      "end_time": 2.56,
      "duration": 2.56,
      "description": "应用启动和初始化"
    }
  ],
  "message": "阶段信息获取成功"
}
```

### 3. 批量阶段匹配

**接口地址**: `POST /stage-matching/batch-match`

**请求参数**:
```json
[
  {
    "user_input": "应用启动",
    "video_id": 1
  },
  {
    "user_input": "登录过程",
    "video_id": 1
  }
]
```

## 使用示例

### Python示例

```python
import requests

# 基础URL
base_url = "http://127.0.0.1:8000"

# 1. 单个阶段匹配
response = requests.post(
    f"{base_url}/stage-matching/match",
    json={
        "user_input": "应用启动",
        "video_id": 1
    }
)

if response.status_code == 200:
    result = response.json()
    print(f"找到 {result['total_matches']} 个匹配阶段")
    for match in result['matched_stages']:
        print(f"阶段: {match['stage_name']}, 相似度: {match['similarity_score']}")

# 2. 获取阶段摘要
response = requests.get(f"{base_url}/stage-matching/video/1/stages-summary")
if response.status_code == 200:
    summary = response.json()
    print(f"视频共有 {summary['total_stages']} 个阶段")
```

### JavaScript示例

```javascript
// 阶段匹配
fetch('http://127.0.0.1:8000/stage-matching/match', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    user_input: '应用启动',
    video_id: 1
  })
})
.then(response => response.json())
.then(data => {
  console.log('匹配结果:', data);
  data.matched_stages.forEach(stage => {
    console.log(`${stage.stage_name}: ${stage.similarity_score}`);
  });
});
```

## 功能特点

1. **智能语义匹配**: 使用豆包AI进行自然语言理解，能够理解用户的意图
2. **相似度评分**: 为每个匹配结果提供0-1之间的相似度分数
3. **详细匹配原因**: 解释为什么某个阶段与用户输入匹配
4. **批量处理**: 支持一次处理多个查询请求
5. **阈值过滤**: 只返回相似度大于0.3的匹配结果

## 注意事项

1. 确保视频已经进行过SSIM分析，生成了阶段信息
2. 用户输入应该尽量具体和清晰
3. 批量请求限制最多10个
4. API需要有效的豆包AI密钥配置

## 错误处理

- `404`: 视频文件不存在
- `400`: 请求参数错误
- `500`: 服务器内部错误

所有错误都会返回详细的错误信息，便于调试和处理。