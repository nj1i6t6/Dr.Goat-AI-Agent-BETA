import { defineStore } from 'pinia'
import { ref, reactive, computed } from 'vue'
import api from '../api'

const CACHE_TTL = 30 * 1000
const THROTTLE_WINDOW = 1500

const serializeKey = (endpoint, payload = {}) => `${endpoint}:${JSON.stringify(payload)}`

export const useAnalyticsStore = defineStore('analytics', () => {
  const costEntries = ref([])
  const revenueEntries = ref([])
  const cohortResult = ref(null)
  const costBenefitResult = ref(null)
  const reportState = reactive({ html: '', markdown: '' })
  const loading = reactive({
    costEntries: false,
    revenueEntries: false,
    cohort: false,
    costBenefit: false,
    report: false,
  })
  const error = ref(null)

  const _cache = reactive(new Map())
  const _inflight = reactive(new Map())
  const _lastCompleted = reactive(new Map())

  const costBenefitSummary = computed(() => costBenefitResult.value?.summary || {})

  const kpiCards = computed(() => {
    const summary = costBenefitSummary.value
    const totalCost = Number(summary.total_cost ?? 0)
    const totalRevenue = Number(summary.total_revenue ?? 0)
    const netProfit = Number(summary.net_profit ?? 0)
    const ratio = totalCost ? totalRevenue / totalCost : null

    return [
      { label: '總成本', value: totalCost, unit: 'TWD' },
      { label: '總收益', value: totalRevenue, unit: 'TWD' },
      { label: '淨收益', value: netProfit, unit: 'TWD' },
      { label: '成本收益比', value: ratio, unit: 'x' },
    ]
  })

  const cohortHasData = computed(() => Array.isArray(cohortResult.value?.items) && cohortResult.value.items.length > 0)
  const costBenefitHasData = computed(
    () => Array.isArray(costBenefitResult.value?.items) && costBenefitResult.value.items.length > 0
  )

  const _throttledRequest = async (endpoint, payload, requestFn, force = false) => {
    const key = serializeKey(endpoint, payload)
    const now = Date.now()

    const cached = _cache.get(key)

    if (!force) {
      if (cached && now - cached.timestamp < CACHE_TTL) {
        return cached.data
      }
      const last = _lastCompleted.get(key) || 0
      if (now - last < THROTTLE_WINDOW) {
        if (_inflight.get(key)) {
          return _inflight.get(key)
        }
        if (cached) {
          return cached.data
        }
      }
    }

    const promise = requestFn()
      .then((data) => {
        _cache.set(key, { data, timestamp: Date.now() })
        return data
      })
      .finally(() => {
        _lastCompleted.set(key, Date.now())
        _inflight.delete(key)
      })

    _inflight.set(key, promise)
    return promise
  }

  const loadCostEntries = async (params = {}) => {
    loading.costEntries = true
    error.value = null
    try {
      const data = await api.listCostEntries(params, (err) => (error.value = err.message))
      costEntries.value = data.items || []
      return data
    } finally {
      loading.costEntries = false
    }
  }

  const loadRevenueEntries = async (params = {}) => {
    loading.revenueEntries = true
    error.value = null
    try {
      const data = await api.listRevenueEntries(params, (err) => (error.value = err.message))
      revenueEntries.value = data.items || []
      return data
    } finally {
      loading.revenueEntries = false
    }
  }

  const fetchCohortAnalysis = async (payload, { force = false } = {}) => {
    loading.cohort = true
    error.value = null
    try {
      const data = await _throttledRequest('cohort', payload, () =>
        api.runCohortAnalysis(payload, (err) => (error.value = err.message))
      , force)
      cohortResult.value = data
      return data
    } finally {
      loading.cohort = false
    }
  }

  const fetchCostBenefit = async (payload, { force = false } = {}) => {
    loading.costBenefit = true
    error.value = null
    try {
      const data = await _throttledRequest('cost-benefit', payload, () =>
        api.runCostBenefit(payload, (err) => (error.value = err.message))
      , force)
      costBenefitResult.value = data
      return data
    } finally {
      loading.costBenefit = false
    }
  }

  const saveCostEntry = async (entry) => {
    error.value = null
    if (entry.id) {
      const updated = await api.updateCostEntry(entry.id, entry, (err) => (error.value = err.message))
      if (updated) {
        const index = costEntries.value.findIndex((item) => item.id === entry.id)
        if (index !== -1) {
          costEntries.value.splice(index, 1, updated)
        }
      }
      return updated
    }
    const created = await api.createCostEntry(entry, (err) => (error.value = err.message))
    if (created) {
      costEntries.value.unshift(created)
    }
    return created
  }

  const saveRevenueEntry = async (entry) => {
    error.value = null
    if (entry.id) {
      const updated = await api.updateRevenueEntry(entry.id, entry, (err) => (error.value = err.message))
      if (updated) {
        const index = revenueEntries.value.findIndex((item) => item.id === entry.id)
        if (index !== -1) {
          revenueEntries.value.splice(index, 1, updated)
        }
      }
      return updated
    }
    const created = await api.createRevenueEntry(entry, (err) => (error.value = err.message))
    if (created) {
      revenueEntries.value.unshift(created)
    }
    return created
  }

  const removeCostEntry = async (id) => {
    await api.deleteCostEntry(id, (err) => (error.value = err.message))
    costEntries.value = costEntries.value.filter((item) => item.id !== id)
  }

  const removeRevenueEntry = async (id) => {
    await api.deleteRevenueEntry(id, (err) => (error.value = err.message))
    revenueEntries.value = revenueEntries.value.filter((item) => item.id !== id)
  }

  const generateReport = async ({ apiKey, ...payload }) => {
    loading.report = true
    error.value = null
    try {
      const data = await api.generateAnalyticsReport(payload, apiKey, (err) => (error.value = err.message))
      reportState.html = data.report_html
      reportState.markdown = data.report_markdown
      return data
    } finally {
      loading.report = false
    }
  }

  const resetReport = () => {
    reportState.html = ''
    reportState.markdown = ''
  }

  return {
    costEntries,
    revenueEntries,
    cohortResult,
    costBenefitResult,
    reportState,
    loading,
    error,
    kpiCards,
    cohortHasData,
    costBenefitHasData,
    loadCostEntries,
    loadRevenueEntries,
    fetchCohortAnalysis,
    fetchCostBenefit,
    saveCostEntry,
    saveRevenueEntry,
    removeCostEntry,
    removeRevenueEntry,
    generateReport,
    resetReport,
  }
})
