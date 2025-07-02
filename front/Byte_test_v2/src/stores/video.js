import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { videoApi } from '../services/videoApi'
import { message } from 'ant-design-vue'

export const useVideoStore = defineStore('video', () => {
  // 状态
  const videoList = ref([])
  const currentVideo = ref(null)
  const videoFrames = ref([])
  const loading = ref(false)
  const uploading = ref(false)

  // 计算属性
  const videoCount = computed(() => videoList.value.length)
  const hasVideos = computed(() => videoList.value.length > 0)

  // 获取视频列表
  const fetchVideoList = async (params = {}) => {
    loading.value = true
    try {
      const data = await videoApi.getVideoList(params)
      videoList.value = data
      return data
    } catch (error) {
      message.error('获取视频列表失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  // 上传视频
  const uploadVideo = async (file) => {
    uploading.value = true
    try {
      const data = await videoApi.uploadVideo(file)
      videoList.value.unshift(data)
      message.success('视频上传成功')
      return data
    } catch (error) {
      message.error('视频上传失败')
      throw error
    } finally {
      uploading.value = false
    }
  }

  // 获取视频详情
  const fetchVideoDetail = async (fileId) => {
    loading.value = true
    try {
      const data = await videoApi.getVideoDetail(fileId)
      currentVideo.value = data
      return data
    } catch (error) {
      message.error('获取视频详情失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  // 更新视频信息
  const updateVideo = async (fileId, updateData) => {
    loading.value = true
    try {
      const data = await videoApi.updateVideo(fileId, updateData)
      // 更新列表中的视频信息
      const index = videoList.value.findIndex(v => v.id === fileId)
      if (index !== -1) {
        videoList.value[index] = data
      }
      // 更新当前视频信息
      if (currentVideo.value && currentVideo.value.id === fileId) {
        currentVideo.value = data
      }
      message.success('视频信息更新成功')
      return data
    } catch (error) {
      message.error('更新视频信息失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  // 删除视频
  const deleteVideo = async (fileId) => {
    loading.value = true
    try {
      await videoApi.deleteVideo(fileId)
      // 从列表中移除
      videoList.value = videoList.value.filter(v => v.id !== fileId)
      // 清空当前视频（如果是被删除的视频）
      if (currentVideo.value && currentVideo.value.id === fileId) {
        currentVideo.value = null
      }
      message.success('视频删除成功')
    } catch (error) {
      message.error('删除视频失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  // 下载视频
  const downloadVideo = async (fileId, filename) => {
    try {
      const blob = await videoApi.downloadVideo(fileId)
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename || 'video.mp4'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      message.success('视频下载成功')
    } catch (error) {
      message.error('视频下载失败')
      throw error
    }
  }

  // 提取视频帧
  const extractFrames = async (fileId, extractData) => {
    loading.value = true
    try {
      const data = await videoApi.extractFrames(fileId, extractData)
      message.success(`成功提取 ${data.total_frames} 帧`)
      return data
    } catch (error) {
      message.error('提取视频帧失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  // 获取视频帧列表
  const fetchVideoFrames = async (fileId) => {
    loading.value = true
    try {
      const data = await videoApi.getVideoFrames(fileId)
      videoFrames.value = data
      return data
    } catch (error) {
      message.error('获取视频帧列表失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  // 清空当前视频
  const clearCurrentVideo = () => {
    currentVideo.value = null
  }

  // 清空视频帧
  const clearVideoFrames = () => {
    videoFrames.value = []
  }

  return {
    // 状态
    videoList,
    currentVideo,
    videoFrames,
    loading,
    uploading,
    // 计算属性
    videoCount,
    hasVideos,
    // 方法
    fetchVideoList,
    uploadVideo,
    fetchVideoDetail,
    updateVideo,
    deleteVideo,
    downloadVideo,
    extractFrames,
    fetchVideoFrames,
    clearCurrentVideo,
    clearVideoFrames
  }
})