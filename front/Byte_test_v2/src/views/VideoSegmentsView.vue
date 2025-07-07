<template>
  <div class="video-segments-view">
    <!-- 页面头部 -->
    <a-page-header
      class="page-header"
      :title="pageTitle"
      :sub-title="pageSubtitle"
      @back="goBack"
    >
      <template #extra>
        <a-button @click="refreshPage">
          <reload-outlined /> 刷新
        </a-button>
        <a-button type="primary" @click="viewVideoDetail">
          <video-camera-outlined /> 视频详情
        </a-button>
        <a-button @click="viewVideoAnalysis">
          <experiment-outlined /> 视频分析
        </a-button>
        <a-button @click="viewKeyframes">
          <picture-outlined /> 关键帧
        </a-button>
      </template>
    </a-page-header>

    <div class="page-content">
      <a-row :gutter="24">
        <!-- 视频预览 -->
        <a-col :span="8">
          <a-card title="视频预览" class="video-preview-card">
            <div v-if="video" class="video-section">
              <div class="video-player">
                <video
                  ref="videoRef"
                  :src="getVideoUrl()"
                  controls
                  class="video-element"
                  @loadedmetadata="onVideoLoaded"
                  @timeupdate="onTimeUpdate"
                >
                  您的浏览器不支持视频播放
                </video>
              </div>
              
              <div class="video-info">
                <a-descriptions :column="1" size="small">
                  <a-descriptions-item label="文件名">
                    {{ video.filename }}
                  </a-descriptions-item>
                  <a-descriptions-item label="时长">
                    {{ formatDuration(video.duration) }}
                  </a-descriptions-item>
                  <a-descriptions-item label="分辨率">
                    {{ video.width }}x{{ video.height }}
                  </a-descriptions-item>
                  <a-descriptions-item label="帧率">
                    {{ video.fps }} FPS
                  </a-descriptions-item>
                  <a-descriptions-item label="格式">
                    {{ video.format }}
                  </a-descriptions-item>
                </a-descriptions>
              </div>
              
              <div class="player-controls">
                <a-row :gutter="8" align="middle">
                  <a-col :span="6">
                    <span class="time-display">{{ formatTime(currentTime) }}</span>
                  </a-col>
                  <a-col :span="12">
                    <a-slider
                      :min="0"
                      :max="video.duration || 100"
                      :value="currentTime"
                      :tip-formatter="formatTime"
                      @change="seekTo"
                    />
                  </a-col>
                  <a-col :span="6">
                    <span class="time-display">{{ formatDuration(video.duration) }}</span>
                  </a-col>
                </a-row>
              </div>
            </div>
            
            <div v-else class="error-state">
              <a-result
                status="error"
                title="视频加载失败"
                sub-title="无法获取视频信息，请检查视频是否存在"
              >
                <template #extra>
                  <a-button type="primary" @click="fetchVideoDetail">
                    重新加载
                  </a-button>
                </template>
              </a-result>
            </div>
          </a-card>
        </a-col>

        <!-- 分割帧内容 -->
        <a-col :span="16">
          <div class="segments-content">
            <VideoSegments :video-id="id" />
          </div>
        </a-col>
      </a-row>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  ReloadOutlined,
  VideoCameraOutlined,
  ExperimentOutlined,
  PictureOutlined
} from '@ant-design/icons-vue'
import { useVideoStore } from '../stores/video'
import VideoSegments from '../components/VideoSegments.vue'

// Props
const props = defineProps({
  id: {
    type: [String, Number],
    required: true
  }
})

// 路由和状态
const router = useRouter()
const videoStore = useVideoStore()

// 响应式数据
const videoRef = ref(null)
const currentTime = ref(0)

// 计算属性
const video = computed(() => videoStore.currentVideo)
const pageTitle = computed(() => {
  return video.value ? `分割帧 - ${video.value.title}` : '分割帧'
})
const pageSubtitle = computed(() => {
  return video.value ? '查看和管理视频分割帧' : '加载中...'
})

// 方法
const fetchVideoDetail = async () => {
  try {
    await videoStore.fetchVideoDetail(props.id)
  } catch (error) {
    console.error('Fetch video detail failed:', error)
    message.error('获取视频信息失败')
  }
}

const getVideoUrl = () => {
  if (!video.value) return ''
  return `http://127.0.0.1:8000/static/files/${video.value.filename}`
}

const formatTime = (seconds) => {
  if (!seconds) return '0ms'
  const milliseconds = Math.round(seconds * 1000)
  return `${milliseconds}ms`
}

const formatDuration = (seconds) => {
  if (!seconds) return '0ms'
  const milliseconds = Math.round(seconds * 1000)
  return `${milliseconds}ms`
}

const goBack = () => {
  router.push({ name: 'videos' })
}

const refreshPage = () => {
  fetchVideoDetail()
}

const viewVideoDetail = () => {
  router.push({ name: 'video-detail', params: { id: props.id } })
}

const viewVideoAnalysis = () => {
  router.push({ name: 'video-analysis', params: { id: props.id } })
}

const viewKeyframes = () => {
  router.push({ name: 'video-keyframes', params: { id: props.id } })
}

const seekTo = (time) => {
  if (videoRef.value) {
    videoRef.value.currentTime = time
  }
}

const onVideoLoaded = (event) => {
  console.log('Video loaded, duration:', event.target.duration)
}

const onTimeUpdate = (event) => {
  currentTime.value = event.target.currentTime
}

// 监听路由参数变化
watch(() => props.id, (newId) => {
  if (newId) {
    fetchVideoDetail()
  }
}, { immediate: true })

// 组件卸载时清理
onMounted(() => {
  return () => {
    videoStore.clearCurrentVideo()
  }
})
</script>

<style scoped>
.video-segments-view {
  padding: 24px;
  background: #f5f5f5;
  min-height: 100vh;
}

.page-header {
  background: white;
  margin-bottom: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.page-content {
  max-width: 1600px;
  margin: 0 auto;
}

.video-preview-card {
  height: fit-content;
  position: sticky;
  top: 24px;
}

.video-section {
  margin-bottom: 16px;
}

.video-player {
  text-align: center;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 16px;
}

.video-element {
  width: 100%;
  max-height: 300px;
  object-fit: contain;
}

.video-info {
  margin-bottom: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.player-controls {
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.time-display {
  font-size: 12px;
  color: #666;
  font-family: monospace;
}

.segments-content {
  background: white;
  border-radius: 8px;
}

.error-state {
  padding: 40px 0;
  text-align: center;
}

:deep(.ant-descriptions-item-label) {
  font-weight: 600;
  color: #262626;
}

:deep(.ant-descriptions-item-content) {
  color: #666;
}

:deep(.ant-slider-tooltip .ant-tooltip-inner) {
  font-family: monospace;
}
</style>