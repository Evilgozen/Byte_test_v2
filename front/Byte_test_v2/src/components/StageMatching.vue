<template>
  <div class="stage-matching">
    <a-card title="阶段匹配" class="matching-card">
      <!-- 匹配输入区域 -->
      <div class="matching-input">
        <a-form layout="vertical" :model="matchingForm">
          <a-form-item label="查询内容" required>
            <a-textarea
              v-model:value="matchingForm.user_input"
              placeholder="请输入您要查找的阶段描述，例如：登录过程、页面加载、用户操作等"
              :rows="3"
              show-count
              :maxlength="500"
            />
          </a-form-item>
          
          <a-form-item>
            <a-space>
              <a-button 
                type="primary" 
                :loading="matching" 
                @click="startMatching"
                :disabled="!matchingForm.user_input.trim() || !videoId"
              >
                <search-outlined /> 开始匹配
              </a-button>
              
              <a-button @click="clearResults">
                <clear-outlined /> 清空结果
              </a-button>
              
              <a-button @click="viewStagesSummary" :disabled="!videoId">
                <unordered-list-outlined /> 查看阶段摘要
              </a-button>
            </a-space>
          </a-form-item>
        </a-form>
      </div>
      
      <!-- 匹配进度 -->
      <div v-if="matching" class="matching-progress">
        <a-alert
          message="正在进行阶段匹配"
          description="AI正在分析您的查询并匹配相关阶段..."
          type="info"
          show-icon
        />
        <a-progress :percent="100" status="active" style="margin-top: 16px" />
      </div>
      
      <!-- 阶段摘要 -->
      <div v-if="showSummary && stagesSummary" class="stages-summary">
        <a-divider>视频阶段摘要</a-divider>
        <div class="summary-info">
          <a-tag color="blue">总阶段数: {{ stagesSummary.total_stages }}</a-tag>
          <a-tag color="green">视频ID: {{ stagesSummary.video_id }}</a-tag>
        </div>
        <div class="summary-list">
          <a-list
            :data-source="stagesSummary.stages_summary"
            size="small"
            :pagination="false"
          >
            <template #renderItem="{ item, index }">
              <a-list-item>
                <a-list-item-meta>
                  <template #title>
                    <span class="stage-title">
                      <a-tag :color="getStageColor(index)">{{ index + 1 }}</a-tag>
                      {{ item.stage_name }}
                    </span>
                  </template>
                  <template #description>
                    <div class="stage-meta">
                      <span class="stage-time">
                        {{ formatTime(item.start_time) }} - {{ formatTime(item.end_time) }}
                        ({{ formatDuration(item.duration) }})
                      </span>
                      <div v-if="item.description" class="stage-desc">
                        {{ item.description }}
                      </div>
                    </div>
                  </template>
                </a-list-item-meta>
              </a-list-item>
            </template>
          </a-list>
        </div>
      </div>
      
      <!-- 匹配结果 -->
      <div v-if="matchingResults && matchingResults.length > 0" class="matching-results">
        <a-divider>匹配结果</a-divider>
        
        <!-- 结果统计 -->
        <div class="results-stats">
          <a-row :gutter="16">
            <a-col :span="8">
              <a-statistic
                title="匹配阶段数"
                :value="matchingResults.length"
                :value-style="{ color: '#1890ff' }"
              />
            </a-col>
            <a-col :span="8">
              <a-statistic
                title="最高相似度"
                :value="getMaxSimilarity()"
                suffix="%"
                :value-style="{ color: '#52c41a' }"
              />
            </a-col>
            <a-col :span="8">
              <a-statistic
                title="查询内容"
                :value="matchingForm.user_input.length"
                suffix="字符"
                :value-style="{ color: '#722ed1' }"
              />
            </a-col>
          </a-row>
        </div>
        
        <!-- 匹配结果列表 -->
        <div class="results-list">
          <a-list
            :data-source="sortedResults"
            :pagination="{ pageSize: 5, showSizeChanger: false }"
          >
            <template #renderItem="{ item, index }">
              <a-list-item class="result-item">
                <a-list-item-meta>
                  <template #avatar>
                    <a-avatar 
                      :style="{ backgroundColor: getSimilarityColor(item.similarity_score) }"
                      size="large"
                    >
                      {{ Math.round(item.similarity_score * 100) }}%
                    </a-avatar>
                  </template>
                  
                  <template #title>
                    <div class="result-title">
                      <span class="stage-name">{{ item.stage_name }}</span>
                      <a-tag 
                        :color="getSimilarityTagColor(item.similarity_score)"
                        class="similarity-tag"
                      >
                        相似度: {{ Math.round(item.similarity_score * 100) }}%
                      </a-tag>
                    </div>
                  </template>
                  
                  <template #description>
                    <div class="result-description">
                      <div class="stage-time">
                        <clock-circle-outlined />
                        {{ formatTime(item.start_time) }} - {{ formatTime(item.end_time) }}
                        ({{ formatDuration(item.duration) }})
                      </div>
                      
                      <div v-if="item.description" class="stage-desc">
                        <file-text-outlined />
                        {{ item.description }}
                      </div>
                      
                      <div v-if="item.match_reason" class="match-reason">
                        <bulb-outlined />
                        <strong>匹配原因:</strong> {{ item.match_reason }}
                      </div>
                    </div>
                  </template>
                </a-list-item-meta>
                
                <!-- 操作按钮 -->
                <template #actions>
                  <a-button 
                    type="link" 
                    size="small"
                    @click="jumpToStage(item)"
                  >
                    <play-circle-outlined /> 跳转播放
                  </a-button>
                </template>
              </a-list-item>
            </template>
          </a-list>
        </div>
      </div>
      
      <!-- 无匹配结果 -->
      <div v-if="hasSearched && (!matchingResults || matchingResults.length === 0)" class="no-results">
        <a-empty
          description="未找到匹配的阶段"
          :image="Empty.PRESENTED_IMAGE_SIMPLE"
        >
          <template #description>
            <span>未找到与 "{{ lastSearchQuery }}" 相关的阶段</span>
          </template>
          <a-button type="primary" @click="clearResults">重新搜索</a-button>
        </a-empty>
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
import { ref, computed, watch } from 'vue'
import { message, Empty } from 'ant-design-vue'
import {
  SearchOutlined,
  ClearOutlined,
  UnorderedListOutlined,
  ClockCircleOutlined,
  FileTextOutlined,
  BulbOutlined,
  PlayCircleOutlined
} from '@ant-design/icons-vue'
import { videoApi } from '../services/videoApi'

const props = defineProps({
  videoId: {
    type: [String, Number],
    required: true
  }
})

const emit = defineEmits(['jump-to-stage', 'view-summary'])

// 响应式数据
const matching = ref(false)
const matchingResults = ref([])
const stagesSummary = ref(null)
const showSummary = ref(false)
const hasSearched = ref(false)
const lastSearchQuery = ref('')
const error = ref(null)

const matchingForm = ref({
  user_input: ''
})

// 计算属性
const sortedResults = computed(() => {
  if (!matchingResults.value) return []
  return [...matchingResults.value].sort((a, b) => b.similarity_score - a.similarity_score)
})

// 方法
const startMatching = async () => {
  if (!props.videoId) {
    message.error('请先选择视频')
    return
  }
  
  if (!matchingForm.value.user_input.trim()) {
    message.error('请输入查询内容')
    return
  }
  
  try {
    matching.value = true
    error.value = null
    hasSearched.value = true
    lastSearchQuery.value = matchingForm.value.user_input.trim()
    
    const requestData = {
      user_input: matchingForm.value.user_input.trim(),
      video_id: props.videoId
    }
    
    const result = await videoApi.matchStages(requestData)
    
    if (result.success) {
      matchingResults.value = result.matched_stages || []
      
      if (matchingResults.value.length > 0) {
        message.success(`找到 ${matchingResults.value.length} 个匹配的阶段`)
      } else {
        message.info('未找到匹配的阶段，请尝试其他关键词')
      }
    } else {
      throw new Error(result.message || '匹配失败')
    }
  } catch (err) {
    console.error('Matching failed:', err)
    error.value = err.response?.data?.detail || err.message || '匹配过程中发生错误'
    message.error('阶段匹配失败')
  } finally {
    matching.value = false
  }
}

const viewStagesSummary = async () => {
  if (!props.videoId) {
    message.error('请先选择视频')
    return
  }
  
  try {
    const result = await videoApi.getVideoStagesSummary(props.videoId)
    
    if (result.success) {
      stagesSummary.value = result
      showSummary.value = true
      message.success('阶段摘要加载成功')
      emit('view-summary', result)
    } else {
      throw new Error(result.message || '获取阶段摘要失败')
    }
  } catch (err) {
    console.error('Fetch summary failed:', err)
    error.value = err.response?.data?.detail || err.message || '获取阶段摘要时发生错误'
    message.error('获取阶段摘要失败')
  }
}

const clearResults = () => {
  matchingResults.value = []
  stagesSummary.value = null
  showSummary.value = false
  hasSearched.value = false
  lastSearchQuery.value = ''
  error.value = null
  matchingForm.value.user_input = ''
}

const jumpToStage = (stage) => {
  emit('jump-to-stage', stage)
  message.info(`跳转到阶段: ${stage.stage_name}`)
}

const getMaxSimilarity = () => {
  if (!matchingResults.value || matchingResults.value.length === 0) return 0
  const maxScore = Math.max(...matchingResults.value.map(r => r.similarity_score))
  return Math.round(maxScore * 100)
}

const getSimilarityColor = (score) => {
  if (score >= 0.8) return '#52c41a' // 绿色
  if (score >= 0.6) return '#1890ff' // 蓝色
  if (score >= 0.4) return '#faad14' // 橙色
  return '#f5222d' // 红色
}

const getSimilarityTagColor = (score) => {
  if (score >= 0.8) return 'green'
  if (score >= 0.6) return 'blue'
  if (score >= 0.4) return 'orange'
  return 'red'
}

const getStageColor = (index) => {
  const colors = ['blue', 'green', 'orange', 'red', 'purple', 'cyan']
  return colors[index % colors.length]
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

// 监听videoId变化，清空结果
watch(() => props.videoId, () => {
  clearResults()
})
</script>

<style scoped>
.stage-matching {
  margin-bottom: 24px;
}

.matching-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.matching-input {
  margin-bottom: 16px;
}

.matching-progress {
  margin: 24px 0;
}

.stages-summary {
  margin-top: 24px;
}

.summary-info {
  margin-bottom: 16px;
}

.summary-list {
  background: #fafafa;
  border-radius: 6px;
  padding: 16px;
}

.stage-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stage-meta {
  margin-top: 4px;
}

.stage-time {
  color: #666;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.stage-desc {
  color: #666;
  font-size: 13px;
  margin-top: 4px;
  line-height: 1.4;
}

.matching-results {
  margin-top: 24px;
}

.results-stats {
  margin-bottom: 24px;
  padding: 16px;
  background: #fafafa;
  border-radius: 6px;
}

.results-list {
  margin-top: 16px;
}

.result-item {
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  margin-bottom: 16px;
  padding: 16px;
  transition: all 0.3s ease;
}

.result-item:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.2);
}

.result-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.stage-name {
  font-weight: 600;
  color: #262626;
  font-size: 16px;
}

.similarity-tag {
  font-weight: 600;
}

.result-description {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.result-description > div {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 14px;
  line-height: 1.5;
}

.match-reason {
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 4px;
  padding: 8px;
  color: #389e0d;
}

.no-results {
  margin: 40px 0;
  text-align: center;
}

.error-section {
  margin-top: 16px;
}

:deep(.ant-list-item-meta-avatar) {
  margin-right: 16px;
}

:deep(.ant-list-item-action) {
  margin-left: 16px;
}

:deep(.ant-statistic-title) {
  font-size: 14px;
  margin-bottom: 4px;
}

:deep(.ant-statistic-content) {
  font-size: 20px;
}

:deep(.ant-empty-description) {
  color: #666;
}

@media (max-width: 768px) {
  .result-title {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .similarity-tag {
    align-self: flex-start;
  }
  
  .results-stats :deep(.ant-col) {
    margin-bottom: 16px;
  }
  
  .result-description > div {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}
</style>