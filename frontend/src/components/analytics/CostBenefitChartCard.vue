<template>
  <BaseAuroraCard :title="title">
    <template v-if="hasData">
      <AsyncChartWrapper :loader="chartLoader" :component-props="{ items }" />
    </template>
    <div v-else class="empty-wrapper">
      <el-empty :description="emptyDescription">
        <template #extra>
          <el-button :type="emptyButtonType" @click="$emit('empty-action')">
            {{ emptyActionLabel }}
          </el-button>
        </template>
      </el-empty>
    </div>
  </BaseAuroraCard>
</template>

<script setup>
import { computed } from 'vue';
import AsyncChartWrapper from '@/components/common/AsyncChartWrapper.vue';
import BaseAuroraCard from '@/components/common/BaseAuroraCard.vue';

const props = defineProps({
  title: {
    type: String,
    default: '成本 / 收益趨勢',
  },
  items: {
    type: Array,
    default: () => [],
  },
  emptyActionLabel: {
    type: String,
    required: true,
  },
  emptyButtonType: {
    type: String,
    default: 'primary',
  },
  emptyDescription: {
    type: String,
    default: '尚無資料',
  },
});

const hasData = computed(() => (props.items ?? []).length > 0);

const chartLoader = () =>
  import(/* webpackChunkName: "cost-benefit-chart-renderer" */ './renderers/CostBenefitChartRenderer.vue');
</script>

<style scoped>
.empty-wrapper {
  display: grid;
  place-items: center;
  min-height: 240px;
  color: var(--aurora-text-muted);
}
</style>
