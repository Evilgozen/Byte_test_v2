<template>
  <div class="video-segments">
    <a-card class="segments-card" title="视频分割帧">
      <!-- 分割帧配置 -->
      <div class="segments-header">
        <a-row :gutter="16" align="middle">
          <a-col :span="8">
            <a-statistic
              title="分割帧总数"
              :value="segments.length"
              :value-style="{ color: '#52c41a' }"
            />
          </a-col>
          <a-col :span="8">
            <a-statistic
              title="视频阶段数"
              :value="stageCount"
              :value-style="{ color: '#1890ff' }"
            />
          </a-col>
          <a-col :span="8">
            <div class="header-actions">
              <a-button @click="refreshSegments" :loading="loading">
                <reload-outlined /> 刷新
              </a-button>
            </div>
          </a-col>
        </a-row>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-section">
        <a-spin size="large">
          <template #tip>正在加载分割帧...</template>
        </a-spin>
      </div>

      <!-- 分割帧按阶段显示 -->
      <div v-else-if="segmentsByStage && Object.keys(segmentsByStage).length > 0" class="segments-content">
        <div
          v-for="(stageSegments, stageName) in segmentsByStage"
          :key="stageName"
          class="stage-section"
        >
          <div class="stage-header">
            <h4>
              <a-tag :color="getStageColor(stageName)">{{ stageName }}</a-tag>
              <span class="stage-info">
                {{ stageSegments.length }} 个分割帧
                <span v-if="stageSegments[0]?.stage_info" class="stage-time">
                  ({{ formatTime(stageSegments[0].stage_info.start_time) }} - 
                  {{ formatTime(stageSegments[0].stage_info.end_time) }})
                </span>
              </span>
            </h4>
            <div v-if="stageSegments[0]?.stage_info?.description" class="stage-description">
              {{ stageSegments[0].stage_info.description }}
            </div>
          </div>
          
          <div class="segments-grid">
            <div
              v-for="(segment, index) in stageSegments"
              :key="segment.id"
              class="segment-item"
            >
              <div class="segment-image-container">
                <img
                  :src="getFrameImageUrl(segment.id)"
                  :alt="`分割帧 ${segment.frame_number}`"
                  class="segment-image"
                  @error="handleImageError"
                  @click="previewSegment(segment)"
                />
                <div class="segment-overlay">
                  <a-button
                    type="primary"
                    shape="circle"
                    size="small"
                    @click="previewSegment(segment)"
                  >
                    <eye-outlined />
                  </a-button>
                </div>
              </div>
              <div class="segment-info">
                <div class="frame-time">{{ formatTime(segment.timestamp) }}</div>
                <div class="frame-number">帧 #{{ segment.frame_number }}</div>
                <div class="frame-index">序号: {{ index + 1 }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="empty-state">
        <a-empty
          description="暂无分割帧数据"
          :image="Empty.PRESENTED_IMAGE_SIMPLE"
        >
          <template #description>
            <span style="color: #999">请先进行视频分析以生成分割帧</span>
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

    <!-- 分割帧预览模态框 -->
    <a-modal
      v-model:open="previewVisible"
      title="分割帧预览"
      :footer="null"
      width="800px"
      centered
    >
      <div v-if="selectedSegment" class="segment-preview">
        <div class="preview-image">
          <img
            :src="getFrameImageUrl(selectedSegment.id)"
            :alt="`分割帧 ${selectedSegment.frame_number}`"
            class="preview-img"
            @error="handleImageError"
          />
        </div>
        <div class="preview-info">
          <a-descriptions :column="2" bordered>
            <a-descriptions-item label="帧号">
              {{ selectedSegment.frame_number }}
            </a-descriptions-item>
            <a-descriptions-item label="时间戳">
              {{ formatTime(selectedSegment.timestamp) }}
            </a-descriptions-item>
            <a-descriptions-item label="所属阶段">
              <a-tag :color="getStageColor(selectedSegment.stage_name)">
                {{ selectedSegment.stage_name }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="帧ID">
              {{ selectedSegment.id }}
            </a-descriptions-item>
            <a-descriptions-item label="文件名">
              {{ selectedSegment.filename || '未知' }}
            </a-descriptions-item>
            <a-descriptions-item label="SSIM值" v-if="selectedSegment.ssim_score">
              {{ selectedSegment.ssim_score.toFixed(4) }}
            </a-descriptions-item>
          </a-descriptions>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
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
const segments = ref([])
const stages = ref([])
const error = ref(null)
const previewVisible = ref(false)
const selectedSegment = ref(null)

// 计算属性
const segmentsByStage = computed(() => {
  if (!segments.value || segments.value.length === 0) return {}
  
  const grouped = {}
  segments.value.forEach(segment => {
    const stageName = segment.stage_name || '未分类'
    if (!grouped[stageName]) {
      grouped[stageName] = []
    }
    grouped[stageName].push(segment)
  })
  
  // 按时间戳排序每个阶段的分割帧
  Object.keys(grouped).forEach(stageName => {
    grouped[stageName].sort((a, b) => a.timestamp - b.timestamp)
  })
  
  return grouped
})

const stageCount = computed(() => {
  return Object.keys(segmentsByStage.value).length
})

// 方法
const fetchSegments = async () => {
  if (!props.videoId) return
  
  try {
    loading.value = true
    error.value = null
    
    // 获取视频阶段信息
    const stagesResult = await videoApi.getVideoStages(props.videoId)
    if (stagesResult.success) {
      stages.value = stagesResult.stages || []
    }
    
    // 获取所有帧信息
    const framesResult = await videoApi.getVideoFrames(props.videoId)
    if (framesResult.success) {
      const allFrames = framesResult.frames || []
      
      // 过滤出分割帧（非关键帧）
      segments.value = allFrames.filter(frame => !frame.is_keyframe)
      
      // 为每个分割帧添加阶段信息
      segments.value.forEach(segment => {
        const stage = stages.value.find(s => 
          segment.timestamp >= s.start_time && segment.timestamp <= s.end_time
        )
        if (stage) {
          segment.stage_name = stage.stage_name
          segment.stage_info = stage
        }
      })
      
      if (segments.value.length > 0) {
        message.success(`加载了 ${segments.value.length} 个分割帧`)
      }
    } else {
      throw new Error(framesResult.message || '获取分割帧失败')
    }
  } catch (err) {
    console.error('Fetch segments failed:', err)
    error.value = err.response?.data?.detail || err.message || '获取分割帧时发生错误'
    message.error('获取分割帧失败')
  } finally {
    loading.value = false
  }
}

const refreshSegments = () => {
  fetchSegments()
}

const getFrameImageUrl = (frameId) => {
  return `http://127.0.0.1:8000/files/frames/${frameId}/image`
}

const handleImageError = (event) => {
  event.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2Y1ZjVmNSIvPjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjEyIiBmaWxsPSIjOTk5IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+5Zu+5YOP5Yqg6L295aSx6LSlPC90ZXh0Pjwvc3ZnPg=='
}

const previewSegment = (segment) => {
  selectedSegment.value = segment
  previewVisible.value = true
}

const formatTime = (seconds) => {
  if (!seconds) return '0ms'
  const milliseconds = Math.round(seconds * 1000)
  return `${milliseconds}ms`
}

const getStageColor = (stageName) => {
  const colors = ['blue', 'green', 'orange', 'red', 'purple', 'cyan', 'magenta', 'lime']
  const hash = stageName.split('').reduce((a, b) => {
    a = ((a << 5) - a) + b.charCodeAt(0)
    return a & a
  }, 0)
  return colors[Math.abs(hash) % colors.length]
}

// 监听videoId变化
watch(() => props.videoId, (newVideoId) => {
  if (newVideoId) {
    fetchSegments()
  }
}, { immediate: true })

// 组件挂载时加载分割帧
onMounted(() => {
  if (props.videoId) {
    fetchSegments()
  }
})
</script>

<style scoped>
.video-segments {
  margin-bottom: 24px;
}

.segments-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.segments-header {
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

.segments-content {
  margin-top: 24px;
}

.stage-section {
  margin-bottom: 32px;
  padding: 20px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
}

.stage-section:last-child {
  margin-bottom: 0;
}

.stage-header {
  margin-bottom: 16px;
}

.stage-header h4 {
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
  font-weight: 600;
  color: #262626;
}

.stage-info {
  font-size: 14px;
  font-weight: normal;
  color: #666;
}

.stage-time {
  font-size: 12px;
  color: #999;
}

.stage-description {
  color: #666;
  font-size: 14px;
  line-height: 1.5;
  margin-top: 4px;
}

.segments-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}

.segment-item {
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  overflow: hidden;
  transition: all 0.3s ease;
  background: white;
}

.segment-item:hover {
  border-color: #52c41a;
  box-shadow: 0 3px 10px rgba(82, 196, 26, 0.2);
  transform: translateY(-1px);
}

.segment-image-container {
  position: relative;
  overflow: hidden;
}

.segment-image {
  width: 100%;
  height: 100px;
  object-fit: cover;
  display: block;
  cursor: pointer;
  transition: transform 0.3s ease;
}

.segment-image:hover {
  transform: scale(1.05);
}

.segment-overlay {
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

.segment-item:hover .segment-overlay {
  opacity: 1;
}

.segment-info {
  padding: 10px;
  background: white;
  text-align: center;
}

.frame-time {
  font-size: 12px;
  color: #52c41a;
  font-weight: 600;
  margin-bottom: 3px;
}

.frame-number {
  font-size: 11px;
  color: #666;
  margin-bottom: 2px;
}

.frame-index {
  font-size: 10px;
  color: #999;
}

.empty-state {
  padding: 60px 0;
  text-align: center;
}

.error-section {
  margin-top: 16px;
}

.segment-preview {
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