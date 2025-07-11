<template>
  <div class="video-upload">
    <a-upload-dragger
      v-model:file-list="fileList"
      name="file"
      :multiple="true"
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
        支持多个视频文件同时上传，支持常见视频格式（MP4、AVI、MOV等）
      </p>
    </a-upload-dragger>

    <!-- 文件列表 -->
    <div v-if="pendingFiles.length > 0" class="file-list">
      <h4>待上传文件 ({{ pendingFiles.length }})</h4>
      <div class="file-items">
        <div v-for="file in pendingFiles" :key="file.uid" class="file-item">
          <div class="file-info">
            <span class="file-name">{{ file.name }}</span>
            <span class="file-size">({{ formatFileSize(file.size) }})</span>
          </div>
          <a-button 
            type="text" 
            danger 
            size="small" 
            @click="removeFile(file.uid)"
          >
            删除
          </a-button>
        </div>
      </div>
      <div class="upload-actions">
        <a-button type="primary" @click="startBatchUpload" :loading="uploading">
          开始上传 ({{ pendingFiles.length }} 个文件)
        </a-button>
        <a-button @click="clearFiles" :disabled="uploading">
          清空列表
        </a-button>
      </div>
    </div>

    <!-- 上传进度 -->
    <div v-if="uploading" class="upload-progress">
      <div class="overall-progress">
        <h4>总体进度: {{ completedCount }}/{{ totalCount }}</h4>
        <a-progress :percent="overallPercent" status="active" />
      </div>
      <div v-if="currentUploadingFile" class="current-file-progress">
        <p>正在上传: {{ currentUploadingFile.name }}</p>
        <a-progress :percent="currentFilePercent" status="active" size="small" />
      </div>
    </div>

    <!-- 上传结果 -->
    <div v-if="uploadResults.length > 0" class="upload-results">
      <h4>上传结果</h4>
      <div class="result-items">
        <a-alert
          v-for="result in uploadResults"
          :key="result.file.uid"
          :message="result.success ? `上传成功: ${result.file.name}` : `上传失败: ${result.file.name} - ${result.error}`"
          :type="result.success ? 'success' : 'error'"
          show-icon
          closable
          @close="removeResult(result.file.uid)"
          style="margin-bottom: 8px;"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { InboxOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useVideoStore } from '../stores/video'

const emit = defineEmits(['upload-success'])

const videoStore = useVideoStore()
const fileList = ref([])
const pendingFiles = ref([])
const uploading = ref(false)
const uploadResults = ref([])
const currentUploadingFile = ref(null)
const currentFilePercent = ref(0)
const completedCount = ref(0)
const totalCount = ref(0)

// 计算总体进度
const overallPercent = computed(() => {
  if (totalCount.value === 0) return 0
  return Math.round((completedCount.value / totalCount.value) * 100)
})

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

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
  
  // 检查是否已存在相同文件
  const exists = pendingFiles.value.some(f => f.name === file.name && f.size === file.size)
  if (exists) {
    message.warning('文件已存在于待上传列表中！')
    return false
  }
  
  // 直接在这里添加文件到待上传列表
  pendingFiles.value.push({
    uid: file.uid,
    name: file.name,
    size: file.size,
    file: file
  })
  
  return false // 阻止自动上传，添加到待上传列表
}

// 自定义上传处理（添加到待上传列表）
const handleUpload = ({ file }) => {
  // 由于beforeUpload返回false，这个函数实际上不会被调用
  // 文件添加逻辑已移至beforeUpload函数中
  fileList.value = [] // 清空文件列表
}

// 移除文件
const removeFile = (uid) => {
  pendingFiles.value = pendingFiles.value.filter(f => f.uid !== uid)
}

// 清空文件列表
const clearFiles = () => {
  pendingFiles.value = []
  uploadResults.value = []
}

// 移除上传结果
const removeResult = (uid) => {
  uploadResults.value = uploadResults.value.filter(r => r.file.uid !== uid)
}

// 开始批量上传
const startBatchUpload = async () => {
  if (pendingFiles.value.length === 0) {
    message.warning('请先选择要上传的文件！')
    return
  }

  uploading.value = true
  completedCount.value = 0
  totalCount.value = pendingFiles.value.length
  uploadResults.value = []
  
  const filesToUpload = [...pendingFiles.value]
  // 不要立即清空待上传列表，让用户能看到正在上传的文件
  
  for (const fileItem of filesToUpload) {
    currentUploadingFile.value = fileItem
    currentFilePercent.value = 0
    
    try {
      // 模拟当前文件上传进度
      const progressInterval = setInterval(() => {
        if (currentFilePercent.value < 90) {
          currentFilePercent.value += 10
        }
      }, 200)
      
      const result = await videoStore.uploadVideo(fileItem.file)
      
      clearInterval(progressInterval)
      currentFilePercent.value = 100
      
      uploadResults.value.push({
        file: fileItem,
        success: true,
        result: result
      })
      
      emit('upload-success', result)
      
    } catch (error) {
      console.error('Upload failed:', error)
      uploadResults.value.push({
        file: fileItem,
        success: false,
        error: error.message || '上传失败'
      })
    }
    
    completedCount.value++
    
    // 从待上传列表中移除已处理的文件
    pendingFiles.value = pendingFiles.value.filter(f => f.uid !== fileItem.uid)
    
    // 短暂延迟，避免请求过于频繁
    if (completedCount.value < totalCount.value) {
      await new Promise(resolve => setTimeout(resolve, 500))
    }
  }
  
  uploading.value = false
  currentUploadingFile.value = null
  currentFilePercent.value = 0
  
  const successCount = uploadResults.value.filter(r => r.success).length
  const failCount = uploadResults.value.filter(r => !r.success).length
  
  if (failCount === 0) {
    message.success(`所有文件上传成功！共 ${successCount} 个文件`)
  } else {
    message.warning(`上传完成！成功 ${successCount} 个，失败 ${failCount} 个`)
  }
}
</script>

<style scoped>
.video-upload {
  margin-bottom: 24px;
}

.file-list {
  margin-top: 16px;
  padding: 16px;
  background: #fafafa;
  border-radius: 6px;
  border: 1px solid #d9d9d9;
}

.file-list h4 {
  margin: 0 0 12px 0;
  color: #262626;
}

.file-items {
  margin-bottom: 16px;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: white;
  border-radius: 4px;
  margin-bottom: 8px;
  border: 1px solid #e8e8e8;
}

.file-info {
  flex: 1;
}

.file-name {
  font-weight: 500;
  color: #262626;
}

.file-size {
  margin-left: 8px;
  color: #8c8c8c;
  font-size: 12px;
}

.upload-actions {
  display: flex;
  gap: 8px;
}

.upload-progress {
  margin-top: 16px;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 6px;
}

.overall-progress {
  margin-bottom: 16px;
}

.overall-progress h4 {
  margin: 0 0 8px 0;
  color: #262626;
}

.current-file-progress p {
  margin: 0 0 8px 0;
  color: #595959;
  font-size: 14px;
}

.upload-results {
  margin-top: 16px;
}

.upload-results h4 {
  margin: 0 0 12px 0;
  color: #262626;
}

.result-items {
  max-height: 200px;
  overflow-y: auto;
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