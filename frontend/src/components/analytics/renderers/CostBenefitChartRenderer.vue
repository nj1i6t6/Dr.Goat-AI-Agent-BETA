<template>
  <div ref="chartRef" class="chart-shell" />
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useLazyCharts } from '@/composables/useLazyCharts';
import { useTheme } from '@/composables/useTheme';
import { readCssVar, withAlpha } from '@/utils/themeColors';

const props = defineProps({
  items: {
    type: Array,
    default: () => [],
  },
});

const chartRef = ref(null);
const { ensureChart, dispose } = useLazyCharts(chartRef, { initOptions: { renderer: 'canvas' } });
const { isDark } = useTheme();

const hasData = computed(() => (props.items ?? []).length > 0);

const renderChart = async () => {
  if (!hasData.value) {
    dispose();
    return;
  }

  const chart = await ensureChart();
  if (!chart) return;

  const labels = props.items.map((item) => item.group);
  const costData = props.items.map((item) => Number(item.metrics?.total_cost ?? 0));
  const revenueData = props.items.map((item) => Number(item.metrics?.total_revenue ?? 0));

  const axisLineColor = readCssVar('--aurora-border', 'rgba(148, 163, 184, 0.4)');
  const axisLabelColor = readCssVar('--aurora-text-muted', '#94a3b8');
  const gridlineColor = readCssVar('--aurora-gridline', 'rgba(148, 163, 184, 0.25)');
  const accentPrimary = readCssVar('--aurora-accent-strong', '#0ea5e9');
  const accentSecondary = readCssVar('--aurora-accent-secondary', '#a855f7');

  chart.setOption(
    {
      grid: {
        left: '6%',
        right: '6%',
        top: 48,
        bottom: 40,
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: readCssVar('--aurora-surface-strong', 'rgba(255,255,255,0.92)'),
        borderColor: axisLineColor,
        textStyle: { color: readCssVar('--aurora-text-primary', '#1f2937') },
      },
      legend: {
        data: ['總成本', '總收益'],
        textStyle: { color: axisLabelColor },
      },
      xAxis: {
        type: 'category',
        data: labels,
        axisLine: { lineStyle: { color: axisLineColor } },
        axisLabel: { color: axisLabelColor },
      },
      yAxis: {
        type: 'value',
        axisLine: { lineStyle: { color: axisLineColor } },
        splitLine: { lineStyle: { color: gridlineColor } },
        axisLabel: { color: axisLabelColor },
      },
      series: [
        {
          name: '總成本',
          type: 'line',
          smooth: true,
          data: costData,
          lineStyle: {
            width: 3,
            color: withAlpha(accentPrimary, 0.85),
          },
          areaStyle: {
            color: withAlpha(accentPrimary, 0.18),
          },
        },
        {
          name: '總收益',
          type: 'line',
          smooth: true,
          data: revenueData,
          lineStyle: {
            width: 3,
            color: withAlpha(accentSecondary, 0.85),
          },
          areaStyle: {
            color: withAlpha(accentSecondary, 0.18),
          },
        },
      ],
    },
    { notMerge: true }
  );
};

watch(
  () => props.items,
  () => {
    renderChart();
  },
  { deep: true }
);

watch(isDark, () => {
  renderChart();
});

onMounted(() => {
  renderChart();
});

onBeforeUnmount(() => {
  dispose();
});
</script>

<style scoped>
.chart-shell {
  width: 100%;
  min-height: 320px;
}
</style>
