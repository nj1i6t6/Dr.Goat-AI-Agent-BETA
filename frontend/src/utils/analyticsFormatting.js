export const formatDisplayNumber = (value) => {
  if (value == null) {
    return '—'
  }
  return new Intl.NumberFormat('zh-TW', { maximumFractionDigits: 2 }).format(value)
}

export const formatCohortGroupLabel = (item) => {
  const dims = Object.entries(item || {}).filter(([key]) => key !== 'metrics')
  if (!dims.length) return '全部'
  return dims
    .map(([key, value]) => {
      if (value == null || value === '未填寫') {
        return `${key}:未指定`
      }
      return `${key}:${value}`
    })
    .join(' / ')
}
