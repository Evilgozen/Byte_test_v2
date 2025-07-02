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
    return `http://127.0.0.1:8000/files/frames/${frameId}/image`
  }
}