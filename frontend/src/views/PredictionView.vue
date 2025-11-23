<template>
  <div class="prediction-page">
    <h1 class="page-title">
      <el-icon><TrendCharts /></el-icon>
      羊隻生長預測
    </h1>

    <el-card shadow="never">
      <template #header>
        <div class="card-header">智慧預測系統</div>
      </template>

      <div class="sheep-selection-area">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="選擇羊隻耳號">
              <el-autocomplete
                v-model="selectedEarTag"
                :fetch-suggestions="querySearch"
                placeholder="輸入耳號搜尋羊隻"
                clearable
                style="width: 100%"
                @select="handleSelect"
                @clear="clearSelection"
              >
                <template #default="{ item }">
                  <div class="ear-tag-suggestion">
                    <span class="ear-tag">{{ item.value }}</span>
                    <span class="sheep-info">{{ item.breed }} | {{ item.sex }}</span>
                  </div>
                </template>
              </el-autocomplete>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="預測時長">
              <el-select
                v-model="targetDays"
                :placeholder="eligibleTargetOptions.length ? '選擇預測天數' : '無可用預測天數'"
                :disabled="eligibleTargetOptions.length === 0"
                style="width: 100%"
              >
                <el-option
                  v-for="option in eligibleTargetOptions"
                  :key="option"
                  :label="`預測${option}天後`"
                  :value="option"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-form-item label=" ">
              <el-button
                type="primary"
                size="large"
                @click="startPrediction"
                :loading="predictionStore.isLoading"
                :disabled="!canStartPrediction"
                style="width: 100%"
              >
                開始預測
              </el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </div>

      <el-alert
        class="policy-alert"
        type="info"
        :closable="false"
        show-icon
        :title="`本系統僅支援出生滿兩個月（≥${MIN_ELIGIBLE_AGE_DAYS}天）且不超過一年（≤${MAX_ELIGIBLE_AGE_DAYS}天）的幼年羊隻體重預測。`"
      />
      <el-alert
        v-if="selectedEarTag && !hasValidBirthDate"
        class="policy-alert"
        type="warning"
        :closable="false"
        show-icon
        title="選定羊隻缺少有效的出生日期，請先補齊資料。"
      />
      <el-alert
        v-else-if="selectedEarTag && !isAboveMinimumAge"
        class="policy-alert"
        type="warning"
        :closable="false"
        show-icon
        :title="underageNotice"
      />
      <el-alert
        v-else-if="selectedEarTag && !isEligibleJuvenile"
        class="policy-alert"
        type="error"
        :closable="false"
        show-icon
        :title="`該羊隻已 ${selectedSheepAgeDays} 天，超過一年限制，暫不支援預測。`"
      />
      <el-alert
        v-else-if="selectedEarTag"
        class="policy-alert"
        type="info"
        :closable="false"
        show-icon
        :title="juvenilePolicySummary"
      />

      <el-alert
        v-if="!settingsStore.hasApiKey"
        title="請先設定 API 金鑰"
        description="請前往「系統設定」頁面設定您的 Gemini API 金鑰以使用預測功能。"
        type="warning"
        :closable="false"
        show-icon
      />
    </el-card>

    <el-card shadow="never" v-if="predictionStore.result || predictionStore.isLoading" class="results-card">
      <template #header>
        <div class="card-header">
          <span>預測分析結果</span>
          <span v-if="predictionStore.result" class="data-info">
            此預測基於 {{ predictionStore.result.historical_data_count }} 筆有效歷史資料
          </span>
        </div>
      </template>

      <div v-loading="predictionStore.isLoading" class="results-content">
        <el-row :gutter="20" v-if="predictionStore.result">
          <el-col :span="14">
            <div class="chart-section">
              <h3>體重成長趨勢圖</h3>
              <div ref="chartContainer" class="chart-container"></div>

              <div class="key-metrics">
                <el-row :gutter="16">
                  <el-col :span="8">
                    <div class="metric-card">
                      <div class="metric-label">預測體重</div>
                      <div class="metric-value">{{ predictionStore.result.predicted_weight }} kg</div>
                      <div class="metric-subvalue">
                        信賴區間 (q10-q90)：{{ formatInterval(predictionStore.result.pred_interval) }}
                      </div>
                    </div>
                  </el-col>
                  <el-col :span="8">
                    <div class="metric-card">
                      <div class="metric-label">平均日增重</div>
                      <div class="metric-value">{{ predictionStore.result.average_daily_gain }} kg/天</div>
                    </div>
                  </el-col>
                  <el-col :span="8">
                    <div class="metric-card" :class="getQualityStatusClass(predictionStore.result.data_quality_report.status)">
                      <div class="metric-label">數據品質</div>
                      <div class="metric-value">{{ predictionStore.result.data_quality_report.status }}</div>
                    </div>
                  </el-col>
                </el-row>
              </div>
            </div>
          </el-col>

          <el-col :span="10">
            <div class="ai-report-section">
              <h3>領頭羊博士 AI 分析報告</h3>
              <div class="ai-analysis-content" v-html="aiAnalysisHtml"></div>
              <el-alert
                v-if="predictionStore.result?.prediction_warning"
                :title="predictionStore.result.prediction_warning"
                type="warning"
                show-icon
                class="prediction-warning"
              />
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, computed, watch } from 'vue';
import { TrendCharts } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { useSettingsStore } from '../stores/settings';
import { usePredictionStore } from '../stores/prediction';
import api from '../api';
import * as echarts from 'echarts';
import markdown from 'markdown-it';

const settingsStore = useSettingsStore();
const predictionStore = usePredictionStore();

const MAX_ELIGIBLE_AGE_DAYS = 365;
const MIN_ELIGIBLE_AGE_DAYS = 60;
const BASE_TARGET_OPTIONS = [14, 30, 60];

const selectedEarTag = ref('');
const targetDays = ref(30);
const chartContainer = ref(null);
const sheepOptions = ref([]);
let chartInstance = null;
let resizeHandler = null;

// 兼容舊代碼/測試的公開狀態（僅讀）
const predictionResult = computed(() => predictionStore.result || null);
const loading = computed(() => predictionStore.isLoading);

const md = markdown();

const aiAnalysisHtml = computed(() => {
  const r = predictionStore.result;
  if (!r || !r.ai_analysis) return '';
  return md.render(r.ai_analysis);
});

const selectedSheepInfo = computed(() => {
  if (!selectedEarTag.value) return null;
  return sheepOptions.value.find(s => s.value === selectedEarTag.value) || null;
});

const selectedSheepAgeDays = computed(() => {
  const info = selectedSheepInfo.value;
  if (!info?.birth_date) return null;
  const birth = new Date(info.birth_date);
  if (Number.isNaN(birth.getTime())) return null;
  const now = new Date();
  const diffMs = now.setHours(0, 0, 0, 0) - birth.setHours(0, 0, 0, 0);
  return Math.floor(diffMs / (1000 * 60 * 60 * 24));
});

const hasValidBirthDate = computed(() => selectedSheepAgeDays.value !== null && selectedSheepAgeDays.value >= 0);
const isAboveMinimumAge = computed(() => hasValidBirthDate.value && selectedSheepAgeDays.value >= MIN_ELIGIBLE_AGE_DAYS);
const isEligibleJuvenile = computed(
  () => hasValidBirthDate.value && isAboveMinimumAge.value && selectedSheepAgeDays.value <= MAX_ELIGIBLE_AGE_DAYS
);
const remainingJuvenileDays = computed(() => {
  if (!hasValidBirthDate.value) return null;
  return Math.max(MAX_ELIGIBLE_AGE_DAYS - selectedSheepAgeDays.value, 0);
});
const daysUntilMinimumAge = computed(() => {
  if (!hasValidBirthDate.value) return null;
  return Math.max(MIN_ELIGIBLE_AGE_DAYS - selectedSheepAgeDays.value, 0);
});
const underageNotice = computed(() => {
  if (!hasValidBirthDate.value || isAboveMinimumAge.value) return '';
  const ageText = selectedSheepAgeDays.value != null ? selectedSheepAgeDays.value : '未知';
  const remaining = daysUntilMinimumAge.value != null ? daysUntilMinimumAge.value : '未知';
  return `該羊隻目前 ${ageText} 天，需滿 ${MIN_ELIGIBLE_AGE_DAYS} 天才能預測，距離門檻尚有 ${remaining} 天。`;
});

const eligibleTargetOptions = computed(() => {
  if (!hasValidBirthDate.value) return BASE_TARGET_OPTIONS;
  if (!isAboveMinimumAge.value) return [];
  return BASE_TARGET_OPTIONS;
});

const targetOptionsText = computed(() => {
  if (!eligibleTargetOptions.value.length) return '無可用預測天數';
  return eligibleTargetOptions.value.map(days => `${days} 天`).join('、');
});

const juvenilePolicySummary = computed(() => {
  if (!hasValidBirthDate.value) {
    return `請確認該羊隻的出生日期，以確保預測僅涵蓋滿兩個月至目前 365 天以內的羊隻。`;
  }
  if (!isAboveMinimumAge.value) {
    return `該羊隻尚未滿兩個月，目前 ${selectedSheepAgeDays.value} 天，距離門檻尚有 ${daysUntilMinimumAge.value} 天。`;
  }
  if (!isEligibleJuvenile.value) {
    return `該羊隻已 ${selectedSheepAgeDays.value} 天，超過 365 天的適用範圍。`;
  }
  return `目前年齡 ${selectedSheepAgeDays.value} 天，可預測 ${targetOptionsText.value}，曲線會延伸至未來 ${targetDays.value || BASE_TARGET_OPTIONS[0]} 天。`;
});

const canStartPrediction = computed(() => {
  if (!selectedEarTag.value || !settingsStore.hasApiKey) return false;
  if (!hasValidBirthDate.value || !isAboveMinimumAge.value || !isEligibleJuvenile.value) return false;
  if (!targetDays.value) return false;
  return eligibleTargetOptions.value.includes(targetDays.value);
});

const loadSheepList = async () => {
  try {
    const response = await api.getAllSheep();
    sheepOptions.value = response.map(sheep => ({
      value: sheep.EarNum,
      breed: sheep.Breed || '未指定',
      sex: sheep.Sex || '未指定',
      birth_date: sheep.BirthDate
    }));
  } catch (error) {
    console.error('載入羊隻清單失敗:', error);
  }
};

const querySearch = (queryString, cb) => {
  const results = queryString
    ? sheepOptions.value.filter(sheep => sheep.value.toLowerCase().includes(queryString.toLowerCase()))
    : sheepOptions.value;
  cb(results);
};

const handleSelect = (item) => {
  selectedEarTag.value = item.value;
  predictionStore.setSelectedEarTag(item.value);
};

const clearSelection = () => {
  selectedEarTag.value = '';
  targetDays.value = 30;
  predictionStore.clear();
};

const getQualityStatusClass = (status) => {
  switch (status) {
    case 'Good':
      return 'status-good';
    case 'Warning':
      return 'status-warning';
    case 'Error':
      return 'status-error';
    default:
      return '';
  }
};

const startPrediction = async () => {
  if (!selectedEarTag.value) {
    ElMessage.error('請選擇羊隻耳號');
    return;
  }
  if (!hasValidBirthDate.value) {
    ElMessage.error('選定羊隻缺少出生日期，無法進行預測');
    return;
  }
  if (!isAboveMinimumAge.value) {
    ElMessage.error(`僅支援滿兩個月（${MIN_ELIGIBLE_AGE_DAYS}天）以上的羊隻預測`);
    return;
  }
  if (!isEligibleJuvenile.value) {
    ElMessage.error('僅支援出生一年內的幼年羊隻預測');
    return;
  }
  if (!targetDays.value || !eligibleTargetOptions.value.includes(targetDays.value)) {
    ElMessage.error('請選擇可用的預測天數');
    return;
  }
  const apiKeyStr = (settingsStore.apiKey || localStorage.getItem('geminiApiKey') || localStorage.getItem('gemini_api_key') || '').trim();
  try {
    predictionStore.setSelectedEarTag(selectedEarTag.value);
    predictionStore.setTargetDays(targetDays.value);
    await predictionStore.startPrediction(apiKeyStr);
    await nextTick();
    await renderChart();
    ElMessage.success('預測分析完成');
  } catch (error) {
    console.error('預測失敗:', error);
    ElMessage.error(error.message || '預測分析失敗');
  }
};

const renderChart = async () => {
  if (!chartContainer.value || !predictionStore.result) return;
  try {
    const old = echarts.getInstanceByDom?.(chartContainer.value);
    if (old) old.dispose();
    chartInstance = echarts.init(chartContainer.value);
    
    const apiKeyStr = (settingsStore.apiKey || localStorage.getItem('geminiApiKey') || localStorage.getItem('gemini_api_key') || '').trim();
    const raw = predictionStore.chartData || await api.getPredictionChartData(selectedEarTag.value, targetDays.value, apiKeyStr);
    const data = raw && raw.value ? raw.value : raw;
    const historicalPoints = Array.isArray(data?.historical_points) ? data.historical_points : [];
    const forecastLine = Array.isArray(data?.forecast_line) && data.forecast_line.length
      ? data.forecast_line
      : (Array.isArray(data?.trend_line) ? data.trend_line : []);
    const confidenceBand = Array.isArray(data?.confidence_band) ? data.confidence_band : [];

    const historicalSeries = historicalPoints.map(p => [p.x, p.y]);
    const forecastSeries = forecastLine.map(p => [p.x, p.y]);
    const confidencePoints = confidenceBand.filter(p => Number.isFinite(p?.lower) && Number.isFinite(p?.upper));
    const confidenceUpperSeries = confidencePoints.map(p => [p.x, p.upper]);
    const confidenceLowerSeries = confidencePoints.map(p => [p.x, p.lower]);

    const projectionPoint = data?.prediction_point || null;
    const predictionSeries = projectionPoint ? [[projectionPoint.x, projectionPoint.y]] : [];

    const historicalLookup = new Map(historicalPoints.map(p => [p.x, p]));
    const forecastLookup = new Map(forecastLine.map(p => [p.x, p]));
    const confidenceLookup = new Map(confidencePoints.map(p => [p.x, p]));

    const legendItems = ['歷史記錄', '預測曲線', '預測值'];
    if (confidencePoints.length) {
      legendItems.push('信賴區間上界', '信賴區間下界');
    }

    const option = {
      title: { text: `${selectedEarTag.value} 體重成長預測`, left: 'center' },
      tooltip: {
        trigger: 'axis',
        formatter: function(params) {
          let result = '';
          params.forEach(param => {
            const xVal = Array.isArray(param.data) ? param.data[0] : param.value?.[0] ?? param.value;
            const roundedX = Math.round(xVal);
            if (param.seriesName === '歷史記錄') {
              const point = historicalLookup.get(roundedX);
              result += `${param.seriesName}: ${point?.label || `${param.data[1]}kg`}<br/>`;
            } else if (param.seriesName === '預測值') {
              result += `${param.seriesName}: ${data.prediction_point?.label || `${param.data[1]}kg`}<br/>`;
            } else if (param.seriesName === '預測曲線') {
              const point = forecastLookup.get(roundedX);
              const label = point?.date ? `${point.date}` : `出生後 ${roundedX} 天`;
              result += `${param.seriesName}: ${param.data[1]?.toFixed?.(2) || '-'}kg (${label})<br/>`;
            } else if (param.seriesName === '信賴區間上界' || param.seriesName === '信賴區間下界') {
              const point = confidenceLookup.get(roundedX);
              const label = point?.date ? `${point.date}` : `出生後 ${roundedX} 天`;
              const value = param.data[1];
              result += `${param.seriesName}: ${Number.isFinite(value) ? value.toFixed(2) : '-'}kg (${label})<br/>`;
            } else {
              const value = Array.isArray(param.data) ? param.data[1] : param.data;
              result += `${param.seriesName}: ${Number.isFinite(value) ? value.toFixed?.(2) : '-'}kg<br/>`;
            }
          });
          return result;
        }
      },
      legend: { data: legendItems, bottom: 10 },
      xAxis: { type: 'value', name: '出生後天數', nameLocation: 'middle', nameGap: 30 },
      yAxis: { type: 'value', name: '體重 (kg)', nameLocation: 'middle', nameGap: 40 },
      series: [
        { name: '歷史記錄', type: 'scatter', data: historicalSeries, itemStyle: { color: '#409EFF' }, symbolSize: 8 },
        { name: '預測曲線', type: 'line', data: forecastSeries, itemStyle: { color: '#67C23A' }, lineStyle: { width: 3 }, symbol: 'none' },
        { name: '預測值', type: 'scatter', data: predictionSeries, itemStyle: { color: '#F56C6C' }, symbolSize: 12, symbol: 'star' }
      ]
    };

    if (confidencePoints.length) {
      option.series.push(
        {
          name: '信賴區間上界',
          type: 'line',
          data: confidenceUpperSeries,
          lineStyle: { type: 'dashed', width: 1.5, color: '#91CC75' },
          symbol: 'none'
        },
        {
          name: '信賴區間下界',
          type: 'line',
          data: confidenceLowerSeries,
          lineStyle: { type: 'dashed', width: 1.5, color: '#6E7074' },
          symbol: 'none'
        }
      );
    }
    chartInstance.setOption(option);
    if (!resizeHandler) {
      resizeHandler = () => { if (chartInstance) chartInstance.resize(); };
      window.addEventListener('resize', resizeHandler);
    }
  } catch (error) {
    console.error('圖表渲染失敗:', error);
    ElMessage.error('圖表載入失敗');
  }
};

const formatInterval = (interval) => {
  if (!interval) return '暫無資料';
  const { q10, q90 } = interval;
  if (q10 == null || q90 == null) return '暫無資料';
  return `${q10} - ${q90} kg`;
};

onMounted(async () => {
  await loadSheepList();
  if (!settingsStore.apiKey) {
    const saved = localStorage.getItem('geminiApiKey') || localStorage.getItem('gemini_api_key');
    if (saved) settingsStore.setApiKey(saved);
  }
  if (predictionStore.selectedEarTag) selectedEarTag.value = predictionStore.selectedEarTag;
  if (predictionStore.targetDays) targetDays.value = predictionStore.targetDays;
  if (predictionStore.result) {
    await nextTick();
    await renderChart();
  }
});

watch(eligibleTargetOptions, (options) => {
  if (!options.length) {
    targetDays.value = null;
    return;
  }
  if (!options.includes(targetDays.value)) {
    targetDays.value = options[0];
  }
});

watch(targetDays, (val) => predictionStore.setTargetDays(val));
watch(() => predictionStore.result, async (val) => {
  if (val) {
    await nextTick();
    await renderChart();
  }
});

onBeforeUnmount(() => {
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler);
    resizeHandler = null;
  }
  if (chartInstance) {
    try { chartInstance.dispose(); } catch (_) {}
    chartInstance = null;
  }
});
</script>

<style scoped>

.prediction-page {
  padding: 1.25rem;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1.25rem;
  color: #303133;
}

.card-header {
  font-size: 1.125rem;
  font-weight: 600;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.data-info {
  font-size: 0.875rem;
  color: #909399;
  font-weight: normal;
}


.sheep-selection-area {
  margin-bottom: 1.25rem;
}

.ear-tag-suggestion {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ear-tag {
  font-weight: 600;
}

.sheep-info {
  color: #909399;
  font-size: 0.75rem;
}


.results-card {
  margin-top: 1.25rem;
}

.results-content {
  min-height: 25rem;
}


.chart-section {
  background: #f8f9fa;
  padding: 1.25rem;
  border-radius: 0.5rem;
}

.chart-container {
  width: 100%;
  height: 25rem;
  margin: 1.25rem 0;
}

.key-metrics {
  margin-top: 1.25rem;
}


.metric-card {
  background: white;
  padding: 1rem;
  border-radius: 0.5rem;
  text-align: center;
  border: 0.125rem solid #e4e7ed;
}

.metric-card.status-good {
  border-color: #67c23a;
}

.metric-card.status-warning {
  border-color: #e6a23c;
}

.metric-card.status-error {
  border-color: #f56c6c;
}

.metric-label {
  font-size: 0.875rem;
  color: #909399;
  margin-bottom: 0.5rem;
}

.metric-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: #303133;
}

.metric-subvalue {
  margin-top: 0.375rem;
  font-size: 0.875rem;
  color: #606266;
}


.ai-report-section {
  background: #f0f9ff;
  padding: 1.25rem;
  border-radius: 0.5rem;
  height: 100%;
}

.ai-analysis-content {
  margin-top: 1rem;
  line-height: 1.6;
}

.ai-analysis-content :deep(h3) {
  color: #409eff;
  font-size: 1.125rem;
  margin: 1rem 0 0.5rem 0;
}

.ai-analysis-content :deep(h4) {
  color: #606266;
  font-size: 1rem;
  margin: 0.75rem 0 0.375rem 0;
}

.ai-analysis-content :deep(p) {
  margin: 0.5rem 0;
}

.ai-analysis-content :deep(strong) {
  color: #303133;
}

.ai-analysis-content :deep(ul) {
  margin: 0.5rem 0;
  padding-left: 1.25rem;
}

.ai-analysis-content :deep(li) {
  margin: 0.25rem 0;
}

.prediction-warning {
  margin-top: 1rem;
}

.policy-alert {
  margin-top: 0.75rem;
}
</style>
