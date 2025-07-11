<template>
  <div class="rag-analysis">
    <a-card title="RAG阶段分析" class="analysis-card">
      <!-- 查询配置 -->
      <div class="query-config">
        <a-form layout="vertical" :model="queryParams">
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="查询描述" required>
                <a-textarea
                  v-model:value="queryParams.query"
                  placeholder="请输入要查询的阶段描述，例如：应用启动阶段、登录流程、页面加载等"
                  :rows="3"
                  show-count
                  :maxlength="500"
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="产品名称过滤">
                <a-input
                  v-model:value="queryParams.product_name"
                  placeholder="可选：过滤特定产品的视频"
                />
                <div class="form-help">留空则查询所有产品的视频</div>
              </a-form-item>
            </a-col>
          </a-row>
          
          <a-row :gutter="16">
            <a-col :span="8">
              <a-form-item label="返回结果数量">
                <a-input-number
                  v-model:value="queryParams.k"
                  :min="1"
                  :max="20"
                  style="width: 100%"
                />
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item label="相似度阈值">
                <a-input-number
                  v-model:value="queryParams.similarity_threshold"
                  :min="0.0"
                  :max="1.0"
                  :step="0.1"
                  style="width: 100%"
                />
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item label="操作">
                <a-space>
                  <a-button 
                    type="primary" 
                    :loading="querying" 
                    @click="querySimilarStages"
                    :disabled="!queryParams.query.trim()"
                  >
                    <search-outlined /> 查询相似阶段
                  </a-button>
                  <a-button 
                    type="default" 
                    :loading="generating" 
                    @click="generateReport"
                    :disabled="!queryParams.query.trim()"
                  >
                    <file-text-outlined /> 生成对比报告
                  </a-button>
                </a-space>
              </a-form-item>
            </a-col>
          </a-row>
        </a-form>
      </div>
      
      <!-- 查询结果 -->
      <div v-if="similarStages && similarStages.length > 0" class="query-results">
        <a-divider>相似阶段查询结果</a-divider>
        
        <div class="results-summary">
          <a-alert
            :message="`找到 ${similarStages.length} 个相似阶段`"
            type="success"
            show-icon
            style="margin-bottom: 16px"
          />
        </div>
        
        <div class="stages-list">
          <a-row :gutter="16">
            <a-col 
              v-for="(stage, index) in similarStages" 
              :key="index"
              :span="12"
              style="margin-bottom: 16px"
            >
              <a-card 
                size="small" 
                :title="`视频 ${stage.video_id} - ${stage.stage_name}`"
                class="stage-card"
              >
                <template #extra>
                  <a-tag :color="getSimilarityColor(stage.similarity_score)">
                    相似度: {{ (stage.similarity_score * 100).toFixed(1) }}%
                  </a-tag>
                </template>
                
                <div class="stage-info">
                  <p><strong>产品:</strong> {{ stage.product_name || '未指定' }}</p>
                  <p><strong>时间范围:</strong> {{ stage.time_range || '未知' }}</p>
                  <p><strong>视频文件:</strong> {{ stage.video_filename || '未知' }}</p>
                  <p v-if="stage.content"><strong>内容:</strong> {{ stage.content }}</p>
                </div>
                
                <template #actions>
                  <a @click="viewVideoDetail(stage.video_id)">查看视频详情</a>
                  <a @click="viewVideoAnalysis(stage.video_id)">查看分析结果</a>
                </template>
              </a-card>
            </a-col>
          </a-row>
        </div>
      </div>
      
      <!-- 对比报告 -->
      <div v-if="comparisonReport" class="comparison-report">
        <a-divider>阶段对比分析报告</a-divider>
        
        <a-card title="AI分析报告" class="report-card">
          <div class="report-content" v-html="formatReport(comparisonReport.report)"></div>
          
          <template #extra>
            <a-space>
              <a-button size="small" @click="copyReport">
                <copy-outlined /> 复制报告
              </a-button>
              <a-button size="small" @click="downloadReport">
                <download-outlined /> 下载报告
              </a-button>
            </a-space>
          </template>
        </a-card>
        
        <div v-if="comparisonReport.similar_stages && comparisonReport.similar_stages.length > 0" class="report-stages">
          <h4>参考阶段数据</h4>
          <a-table 
            :columns="reportTableColumns"
            :data-source="comparisonReport.similar_stages"
            size="small"
            :pagination="false"
          />
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
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  SearchOutlined,
  FileTextOutlined,
  CopyOutlined,
  DownloadOutlined
} from '@ant-design/icons-vue'
import { videoApi } from '../services/videoApi'

const router = useRouter()

// 响应式数据
const querying = ref(false)
const generating = ref(false)
const similarStages = ref([])
const comparisonReport = ref(null)
const error = ref(null)

const queryParams = ref({
  query: '',
  product_name: '',
  k: 5,
  similarity_threshold: 0.7
})

// 表格列配置
const reportTableColumns = [
  {
    title: '视频ID',
    dataIndex: 'video_id',
    key: 'video_id',
    width: 80
  },
  {
    title: '阶段名称',
    dataIndex: 'stage_name',
    key: 'stage_name'
  },
  {
    title: '产品',
    dataIndex: 'product_name',
    key: 'product_name'
  },
  {
    title: '时间范围',
    dataIndex: 'time_range',
    key: 'time_range'
  },
  {
    title: '视频文件',
    dataIndex: 'video_filename',
    key: 'video_filename'
  },
  {
    title: '内容',
    dataIndex: 'content',
    key: 'content'
  },
  {
    title: '相似度',
    dataIndex: 'similarity_score',
    key: 'similarity_score',
    customRender: ({ text }) => `${(text * 100).toFixed(1)}%`
  }
]

// 方法
const querySimilarStages = async () => {
  if (!queryParams.value.query.trim()) {
    message.error('请输入查询描述')
    return
  }
  
  try {
    querying.value = true
    error.value = null
    
    const result = await videoApi.querySimilarStages(queryParams.value)
    
    if (result.success) {
      // 修复数据结构：API返回的是result.data.results，不是result.data.similar_stages
      similarStages.value = result.data.results || []
      message.success(`找到 ${similarStages.value.length} 个相似阶段`)
    } else {
      throw new Error(result.message || '查询失败')
    }
  } catch (err) {
    console.error('Query failed:', err)
    error.value = err.response?.data?.detail || err.message || '查询过程中发生错误'
    message.error('查询相似阶段失败')
  } finally {
    querying.value = false
  }
}

const generateReport = async () => {
  if (!queryParams.value.query.trim()) {
    message.error('请输入查询描述')
    return
  }
  
  try {
    generating.value = true
    error.value = null
    
    const result = await videoApi.generateComparisonReport({
      query: queryParams.value.query,
      product_name: queryParams.value.product_name,
      similarity_threshold: queryParams.value.similarity_threshold
    })
    
    if (result.success) {
      comparisonReport.value = result.data
      message.success('对比报告生成完成')
    } else {
      throw new Error(result.message || '报告生成失败')
    }
  } catch (err) {
    console.error('Report generation failed:', err)
    error.value = err.response?.data?.detail || err.message || '报告生成过程中发生错误'
    message.error('生成对比报告失败')
  } finally {
    generating.value = false
  }
}

const getSimilarityColor = (similarity) => {
  if (similarity >= 0.9) return 'green'
  if (similarity >= 0.8) return 'blue'
  if (similarity >= 0.7) return 'orange'
  return 'red'
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

const formatReport = (report) => {
  if (!report) return ''
  // 简单的Markdown到HTML转换
  return report
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
}

const viewVideoDetail = (videoId) => {
  router.push({ name: 'video-detail', params: { id: videoId } })
}

const viewVideoAnalysis = (videoId) => {
  router.push({ name: 'video-analysis', params: { id: videoId } })
}

const copyReport = async () => {
  if (!comparisonReport.value?.report) return
  
  try {
    await navigator.clipboard.writeText(comparisonReport.value.report)
    message.success('报告已复制到剪贴板')
  } catch (err) {
    message.error('复制失败')
  }
}

const downloadReport = () => {
  if (!comparisonReport.value?.report) return
  
  const blob = new Blob([comparisonReport.value.report], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `RAG分析报告_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  
  message.success('报告下载完成')
}
</script>

<style scoped>
.rag-analysis {
  margin-bottom: 24px;
}

.analysis-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.query-config {
  margin-bottom: 24px;
}

.form-help {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.query-results {
  margin-top: 24px;
}

.results-summary {
  margin-bottom: 16px;
}

.stages-list {
  margin-top: 16px;
}

.stage-card {
  height: 100%;
  transition: all 0.3s ease;
}

.stage-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.stage-info p {
  margin-bottom: 8px;
  font-size: 14px;
}

.comparison-report {
  margin-top: 24px;
}

.report-card {
  margin-bottom: 16px;
}

.report-content {
  line-height: 1.6;
  font-size: 14px;
  white-space: pre-wrap;
}

.report-stages {
  margin-top: 16px;
}

.report-stages h4 {
  margin-bottom: 12px;
  color: #1890ff;
}

.error-section {
  margin-top: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .stages-list .ant-col {
    margin-bottom: 12px;
  }
  
  .stage-card {
    margin-bottom: 12px;
  }
}
</style>