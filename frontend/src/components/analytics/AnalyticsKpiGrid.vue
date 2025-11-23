<template>
  <el-row :gutter="16" class="kpi-row">
    <el-col v-for="card in cards" :key="card.label" :lg="8" :md="12" :sm="12" :xs="24">
      <el-card shadow="hover" class="kpi-card">
        <div class="kpi-label">{{ card.label }}</div>
        <div class="kpi-value">
          {{ formatNumber(card.value) }}
          <span class="kpi-unit">{{ card.unit }}</span>
        </div>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup>
import { formatDisplayNumber } from '../../utils/analyticsFormatting'

const { cards } = defineProps({
  cards: {
    type: Array,
    default: () => [],
  },
})

const formatNumber = (value) => formatDisplayNumber(value)
</script>
