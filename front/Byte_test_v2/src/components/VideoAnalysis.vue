<template>
  <div class="video-analysis">
    <a-card title="视频分析" class="analysis-card">
      <!-- 分析参数配置 -->
      <div class="analysis-config">
        <a-form layout="inline" :model="analysisParams">
          <a-form-item label="产品名称" required>
            <a-input
              v-model:value="analysisParams.product_name"
              placeholder="请输入产品名称"
              style="width: 150px"
            />
            <a-tooltip title="产品名称用于向量存储的元数据，便于后续RAG分析">
              <question-circle-outlined style="margin-left: 8px; color: #999" />
            </a-tooltip>
          </a-form-item>
          
          <a-form-item label="帧间隔">
            <a-input-number
              v-model:value="analysisParams.frame_interval"
              :min="1"
              :max="300"
              placeholder="帧间隔"
              style="width: 120px"
            />
            <a-tooltip title="每隔多少帧进行一次SSIM检测，默认30帧">
              <question-circle-outlined style="margin-left: 8px; color: #999" />
            </a-tooltip>
          </a-form-item>
          
          <a-form-item label="SSIM阈值">
            <a-input-number
              v-model:value="analysisParams.ssim_threshold"
              :min="0.1"
              :max="0.99"
              :step="0.01"
              placeholder="SSIM阈值"
              style="width: 120px"
            />
            <a-tooltip title="SSIM相似度阈值，低于此值认为是关键帧，默认0.75">
              <question-circle-outlined style="margin-left: 8px; color: #999" />
            </a-tooltip>
          </a-form-item>
          
          <a-form-item>
            <a-button 
              type="primary" 
              :loading="analyzing" 
              @click="startAnalysis"
              :disabled="!videoId"
            >
              <play-circle-outlined /> 开始分析
            </a-button>
          </a-form-item>
          
          <a-form-item v-if="hasAnalysisResult">
            <a-button 
              danger 
              :loading="deleting" 
              @click="deleteAnalysis"
            >
              <delete-outlined /> 删除分析结果
            </a-button>
          </a-form-item>
        </a-form>
      </div>
      
      <!-- 分析进度 -->
      <div v-if="analyzing" class="analysis-progress">
        <a-alert
          message="正在进行视频分析"
          description="请耐心等待，分析过程可能需要几分钟时间..."
          type="info"
          show-icon
        />
        <a-progress :percent="100" status="active" style="margin-top: 16px" />
      </div>
      
      <!-- 分析结果 -->
      <div v-if="analysisResult && !analyzing" class="analysis-result">
        <a-divider>分析结果</a-divider>
        
        <!-- 统计信息 -->
        <a-row :gutter="16" class="stats-row">
          <a-col :span="6">
            <a-statistic
              title="关键帧数量"
              :value="analysisResult.total_keyframes || 0"
              :value-style="{ color: '#1890ff' }"
            />
          </a-col>
          <a-col :span="6">
            <a-statistic
              title="阶段数量"
              :value="analysisResult.total_stages || 0"
              :value-style="{ color: '#52c41a' }"
            />
          </a-col>
          <a-col :span="6">
            <a-statistic
              title="分析时长"
              :value="analysisResult.analysis_duration || 0"
              suffix="秒"
              :value-style="{ color: '#722ed1' }"
            />
          </a-col>
          <a-col :span="6">
            <a-statistic
              title="分析状态"
              value="完成"
              :value-style="{ color: '#52c41a' }"
            />
          </a-col>
        </a-row>
        
        <!-- 阶段信息 -->
        <div v-if="stages && stages.length > 0" class="stages-section">
          <h4>视频阶段信息</h4>
          <a-timeline>
            <a-timeline-item
              v-for="(stage, index) in stages"
              :key="stage.id"
              :color="getStageColor(index)"
            >
              <template #dot>
                <clock-circle-outlined style="font-size: 16px" />
              </template>
              <div class="stage-item">
                <div class="stage-header">
                  <span class="stage-name">{{ stage.stage_name }}</span>
                  <span class="stage-time">
                        {{ formatTime(stage.start_time) }} - {{ formatTime(stage.end_time) }}
                        (持续: {{ formatDuration(stage.duration) }})
                      </span>
                </div>
                <div v-if="stage.description" class="stage-description">
                  {{ stage.description }}
                </div>
              </div>
            </a-timeline-item>
          </a-timeline>
        </div>
        
        <!-- 关键帧链接 -->
        <div v-if="keyframes && keyframes.length > 0" class="keyframes-section">
          <h4>关键帧信息</h4>
          <div class="keyframes-summary">
            <a-row :gutter="16">
              <a-col :span="8">
                <a-statistic
                  title="关键帧总数"
                  :value="keyframes.length"
                  :value-style="{ color: '#1890ff' }"
                />
              </a-col>
              <a-col :span="16">
                <div class="keyframes-action">
                  <a-space>
                    <a-button type="primary" @click="viewAllKeyframes">
                      <picture-outlined /> 查看关键帧
                    </a-button>
                    <a-button type="default" @click="goToRAGAnalysis">
                      <search-outlined /> RAG智能分析
                    </a-button>
                  </a-space>
                </div>
              </a-col>
            </a-row>
          </div>
        </div>
      </div>
      
      <!-- 错误信息 -->
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
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  PlayCircleOutlined,
  DeleteOutlined,
  QuestionCircleOutlined,
  ClockCircleOutlined,
  PictureOutlined,
  SearchOutlined
} from '@ant-design/icons-vue'
import { videoApi } from '../services/videoApi'

const router = useRouter()

const props = defineProps({
  videoId: {
    type: [String, Number],
    required: true
  }
})

const emit = defineEmits(['analysis-complete', 'view-keyframes'])

// 响应式数据
const analyzing = ref(false)
const deleting = ref(false)
const analysisResult = ref(null)
const stages = ref([])
const keyframes = ref([])
const error = ref(null)

const analysisParams = ref({
  product_name: '',
  frame_interval: 30,
  ssim_threshold: 0.75
})

// 计算属性
const hasAnalysisResult = computed(() => {
  return analysisResult.value || (stages.value && stages.value.length > 0)
})

// 方法
const startAnalysis = async () => {
  if (!props.videoId) {
    message.error('请先选择视频')
    return
  }
  
  if (!analysisParams.value.product_name.trim()) {
    message.error('请输入产品名称')
    return
  }
  
  try {
    analyzing.value = true
    error.value = null
    
    const result = await videoApi.analyzeVideoWithSSIM(props.videoId, analysisParams.value)
    
    if (result.success) {
      analysisResult.value = result.data
      message.success('视频分析完成')
      
      // 获取阶段和关键帧信息
      await Promise.all([
        fetchStages(),
        fetchKeyframes()
      ])
      
      emit('analysis-complete', result.data)
    } else {
      throw new Error(result.message || '分析失败')
    }
  } catch (err) {
    console.error('Analysis failed:', err)
    error.value = err.response?.data?.detail || err.message || '分析过程中发生错误'
    message.error('视频分析失败')
  } finally {
    analyzing.value = false
  }
}

const deleteAnalysis = async () => {
  try {
    deleting.value = true
    
    const result = await videoApi.deleteVideoAnalysis(props.videoId)
    
    if (result.success) {
      analysisResult.value = null
      stages.value = []
      keyframes.value = []
      message.success('分析结果删除成功')
    } else {
      throw new Error(result.message || '删除失败')
    }
  } catch (err) {
    console.error('Delete failed:', err)
    error.value = err.response?.data?.detail || err.message || '删除过程中发生错误'
    message.error('删除分析结果失败')
  } finally {
    deleting.value = false
  }
}

const fetchStages = async () => {
  try {
    const result = await videoApi.getVideoStages(props.videoId)
    if (result.success) {
      stages.value = result.stages || []
    }
  } catch (err) {
    console.error('Fetch stages failed:', err)
  }
}

const fetchKeyframes = async () => {
  try {
    const result = await videoApi.getVideoKeyframes(props.videoId)
    if (result.success) {
      keyframes.value = result.keyframes || []
    }
  } catch (err) {
    console.error('Fetch keyframes failed:', err)
  }
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

const getStageColor = (index) => {
  const colors = ['blue', 'green', 'orange', 'red', 'purple', 'cyan']
  return colors[index % colors.length]
}

const viewAllKeyframes = () => {
  emit('view-keyframes')
}

const goToRAGAnalysis = () => {
  router.push('/rag-analysis')
}

// 监听videoId变化，自动加载已有的分析结果
watch(() => props.videoId, async (newVideoId) => {
  if (newVideoId) {
    await Promise.all([
      fetchStages(),
      fetchKeyframes()
    ])
  }
}, { immediate: true })

// 组件挂载时检查是否有已有的分析结果
onMounted(async () => {
  if (props.videoId) {
    await Promise.all([
      fetchStages(),
      fetchKeyframes()
    ])
  }
})
</script>

<style scoped>
.video-analysis {
  margin-bottom: 24px;
}

.analysis-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.analysis-config {
  margin-bottom: 16px;
}

.analysis-progress {
  margin: 24px 0;
}

.analysis-result {
  margin-top: 24px;
}

.stats-row {
  margin-bottom: 24px;
}

.stages-section {
  margin-bottom: 32px;
}

.stages-section h4 {
  margin-bottom: 16px;
  color: #262626;
  font-weight: 600;
}

.stage-item {
  padding: 8px 0;
}

.stage-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.stage-name {
  font-weight: 600;
  color: #262626;
}

.stage-time {
  color: #666;
  font-size: 12px;
}

.stage-description {
  color: #666;
  font-size: 14px;
  line-height: 1.5;
}

.keyframes-section h4 {
  margin-bottom: 16px;
  color: #262626;
  font-weight: 600;
}

.keyframes-summary {
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
}

.keyframes-action {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  height: 100%;
}

.error-section {
  margin-top: 16px;
}

:deep(.ant-timeline-item-content) {
  min-height: auto;
}

:deep(.ant-statistic-title) {
  font-size: 14px;
  margin-bottom: 4px;
}

:deep(.ant-statistic-content) {
  font-size: 20px;
}

@media (max-width: 768px) {
  .analysis-config :deep(.ant-form) {
    flex-direction: column;
  }
  
  .analysis-config :deep(.ant-form-item) {
    margin-bottom: 16px;
  }
  
  .stage-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .stage-time {
    margin-top: 4px;
  }
  
  .keyframes-grid {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 12px;
  }
}
</style>