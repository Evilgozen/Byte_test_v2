<template>
  <a-modal
    v-model:open="visible"
    title="提取视频帧"
    :confirm-loading="loading"
    @ok="handleExtract"
    @cancel="handleCancel"
    width="600px"
  >
    <div class="frame-extract-form">
      <a-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        layout="vertical"
      >
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="提取间隔（秒）" name="interval">
              <a-input-number
                v-model:value="formData.interval"
                :min="0.1"
                :max="60"
                :step="0.1"
                placeholder="每隔多少秒提取一帧"
                style="width: 100%"
              />
              <div class="form-help">设置为0则提取所有帧</div>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="最大帧数" name="max_frames">
              <a-input-number
                v-model:value="formData.max_frames"
                :min="1"
                :max="10000"
                placeholder="最多提取多少帧"
                style="width: 100%"
              />
              <div class="form-help">留空则不限制</div>
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="开始时间（秒）" name="start_time">
          <a-input-number
            v-model:value="formData.start_time"
            :min="0"
            :max="videoDuration"
            :step="0.1"
            placeholder="从视频的第几秒开始提取"
            style="width: 100%"
          />
          <div class="form-help">留空则从视频开始处提取</div>
        </a-form-item>

        <a-form-item label="结束时间（秒）" name="end_time">
          <a-input-number
            v-model:value="formData.end_time"
            :min="0"
            :max="videoDuration"
            :step="0.1"
            placeholder="提取到视频的第几秒"
            style="width: 100%"
          />
          <div class="form-help">留空则提取到视频结束</div>
        </a-form-item>
      </a-form>

      <!-- 视频信息 -->
      <div v-if="video" class="video-info">
        <a-divider>视频信息</a-divider>
        <a-descriptions :column="2" size="small">
          <a-descriptions-item label="文件名">{{ video.original_filename }}</a-descriptions-item>
          <a-descriptions-item label="时长">{{ formatDuration(video.duration) }}</a-descriptions-item>
          <a-descriptions-item label="分辨率">{{ video.width }}x{{ video.height }}</a-descriptions-item>
          <a-descriptions-item label="帧率">{{ video.fps }} fps</a-descriptions-item>
        </a-descriptions>
      </div>

      <!-- 预估信息 -->
      <div class="extract-preview">
        <a-divider>预估结果</a-divider>
        <a-alert
          :message="previewMessage"
          type="info"
          show-icon
        />
      </div>
    </div>
  </a-modal>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useVideoStore } from '../stores/video'

const props = defineProps({
  open: {
    type: Boolean,
    default: false
  },
  video: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:open', 'extract-success'])

const videoStore = useVideoStore()
const formRef = ref()
const loading = ref(false)

// 表单数据
const formData = ref({
  interval: 1,
  max_frames: null,
  start_time: null,
  end_time: null
})

// 表单验证规则
const rules = {
  interval: [
    { required: true, message: '请输入提取间隔', type: 'number' },
    { min: 0.1, message: '间隔不能小于0.1秒', type: 'number' }
  ]
}

// 计算属性
const visible = computed({
  get: () => props.open,
  set: (value) => emit('update:open', value)
})

const videoDuration = computed(() => {
  return props.video?.duration || 0
})

const previewMessage = computed(() => {
  if (!props.video) return '请选择视频文件'
  
  const duration = props.video.duration
  const startTime = formData.value.start_time || 0
  const endTime = formData.value.end_time || duration
  const interval = formData.value.interval || 1
  const maxFrames = formData.value.max_frames
  
  const extractDuration = Math.max(0, endTime - startTime)
  let estimatedFrames = Math.floor(extractDuration / interval) + 1
  
  if (maxFrames && estimatedFrames > maxFrames) {
    estimatedFrames = maxFrames
  }
  
  return `预计提取 ${estimatedFrames} 帧，时间范围：${formatDuration(startTime)} - ${formatDuration(endTime)}`
})

// 方法
const formatDuration = (seconds) => {
  if (!seconds) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

const handleExtract = async () => {
  try {
    await formRef.value.validate()
    
    loading.value = true
    
    const extractData = {
      interval: formData.value.interval,
      max_frames: formData.value.max_frames || undefined,
      start_time: formData.value.start_time || undefined,
      end_time: formData.value.end_time || undefined
    }
    
    const result = await videoStore.extractFrames(props.video.id, extractData)
    
    emit('extract-success', result)
    visible.value = false
    resetForm()
    
  } catch (error) {
    console.error('Extract frames failed:', error)
  } finally {
    loading.value = false
  }
}

const handleCancel = () => {
  visible.value = false
  resetForm()
}

const resetForm = () => {
  formData.value = {
    interval: 1,
    max_frames: null,
    start_time: null,
    end_time: null
  }
  formRef.value?.resetFields()
}

// 监听视频变化，重置表单
watch(() => props.video, (newVideo) => {
  if (newVideo) {
    resetForm()
  }
})
</script>

<style scoped>
.frame-extract-form {
  padding: 16px 0;
}

.form-help {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.video-info {
  margin-top: 24px;
}

.extract-preview {
  margin-top: 24px;
}

:deep(.ant-descriptions-item-label) {
  font-weight: 500;
}
</style>