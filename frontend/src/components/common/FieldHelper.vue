<template>
  <el-tooltip :content="content" placement="top" :disabled="!content">
    <el-icon class="field-helper-icon" :class="{ 'has-help': !!content }">
      <QuestionFilled />
    </el-icon>
  </el-tooltip>
</template>

<script setup>
import { QuestionFilled } from '@element-plus/icons-vue'

defineProps({
  content: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.field-helper-icon {
  margin-left: 4px;
  color: #909399;
  cursor: help;
  font-size: 14px;
}

.field-helper-icon.has-help:hover {
  color: #409eff;
}

.field-helper-icon:not(.has-help) {
  display: none;
}
</style>