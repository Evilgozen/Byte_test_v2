<template>
  <div class="video-analysis-view">
    <div class="page-header">
      <a-page-header
        :title="`视频分析 - ${video?.original_filename || '未知视频'}`"
        :sub-title="video?.description || '视频智能分析与阶段匹配'"
        @back="goBack"
      >
        <template #extra>
          <a-space>
            <a-button @click="refreshVideo">
              <reload-outlined /> 刷新
            </a-button>
            <a-button type="primary" @click="viewVideoDetail">
              <eye-outlined /> 查看详情
            </a-button>
            <a-button @click="viewKeyframes">
              <picture-outlined /> 关键帧
            </a-button>
          </a-space>
        </template>
      </a-page-header>
    </div>

    <div class="page-content">
      <a-spin :spinning="loading" tip="加载中...">
        <div v-if="video" class="analysis-content">
          <a-row :gutter="24">
            <!-- 左侧：视频预览 -->
            <a-col :xs="24" :lg="10">
              <a-card title="视频预览" class="video-preview-card">
                <div class="video-player">
                  <video
                    ref="videoRef"
                    :src="getVideoUrl()"
                    controls
                    preload="metadata"
                    class="video-element"
                    @loadedmetadata="onVideoLoaded"
                    @timeupdate="onTimeUpdate"
                  >
                    您的浏览器不支持视频播放
                  </video>
                </div>
                
                <!-- 视频基本信息 -->
                <div class="video-info">
                  <a-descriptions :column="2" size="small">
                    <a-descriptions-item label="时长">
                      {{ formatTime(video.duration) }}
                    </a-descriptions-item>
                    <a-descriptions-item label="分辨率">
                      {{ video.width }} × {{ video.height }}
                    </a-descriptions-item>
                    <a-descriptions-item label="帧率">
                      {{ video.fps }} fps
                    </a-descriptions-item>
                    <a-descriptions-item label="格式">
                      {{ video.format }}
                    </a-descriptions-item>
                  </a-descriptions>
                </div>
                
                <!-- 播放控制 -->
                <div class="player-controls">
                  <a-row :gutter="8">
                    <a-col :span="12">
                      <a-statistic
                        title="当前时间"
                        :value="formatTime(currentTime)"
                        :value-style="{ fontSize: '14px' }"
                      />
                    </a-col>
                    <a-col :span="12">
                      <a-statistic
                        title="播放进度"
                        :value="playProgress"
                        suffix="%"
                        :value-style="{ fontSize: '14px' }"
                      />
                    </a-col>
                  </a-row>
                </div>
              </a-card>
            </a-col>

            <!-- 右侧：分析功能 -->
            <a-col :xs="24" :lg="14">
              <div class="analysis-panels">
                <!-- 视频分析组件 -->
                <video-analysis
                  :video-id="videoId"
                  @analysis-complete="handleAnalysisComplete"
                  @view-keyframes="viewKeyframes"
                />
                
                <!-- 阶段匹配组件 -->
                <stage-matching
                  :video-id="videoId"
                  @jump-to-stage="handleJumpToStage"
                  @view-summary="handleViewSummary"
                />
              </div>
            </a-col>
          </a-row>
        </div>

        <div v-else-if="!loading" class="error-state">
          <a-result
            status="404"
            title="视频不存在"
            sub-title="请检查视频ID是否正确"
          >
            <template #extra>
              <a-button type="primary" @click="goBack">
                返回列表
              </a-button>
            </template>
          </a-result>
        </div>
      </a-spin>
    </div>

    <!-- 阶段跳转确认对话框 -->
    <a-modal
      v-model:open="jumpModalVisible"
      title="跳转到阶段"
      :footer="null"
      width="500px"
    >
      <div v-if="selectedStage" class="jump-modal-content">
        <div class="stage-info">
          <h4>{{ selectedStage.stage_name }}</h4>
          <p class="stage-time">
            <clock-circle-outlined />
            {{ formatTime(selectedStage.start_time) }} - {{ formatTime(selectedStage.end_time) }}
            ({{ formatDuration(selectedStage.duration) }})
          </p>
          <p v-if="selectedStage.description" class="stage-description">
            {{ selectedStage.description }}
          </p>
          <p v-if="selectedStage.match_reason" class="match-reason">
            <strong>匹配原因:</strong> {{ selectedStage.match_reason }}
          </p>
        </div>
        
        <div class="jump-actions">
          <a-space>
            <a-button @click="jumpModalVisible = false">
              取消
            </a-button>
            <a-button type="primary" @click="confirmJumpToStage">
              <play-circle-outlined /> 跳转播放
            </a-button>
          </a-space>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  ReloadOutlined,
  EyeOutlined,
  ClockCircleOutlined,
  PlayCircleOutlined,
  PictureOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useVideoStore } from '../stores/video'
import VideoAnalysis from '../components/VideoAnalysis.vue'
import StageMatching from '../components/StageMatching.vue'
import dayjs from 'dayjs'

const props = defineProps({
  id: {
    type: [String, Number],
    required: true
  }
})

const router = useRouter()
const route = useRoute()
const videoStore = useVideoStore()

// 响应式数据
const videoRef = ref()
const currentTime = ref(0)
const jumpModalVisible = ref(false)
const selectedStage = ref(null)

// 计算属性
const loading = computed(() => videoStore.loading)
const video = computed(() => videoStore.currentVideo)
const videoId = computed(() => props.id)

const playProgress = computed(() => {
  if (!video.value?.duration || currentTime.value === 0) return 0
  return Math.round((currentTime.value / video.value.duration) * 100)
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

const refreshVideo = () => {
  fetchVideoDetail()
}

const viewVideoDetail = () => {
  router.push({ name: 'video-detail', params: { id: props.id } })
}

const viewKeyframes = () => {
  router.push({ name: 'video-keyframes', params: { id: props.id } })
}



const handleAnalysisComplete = (result) => {
  console.log('Analysis completed:', result)
  message.success('视频分析完成')
}

const handleJumpToStage = (stage) => {
  selectedStage.value = stage
  jumpModalVisible.value = true
}

const confirmJumpToStage = () => {
  if (selectedStage.value && videoRef.value) {
    const startTime = selectedStage.value.start_time
    videoRef.value.currentTime = startTime
    videoRef.value.play()
    jumpModalVisible.value = false
    message.success(`已跳转到阶段: ${selectedStage.value.stage_name}`)
  }
}

const handleViewSummary = (summary) => {
  console.log('View summary:', summary)
  message.info('阶段摘要已加载')
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
.video-analysis-view {
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

.analysis-content {
  background: white;
}

.video-preview-card {
  margin-bottom: 24px;
  height: fit-content;
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
  max-height: 400px;
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

.analysis-panels {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.error-state {
  padding: 60px 0;
  text-align: center;
}

.jump-modal-content {
  padding: 16px 0;
}

.stage-info h4 {
  margin-bottom: 12px;
  color: #262626;
  font-size: 18px;
  font-weight: 600;
}

.stage-time {
  color: #666;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.stage-description {
  color: #666;
  line-height: 1.6;
  margin-bottom: 12px;
}

.match-reason {
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 4px;
  padding: 12px;
  color: #389e0d;
  line-height: 1.5;
  margin-bottom: 16px;
}

.jump-actions {
  text-align: right;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

:deep(.ant-page-header) {
  padding: 16px 24px;
}

:deep(.ant-descriptions-item-label) {
  font-weight: 500;
  width: 60px;
}

:deep(.ant-statistic-title) {
  font-size: 12px;
  color: #666;
}

@media (max-width: 1200px) {
  .analysis-panels {
    gap: 16px;
  }
}

@media (max-width: 768px) {
  .video-analysis-view {
    padding: 16px;
  }
  
  .video-element {
    max-height: 250px;
  }
  
  .analysis-panels {
    gap: 16px;
  }
  
  .jump-modal-content {
    padding: 8px 0;
  }
  
  .stage-info h4 {
    font-size: 16px;
  }
}
</style>