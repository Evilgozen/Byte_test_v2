<template>
  <div class="video-keyframes">
    <a-card class="keyframes-card" title="视频关键帧">
      <!-- 关键帧配置 -->
      <div class="keyframes-header">
        <a-row :gutter="16" align="middle">
          <a-col :span="12">
            <a-statistic
              title="关键帧总数"
              :value="keyframes.length"
              :value-style="{ color: '#1890ff' }"
            />
          </a-col>
          <a-col :span="12">
            <div class="header-actions">
              <a-button @click="refreshKeyframes" :loading="loading">
                <reload-outlined /> 刷新
              </a-button>
            </div>
          </a-col>
        </a-row>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-section">
        <a-spin size="large">
          <template #tip>正在加载关键帧...</template>
        </a-spin>
      </div>

      <!-- 关键帧网格 -->
      <div v-else-if="keyframes && keyframes.length > 0" class="keyframes-content">
        <div class="keyframes-grid">
          <div
            v-for="(frame, index) in keyframes"
            :key="frame.id"
            class="keyframe-item"
          >
            <div class="keyframe-image-container">
              <img
                :src="getFrameImageUrl(frame.id)"
                :alt="`关键帧 ${frame.frame_number}`"
                class="keyframe-image"
                @error="handleImageError"
                @click="previewFrame(frame)"
              />
              <div class="keyframe-overlay">
                <a-button
                  type="primary"
                  shape="circle"
                  size="small"
                  @click="previewFrame(frame)"
                >
                  <eye-outlined />
                </a-button>
              </div>
            </div>
            <div class="keyframe-info">
              <div class="frame-time">{{ formatTime(frame.timestamp) }}</div>
              <div class="frame-number">帧 #{{ frame.frame_number }}</div>
              <div class="frame-index">序号: {{ index + 1 }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="empty-state">
        <a-empty
          description="暂无关键帧数据"
          :image="Empty.PRESENTED_IMAGE_SIMPLE"
        >
          <template #description>
            <span style="color: #999">请先进行视频分析以生成关键帧</span>
          </template>
        </a-empty>
      </div>

      <!-- 错误状态 -->
      <div v-if="error" class="error-section">
        <a-alert
          :message="error"
          type="error"
          show-icon
          closable
          @close="error = null"
        />
      </div>
    </a-card>

    <!-- 关键帧预览模态框 -->
    <a-modal
      v-model:open="previewVisible"
      title="关键帧预览"
      :footer="null"
      width="800px"
      centered
    >
      <div v-if="selectedFrame" class="frame-preview">
        <div class="preview-image">
          <img
            :src="getFrameImageUrl(selectedFrame.id)"
            :alt="`关键帧 ${selectedFrame.frame_number}`"
            class="preview-img"
            @error="handleImageError"
          />
        </div>
        <div class="preview-info">
          <a-descriptions :column="2" bordered>
            <a-descriptions-item label="帧号">
              {{ selectedFrame.frame_number }}
            </a-descriptions-item>
            <a-descriptions-item label="时间戳">
              {{ formatTime(selectedFrame.timestamp) }}
            </a-descriptions-item>
            <a-descriptions-item label="帧ID">
              {{ selectedFrame.id }}
            </a-descriptions-item>
            <a-descriptions-item label="文件名">
              {{ selectedFrame.filename || '未知' }}
            </a-descriptions-item>
          </a-descriptions>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { message, Empty } from 'ant-design-vue'
import {
  ReloadOutlined,
  EyeOutlined
} from '@ant-design/icons-vue'
import { videoApi } from '../services/videoApi'

// Props
const props = defineProps({
  videoId: {
    type: [String, Number],
    required: true
  }
})

// 响应式数据
const loading = ref(false)
const keyframes = ref([])
const error = ref(null)
const previewVisible = ref(false)
const selectedFrame = ref(null)

// 方法
const fetchKeyframes = async () => {
  if (!props.videoId) return
  
  try {
    loading.value = true
    error.value = null
    
    const result = await videoApi.getVideoKeyframes(props.videoId)
    if (result.success) {
      keyframes.value = result.keyframes || []
      if (keyframes.value.length > 0) {
        message.success(`加载了 ${keyframes.value.length} 个关键帧`)
      }
    } else {
      throw new Error(result.message || '获取关键帧失败')
    }
  } catch (err) {
    console.error('Fetch keyframes failed:', err)
    error.value = err.response?.data?.detail || err.message || '获取关键帧时发生错误'
    message.error('获取关键帧失败')
  } finally {
    loading.value = false
  }
}

const refreshKeyframes = () => {
  fetchKeyframes()
}

const getFrameImageUrl = (frameId) => {
  return `http://127.0.0.1:8000/files/frames/${frameId}/image`
}

const handleImageError = (event) => {
  event.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2Y1ZjVmNSIvPjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjEyIiBmaWxsPSIjOTk5IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+5Zu+5YOP5Yqg6L295aSx6LSlPC90ZXh0Pjwvc3ZnPg=='
}

const previewFrame = (frame) => {
  selectedFrame.value = frame
  previewVisible.value = true
}

const formatTime = (seconds) => {
  if (!seconds) return '0ms'
  const milliseconds = Math.round(seconds * 1000)
  return `${milliseconds}ms`
}

// 监听videoId变化
watch(() => props.videoId, (newVideoId) => {
  if (newVideoId) {
    fetchKeyframes()
  }
}, { immediate: true })

// 组件挂载时加载关键帧
onMounted(() => {
  if (props.videoId) {
    fetchKeyframes()
  }
})
</script>

<style scoped>
.video-keyframes {
  margin-bottom: 24px;
}

.keyframes-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.keyframes-header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.header-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.loading-section {
  text-align: center;
  padding: 60px 0;
}

.keyframes-content {
  margin-top: 24px;
}

.keyframes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
}

.keyframe-item {
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease;
  background: white;
}

.keyframe-item:hover {
  border-color: #1890ff;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.2);
  transform: translateY(-2px);
}

.keyframe-image-container {
  position: relative;
  overflow: hidden;
}

.keyframe-image {
  width: 100%;
  height: 120px;
  object-fit: cover;
  display: block;
  cursor: pointer;
  transition: transform 0.3s ease;
}

.keyframe-image:hover {
  transform: scale(1.05);
}

.keyframe-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.keyframe-item:hover .keyframe-overlay {
  opacity: 1;
}

.keyframe-info {
  padding: 12px;
  background: #fafafa;
  text-align: center;
}

.frame-time {
  font-size: 13px;
  color: #1890ff;
  font-weight: 600;
  margin-bottom: 4px;
}

.frame-number {
  font-size: 12px;
  color: #666;
  margin-bottom: 2px;
}

.frame-index {
  font-size: 11px;
  color: #999;
}

.empty-state {
  padding: 60px 0;
  text-align: center;
}

.error-section {
  margin-top: 16px;
}

.frame-preview {
  text-align: center;
}

.preview-image {
  margin-bottom: 20px;
  border-radius: 8px;
  overflow: hidden;
  background: #f5f5f5;
}

.preview-img {
  width: 100%;
  max-height: 400px;
  object-fit: contain;
}

.preview-info {
  text-align: left;
}

:deep(.ant-statistic-title) {
  font-size: 14px;
  margin-bottom: 4px;
}

:deep(.ant-statistic-content) {
  font-size: 20px;
  font-weight: 600;
}

:deep(.ant-descriptions-item-label) {
  font-weight: 600;
}
</style>