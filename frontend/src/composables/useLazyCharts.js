import { onBeforeUnmount, ref, shallowRef, watch } from 'vue';
import { useIntersectionObserver } from '@vueuse/core';

const defaultOptions = {
  autoInit: true,
  threshold: 0.15,
};

export function useLazyCharts(targetRef, options = {}) {
  const config = { ...defaultOptions, ...options };
  const chartInstance = shallowRef(null);
  const loading = ref(false);
  const hasError = ref(null);
  const hasLoadedOnce = ref(false);
  const isIntersecting = ref(false);

  const ensureChart = async () => {
    if (!targetRef?.value) return null;
    if (chartInstance.value) return chartInstance.value;
    if (loading.value) return null;

    loading.value = true;
    try {
      const echarts = await import('echarts');
      chartInstance.value = echarts.init(targetRef.value, null, config.initOptions);
      hasLoadedOnce.value = true;
      hasError.value = null;
    } catch (error) {
      hasError.value = error;
      throw error;
    } finally {
      loading.value = false;
    }

    return chartInstance.value;
  };

  const dispose = () => {
    if (chartInstance.value) {
      chartInstance.value.dispose();
      chartInstance.value = null;
    }
  };

  const refresh = async () => {
    if (!targetRef?.value) return;
    if (!chartInstance.value) {
      await ensureChart();
      return;
    }
    chartInstance.value.resize();
  };

  if (config.autoInit && typeof window !== 'undefined') {
    const { stop } = useIntersectionObserver(
      targetRef,
      ([entry]) => {
        if (!entry) return;
        isIntersecting.value = entry.isIntersecting;
        if (entry.isIntersecting) {
          ensureChart();
          stop();
        }
      },
      { threshold: config.threshold }
    );
  }

  watch(
    () => targetRef?.value,
    (value) => {
      if (value && (isIntersecting.value || !config.autoInit)) {
        ensureChart();
      }
    }
  );

  onBeforeUnmount(() => {
    dispose();
  });

  return {
    chartInstance,
    loading,
    hasError,
    hasLoadedOnce,
    ensureChart,
    refresh,
    dispose,
  };
}
