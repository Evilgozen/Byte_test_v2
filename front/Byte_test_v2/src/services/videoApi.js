import api from './api'

// 视频文件相关API
export const videoApi = {
  // 上传视频文件
  uploadVideo(file) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 获取视频文件列表
  getVideoList(params = {}) {
    return api.get('/files/', { params })
  },

  // 获取视频文件详情
  getVideoDetail(fileId) {
    return api.get(`/files/${fileId}`)
  },

  // 更新视频文件信息
  updateVideo(fileId, data) {
    return api.put(`/files/${fileId}`, data)
  },

  // 删除视频文件
  deleteVideo(fileId) {
    return api.delete(`/files/${fileId}`)
  },

  // 下载视频文件
  downloadVideo(fileId) {
    return api.get(`/files/${fileId}/download`, {
      responseType: 'blob'
    })
  },

  // 提取视频帧
  extractFrames(fileId, data) {
    return api.post(`/files/${fileId}/extract-frames`, data)
  },

  // 获取视频帧列表
  getVideoFrames(fileId) {
    return api.get(`/files/${fileId}/frames`)
  },

  // 获取帧图片
  getFrameImage(frameId) {
    return `http://127.0.0.1:8000//files/frames/${frameId}/image`
  },

  // 视频分析相关API
  // SSIM视频分析
  analyzeVideoWithSSIM(videoId, params = {}) {
    const { product_name, frame_interval = 30, ssim_threshold = 0.75 } = params
    const queryParams = new URLSearchParams({
      product_name,
      frame_interval: frame_interval.toString(),
      ssim_threshold: ssim_threshold.toString()
    })
    return api.post(`/video-analysis/ssim-analysis/${videoId}?${queryParams}`)
  },

  // 删除视频分析结果
  deleteVideoAnalysis(videoId) {
    return api.delete(`/video-analysis/analysis/${videoId}`)
  },

  // 获取视频阶段信息
  getVideoStages(videoId) {
    return api.get(`/video-analysis/video/${videoId}/stages`)
  },

  // 获取视频关键帧信息
  getVideoKeyframes(videoId) {
    return api.get(`/video-analysis/video/${videoId}/keyframes`)
  },

  // 阶段匹配相关API
  // 阶段匹配分析
  matchStages(data) {
    return api.post('/stage-matching/match', data)
  },

  // 获取视频阶段摘要
  getVideoStagesSummary(videoId) {
    return api.get(`/stage-matching/video/${videoId}/stages-summary`)
  },

  // 批量阶段匹配
  batchMatchStages(requests) {
    return api.post('/stage-matching/batch-match', requests)
  },

  // RAG分析相关API
  // 查询相似视频阶段
  querySimilarStages(params = {}) {
    const { query, product_name, k = 5, similarity_threshold = 0.7 } = params
    const queryParams = new URLSearchParams({
      query,
      k: k.toString(),
      similarity_threshold: similarity_threshold.toString()
    })
    if (product_name) {
      queryParams.append('product_name', product_name)
    }
    return api.post(`/video-analysis/rag/query-similar-stages?${queryParams}`)
  },

  // 生成阶段对比报告
  generateComparisonReport(params = {}) {
    const { query, product_name, similarity_threshold = 0.7 } = params
    const queryParams = new URLSearchParams({
      query,
      similarity_threshold: similarity_threshold.toString()
    })
    if (product_name) {
      queryParams.append('product_name', product_name)
    }
    return api.post(`/video-analysis/rag/generate-comparison-report?${queryParams}`)
  }
}