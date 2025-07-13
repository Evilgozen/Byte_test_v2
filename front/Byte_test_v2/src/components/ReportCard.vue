<template>
  <div v-if="comparisonReport || streamReport.length > 0 || streamGenerating" class="comparison-report">
    <a-divider>阶段对比分析报告</a-divider>
    
    <a-card title="AI分析报告" class="report-card">
      <!-- 流式报告内容 -->
      <div v-if="streamGenerating || streamReport.length > 0" class="stream-content">
        <!-- 流式生成进度 -->
        <div v-if="streamGenerating" class="stream-header">
          <div class="stream-progress">
            <p>{{ streamStatus }}</p>
            <a-progress :percent="streamProgress" status="active" size="small" />
          </div>
        </div>
        
        <div class="report-content" ref="streamReportRef">
          <div v-if="streamReport" v-html="formatReport(streamReport)" class="stream-text"></div>
          <div v-if="streamGenerating" class="typing-indicator">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
          </div>
        </div>
      </div>
      <!-- 普通报告内容 -->
      <div v-else-if="comparisonReport" class="report-content" v-html="formatReport(comparisonReport.report)"></div>
      
      <template #extra>
        <a-space>
          <a-button v-if="streamGenerating" size="small" danger @click="$emit('stop-generation')">
            停止生成
          </a-button>
          <a-button v-else size="small" @click="$emit('copy-report')">
            <copy-outlined /> 复制报告
          </a-button>
          <a-button v-if="!streamGenerating" size="small" @click="$emit('download-report')">
            <download-outlined /> 下载报告
          </a-button>
          <a-button v-if="!streamGenerating" size="small" @click="showFeishuExportModal">
            <file-text-outlined /> 导出到飞书
          </a-button>
        </a-space>
      </template>
    </a-card>
    
    <div v-if="comparisonReport && comparisonReport.similar_stages && comparisonReport.similar_stages.length > 0" class="report-stages">
      <h4>参考阶段数据</h4>
      <a-table 
        :columns="reportTableColumns"
        :data-source="comparisonReport.similar_stages"
        size="small"
        :pagination="false"
      />
    </div>
    
    <!-- 飞书导出模态框 -->
    <a-modal
      v-model:open="feishuExportVisible"
      title="导出到飞书文档"
      :confirm-loading="feishuExporting"
      @ok="handleFeishuExport"
      @cancel="feishuExportVisible = false"
    >
      <a-form :model="feishuExportForm" layout="vertical">
        <a-form-item label="文档标题" required>
          <a-input v-model:value="feishuExportForm.title" placeholder="请输入文档标题" />
        </a-form-item>
        
        <a-form-item label="导出内容预览">
          <div class="export-preview">
            <a-textarea 
              :value="getReportContent()" 
              :rows="8" 
              readonly 
              placeholder="暂无报告内容"
            />
          </div>
        </a-form-item>
      </a-form>
      
      <!-- 导出结果显示 -->
      <div v-if="feishuExportResult" class="export-result">
        <a-alert
          :message="feishuExportResult.success ? '导出成功' : '导出失败'"
          :description="feishuExportResult.message"
          :type="feishuExportResult.success ? 'success' : 'error'"
          show-icon
        />
        <div v-if="feishuExportResult.success && feishuExportResult.data" class="document-link">
          <p>文档ID: {{ feishuExportResult.data.document_id }}</p>
          <a 
            v-if="feishuExportResult.data.document_url" 
            :href="feishuExportResult.data.document_url" 
            target="_blank"
            class="document-url"
          >
            打开飞书文档
          </a>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { CopyOutlined, DownloadOutlined, FileTextOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { marked } from 'marked'
import { videoApi } from '../services/videoApi'

const streamReportRef = ref(null)

// 飞书导出相关数据
const feishuExportVisible = ref(false)
const feishuExporting = ref(false)
const feishuExportResult = ref(null)
const feishuExportForm = ref({
  title: ''
})

const props = defineProps({
  comparisonReport: {
    type: Object,
    default: null
  },
  streamReport: {
    type: String,
    default: ''
  },
  streamGenerating: {
    type: Boolean,
    default: false
  },
  streamStatus: {
    type: String,
    default: ''
  },
  streamProgress: {
    type: Number,
    default: 0
  },
  reportTableColumns: {
    type: Array,
    default: () => []
  }
})

defineEmits(['stop-generation', 'copy-report', 'download-report'])

const formatReport = (report) => {
  if (!report) return ''
  try {
    // 使用marked库解析markdown
    return marked.parse(report, {
      breaks: true,  // 支持换行
      gfm: true,     // 支持GitHub风格的markdown
      sanitize: false // 允许HTML标签
    })
  } catch (error) {
    console.error('Markdown解析失败:', error)
    // 如果marked解析失败，回退到简单的文本处理
    return report
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/^# (.*$)/gm, '<h1>$1</h1>')
      .replace(/^## (.*$)/gm, '<h2>$1</h2>')
      .replace(/^### (.*$)/gm, '<h3>$1</h3>')
  }
}

// 自动滚动到底部的函数
const scrollToBottom = async () => {
  await nextTick()
  if (streamReportRef.value) {
    streamReportRef.value.scrollTop = streamReportRef.value.scrollHeight
  }
}

// 获取报告内容
const getReportContent = () => {
  return props.streamReport || props.comparisonReport?.report || ''
}

// 飞书导出相关函数
const showFeishuExportModal = () => {
  // 设置默认标题
  const currentDate = new Date().toLocaleDateString('zh-CN')
  feishuExportForm.value.title = `视频分析报告_${currentDate}`
  
  // 清除之前的结果
  feishuExportResult.value = null
  
  // 显示模态框
  feishuExportVisible.value = true
}

const handleFeishuExport = async () => {
  if (!feishuExportForm.value.title.trim()) {
    message.error('请输入文档标题')
    return
  }
  
  const content = getReportContent()
  if (!content) {
    message.error('暂无报告内容可导出')
    return
  }
  
  feishuExporting.value = true
  feishuExportResult.value = null
  
  try {
    const response = await videoApi.createFeishuDocument({
      title: feishuExportForm.value.title,
      content: content
    })
    
    // 根据实际API响应结构处理数据
    // 完整响应: {success: true, message: '...', data: {...}, error: null}
    // response.data 直接是文档数据: {document_id: '...', document_url: '...'}
    const apiResponse = response // 完整的API响应
    const documentData = response.data // 文档数据
    
    // 构造标准化的结果对象
    const result = {
      success: apiResponse.success || (documentData && documentData.document_id ? true : false),
      message: apiResponse.message || '文档创建成功',
      data: documentData,
      error: apiResponse.error || null
    }
    
    // 清理document_url中的多余字符（空格、反引号等）
    if (result.data && result.data.document_url) {
      result.data.document_url = result.data.document_url
        .replace(/[`\s]/g, '') // 移除反引号和所有空格
        .trim()
    }
    
    feishuExportResult.value = result
    
    // 判断成功状态
    const isSuccess = result.success === true && result.data && result.data.document_id
    
    if (isSuccess) {
      message.success('飞书文档创建成功！')
    } else {
      message.error(result.message || '导出失败')
    }
  } catch (error) {
    console.error('飞书导出失败:', error)
    feishuExportResult.value = {
      success: false,
      message: error.response?.data?.detail || error.message || '导出过程中发生错误'
    }
    message.error('导出失败，请稍后重试')
  } finally {
    feishuExporting.value = false
  }
}

// 暴露方法给父组件
defineExpose({
  scrollToBottom
})
</script>

<style scoped>
.comparison-report {
  margin-top: 24px;
}

.report-card {
  margin-bottom: 16px;
}

.report-content {
  line-height: 1.8;
  font-size: 14px;
  white-space: pre-wrap;
  padding: 16px;
  background: #fafafa;
  border-radius: 6px;
  border: 1px solid #e8e8e8;
  max-height: 600px;
  overflow-y: auto;
}

.report-content h1, .report-content h2, .report-content h3 {
  color: #1890ff;
  margin: 16px 0 8px 0;
}

.report-content h1 {
  font-size: 18px;
  border-bottom: 2px solid #1890ff;
  padding-bottom: 4px;
}

.report-content h2 {
  font-size: 16px;
}

.report-content h3 {
  font-size: 14px;
}

.report-content p {
  margin: 8px 0;
  text-align: justify;
}

.report-content ul {
  margin: 8px 0;
  padding-left: 20px;
}

.report-content li {
  margin: 4px 0;
}

.report-content strong {
  color: #d4380d;
  font-weight: 600;
}

.report-content em {
  color: #722ed1;
  font-style: italic;
}

.report-stages {
  margin-top: 16px;
}

.report-stages h4 {
  margin-bottom: 12px;
  color: #1890ff;
}

/* 流式生成样式 */
.stream-content {
  position: relative;
}

/* 流式报告头部样式 */
.stream-header {
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 6px;
  padding: 12px 16px;
  margin-bottom: 16px;
}

.stream-header .stream-progress {
  padding: 0;
}

.stream-header .stream-progress p {
  margin-bottom: 8px;
  font-size: 14px;
  color: #52c41a;
  font-weight: 500;
}

.typing-indicator {
  display: inline-flex;
  align-items: center;
  margin: 8px 0;
  padding: 8px 12px;
  background: linear-gradient(90deg, #e6f7ff, #bae7ff);
  border-radius: 16px;
  border: 1px solid #91d5ff;
}

.typing-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #1890ff;
  margin: 0 3px;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-dot:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 流式内容动画 */
.stream-content {
  animation: fadeIn 0.3s ease-in;
  position: relative;
}

.stream-content .report-content {
  transition: all 0.2s ease-out;
}

.stream-text {
  animation: contentAppear 0.2s ease-out;
  transition: opacity 0.1s ease-in-out;
}

.stream-content::after {
  content: '';
  position: absolute;
  bottom: 16px;
  right: 16px;
  width: 2px;
  height: 20px;
  background: #1890ff;
  animation: blink 1s infinite;
  z-index: 10;
}

/* 内容更新动画 */
.stream-content .report-content > div {
  animation: contentAppear 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes contentAppear {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes blink {
  0%, 50% {
    opacity: 1;
  }
  51%, 100% {
    opacity: 0;
  }
}

/* 飞书导出相关样式 */
.export-preview {
  margin-bottom: 16px;
}

.export-result {
  margin-top: 16px;
}

.document-link {
  margin-top: 12px;
  padding: 12px;
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 6px;
}

.document-link p {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #52c41a;
}

.document-url {
  display: inline-block;
  padding: 4px 12px;
  background: #52c41a;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  font-size: 14px;
  transition: background-color 0.3s;
}

.document-url:hover {
  background: #389e0d;
  color: white;
}
</style>