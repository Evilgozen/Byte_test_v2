<script setup>
import { useRouter } from 'vue-router'
import {
  VideoCameraOutlined,
  PlayCircleOutlined,
  ScissorOutlined,
  BarChartOutlined,
  FileTextOutlined,
  RocketOutlined,
  SafetyOutlined,
  ThunderboltOutlined
} from '@ant-design/icons-vue'

const router = useRouter()

const features = [
  {
    icon: VideoCameraOutlined,
    title: '视频文件管理',
    description: '支持多种视频格式的上传、存储和管理，提供完整的文件信息展示',
    color: '#1890ff'
  },
  {
    icon: ScissorOutlined,
    title: '智能帧提取',
    description: '自动提取视频关键帧，支持自定义时间间隔和帧数限制',
    color: '#52c41a'
  },
  {
    icon: BarChartOutlined,
    title: '性能分析',
    description: '深度分析视频性能指标，生成详细的统计报告和可视化图表',
    color: '#faad14'
  },
  {
    icon: FileTextOutlined,
    title: 'AI行为描述',
    description: '基于AI技术自动生成视频帧的行为描述和场景分析',
    color: '#722ed1'
  }
]

const quickActions = [
  {
    title: '上传视频',
    description: '快速上传新的视频文件',
    action: () => router.push('/videos'),
    type: 'primary'
  },
  {
    title: '查看视频库',
    description: '浏览所有已上传的视频',
    action: () => router.push('/videos'),
    type: 'default'
  }
]
</script>

<template>
  <div class="home-container">
    <!-- 英雄区域 -->
    <div class="hero-section">
      <div class="hero-content">
        <div class="hero-text">
          <h1 class="hero-title">
            <video-camera-outlined class="hero-icon" />
            视频分析管理系统
          </h1>
          <p class="hero-subtitle">
            专业的视频录屏分析平台，提供智能帧提取、AI行为描述、阶段识别和性能对比功能
          </p>
          <div class="hero-actions">
            <a-button 
              v-for="action in quickActions" 
              :key="action.title"
              :type="action.type" 
              size="large" 
              @click="action.action"
              class="action-btn"
            >
              <play-circle-outlined />
              {{ action.title }}
            </a-button>
          </div>
        </div>
        <div class="hero-visual">
          <div class="visual-card">
            <div class="visual-content">
              <rocket-outlined class="visual-icon" />
              <h3>高效分析</h3>
              <p>快速处理视频文件</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 功能特性 -->
    <div class="features-section">
      <div class="section-header">
        <h2>核心功能</h2>
        <p>为您提供全方位的视频分析解决方案</p>
      </div>
      <a-row :gutter="[24, 24]" class="features-grid">
        <a-col :xs="24" :sm="12" :lg="6" v-for="feature in features" :key="feature.title">
          <a-card class="feature-card" hoverable>
            <div class="feature-content">
              <div class="feature-icon" :style="{ color: feature.color }">
                <component :is="feature.icon" />
              </div>
              <h3 class="feature-title">{{ feature.title }}</h3>
              <p class="feature-description">{{ feature.description }}</p>
            </div>
          </a-card>
        </a-col>
      </a-row>
    </div>

    <!-- 统计信息 -->
    <div class="stats-section">
      <a-row :gutter="24">
        <a-col :xs="24" :sm="8">
          <a-statistic
            title="支持格式"
            :value="10"
            suffix="+"
            :value-style="{ color: '#1890ff' }"
          >
            <template #prefix>
              <safety-outlined />
            </template>
          </a-statistic>
        </a-col>
        <a-col :xs="24" :sm="8">
          <a-statistic
            title="处理速度"
            :value="99.9"
            suffix="%"
            :value-style="{ color: '#52c41a' }"
          >
            <template #prefix>
              <thunderbolt-outlined />
            </template>
          </a-statistic>
        </a-col>
        <a-col :xs="24" :sm="8">
          <a-statistic
            title="分析精度"
            :value="95"
            suffix="%"
            :value-style="{ color: '#faad14' }"
          >
            <template #prefix>
              <bar-chart-outlined />
            </template>
          </a-statistic>
        </a-col>
      </a-row>
    </div>

    <!-- 快速开始 -->
    <div class="getting-started">
      <a-card title="快速开始" class="start-card">
        <div class="start-content">
          <div class="start-steps">
            <a-steps direction="vertical" size="small">
              <a-step title="上传视频" description="选择并上传您的视频文件" />
              <a-step title="提取帧" description="自动提取关键帧进行分析" />
              <a-step title="查看结果" description="获取详细的分析报告" />
            </a-steps>
          </div>
          <div class="start-action">
            <a-button type="primary" size="large" @click="router.push('/videos')">
              立即开始
              <template #icon>
                <rocket-outlined />
              </template>
            </a-button>
          </div>
        </div>
      </a-card>
    </div>
  </div>
</template>

<style scoped>
.home-container {
  padding: 0;
}

/* 英雄区域 */
.hero-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 80px 24px;
  text-align: center;
}

.hero-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 60px;
}

.hero-text {
  flex: 1;
  text-align: left;
}

.hero-title {
  font-size: 3.5rem;
  font-weight: bold;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.hero-icon {
  font-size: 4rem;
  color: #40a9ff;
}

.hero-subtitle {
  font-size: 1.25rem;
  margin-bottom: 40px;
  opacity: 0.9;
  line-height: 1.6;
}

.hero-actions {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.action-btn {
  height: 48px;
  padding: 0 32px;
  font-size: 16px;
  border-radius: 24px;
}

.hero-visual {
  flex: 0 0 300px;
}

.visual-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 40px;
  text-align: center;
}

.visual-icon {
  font-size: 4rem;
  color: #40a9ff;
  margin-bottom: 16px;
}

.visual-content h3 {
  color: white;
  margin-bottom: 8px;
  font-size: 1.5rem;
}

.visual-content p {
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
}

/* 功能特性 */
.features-section {
  padding: 80px 24px;
  background: white;
}

.section-header {
  text-align: center;
  margin-bottom: 60px;
}

.section-header h2 {
  font-size: 2.5rem;
  margin-bottom: 16px;
  color: #262626;
}

.section-header p {
  font-size: 1.125rem;
  color: #8c8c8c;
  margin: 0;
}

.features-grid {
  max-width: 1200px;
  margin: 0 auto;
}

.feature-card {
  height: 100%;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}

.feature-content {
  text-align: center;
  padding: 24px 16px;
}

.feature-icon {
  font-size: 3rem;
  margin-bottom: 20px;
}

.feature-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 12px;
  color: #262626;
}

.feature-description {
  color: #8c8c8c;
  line-height: 1.6;
  margin: 0;
}

/* 统计信息 */
.stats-section {
  padding: 60px 24px;
  background: #fafafa;
}

.stats-section .ant-row {
  max-width: 800px;
  margin: 0 auto;
}

/* 快速开始 */
.getting-started {
  padding: 80px 24px;
  background: white;
}

.start-card {
  max-width: 800px;
  margin: 0 auto;
  border-radius: 12px;
}

.start-content {
  display: flex;
  align-items: center;
  gap: 60px;
}

.start-steps {
  flex: 1;
}

.start-action {
  flex: 0 0 auto;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .hero-content {
    flex-direction: column;
    text-align: center;
  }
  
  .hero-text {
    text-align: center;
  }
  
  .hero-title {
    font-size: 2.5rem;
    justify-content: center;
  }
  
  .hero-visual {
    flex: none;
  }
  
  .start-content {
    flex-direction: column;
    gap: 40px;
  }
  
  .features-section,
  .stats-section,
  .getting-started {
    padding: 40px 16px;
  }
}
</style>
