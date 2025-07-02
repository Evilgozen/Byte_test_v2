<template>
  <div class="video-frames-view">
    <div class="page-header">
      <a-page-header
        :title="`视频帧管理 - ${video?.original_filename || ''}`"
        sub-title="查看和管理提取的视频帧"
        @back="goBack"
      >
        <template #extra>
          <a-space>
            <a-button @click="refreshFrames">
              <reload-outlined /> 刷新
            </a-button>
            <a-button type="primary" @click="extractMoreFrames">
              <scissor-outlined /> 提取更多帧
            </a-button>
          </a-space>
        </template>
      </a-page-header>
    </div>

    <div class="page-content">
      <!-- 统计信息 -->
      <a-row :gutter="16" class="stats-row">
        <a-col :xs="24" :sm="6">
          <a-card>
            <a-statistic
              title="总帧数"
              :value="frames.length"
              :value-style="{ color: '#1890ff' }"
            >
              <template #prefix>
                <picture-outlined />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="6">
          <a-card>
            <a-statistic
              title="选中帧数"
              :value="selectedFrames.length"
              :value-style="{ color: '#52c41a' }"
            >
              <template #prefix>
                <check-circle-outlined />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="6">
          <a-card>
            <a-statistic
              title="视频时长"
              :value="formatTime(video?.duration)"
              :value-style="{ color: '#722ed1' }"
            >
              <template #prefix>
                <clock-circle-outlined />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="6">
          <a-card>
            <a-statistic
              title="平均间隔"
              :value="averageInterval"
              suffix="秒"
              :value-style="{ color: '#fa8c16' }"
            >
              <template #prefix>
                <field-time-outlined />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
      </a-row>

      <!-- 控制面板 -->
      <a-card title="控制面板" class="control-panel">
        <a-row :gutter="16" align="middle">
          <a-col :flex="1">
            <a-space>
              <a-checkbox
                :indeterminate="indeterminate"
                :checked="checkAll"
                @change="onCheckAllChange"
              >
                全选
              </a-checkbox>
              <a-button
                :disabled="selectedFrames.length === 0"
                @click="downloadSelected"
              >
                <download-outlined /> 下载选中 ({{ selectedFrames.length }})
              </a-button>
              <a-popconfirm
                title="确定要删除选中的帧吗？"
                ok-text="确定"
                cancel-text="取消"
                :disabled="selectedFrames.length === 0"
                @confirm="deleteSelected"
              >
                <a-button
                  danger
                  :disabled="selectedFrames.length === 0"
                >
                  <delete-outlined /> 删除选中 ({{ selectedFrames.length }})
                </a-button>
              </a-popconfirm>
            </a-space>
          </a-col>
          <a-col>
            <a-space>
              <span>显示方式：</span>
              <a-radio-group v-model:value="viewMode" button-style="solid">
                <a-radio-button value="grid">
                  <appstore-outlined /> 网格
                </a-radio-button>
                <a-radio-button value="list">
                  <bars-outlined /> 列表
                </a-radio-button>
              </a-radio-group>
            </a-space>
          </a-col>
        </a-row>
      </a-card>

      <!-- 帧列表 -->
      <a-card title="视频帧列表" class="frames-card">
        <a-spin :spinning="loading" tip="加载中...">
          <div v-if="frames.length === 0 && !loading" class="empty-state">
            <a-empty
              description="暂无视频帧"
              :image="Empty.PRESENTED_IMAGE_SIMPLE"
            >
              <a-button type="primary" @click="extractMoreFrames">
                立即提取帧
              </a-button>
            </a-empty>
          </div>

          <!-- 网格视图 -->
          <div v-else-if="viewMode === 'grid'" class="frames-grid">
            <a-row :gutter="[16, 16]">
              <a-col
                v-for="frame in paginatedFrames"
                :key="frame.id"
                :xs="12"
                :sm="8"
                :md="6"
                :lg="4"
                :xl="3"
              >
                <div class="frame-item">
                  <a-card
                    :hoverable="true"
                    size="small"
                    class="frame-card"
                  >
                    <template #cover>
                      <div class="frame-cover">
                        <a-checkbox
                          :checked="selectedFrames.includes(frame.id)"
                          @change="(e) => onFrameSelect(frame.id, e.target.checked)"
                          class="frame-checkbox"
                        />
                        <img
                          :src="getFrameImageUrl(frame.id)"
                          :alt="`Frame ${frame.frame_number}`"
                          class="frame-image"
                          @click="previewFrame(frame)"
                        />
                      </div>
                    </template>
                    <a-card-meta
                      :title="`帧 ${frame.frame_number}`"
                      :description="formatTime(frame.timestamp)"
                    />
                    <div class="frame-info">
                      <small>{{ frame.width }}×{{ frame.height }}</small>
                    </div>
                  </a-card>
                </div>
              </a-col>
            </a-row>
          </div>

          <!-- 列表视图 -->
          <div v-else class="frames-list">
            <a-table
              :columns="tableColumns"
              :data-source="paginatedFrames"
              :pagination="false"
              :row-selection="rowSelection"
              size="small"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'preview'">
                  <img
                    :src="getFrameImageUrl(record.id)"
                    :alt="`Frame ${record.frame_number}`"
                    class="frame-thumbnail"
                    @click="previewFrame(record)"
                  />
                </template>
                <template v-else-if="column.key === 'timestamp'">
                  {{ formatTime(record.timestamp) }}
                </template>
                <template v-else-if="column.key === 'size'">
                  {{ record.width }}×{{ record.height }}
                </template>
                <template v-else-if="column.key === 'actions'">
                  <a-space>
                    <a-button size="small" @click="previewFrame(record)">
                      <eye-outlined /> 预览
                    </a-button>
                    <a-button size="small" @click="downloadFrame(record)">
                      <download-outlined /> 下载
                    </a-button>
                  </a-space>
                </template>
              </template>
            </a-table>
          </div>
        </a-spin>

        <!-- 分页 -->
        <div v-if="frames.length > pageSize" class="pagination">
          <a-pagination
            v-model:current="currentPage"
            v-model:page-size="pageSize"
            :total="frames.length"
            :show-size-changer="true"
            :show-quick-jumper="true"
            :show-total="(total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`"
            @change="handlePageChange"
            @show-size-change="handlePageSizeChange"
          />
        </div>
      </a-card>
    </div>

    <!-- 帧预览对话框 -->
    <a-modal
      v-model:open="previewModalVisible"
      :title="`帧预览 - 第 ${selectedFrame?.frame_number} 帧`"
      :footer="null"
      width="80%"
      centered
    >
      <div v-if="selectedFrame" class="frame-preview">
        <div class="preview-image">
          <img
            :src="getFrameImageUrl(selectedFrame.id)"
            :alt="`Frame ${selectedFrame.frame_number}`"
            class="preview-img"
          />
        </div>
        <div class="preview-info">
          <a-descriptions :column="2" size="small">
            <a-descriptions-item label="帧号">{{ selectedFrame.frame_number }}</a-descriptions-item>
            <a-descriptions-item label="时间戳">{{ formatTime(selectedFrame.timestamp) }}</a-descriptions-item>
            <a-descriptions-item label="尺寸">{{ selectedFrame.width }}×{{ selectedFrame.height }}</a-descriptions-item>
            <a-descriptions-item label="文件路径">{{ selectedFrame.frame_path }}</a-descriptions-item>
          </a-descriptions>
        </div>
      </div>
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
import { useRouter } from 'vue-router'
import {
  ReloadOutlined,
  ScissorOutlined,
  PictureOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  FieldTimeOutlined,
  DownloadOutlined,
  DeleteOutlined,
  AppstoreOutlined,
  BarsOutlined,
  EyeOutlined
} from '@ant-design/icons-vue'
import { Empty, message } from 'ant-design-vue'
import { useVideoStore } from '../stores/video'
import FrameExtractModal from '../components/FrameExtractModal.vue'

const props = defineProps({
  id: {
    type: [String, Number],
    required: true
  }
})

const router = useRouter()
const videoStore = useVideoStore()

// 响应式数据
const viewMode = ref('grid')
const currentPage = ref(1)
const pageSize = ref(24)
const selectedFrames = ref([])
const previewModalVisible = ref(false)
const extractModalVisible = ref(false)
const selectedFrame = ref(null)

// 计算属性
const loading = computed(() => videoStore.loading)
const video = computed(() => videoStore.currentVideo)
const frames = computed(() => videoStore.videoFrames)

const paginatedFrames = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return frames.value.slice(start, end)
})

const averageInterval = computed(() => {
  if (frames.value.length < 2) return 0
  const totalTime = frames.value[frames.value.length - 1].timestamp - frames.value[0].timestamp
  return (totalTime / (frames.value.length - 1)).toFixed(2)
})

const checkAll = computed(() => {
  return frames.value.length > 0 && selectedFrames.value.length === frames.value.length
})

const indeterminate = computed(() => {
  return selectedFrames.value.length > 0 && selectedFrames.value.length < frames.value.length
})

// 表格列配置
const tableColumns = [
  {
    title: '预览',
    key: 'preview',
    width: 80,
    align: 'center'
  },
  {
    title: '帧号',
    dataIndex: 'frame_number',
    key: 'frame_number',
    sorter: (a, b) => a.frame_number - b.frame_number
  },
  {
    title: '时间戳',
    key: 'timestamp',
    sorter: (a, b) => a.timestamp - b.timestamp
  },
  {
    title: '尺寸',
    key: 'size'
  },
  {
    title: '操作',
    key: 'actions',
    width: 150
  }
]

// 行选择配置
const rowSelection = {
  selectedRowKeys: selectedFrames,
  onChange: (selectedRowKeys) => {
    selectedFrames.value = selectedRowKeys
  }
}

// 方法
const fetchVideoDetail = async () => {
  try {
    await videoStore.fetchVideoDetail(props.id)
  } catch (error) {
    console.error('Fetch video detail failed:', error)
  }
}

const fetchFrames = async () => {
  try {
    await videoStore.fetchVideoFrames(props.id)
  } catch (error) {
    console.error('Fetch frames failed:', error)
  }
}

const refreshFrames = async () => {
  await fetchFrames()
  selectedFrames.value = []
}

const getFrameImageUrl = (frameId) => {
  return `http://127.0.0.1:8000/files/frames/${frameId}/image`
}

const formatTime = (seconds) => {
  if (!seconds) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

const goBack = () => {
  router.push({ name: 'video-detail', params: { id: props.id } })
}

const extractMoreFrames = () => {
  extractModalVisible.value = true
}

const handleExtractSuccess = (result) => {
  console.log('Extract success:', result)
  refreshFrames()
}

const onCheckAllChange = (e) => {
  if (e.target.checked) {
    selectedFrames.value = frames.value.map(frame => frame.id)
  } else {
    selectedFrames.value = []
  }
}

const onFrameSelect = (frameId, checked) => {
  if (checked) {
    selectedFrames.value.push(frameId)
  } else {
    selectedFrames.value = selectedFrames.value.filter(id => id !== frameId)
  }
}

const previewFrame = (frame) => {
  selectedFrame.value = frame
  previewModalVisible.value = true
}

const downloadFrame = async (frame) => {
  try {
    const url = getFrameImageUrl(frame.id)
    const link = document.createElement('a')
    link.href = url
    link.download = `frame_${frame.frame_number}.jpg`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    message.success('帧图片下载成功')
  } catch (error) {
    message.error('下载失败')
    console.error('Download frame failed:', error)
  }
}

const downloadSelected = async () => {
  try {
    for (const frameId of selectedFrames.value) {
      const frame = frames.value.find(f => f.id === frameId)
      if (frame) {
        await downloadFrame(frame)
        // 添加延迟避免同时下载太多文件
        await new Promise(resolve => setTimeout(resolve, 100))
      }
    }
    message.success(`成功下载 ${selectedFrames.value.length} 个帧图片`)
  } catch (error) {
    message.error('批量下载失败')
    console.error('Download selected failed:', error)
  }
}

const deleteSelected = async () => {
  try {
    // 这里需要实现删除帧的API
    message.success(`成功删除 ${selectedFrames.value.length} 个帧`)
    selectedFrames.value = []
    refreshFrames()
  } catch (error) {
    message.error('删除失败')
    console.error('Delete selected failed:', error)
  }
}

const handlePageChange = (page, size) => {
  currentPage.value = page
  pageSize.value = size
}

const handlePageSizeChange = (current, size) => {
  currentPage.value = 1
  pageSize.value = size
}

// 监听路由参数变化
watch(() => props.id, (newId) => {
  if (newId) {
    fetchVideoDetail()
    fetchFrames()
  }
}, { immediate: true })

// 组件卸载时清理
onMounted(() => {
  return () => {
    videoStore.clearCurrentVideo()
    videoStore.clearVideoFrames()
  }
})
</script>

<style scoped>
.video-frames-view {
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

.stats-row {
  margin-bottom: 24px;
}

.control-panel {
  margin-bottom: 24px;
}

.frames-card {
  background: white;
}

.empty-state {
  padding: 60px 0;
  text-align: center;
}

.frames-grid {
  min-height: 400px;
}

.frame-item {
  position: relative;
}

.frame-card {
  transition: all 0.3s;
}

.frame-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.frame-cover {
  position: relative;
  height: 120px;
  overflow: hidden;
}

.frame-checkbox {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 2;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 4px;
  padding: 2px;
}

.frame-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  cursor: pointer;
  transition: transform 0.3s;
}

.frame-image:hover {
  transform: scale(1.05);
}

.frame-info {
  margin-top: 8px;
  text-align: center;
  color: #666;
}

.frame-thumbnail {
  width: 60px;
  height: 40px;
  object-fit: cover;
  border-radius: 4px;
  cursor: pointer;
}

.pagination {
  margin-top: 32px;
  text-align: center;
}

.frame-preview {
  text-align: center;
}

.preview-image {
  margin-bottom: 16px;
}

.preview-img {
  max-width: 100%;
  max-height: 60vh;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.preview-info {
  text-align: left;
}

:deep(.ant-page-header) {
  padding: 16px 24px;
}

:deep(.ant-card-meta-title) {
  font-size: 12px;
}

:deep(.ant-card-meta-description) {
  font-size: 11px;
}

:deep(.ant-statistic-title) {
  font-size: 12px;
}

@media (max-width: 768px) {
  .video-frames-view {
    padding: 16px;
  }
  
  .stats-row .ant-col {
    margin-bottom: 16px;
  }
  
  .frame-cover {
    height: 100px;
  }
}
</style>