<template>
  <div class="video-upload">
    <a-upload-dragger
      v-model:file-list="fileList"
      name="file"
      :multiple="false"
      :before-upload="beforeUpload"
      :custom-request="handleUpload"
      accept="video/*"
      :show-upload-list="false"
    >
      <p class="ant-upload-drag-icon">
        <inbox-outlined />
      </p>
      <p class="ant-upload-text">点击或拖拽视频文件到此区域上传</p>
      <p class="ant-upload-hint">
        支持单个视频文件上传，支持常见视频格式（MP4、AVI、MOV等）
      </p>
    </a-upload-dragger>

    <!-- 上传进度 -->
    <div v-if="uploading" class="upload-progress">
      <a-progress :percent="uploadPercent" status="active" />
      <p>正在上传视频文件...</p>
    </div>

    <!-- 上传成功信息 -->
    <div v-if="uploadedFile" class="upload-success">
      <a-alert
        :message="`视频上传成功: ${uploadedFile.original_filename}`"
        type="success"
        show-icon
        closable
        @close="uploadedFile = null"
      />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { InboxOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useVideoStore } from '../stores/video'

const emit = defineEmits(['upload-success'])

const videoStore = useVideoStore()
const fileList = ref([])
const uploading = ref(false)
const uploadPercent = ref(0)
const uploadedFile = ref(null)

// 上传前检查
const beforeUpload = (file) => {
  const isVideo = file.type.startsWith('video/')
  if (!isVideo) {
    message.error('只能上传视频文件！')
    return false
  }
  
  const isLt500M = file.size / 1024 / 1024 < 500
  if (!isLt500M) {
    message.error('视频文件大小不能超过 500MB！')
    return false
  }
  
  return true
}

// 自定义上传
const handleUpload = async ({ file }) => {
  uploading.value = true
  uploadPercent.value = 0
  
  try {
    // 模拟上传进度
    const progressInterval = setInterval(() => {
      if (uploadPercent.value < 90) {
        uploadPercent.value += 10
      }
    }, 200)
    
    const result = await videoStore.uploadVideo(file)
    
    clearInterval(progressInterval)
    uploadPercent.value = 100
    
    uploadedFile.value = result
    fileList.value = []
    
    emit('upload-success', result)
    
  } catch (error) {
    console.error('Upload failed:', error)
  } finally {
    uploading.value = false
    setTimeout(() => {
      uploadPercent.value = 0
    }, 1000)
  }
}
</script>

<style scoped>
.video-upload {
  margin-bottom: 24px;
}

.upload-progress {
  margin-top: 16px;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 6px;
}

.upload-success {
  margin-top: 16px;
}

.ant-upload-drag-icon {
  font-size: 48px;
  color: #1890ff;
}

.ant-upload-text {
  font-size: 16px;
  color: #666;
}

.ant-upload-hint {
  color: #999;
}
</style>