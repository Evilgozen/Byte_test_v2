<template>
  <div class="rag-analysis-view">
    <div class="page-header">
      <a-page-header
        title="RAG阶段分析"
        sub-title="基于向量检索的视频阶段智能分析"
        @back="() => $router.go(-1)"
      >
        <template #extra>
          <a-space>
            <a-button @click="$router.push('/videos')">
              <video-camera-outlined /> 视频列表
            </a-button>
            <a-button type="primary" @click="$router.push('/videos')">
              <plus-outlined /> 上传新视频
            </a-button>
          </a-space>
        </template>
        
        <template #content>
          <div class="page-description">
            <p>使用RAG（检索增强生成）技术，智能分析和对比不同视频中的相似阶段。</p>
            <div class="feature-tags">
              <a-tag color="blue">语义检索</a-tag>
              <a-tag color="green">智能对比</a-tag>
              <a-tag color="orange">报告生成</a-tag>
              <a-tag color="purple">跨视频分析</a-tag>
            </div>
          </div>
        </template>
      </a-page-header>
    </div>
    
    <div class="page-content">
      <a-row :gutter="24">
        <a-col :span="24">
          <!-- 使用说明 -->
          <a-card class="usage-guide" style="margin-bottom: 24px">
            <template #title>
              <info-circle-outlined style="margin-right: 8px" />
              使用说明
            </template>
            
            <a-collapse ghost>
              <a-collapse-panel key="1" header="如何使用RAG分析功能？">
                <div class="usage-content">
                  <ol>
                    <li><strong>输入查询描述：</strong>描述您要查找的视频阶段，例如"应用启动过程"、"用户登录流程"等</li>
                    <li><strong>设置过滤条件：</strong>可选择特定产品名称进行过滤，或调整相似度阈值和返回结果数量</li>
                    <li><strong>查询相似阶段：</strong>系统会在所有已分析的视频中查找语义相似的阶段</li>
                    <li><strong>生成对比报告：</strong>AI会分析相似阶段的差异和共同点，生成详细的对比报告</li>
                  </ol>
                </div>
              </a-collapse-panel>
              
              <a-collapse-panel key="2" header="什么是相似度阈值？">
                <div class="usage-content">
                  <p>相似度阈值决定了返回结果的相关性程度：</p>
                  <ul>
                    <li><strong>0.9-1.0：</strong>非常相似，几乎完全匹配</li>
                    <li><strong>0.8-0.9：</strong>高度相似，主要特征匹配</li>
                    <li><strong>0.7-0.8：</strong>中等相似，部分特征匹配</li>
                    <li><strong>0.6-0.7：</strong>低相似度，可能存在关联</li>
                  </ul>
                </div>
              </a-collapse-panel>
              
              <a-collapse-panel key="3" header="如何提高查询效果？">
                <div class="usage-content">
                  <ul>
                    <li>使用具体、描述性的关键词</li>
                    <li>包含动作词汇，如"启动"、"加载"、"切换"等</li>
                    <li>描述用户行为或界面变化</li>
                    <li>避免过于宽泛的描述</li>
                  </ul>
                </div>
              </a-collapse-panel>
            </a-collapse>
          </a-card>
          
          <!-- RAG分析组件 -->
          <RAGAnalysis />
        </a-col>
      </a-row>
    </div>
  </div>
</template>

<script setup>
import { 
  VideoCameraOutlined, 
  PlusOutlined, 
  InfoCircleOutlined 
} from '@ant-design/icons-vue'
import RAGAnalysis from '../components/RAGAnalysis.vue'
</script>

<style scoped>
.rag-analysis-view {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.page-header {
  background: white;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.page-description {
  margin-top: 16px;
}

.page-description p {
  margin-bottom: 12px;
  color: #666;
  font-size: 14px;
}

.feature-tags {
  margin-top: 8px;
}

.page-content {
  padding: 0 24px 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.usage-guide {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.usage-content {
  font-size: 14px;
  line-height: 1.6;
}

.usage-content ol,
.usage-content ul {
  margin: 0;
  padding-left: 20px;
}

.usage-content li {
  margin-bottom: 8px;
}

.usage-content strong {
  color: #1890ff;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-content {
    padding: 0 16px 16px;
  }
  
  .page-header {
    margin-bottom: 16px;
  }
}
</style>