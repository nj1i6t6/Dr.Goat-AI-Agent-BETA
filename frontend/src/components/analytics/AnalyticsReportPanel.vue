<template>
  <el-card class="form-card" shadow="never">
    <template #header>
      <span>AI 報告</span>
    </template>
    <el-form label-width="80px">
      <el-form-item label="API Key">
        <el-input v-model="apiKey" placeholder="輸入 X-Api-Key" />
      </el-form-item>
      <el-form-item label="備註">
        <el-input v-model="notes" type="textarea" :rows="2" placeholder="可選的補充說明" />
      </el-form-item>
      <el-text class="helper-text" size="small">使用下方浮動按鈕即可即時產生報告</el-text>
      <div class="report-actions">
        <el-button text type="primary" :disabled="!hasMarkdown" @click="copyReport">複製 Markdown</el-button>
        <el-button text type="primary" :disabled="!hasMarkdown" @click="downloadReport">下載報告</el-button>
      </div>
    </el-form>
    <div v-if="reportState.html" class="report-preview" v-html="reportState.html"></div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import { ElMessage } from 'element-plus'

const apiKey = defineModel('apiKey', { type: String, default: '' })
const notes = defineModel('notes', { type: String, default: '' })

const props = defineProps({
  reportState: {
    type: Object,
    required: true,
  },
})

const hasMarkdown = computed(() => Boolean(props.reportState?.markdown))

const copyReport = async () => {
  if (!props.reportState?.markdown) return
  try {
    await navigator.clipboard.writeText(props.reportState.markdown)
    ElMessage.success('已複製 Markdown')
  } catch (error) {
    ElMessage.error('複製失敗，請手動選取內容')
  }
}

const downloadReport = () => {
  if (!props.reportState?.markdown) return
  const blob = new Blob([props.reportState.markdown], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `analytics-report-${Date.now()}.md`
  link.click()
  URL.revokeObjectURL(url)
}
</script>
