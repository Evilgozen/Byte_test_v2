<template>
  <a-card
    :hoverable="true"
    class="video-card"
    :actions="actions"
  >
    <template #cover>
      <div class="video-cover">
        <video
          v-if="video.file_path"
          :src="getVideoUrl(video.file_path)"
          class="video-preview"
          controls
          preload="metadata"
          @loadedmetadata="onVideoLoaded"
        >
          您的浏览器不支持视频播放
        </video>
        <div v-else class="video-placeholder">
          <video-camera-outlined style="font-size: 48px; color: #ccc" />
        </div>
      </div>
    </template>

    <a-card-meta
      :title="video.original_filename"
      :description="videoDescription"
    />

    <div class="video-info">
      <a-row :gutter="16">
        <a-col :span="12">
          <a-statistic
            title="文件大小"
            :value="formatFileSize(video.file_size)"
            :value-style="{ fontSize: '14px' }"
          />
        </a-col>
        <a-col :span="12">
          <a-statistic
            title="时长"
            :value="formatDuration(video.duration)"
            :value-style="{ fontSize: '14px' }"
          />
        </a-col>
      </a-row>
      
      <a-row :gutter="16" style="margin-top: 16px">
        <a-col :span="12">
          <a-statistic
            title="分辨率"
            :value="`${video.width}x${video.height}`"
            :value-style="{ fontSize: '14px' }"
          />
        </a-col>
        <a-col :span="12">
          <a-statistic
            title="帧率"
            :value="video.fps"
            suffix="fps"
            :value-style="{ fontSize: '14px' }"
          />
        </a-col>
      </a-row>
    </div>

    <div class="video-actions">
      <a-space>
        <a-button type="primary" size="small" @click="viewDetail">
          <eye-outlined /> 查看详情
        </a-button>
        <a-button size="small" @click="extractFrames">
          <scissor-outlined /> 提取帧
        </a-button>
        <a-button size="small" @click="downloadVideo">
          <download-outlined /> 下载
        </a-button>
        <a-popconfirm
          title="确定要删除这个视频吗？"
          ok-text="确定"
          cancel-text="取消"
          @confirm="deleteVideo"
        >
          <a-button size="small" danger>
            <delete-outlined /> 删除
          </a-button>
        </a-popconfirm>
      </a-space>
    </div>
  </a-card>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  EyeOutlined,
  ScissorOutlined,
  DownloadOutlined,
  DeleteOutlined,
  VideoCameraOutlined
} from '@ant-design/icons-vue'
import { useVideoStore } from '../stores/video'
import dayjs from 'dayjs'

const props = defineProps({
  video: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['extract-frames', 'delete-success'])

const router = useRouter()
const videoStore = useVideoStore()

// 计算属性
const videoDescription = computed(() => {
  return props.video.description || `上传于 ${dayjs(props.video.created_at).format('YYYY-MM-DD HH:mm')}`
})

const actions = computed(() => [
  { key: 'detail', icon: 'EyeOutlined', text: '详情' },
  { key: 'frames', icon: 'ScissorOutlined', text: '帧提取' },
  { key: 'download', icon: 'DownloadOutlined', text: '下载' }
])

// 方法
const getVideoUrl = (filePath) => {
  // 这里需要根据后端的静态文件服务配置来构建URL
  return `http://127.0.0.1:8000/static/files/${props.video.id}/${props.video.original_filename}`
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDuration = (seconds) => {
  if (!seconds) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

const viewDetail = () => {
  router.push({ name: 'video-detail', params: { id: props.video.id } })
}

const extractFrames = () => {
  emit('extract-frames', props.video)
}

const downloadVideo = async () => {
  try {
    await videoStore.downloadVideo(props.video.id, props.video.original_filename)
  } catch (error) {
    console.error('Download failed:', error)
  }
}

const deleteVideo = async () => {
  try {
    await videoStore.deleteVideo(props.video.id)
    emit('delete-success', props.video.id)
  } catch (error) {
    console.error('Delete failed:', error)
  }
}

const onVideoLoaded = (event) => {
  // 视频加载完成后的处理
  console.log('Video loaded:', event.target.duration)
}
</script>

<style scoped>
.video-card {
  margin-bottom: 16px;
}

.video-cover {
  height: 200px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
}

.video-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: #fafafa;
}

.video-info {
  margin-top: 16px;
}

.video-actions {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

:deep(.ant-card-actions) {
  background: #fafafa;
}

:deep(.ant-statistic-title) {
  font-size: 12px;
  color: #666;
}
</style>