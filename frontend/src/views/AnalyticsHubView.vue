<template>
  <div class="analytics-hub">
  <el-page-header content="數據分析中心" class="page-header" />

    <el-row :gutter="16">
      <el-col :lg="18" :md="24">
        <AnalyticsFiltersCard
          v-model:filters="filters"
          :dimension-options="dimensionOptions"
          :metric-options="metricOptions"
        />

        <el-alert
          v-if="store.error"
          class="error-alert"
          type="error"
          show-icon
          :closable="false"
        >
          {{ store.error }}
        </el-alert>

        <AnalyticsKpiGrid :cards="store.kpiCards" />

        <CohortChartCard
          :items="store.cohortResult?.items || []"
          empty-action-label="前往新增成本紀錄"
          empty-button-type="primary"
          @empty-action="scrollToFinanceForms('cost')"
        />

        <CostBenefitChartCard
          :items="store.costBenefitResult?.items || []"
          empty-action-label="前往新增收益紀錄"
          empty-button-type="success"
          @empty-action="scrollToFinanceForms('revenue')"
        />
      </el-col>

      <el-col :lg="6" :md="24">
        <div ref="financeSectionRef" class="finance-section">
          <FinanceEntryForm
            ref="costFormRef"
            v-model:form="costForm"
            :rules="financeRules"
            title="新增成本紀錄"
            submit-label="新增成本"
            button-type="primary"
            :loading="store.loading.costEntries"
            @submit="submitCostForm"
          />

          <FinanceEntryForm
            ref="revenueFormRef"
            v-model:form="revenueForm"
            :rules="financeRules"
            title="新增收益紀錄"
            submit-label="新增收益"
            button-type="success"
            :loading="store.loading.revenueEntries"
            category-placeholder="例如：milk"
            @submit="submitRevenueForm"
          />

          <AnalyticsReportPanel
            v-model:api-key="reportApiKey"
            v-model:notes="reportNotes"
            :report-state="store.reportState"
          />
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="tables-row">
      <el-col :md="12" :sm="24">
        <AnalyticsRecordTable
          title="最新成本紀錄"
          :entries="store.costEntries"
          cta-label="前往新增成本紀錄"
          cta-type="primary"
          empty-description="尚無成本資料"
          @cta-click="() => scrollToFinanceForms('cost')"
          @delete="store.removeCostEntry"
        />
      </el-col>
      <el-col :md="12" :sm="24">
        <AnalyticsRecordTable
          title="最新收益紀錄"
          :entries="store.revenueEntries"
          cta-label="前往新增收益紀錄"
          cta-type="success"
          empty-description="尚無收益資料"
          @cta-click="() => scrollToFinanceForms('revenue')"
          @delete="store.removeRevenueEntry"
        />
      </el-col>
    </el-row>

    <div class="floating-actions">
      <el-button-group>
        <el-button
          class="fab-button"
          type="primary"
          :loading="store.loading.cohort || store.loading.costBenefit"
          @click="runAnalysis"
        >
          重新分析
        </el-button>
        <el-button
          class="fab-button"
          type="info"
          :disabled="!store.costBenefitHasData && !(store.costBenefitResult?.summary)"
          @click="exportCostBenefitCsv"
        >
          匯出 CSV
        </el-button>
        <el-button
          class="fab-button"
          type="success"
          :loading="store.loading.report"
          :disabled="!reportApiKey"
          @click="generateReport"
        >
          產生報告
        </el-button>
      </el-button-group>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

import AnalyticsFiltersCard from '../components/analytics/AnalyticsFiltersCard.vue'
import AnalyticsKpiGrid from '../components/analytics/AnalyticsKpiGrid.vue'
import AnalyticsRecordTable from '../components/analytics/AnalyticsRecordTable.vue'
import CohortChartCard from '../components/analytics/CohortChartCard.vue'
import CostBenefitChartCard from '../components/analytics/CostBenefitChartCard.vue'
import FinanceEntryForm from '../components/analytics/FinanceEntryForm.vue'
import AnalyticsReportPanel from '../components/analytics/AnalyticsReportPanel.vue'
import { exportCsv, formatCsvNumber } from '../utils/analyticsCsv'
import { useAnalyticsStore } from '../stores/analytics'

const store = useAnalyticsStore()

const filters = reactive({
  timeRange: [],
  cohortBy: ['breed'],
  metrics: ['sheep_count', 'total_cost', 'total_revenue', 'net_profit'],
  categories: [],
})

const dimensionOptions = [
  { label: '品種', value: 'breed' },
  { label: '胎次', value: 'lactation_number' },
  { label: '生產階段', value: 'production_stage' },
]

const metricOptions = [
  { label: '羊隻數量', value: 'sheep_count' },
  { label: '平均體重', value: 'avg_weight' },
  { label: '總成本', value: 'total_cost' },
  { label: '總收益', value: 'total_revenue' },
  { label: '淨收益', value: 'net_profit' },
  { label: '每頭成本', value: 'cost_per_head' },
  { label: '每頭收益', value: 'revenue_per_head' },
]

const financeRules = {
  recorded_at: [{ required: true, message: '請選擇日期', trigger: 'change' }],
  category: [{ required: true, message: '請輸入分類', trigger: 'blur' }],
  amount: [{ required: true, message: '請輸入金額', trigger: 'blur' }],
}

const costForm = reactive({
  recorded_at: '',
  category: '',
  amount: null,
  notes: '',
})

const revenueForm = reactive({
  recorded_at: '',
  category: '',
  amount: null,
  notes: '',
})

const costFormRef = ref()
const revenueFormRef = ref()
const financeSectionRef = ref(null)

const reportApiKey = ref('')
const reportNotes = ref('')

const runAnalysis = async () => {
  const payload = {
    cohort_by: filters.cohortBy,
    metrics: filters.metrics,
    filters: {},
  }
  if (filters.categories.length) {
    payload.filters.category = filters.categories
  }
  if (filters.timeRange?.length === 2) {
    payload.time_range = {
      start: `${filters.timeRange[0]}T00:00:00Z`,
      end: `${filters.timeRange[1]}T23:59:59Z`,
    }
  }
  await Promise.all([
    store.fetchCohortAnalysis(payload),
    store.fetchCostBenefit({
      filters: payload.filters,
      time_range: payload.time_range,
      metrics: ['total_cost', 'total_revenue', 'net_profit', 'avg_cost_per_head', 'avg_revenue_per_head'],
      group_by: 'month',
    }),
  ])
}

const submitCostForm = async () => {
  await store.saveCostEntry({
    ...costForm,
    recorded_at: costForm.recorded_at ? `${costForm.recorded_at}T00:00:00Z` : null,
  })
  Object.assign(costForm, { recorded_at: '', category: '', amount: null, notes: '' })
  costFormRef.value?.clearValidation()
  ElMessage.success('已新增成本紀錄')
}

const submitRevenueForm = async () => {
  await store.saveRevenueEntry({
    ...revenueForm,
    recorded_at: revenueForm.recorded_at ? `${revenueForm.recorded_at}T00:00:00Z` : null,
  })
  Object.assign(revenueForm, { recorded_at: '', category: '', amount: null, notes: '' })
  revenueFormRef.value?.clearValidation()
  ElMessage.success('已新增收益紀錄')
}

const generateReport = async () => {
  if (!reportApiKey.value) {
    ElMessage.warning('請先填寫 API Key')
    return
  }
  const reportFilters = {}
  if (filters.categories.length) {
    reportFilters.category = [...filters.categories]
  }
  if (filters.timeRange?.length === 2) {
    reportFilters.time_range = `${filters.timeRange[0]} 至 ${filters.timeRange[1]}`
  }
  await store.generateReport({
    apiKey: reportApiKey.value,
    filters: reportFilters,
    cohort: store.cohortResult?.items || [],
    cost_benefit: store.costBenefitResult || {},
    insights: reportNotes.value ? [reportNotes.value] : [],
  })
  ElMessage.success('AI 報告已產生')
}

const scrollToFinanceForms = (target = 'cost') => {
  if (financeSectionRef.value) {
    financeSectionRef.value.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
  nextTick(() => {
    if (target === 'cost') {
      costFormRef.value?.focusFirstField()
    } else {
      revenueFormRef.value?.focusFirstField()
    }
  })
}

const exportCostBenefitCsv = () => {
  const analysis = store.costBenefitResult
  const summary = analysis?.summary
  const items = analysis?.items || []

  const rows = [['群組', '總成本', '總收益', '淨收益', '成本收益比']]
  items.forEach((item) => {
    const metrics = item.metrics || {}
    const totalCost = Number(metrics.total_cost ?? 0)
    const totalRevenue = Number(metrics.total_revenue ?? 0)
    const netProfit = Number(metrics.net_profit ?? 0)
    const ratio = totalCost ? totalRevenue / totalCost : null
    rows.push([
      item.group ?? '未命名',
      formatCsvNumber(totalCost),
      formatCsvNumber(totalRevenue),
      formatCsvNumber(netProfit),
      ratio === null ? '' : formatCsvNumber(ratio),
    ])
  })
  if (summary) {
    const totalCost = Number(summary.total_cost ?? 0)
    const totalRevenue = Number(summary.total_revenue ?? 0)
    const netProfit = Number(summary.net_profit ?? 0)
    const ratio = totalCost ? totalRevenue / totalCost : null
    rows.push([
      '總計',
      formatCsvNumber(totalCost),
      formatCsvNumber(totalRevenue),
      formatCsvNumber(netProfit),
      ratio === null ? '' : formatCsvNumber(ratio),
    ])
  }

  exportCsv(`cost-benefit-${Date.now()}.csv`, rows)
  ElMessage.success('已匯出成本收益 CSV')
}

onMounted(async () => {
  await Promise.all([store.loadCostEntries(), store.loadRevenueEntries()])
  await runAnalysis()
})
</script>

<style scoped>
.analytics-hub {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  margin-bottom: 8px;
}

::v-deep(.filters-card) {
  margin-bottom: 16px;
}

::v-deep(.filters-form) {
  width: 100%;
}

.error-alert {
  margin-bottom: 12px;
}

::v-deep(.kpi-row) {
  margin-bottom: 16px;
}

::v-deep(.kpi-card) {
  text-align: center;
  padding: 12px 0;
}

::v-deep(.kpi-label) {
  font-size: 0.9rem;
  color: #475569;
  margin-bottom: 8px;
}

::v-deep(.kpi-value) {
  font-size: 1.6rem;
  font-weight: 600;
}

::v-deep(.kpi-unit) {
  font-size: 0.8rem;
  margin-left: 4px;
  color: #64748b;
}

::v-deep(.chart-card) {
  margin-bottom: 16px;
}

::v-deep(.chart-container) {
  width: 100%;
  height: 320px;
}

::v-deep(.form-card) {
  margin-bottom: 16px;
}

.finance-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

::v-deep(.helper-text) {
  display: block;
  color: #64748b;
}

::v-deep(.report-actions) {
  margin-top: 8px;
  display: flex;
  gap: 8px;
}

::v-deep(.report-preview) {
  margin-top: 12px;
  padding: 12px;
  border: 1px dashed #cbd5f5;
  border-radius: 6px;
  max-height: 280px;
  overflow: auto;
}

::v-deep(.empty-wrapper) {
  padding: 32px 0;
}

.tables-row {
  margin-top: 12px;
}

::v-deep(.card-header) {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.floating-actions {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 1000;
}

.fab-button {
  min-width: 120px;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.18);
}

@media (max-width: 768px) {
  ::v-deep(.chart-container) {
    height: 260px;
  }

  .floating-actions {
    right: 16px;
    bottom: 16px;
  }
}
</style>
