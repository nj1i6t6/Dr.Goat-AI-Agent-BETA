/**
 * 錯誤處理工具
 * 將後端的結構化錯誤轉換為用戶友好的中文訊息
 */

// 欄位名稱中文對照表
const fieldDisplayNames = {
  // 認證相關
  username: '用戶名',
  password: '密碼',
  
  // 羊隻基本資料
  EarNum: '耳號',
  BirthDate: '出生日期',
  Sex: '性別',
  Breed: '品種',
  Sire: '父號',
  Dam: '母號',
  BirWei: '出生體重',
  Body_Weight_kg: '體重',
  Age_Months: '月齡',
  breed_category: '品種類別',
  status: '生理狀態',
  status_description: '生理狀態描述',
  target_average_daily_gain_g: '目標日增重',
  milk_yield_kg_day: '日產奶量',
  milk_fat_percentage: '乳脂率',
  number_of_fetuses: '懷胎數',
  activity_level: '活動量',
  other_remarks: '其他備註',
  agent_notes: 'AI代理人備註',
  next_vaccination_due_date: '下次疫苗日期',
  next_deworming_due_date: '下次驅蟲日期',
  expected_lambing_date: '預計產仔日期',
  manure_management: '糞肥管理方式',
  primary_forage_type: '主要草料類型',
  welfare_score: '動物福利評分',
  FarmNum: '牧場編號',
  
  // 事件相關
  event_date: '事件日期',
  event_type: '事件類型',
  description: '事件描述',
  notes: '備註',
  medication: '用藥名稱',
  withdrawal_days: '停藥天數',
  
  // 歷史數據相關
  record_date: '記錄日期',
  record_type: '記錄類型',
  value: '數值',
  
  // AI 代理人相關
  api_key: 'API金鑰',
  message: '訊息',
  session_id: '會話ID',
  ear_num_context: '羊隻耳號上下文',
}

// 錯誤類型中文對照表
const errorTypeMessages = {
  'Field required': '為必填欄位',
  'string too short': '長度不足',
  'string too long': '長度超出限制',
  'value is not a valid integer': '必須是整數',
  'value is not a valid float': '必須是數字',
  'ensure this value is greater than or equal to': '必須大於等於',
  'ensure this value is less than or equal to': '必須小於等於',
  'invalid datetime format': '日期格式無效',
  'field required': '為必填欄位',
  'extra fields not permitted': '包含不允許的欄位',
}

/**
 * 轉換後端驗證錯誤為用戶友好的訊息
 * @param {Object} errorResponse - 後端返回的錯誤響應
 * @returns {Object} 格式化後的錯誤訊息
 */
export function formatValidationErrors(errorResponse) {
  if (!errorResponse || typeof errorResponse !== 'object') {
    return {
      general: '發生未知錯誤',
      fields: {}
    }
  }

  const result = {
    general: errorResponse.error || '操作失敗',
    fields: {}
  }

  // 處理 field_errors (已經轉換過的欄位錯誤)
  if (errorResponse.field_errors) {
    result.fields = { ...errorResponse.field_errors }
  }

  // 處理原始的 Pydantic 驗證錯誤
  if (errorResponse.details && Array.isArray(errorResponse.details)) {
    for (const error of errorResponse.details) {
      const fieldPath = error.loc || ['unknown']
      const fieldName = fieldPath[fieldPath.length - 1]
      const displayName = fieldDisplayNames[fieldName] || fieldName
      const errorMsg = error.msg || '驗證失敗'
      
      // 轉換常見的錯誤訊息
      let translatedMsg = errorMsg
      for (const [pattern, translation] of Object.entries(errorTypeMessages)) {
        if (errorMsg.includes(pattern)) {
          translatedMsg = `${displayName}${translation}`
          break
        }
      }
      
      result.fields[fieldName] = translatedMsg
    }
  }

  return result
}

/**
 * 顯示用戶友好的錯誤訊息
 * @param {Object} errorResponse - 後端錯誤響應
 * @param {Function} messageHandler - 訊息顯示函數 (如 ElMessage.error)
 * @returns {Object} 格式化後的錯誤訊息
 */
export function showFormattedError(errorResponse, messageHandler) {
  const formatted = formatValidationErrors(errorResponse)
  
  // 顯示一般錯誤訊息
  if (messageHandler && typeof messageHandler === 'function') {
    messageHandler(formatted.general)
  }
  
  return formatted
}

/**
 * 從錯誤響應中提取欄位錯誤
 * @param {Object} errorResponse - 後端錯誤響應
 * @returns {Object} 欄位錯誤對象，適用於表單驗證
 */
export function extractFieldErrors(errorResponse) {
  const formatted = formatValidationErrors(errorResponse)
  return formatted.fields || {}
}

/**
 * 檢查是否為驗證錯誤
 * @param {Object} errorResponse - 錯誤響應
 * @returns {boolean} 是否為驗證錯誤
 */
export function isValidationError(errorResponse) {
  return errorResponse && (
    errorResponse.field_errors || 
    (errorResponse.details && Array.isArray(errorResponse.details))
  )
}

/**
 * 創建表單驗證規則的錯誤顯示器
 * @param {Object} fieldErrors - 欄位錯誤對象
 * @returns {Function} 驗證函數
 */
export function createFieldValidator(fieldErrors) {
  return (rule, value, callback) => {
    const fieldName = rule.field
    if (fieldErrors && fieldErrors[fieldName]) {
      callback(new Error(fieldErrors[fieldName]))
    } else {
      callback()
    }
  }
}

/**
 * 常用的成功訊息顯示
 * @param {string} message - 成功訊息
 * @param {Function} messageHandler - 訊息顯示函數
 */
export function showSuccessMessage(message, messageHandler) {
  if (messageHandler && typeof messageHandler === 'function') {
    messageHandler({
      message: message || '操作成功',
      type: 'success'
    })
  }
}

/**
 * 網路錯誤處理
 * @param {Error} error - 網路錯誤對象
 * @returns {string} 用戶友好的錯誤訊息
 */
export function handleNetworkError(error) {
  if (!error.response) {
    return '網路連接失敗，請檢查網路設定'
  }
  
  const status = error.response.status
  const statusMessages = {
    400: '請求參數錯誤',
    401: '未授權，請重新登入',
    403: '權限不足',
    404: '請求的資源不存在',
    409: '資料衝突，請檢查輸入',
    422: '資料驗證失敗',
    500: '伺服器內部錯誤',
    502: '服務暫時不可用',
    503: '服務維護中',
    504: '請求超時'
  }
  
  return statusMessages[status] || `請求失敗 (錯誤代碼: ${status})`
}

/**
 * API 錯誤統一處理函數
 * @param {Error} error - API 錯誤
 * @param {Function} messageHandler - 訊息顯示函數
 * @returns {Object} 處理後的錯誤訊息
 */
export function handleApiError(error, messageHandler) {
  let errorMessage = '操作失敗'
  let fieldErrors = {}
  
  if (error.response && error.response.data) {
    const responseData = error.response.data
    
    if (isValidationError(responseData)) {
      // 驗證錯誤
      const formatted = formatValidationErrors(responseData)
      errorMessage = formatted.general
      fieldErrors = formatted.fields
    } else if (typeof responseData.error === 'string') {
      // 一般錯誤
      errorMessage = responseData.error
    } else {
      // 網路錯誤
      errorMessage = handleNetworkError(error)
    }
  } else {
    errorMessage = handleNetworkError(error)
  }
  
  // 顯示錯誤訊息
  if (messageHandler) {
    showFormattedError({ error: errorMessage }, messageHandler)
  }
  
  return {
    message: errorMessage,
    fields: fieldErrors
  }
}

// 預設導出
export default {
  formatValidationErrors,
  showFormattedError,
  extractFieldErrors,
  isValidationError,
  createFieldValidator,
  showSuccessMessage,
  handleNetworkError,
  handleApiError
}
