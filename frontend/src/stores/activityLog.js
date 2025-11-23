import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import api from '../api';

const createFallbackSample = () =>
  Array.from({ length: 30 }).map((_, index) => ({
    id: `sample-${index}`,
    timestamp: new Date(Date.now() - index * 3600_000).toISOString(),
    actor: index % 3 === 0 ? '系統排程' : index % 2 === 0 ? '牧場管理員' : '領頭羊博士 AI',
    message: index % 2 === 0 ? '更新羊群健康指標成功' : '完成日誌同步',
    severity: index % 3 === 0 ? 'info' : index % 3 === 1 ? 'warning' : 'success',
  }));

export const useActivityLogStore = defineStore('activityLog', () => {
  const entries = ref([]);
  const page = ref(0);
  const pageSize = ref(20);
  const isLoading = ref(false);
  const isEnd = ref(false);
  const hasError = ref(false);

  const formattedEntries = computed(() =>
    entries.value.map((entry) => ({
      ...entry,
      timestampLabel: new Date(entry.timestamp).toLocaleString(),
    }))
  );

  function reset() {
    entries.value = [];
    page.value = 0;
    isEnd.value = false;
    hasError.value = false;
  }

  async function fetchNextPage() {
    if (isLoading.value || isEnd.value) return;
    isLoading.value = true;

    try {
      const nextPage = page.value + 1;
      const response = await api.getActivityLogs({ page: nextPage, page_size: pageSize.value });
      const items = response?.items || response || [];

      if (!Array.isArray(items) || items.length === 0) {
        if (page.value === 0 && !response) {
          entries.value = [...createFallbackSample()];
        }
        isEnd.value = true;
        return;
      }

      entries.value = [...entries.value, ...items];
      page.value = nextPage;
      if (items.length < pageSize.value) {
        isEnd.value = true;
      }
    } catch (error) {
      console.error('載入活動日誌失敗', error);
      hasError.value = true;
      if (entries.value.length === 0) {
        entries.value = [...createFallbackSample()];
        isEnd.value = true;
      }
    } finally {
      isLoading.value = false;
    }
  }

  return {
    entries,
    formattedEntries,
    isLoading,
    isEnd,
    hasError,
    fetchNextPage,
    reset,
  };
});
