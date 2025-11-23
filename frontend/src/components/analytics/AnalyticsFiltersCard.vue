<template>
  <el-card class="filters-card" shadow="never">
    <template #header>
      <div class="card-header">
        <span>分析篩選條件</span>
      </div>
    </template>
    <el-form label-width="90px" :model="filters" class="filters-form">
      <el-row :gutter="12">
        <el-col :md="12" :sm="24">
          <el-form-item label="時間範圍">
            <el-date-picker
              v-model="filters.timeRange"
              type="daterange"
              range-separator="至"
              start-placeholder="開始日期"
              end-placeholder="結束日期"
              value-format="YYYY-MM-DD"
              unlink-panels
            />
          </el-form-item>
        </el-col>
        <el-col :md="12" :sm="24">
          <el-form-item label="聚合維度">
            <el-select v-model="filters.cohortBy" multiple collapse-tags placeholder="選擇維度">
              <el-option
                v-for="item in dimensionOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :md="12" :sm="24">
          <el-form-item label="指標">
            <el-select v-model="filters.metrics" multiple collapse-tags placeholder="選擇 KPI">
              <el-option
                v-for="item in metricOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :md="12" :sm="24">
          <el-form-item label="成本分類">
            <el-select v-model="filters.categories" multiple collapse-tags placeholder="全部">
              <el-option label="飼料" value="feed" />
              <el-option label="保健" value="health" />
              <el-option label="人工" value="labor" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>
  </el-card>
</template>

<script setup>
const filters = defineModel('filters', { type: Object, required: true })

defineProps({
  dimensionOptions: {
    type: Array,
    required: true,
  },
  metricOptions: {
    type: Array,
    required: true,
  },
})
</script>
