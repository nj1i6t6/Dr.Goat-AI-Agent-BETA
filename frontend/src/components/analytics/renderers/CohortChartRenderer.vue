<template>
  <div ref="chartRef" class="chart-shell" />
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useLazyCharts } from '@/composables/useLazyCharts';
import { formatCohortGroupLabel } from '@/utils/analyticsFormatting';
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

  const categories = props.items.map((item) => formatCohortGroupLabel(item));
  const profits = props.items.map((item) => Number(item.metrics?.net_profit ?? 0));

  const axisLineColor = readCssVar('--aurora-border', 'rgba(148, 163, 184, 0.4)');
  const axisLabelColor = readCssVar('--aurora-text-muted', '#94a3b8');
  const gridlineColor = readCssVar('--aurora-gridline', 'rgba(148, 163, 184, 0.25)');
  const accentStart = readCssVar('--aurora-accent-strong', '#0ea5e9');
  const accentEnd = readCssVar('--aurora-accent-secondary', '#a855f7');

  chart.setOption(
    {
      grid: {
        left: '5%',
        right: '5%',
        top: 40,
        bottom: 40,
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: readCssVar('--aurora-surface-strong', 'rgba(255,255,255,0.92)'),
        borderColor: axisLineColor,
        textStyle: { color: readCssVar('--aurora-text-primary', '#1f2937') },
      },
      xAxis: {
        type: 'category',
        data: categories,
        axisLine: { lineStyle: { color: axisLineColor } },
        axisLabel: { color: axisLabelColor },
      },
      yAxis: {
        type: 'value',
        name: '淨收益 (TWD)',
        axisLine: { lineStyle: { color: axisLineColor } },
        splitLine: { lineStyle: { color: gridlineColor } },
        axisLabel: { color: axisLabelColor },
      },
      series: [
        {
          name: '淨收益',
          type: 'bar',
          data: profits,
          itemStyle: {
            borderRadius: [10, 10, 0, 0],
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: withAlpha(accentStart, 0.95) },
                { offset: 1, color: withAlpha(accentEnd, 0.65) },
              ],
            },
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
