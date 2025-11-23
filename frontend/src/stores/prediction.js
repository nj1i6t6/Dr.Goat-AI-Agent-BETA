import { defineStore } from 'pinia';
import { ref } from 'vue';
import api from '../api';

export const usePredictionStore = defineStore('prediction', () => {
  // --- State ---
  const selectedEarTag = ref('');
  const targetDays = ref(30);
  const isLoading = ref(false);
  const result = ref(null);
  const chartData = ref(null);
  const error = ref('');

  // --- Actions ---
  function setSelectedEarTag(val) {
    selectedEarTag.value = val || '';
  }

  function setTargetDays(days) {
    if (days === undefined) {
      return;
    }
    targetDays.value = days;
  }

  async function startPrediction(apiKey) {
    if (!selectedEarTag.value) {
      throw new Error('請先選擇羊隻耳號');
    }
    if (targetDays.value == null) {
      throw new Error('請選擇可用的預測天數');
    }
    isLoading.value = true;
    result.value = null;
    chartData.value = null;
    error.value = '';
    try {
      const prediction = await api.getSheepPrediction(
        selectedEarTag.value,
        targetDays.value,
        apiKey
      );
      result.value = prediction;

      // 預先抓取圖表資料以利返回頁面時立即渲染
      chartData.value = await api.getPredictionChartData(
        selectedEarTag.value,
        targetDays.value,
        apiKey
      );
    } catch (err) {
      error.value = err?.message || '預測失敗';
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  function clear() {
    selectedEarTag.value = '';
    targetDays.value = 30;
    isLoading.value = false;
    result.value = null;
    chartData.value = null;
    error.value = '';
  }

  return {
    // state
    selectedEarTag,
    targetDays,
    isLoading,
    result,
    chartData,
    error,
    // actions
    setSelectedEarTag,
    setTargetDays,
    startPrediction,
    clear,
  };
});
