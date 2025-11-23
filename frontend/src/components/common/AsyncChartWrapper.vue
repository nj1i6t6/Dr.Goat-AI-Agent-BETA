<template>
  <div ref="target" class="async-chart-wrapper">
    <component v-if="targetIsVisible" :is="ChartComponent" v-bind="componentProps" />
  </div>
</template>

<script setup>
import { computed, defineAsyncComponent, h, ref } from 'vue';
import { useIntersectionObserver } from '@vueuse/core';
import { ElResult, ElSkeleton } from 'element-plus';

const props = defineProps({
  loader: {
    type: Function,
    required: true,
  },
  componentProps: {
    type: Object,
    default: () => ({}),
  },
  delay: {
    type: Number,
    default: 200,
  },
  timeout: {
    type: Number,
    default: 15000,
  },
  errorTitle: {
    type: String,
    default: '圖表載入失敗',
  },
  errorSubtitle: {
    type: String,
    default: '請稍後再試或聯繫管理員',
  },
});

const target = ref(null);
const targetIsVisible = ref(false);

const { stop } = useIntersectionObserver(target, ([entry]) => {
  if (entry?.isIntersecting) {
    targetIsVisible.value = true;
    stop();
  }
});

const errorComponent = {
  setup() {
    const { errorTitle, errorSubtitle } = props;
    return () =>
      h(ElResult, {
        icon: 'error',
        title: errorTitle,
        subTitle: errorSubtitle,
      });
  },
};

const ChartComponent = defineAsyncComponent({
  loader: props.loader,
  loadingComponent: ElSkeleton,
  delay: props.delay,
  errorComponent,
  timeout: props.timeout,
});

const componentProps = computed(() => props.componentProps);
</script>

<style scoped>
.async-chart-wrapper {
  min-height: 220px;
  display: grid;
  place-items: center;
}
</style>
