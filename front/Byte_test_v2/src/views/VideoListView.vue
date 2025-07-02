<template>
  <div class="video-list-view">
    <div class="page-header">
      <a-page-header
        title="视频管理"
        sub-title="上传、管理和处理您的视频文件"
      >
        <template #extra>
          <a-button type="primary" @click="refreshList">
            <reload-outlined /> 刷新
          </a-button>
        </template>
      </a-page-header>
    </div>

    <div class="page-content">
      <!-- 上传区域 -->
      <a-card title="上传视频" class="upload-card">
        <video-upload @upload-success="handleUploadSuccess" />
      </a-card>

      <!-- 搜索和筛选 -->
      <a-card title="视频列表" class="list-card">
        <div class="list-controls">
          <a-row :gutter="16" align="middle">
            <a-col :flex="1">
              <a-input-search
                v-model:value="searchKeyword"
                placeholder="搜索视频文件名"
                enter-button="搜索"
                @search="handleSearch"
                style="max-width: 400px"
              />
            </a-col>
            <a-col>
              <a-select
                v-model:value="sortBy"
                placeholder="排序方式"
                style="width: 150px"
                @change="handleSort"
              >
                <a-select-option value="created_at_desc">最新上传</a-select-option>
                <a-select-option value="created_at_asc">最早上传</a-select-option>
                <a-select-option value="file_size_desc">文件大小↓</a-select-option>
                <a-select-option value="file_size_asc">文件大小↑</a-select-option>
                <a-select-option value="duration_desc">时长↓</a-select-option>
                <a-select-option value="duration_asc">时长↑</a-select-option>
              </a-select>
            </a-col>
          </a-row>
        </div>

        <!-- 视频列表 -->
        <div class="video-list">
          <a-spin :spinning="loading" tip="加载中...">
            <div v-if="filteredVideoList.length === 0 && !loading" class="empty-state">
              <a-empty
                description="暂无视频文件"
                :image="Empty.PRESENTED_IMAGE_SIMPLE"
              >
                <a-button type="primary" @click="scrollToUpload">
                  立即上传
                </a-button>
              </a-empty>
            </div>
            
            <a-row v-else :gutter="[16, 16]">
              <a-col
                v-for="video in paginatedVideoList"
                :key="video.id"
                :xs="24"
                :sm="12"
                :md="8"
                :lg="6"
                :xl="6"
              >
                <video-card
                  :video="video"
                  @extract-frames="handleExtractFrames"
                  @delete-success="handleDeleteSuccess"
                />
              </a-col>
            </a-row>
          </a-spin>
        </div>

        <!-- 分页 -->
        <div v-if="filteredVideoList.length > pageSize" class="pagination">
          <a-pagination
            v-model:current="currentPage"
            v-model:page-size="pageSize"
            :total="filteredVideoList.length"
            :show-size-changer="true"
            :show-quick-jumper="true"
            :show-total="(total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`"
            @change="handlePageChange"
            @show-size-change="handlePageSizeChange"
          />
        </div>
      </a-card>
    </div>

    <!-- 帧提取对话框 -->
    <frame-extract-modal
      v-model:open="extractModalVisible"
      :video="selectedVideo"
      @extract-success="handleExtractSuccess"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ReloadOutlined } from '@ant-design/icons-vue'
import { Empty } from 'ant-design-vue'
import { useVideoStore } from '../stores/video'
import VideoUpload from '../components/VideoUpload.vue'
import VideoCard from '../components/VideoCard.vue'
import FrameExtractModal from '../components/FrameExtractModal.vue'

const router = useRouter()
const videoStore = useVideoStore()

// 响应式数据
const searchKeyword = ref('')
const sortBy = ref('created_at_desc')
const currentPage = ref(1)
const pageSize = ref(12)
const extractModalVisible = ref(false)
const selectedVideo = ref(null)

// 计算属性
const loading = computed(() => videoStore.loading)
const videoList = computed(() => videoStore.videoList)

const filteredVideoList = computed(() => {
  let list = [...videoList.value]
  
  // 搜索过滤
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    list = list.filter(video => 
      video.original_filename.toLowerCase().includes(keyword) ||
      (video.description && video.description.toLowerCase().includes(keyword))
    )
  }
  
  // 排序
  switch (sortBy.value) {
    case 'created_at_desc':
      list.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      break
    case 'created_at_asc':
      list.sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
      break
    case 'file_size_desc':
      list.sort((a, b) => b.file_size - a.file_size)
      break
    case 'file_size_asc':
      list.sort((a, b) => a.file_size - b.file_size)
      break
    case 'duration_desc':
      list.sort((a, b) => b.duration - a.duration)
      break
    case 'duration_asc':
      list.sort((a, b) => a.duration - b.duration)
      break
  }
  
  return list
})

const paginatedVideoList = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredVideoList.value.slice(start, end)
})

// 方法
const refreshList = async () => {
  try {
    await videoStore.fetchVideoList()
  } catch (error) {
    console.error('Refresh failed:', error)
  }
}

const handleUploadSuccess = (video) => {
  console.log('Upload success:', video)
  // 视频列表会自动更新，因为store中已经添加了新视频
}

const handleSearch = () => {
  currentPage.value = 1 // 重置到第一页
}

const handleSort = () => {
  currentPage.value = 1 // 重置到第一页
}

const handlePageChange = (page, size) => {
  currentPage.value = page
  pageSize.value = size
}

const handlePageSizeChange = (current, size) => {
  currentPage.value = 1
  pageSize.value = size
}

const handleExtractFrames = (video) => {
  selectedVideo.value = video
  extractModalVisible.value = true
}

const handleExtractSuccess = (result) => {
  console.log('Extract success:', result)
  // 可以跳转到帧列表页面
  router.push({ 
    name: 'video-frames', 
    params: { id: selectedVideo.value.id } 
  })
}

const handleDeleteSuccess = (videoId) => {
  console.log('Delete success:', videoId)
  // 视频已从store中删除，列表会自动更新
}

const scrollToUpload = () => {
  const uploadCard = document.querySelector('.upload-card')
  if (uploadCard) {
    uploadCard.scrollIntoView({ behavior: 'smooth' })
  }
}

// 生命周期
onMounted(() => {
  refreshList()
})
</script>

<style scoped>
.video-list-view {
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

.upload-card {
  margin-bottom: 24px;
}

.list-card {
  background: white;
}

.list-controls {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.video-list {
  min-height: 400px;
}

.empty-state {
  padding: 60px 0;
  text-align: center;
}

.pagination {
  margin-top: 32px;
  text-align: center;
}

:deep(.ant-page-header) {
  padding: 16px 24px;
}

:deep(.ant-card-head-title) {
  font-size: 18px;
  font-weight: 600;
}
</style>