<template>
  <div class="video-detail-view">
    <div class="page-header">
      <a-page-header
        :title="video?.original_filename || '视频详情'"
        :sub-title="video?.description"
        @back="goBack"
      >
        <template #extra>
          <a-space>
            <a-button @click="editVideo">
              <edit-outlined /> 编辑
            </a-button>
            <a-button type="primary" @click="extractFrames">
              <scissor-outlined /> 提取帧
            </a-button>
            <a-button @click="downloadVideo">
              <download-outlined /> 下载
            </a-button>
            <a-popconfirm
              title="确定要删除这个视频吗？"
              ok-text="确定"
              cancel-text="取消"
              @confirm="deleteVideo"
            >
              <a-button danger>
                <delete-outlined /> 删除
              </a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </a-page-header>
    </div>

    <div class="page-content">
      <a-spin :spinning="loading" tip="加载中...">
        <div v-if="video" class="video-content">
          <a-row :gutter="24">
            <!-- 视频播放器 -->
            <a-col :xs="24" :lg="16">
              <a-card title="视频预览" class="video-player-card">
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
                
                <!-- 播放控制信息 -->
                <div class="player-info">
                  <a-row :gutter="16">
                    <a-col :span="8">
                      <a-statistic
                        title="当前时间"
                        :value="formatTime(currentTime)"
                        :value-style="{ fontSize: '16px' }"
                      />
                    </a-col>
                    <a-col :span="8">
                      <a-statistic
                        title="总时长"
                        :value="formatTime(video.duration)"
                        :value-style="{ fontSize: '16px' }"
                      />
                    </a-col>
                    <a-col :span="8">
                      <a-statistic
                        title="播放进度"
                        :value="playProgress"
                        suffix="%"
                        :value-style="{ fontSize: '16px' }"
                      />
                    </a-col>
                  </a-row>
                </div>
              </a-card>
            </a-col>

            <!-- 视频信息 -->
            <a-col :xs="24" :lg="8">
              <a-card title="视频信息" class="video-info-card">
                <a-descriptions :column="1" size="small">
                  <a-descriptions-item label="文件名">
                    {{ video.original_filename }}
                  </a-descriptions-item>
                  <a-descriptions-item label="文件大小">
                    {{ formatFileSize(video.file_size) }}
                  </a-descriptions-item>
                  <a-descriptions-item label="视频时长">
                    {{ formatTime(video.duration) }}
                  </a-descriptions-item>
                  <a-descriptions-item label="分辨率">
                    {{ video.width }} × {{ video.height }}
                  </a-descriptions-item>
                  <a-descriptions-item label="帧率">
                    {{ video.fps }} fps
                  </a-descriptions-item>
                  <a-descriptions-item label="视频格式">
                    {{ video.format }}
                  </a-descriptions-item>
                  <a-descriptions-item label="上传时间">
                    {{ formatDateTime(video.created_at) }}
                  </a-descriptions-item>
                  <a-descriptions-item label="更新时间">
                    {{ formatDateTime(video.updated_at) }}
                  </a-descriptions-item>
                  <a-descriptions-item label="描述">
                    <div v-if="video.description" class="description">
                      {{ video.description }}
                    </div>
                    <a-typography-text v-else type="secondary">
                      暂无描述
                    </a-typography-text>
                  </a-descriptions-item>
                </a-descriptions>
              </a-card>

              <!-- 快速操作 -->
              <a-card title="快速操作" class="quick-actions-card">
                <a-space direction="vertical" style="width: 100%">
                  <a-button block type="primary" @click="extractFrames">
                    <scissor-outlined /> 提取视频帧
                  </a-button>
                  <a-button block @click="viewFrames">
                    <picture-outlined /> 查看已提取的帧
                  </a-button>
                  <a-button block @click="downloadVideo">
                    <download-outlined /> 下载视频文件
                  </a-button>
                  <a-button block @click="editVideo">
                    <edit-outlined /> 编辑视频信息
                  </a-button>
                </a-space>
              </a-card>
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

    <!-- 编辑对话框 -->
    <a-modal
      v-model:open="editModalVisible"
      title="编辑视频信息"
      :confirm-loading="updating"
      @ok="handleUpdate"
      @cancel="cancelEdit"
    >
      <a-form
        ref="editFormRef"
        :model="editForm"
        layout="vertical"
      >
        <a-form-item label="描述" name="description">
          <a-textarea
            v-model:value="editForm.description"
            placeholder="请输入视频描述"
            :rows="4"
            show-count
            :maxlength="500"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 帧提取对话框 -->
    <frame-extract-modal
      v-model:open="extractModalVisible"
      :video="video"
      @extract-success="handleExtractSuccess"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  EditOutlined,
  ScissorOutlined,
  DownloadOutlined,
  DeleteOutlined,
  PictureOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useVideoStore } from '../stores/video'
import FrameExtractModal from '../components/FrameExtractModal.vue'
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
const editModalVisible = ref(false)
const extractModalVisible = ref(false)
const editFormRef = ref()
const updating = ref(false)

const editForm = ref({
  description: ''
})

// 计算属性
const loading = computed(() => videoStore.loading)
const video = computed(() => videoStore.currentVideo)

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
  }
}

const getVideoUrl = () => {
  if (!video.value) return ''
  return `http://127.0.0.1:8000/static/files/${video.value.id}/${video.value.original_filename}`
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatTime = (seconds) => {
  if (!seconds) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

const formatDateTime = (dateString) => {
  return dayjs(dateString).format('YYYY-MM-DD HH:mm:ss')
}

const goBack = () => {
  router.push({ name: 'videos' })
}

const editVideo = () => {
  editForm.value.description = video.value?.description || ''
  editModalVisible.value = true
}

const handleUpdate = async () => {
  try {
    updating.value = true
    await videoStore.updateVideo(props.id, editForm.value)
    editModalVisible.value = false
    message.success('视频信息更新成功')
  } catch (error) {
    console.error('Update failed:', error)
  } finally {
    updating.value = false
  }
}

const cancelEdit = () => {
  editModalVisible.value = false
  editForm.value.description = ''
}

const extractFrames = () => {
  extractModalVisible.value = true
}

const handleExtractSuccess = (result) => {
  console.log('Extract success:', result)
  router.push({ 
    name: 'video-frames', 
    params: { id: props.id } 
  })
}

const viewFrames = () => {
  router.push({ 
    name: 'video-frames', 
    params: { id: props.id } 
  })
}

const downloadVideo = async () => {
  try {
    await videoStore.downloadVideo(props.id, video.value?.original_filename)
  } catch (error) {
    console.error('Download failed:', error)
  }
}

const deleteVideo = async () => {
  try {
    await videoStore.deleteVideo(props.id)
    message.success('视频删除成功')
    router.push({ name: 'videos' })
  } catch (error) {
    console.error('Delete failed:', error)
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
.video-detail-view {
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
  max-width: 1400px;
  margin: 0 auto;
}

.video-content {
  background: white;
}

.video-player-card {
  margin-bottom: 24px;
}

.video-player {
  text-align: center;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

.video-element {
  width: 100%;
  max-height: 500px;
  object-fit: contain;
}

.player-info {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.video-info-card {
  margin-bottom: 24px;
}

.quick-actions-card {
  margin-bottom: 24px;
}

.description {
  white-space: pre-wrap;
  word-break: break-word;
}

.error-state {
  padding: 60px 0;
  text-align: center;
}

:deep(.ant-page-header) {
  padding: 16px 24px;
}

:deep(.ant-descriptions-item-label) {
  font-weight: 500;
  width: 80px;
}

:deep(.ant-statistic-title) {
  font-size: 12px;
  color: #666;
}

@media (max-width: 768px) {
  .video-detail-view {
    padding: 16px;
  }
  
  .video-element {
    max-height: 300px;
  }
}
</style>