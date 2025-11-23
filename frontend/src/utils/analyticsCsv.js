export const formatCsvNumber = (value) => {
  if (value === null || value === undefined) {
    return ''
  }
  const numeric = Number(value)
  if (Number.isNaN(numeric)) {
    return ''
  }
  return numeric.toFixed(2)
}

export const escapeCsvValue = (value) => {
  if (value === null || value === undefined) {
    return ''
  }
  let stringValue = String(value)
  if (stringValue.includes('"')) {
    stringValue = stringValue.replace(/"/g, '""')
  }
  if (/[",\n]/.test(stringValue)) {
    return `"${stringValue}"`
  }
  return stringValue
}

export const buildCsvContent = (rows) =>
  rows
    .map((row) => row.map((cell) => escapeCsvValue(cell)).join(','))
    .join('\n')

export const exportCsv = (filename, rows) => {
  const csvContent = buildCsvContent(rows)
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}
