<script setup>
import { ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  VideoCameraOutlined,
  PlayCircleOutlined,
  InfoCircleOutlined
} from '@ant-design/icons-vue'

const router = useRouter()
const route = useRoute()
const selectedKeys = ref(['videos'])

// 监听路由变化更新选中的菜单项
watch(
  () => route.path,
  (newPath) => {
    if (newPath === '/') {
      selectedKeys.value = ['home']
    } else if (newPath.startsWith('/videos')) {
      selectedKeys.value = ['videos']
    } else if (newPath === '/about') {
      selectedKeys.value = ['about']
    } else {
      selectedKeys.value = []
    }
  },
  { immediate: true }
)
</script>

<template>
  <a-layout id="app">
    <a-layout-header class="header">
      <div class="logo">
        <video-camera-outlined />
        <span>视频管理系统</span>
      </div>
      <a-menu
        v-model:selectedKeys="selectedKeys"
        theme="dark"
        mode="horizontal"
        class="menu"
      >
        <a-menu-item key="home" @click="$router.push('/')">
          <video-camera-outlined />
          首页
        </a-menu-item>
        <a-menu-item key="videos" @click="$router.push('/videos')">
          <play-circle-outlined />
          视频管理
        </a-menu-item>
        <a-menu-item key="about" @click="$router.push('/about')">
          <info-circle-outlined />
          关于
        </a-menu-item>
      </a-menu>
    </a-layout-header>
    <a-layout-content class="content">
      <router-view />
    </a-layout-content>
  </a-layout>
</template>

<style scoped>
#app {
  min-height: 100vh;
}

.header {
  display: flex;
  align-items: center;
  padding: 0 24px;
  background: #001529;
}

.logo {
  display: flex;
  align-items: center;
  color: white;
  font-size: 18px;
  font-weight: bold;
  margin-right: auto;
}

.logo .anticon {
  font-size: 24px;
  margin-right: 8px;
  color: #1890ff;
}

.menu {
  flex: 1;
  justify-content: flex-end;
  border-bottom: none;
}

.content {
  min-height: calc(100vh - 64px);
  background: #f0f2f5;
}

:deep(.ant-layout-header) {
  height: 64px;
  line-height: 64px;
}

:deep(.ant-menu-horizontal) {
  border-bottom: none;
}

:deep(.ant-menu-item) {
  display: flex;
  align-items: center;
}

:deep(.ant-menu-item .anticon) {
  margin-right: 8px;
}
</style>
