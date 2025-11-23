<template>
  <BaseAuroraCard :title="title" :subtitle="subtitle">
    <template v-if="$slots.actions" #actions>
      <slot name="actions" />
    </template>

    <div ref="containerRef" class="log-table-container">
      <div v-if="store.hasError" class="error-banner">
        <el-icon><Warning /></el-icon>
        <span>暫時無法從伺服器取得最新日誌，已顯示快取資料。</span>
      </div>

      <el-table-v2
        v-if="rows.length"
        class="aurora-log-table"
        :columns="resolvedColumns"
        :data="rows"
        :width="tableWidth"
        :height="height"
        fixed
        :estimated-row-height="estimatedRowHeight"
        @scroll="handleScroll"
      />

      <el-empty v-else description="尚無活動紀錄" />

      <div v-if="store.isLoading" class="loading-indicator">載入更多...</div>
    </div>
  </BaseAuroraCard>
</template>

<script setup>
import { computed, h, onMounted, ref } from 'vue';
import { useElementSize, useThrottleFn } from '@vueuse/core';
import { Warning } from '@element-plus/icons-vue';
import { ElTag } from 'element-plus';
import BaseAuroraCard from '@/components/common/BaseAuroraCard.vue';
import { useActivityLogStore } from '@/stores/activityLog';

const props = defineProps({
  title: {
    type: String,
    default: '即時活動日誌',
  },
  subtitle: {
    type: String,
    default: '追蹤代理動作、排程與自動化事件',
  },
  height: {
    type: Number,
    default: 420,
  },
  loadMoreOffset: {
    type: Number,
    default: 120,
  },
  columns: {
    type: Array,
    default: null,
  },
  estimatedRowHeight: {
    type: Number,
    default: 54,
  },
});

const store = useActivityLogStore();
const containerRef = ref(null);
const { width } = useElementSize(containerRef);

const tableWidth = computed(() => Math.max(width.value, 480));

const severityTagType = {
  success: 'success',
  info: 'info',
  warning: 'warning',
  danger: 'danger',
  error: 'danger',
};

const defaultColumns = [
  {
    key: 'timestamp',
    dataKey: 'timestampLabel',
    title: '時間',
    width: 200,
  },
  {
    key: 'actor',
    dataKey: 'actor',
    title: '觸發者',
    width: 160,
  },
  {
    key: 'message',
    dataKey: 'message',
    title: '事件',
    width: 320,
  },
  {
    key: 'severity',
    dataKey: 'severity',
    title: '狀態',
    width: 120,
    cellRenderer: ({ cellData }) => {
      const type = severityTagType[cellData] || 'info';
      const label = (cellData || 'info').toUpperCase();
      return h(
        ElTag,
        {
          effect: 'light',
          type,
          size: 'small',
          round: true,
        },
        () => label
      );
    },
  },
];

const resolvedColumns = computed(() => props.columns || defaultColumns);

const rows = computed(() => store.formattedEntries);

const handleScroll = useThrottleFn(async ({ scrollTop }) => {
  if (store.isLoading || store.isEnd) return;

  const bodyEl = containerRef.value?.querySelector('.el-table-v2__body');
  if (!bodyEl) return;

  const distanceToBottom = bodyEl.scrollHeight - scrollTop - bodyEl.clientHeight;
  if (distanceToBottom <= props.loadMoreOffset) {
    await store.fetchNextPage();
  }
}, 200);

onMounted(() => {
  if (!store.entries.length) {
    store.fetchNextPage();
  }
});
</script>

<style scoped>
.log-table-container {
  position: relative;
  min-height: 240px;
}

.aurora-log-table {
  border-radius: calc(var(--aurora-card-radius) - 6px);
  border: 1px solid rgba(255, 255, 255, 0.4);
  overflow: hidden;
}

.loading-indicator {
  text-align: center;
  padding: 1rem 0;
  color: var(--aurora-accent);
  font-weight: 600;
}

.error-banner {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 14px;
  background: rgba(249, 115, 22, 0.14);
  color: var(--aurora-warning);
  border: 1px solid rgba(249, 115, 22, 0.3);
}

.error-banner :deep(svg) {
  width: 18px;
  height: 18px;
}

:deep(.el-table-v2__header-wrapper) {
  /* 覆寫 Element Plus 預設背景，使表頭融入 Aurora 玻璃質感卡片 */
  background: transparent;
}

:deep(.el-table-v2__row) {
  transition: background var(--aurora-transition-base);
}

:deep(.el-table-v2__row:hover) {
  background: rgba(56, 189, 248, 0.08);
}

:deep(.el-table-v2__header-cell) {
  color: var(--aurora-text-secondary);
  font-weight: 600;
}

:deep(.el-table-v2__row-cell) {
  color: var(--aurora-text-primary);
}

:deep(.el-tag) {
  border-radius: 999px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
</style>
