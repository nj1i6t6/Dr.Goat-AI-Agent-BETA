<template>
  <el-card shadow="never" class="analytics-record-table">
    <template #header>
      <span>{{ title }}</span>
    </template>
    <el-table :data="entries" size="small" height="260">
      <el-table-column prop="recorded_at" label="日期" width="120" />
      <el-table-column prop="category" label="分類" />
      <el-table-column prop="amount" label="金額" width="100" />
      <el-table-column prop="notes" label="備註" />
      <el-table-column label="操作" width="80">
        <template #default="scope">
          <el-button type="danger" size="small" link @click="emitDelete(scope.row.id)">
            刪除
          </el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty :description="emptyDescription">
          <template #extra>
            <el-button :type="ctaType" @click="emit('cta-click')">{{ ctaLabel }}</el-button>
          </template>
        </el-empty>
      </template>
    </el-table>
  </el-card>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  entries: { type: Array, default: () => [] },
  ctaLabel: { type: String, required: true },
  ctaType: { type: String, default: 'primary' },
  emptyDescription: { type: String, default: '尚無資料' },
})

const emit = defineEmits(['delete', 'cta-click'])

const emitDelete = (id) => {
  if (id === undefined || id === null) {
    return
  }
  emit('delete', id)
}
</script>

<style scoped>
.analytics-record-table :deep(.el-card__header) {
  font-weight: 600;
}
</style>
