<template>
  <div v-if="streamGenerating && streamReport.length === 0" class="stream-status">
    <a-divider>正在生成报告...</a-divider>
    <a-card title="AI正在分析" class="stream-card">
      <a-spin size="large">
        <div class="stream-progress">
          <p>{{ streamStatus }}</p>
          <a-progress :percent="streamProgress" status="active" />
        </div>
      </a-spin>
      <template #extra>
        <a-button size="small" danger @click="$emit('stop-generation')">
          停止生成
        </a-button>
      </template>
    </a-card>
  </div>
</template>

<script setup>
defineProps({
  streamGenerating: {
    type: Boolean,
    default: false
  },
  streamReport: {
    type: String,
    default: ''
  },
  streamStatus: {
    type: String,
    default: ''
  },
  streamProgress: {
    type: Number,
    default: 0
  }
})

defineEmits(['stop-generation'])
</script>

<style scoped>
.stream-status {
  margin-top: 24px;
}

.stream-card {
  text-align: center;
}

.stream-progress {
  padding: 20px;
}

.stream-progress p {
  margin-bottom: 16px;
  font-size: 16px;
  color: #1890ff;
}
</style>