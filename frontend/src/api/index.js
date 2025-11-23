import axios from 'axios';
import { handleApiError } from '../utils/errorHandler';

const apiClient = axios.create({
  // 【修改：改回相對路徑】
  // 因為 Flask 將同時提供 API 和前端檔案，它們是同源的。
  baseURL: '/', 
  headers: {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
  },
  // 同源請求也需要發送 cookie
  withCredentials: true, 
});

apiClient.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

apiClient.interceptors.response.use(
  (response) => {
    if (response.config.responseType === 'blob') {
      return response;
    }
    return response.data;
  },
  async (error) => {
    if (error.response) {
      switch (error.response.status) {
        case 401:
          // 避免無限循環：只有在非登出請求時才自動登出
          const isLogoutRequest = error.config.url && error.config.url.includes('/logout');
          const isLoginRequest = error.config.url && error.config.url.includes('/login');
          
          if (!isLogoutRequest && !isLoginRequest) {
            console.error("收到 401 未授權錯誤，執行登出。");
            // 使用動態導入避免循環依賴
            const { useAuthStore } = await import('../stores/auth');
            const authStore = useAuthStore();
            authStore.logout();
          } else if (isLoginRequest) {
            console.log("登入失敗：憑證無效");
          } else {
            console.log("登出請求失敗，但這是正常的");
          }
          break;
        case 404:
          console.error("請求的資源不存在 (404)。");
          break;
        default:
          console.error(`收到伺服器錯誤: ${error.response.status}`);
      }
    } else {
      console.error("網路錯誤或請求無法發送:", error.message);
    }
    return Promise.reject(error);
  }
);

/**
 * 帶錯誤處理的 API 包裝器
 * @param {Function} apiCall - API 調用函數
 * @param {Function} errorHandler - 錯誤處理函數 (可選)
 * @returns {Promise} API 調用結果
 */
async function withErrorHandling(apiCall, errorHandler = null) {
  try {
    return await apiCall();
  } catch (error) {
    if (errorHandler) {
      const formatted = handleApiError(error);
      errorHandler(formatted);
    }
    throw error;
  }
}

// 包裝 API 方法以提供錯誤處理
export default {
  // 身份驗證 API
  login(credentials, errorHandler) { 
    return withErrorHandling(() => apiClient.post('/api/auth/login', credentials), errorHandler); 
  },
  register(credentials, errorHandler) { 
    return withErrorHandling(() => apiClient.post('/api/auth/register', credentials), errorHandler); 
  },
  logout(errorHandler) { 
    return withErrorHandling(() => apiClient.post('/api/auth/logout'), errorHandler); 
  },
  getAuthStatus(errorHandler) { 
    return withErrorHandling(() => apiClient.get('/api/auth/status'), errorHandler); 
  },

  // 羊隻管理 API
  getAllSheep(errorHandler) { 
    return withErrorHandling(() => apiClient.get('/api/sheep/'), errorHandler); 
  },
  getSheepDetails(earNum, errorHandler) { 
    return withErrorHandling(() => apiClient.get(`/api/sheep/${earNum}`), errorHandler); 
  },
  addSheep(data, errorHandler) { 
    return withErrorHandling(() => apiClient.post('/api/sheep/', data), errorHandler); 
  },
  updateSheep(earNum, data, errorHandler) { 
    return withErrorHandling(() => apiClient.put(`/api/sheep/${earNum}`, data), errorHandler); 
  },
  deleteSheep(earNum, errorHandler) { 
    return withErrorHandling(() => apiClient.delete(`/api/sheep/${earNum}`), errorHandler); 
  },

  // 羊隻事件 API
  getSheepEvents(earNum, errorHandler) { 
    return withErrorHandling(() => apiClient.get(`/api/sheep/${earNum}/events`), errorHandler); 
  },
  addSheepEvent(earNum, data, errorHandler) { 
    return withErrorHandling(() => apiClient.post(`/api/sheep/${earNum}/events`, data), errorHandler); 
  },
  updateSheepEvent(eventId, data, errorHandler) { 
    return withErrorHandling(() => apiClient.put(`/api/sheep/events/${eventId}`, data), errorHandler); 
  },
  deleteSheepEvent(eventId, errorHandler) { 
    return withErrorHandling(() => apiClient.delete(`/api/sheep/events/${eventId}`), errorHandler); 
  },

  // 羊隻歷史記錄 API
  getSheepHistory(earNum, errorHandler) { 
    return withErrorHandling(() => apiClient.get(`/api/sheep/${earNum}/history`), errorHandler); 
  },
  deleteSheepHistory(recordId, errorHandler) { 
    return withErrorHandling(() => apiClient.delete(`/api/sheep/history/${recordId}`), errorHandler); 
  },

  // AI 代理 API
  getAgentTip(apiKey, errorHandler) {
    return withErrorHandling(() => apiClient.get('/api/agent/tip', { headers: { 'X-Api-Key': apiKey } }), errorHandler);
  },
  getAgentStatus(apiKey, errorHandler) {
    return withErrorHandling(() => apiClient.get('/api/agent/status', { headers: { 'X-Api-Key': apiKey } }), errorHandler);
  },
  getRecommendation(apiKey, data, errorHandler) {
    return withErrorHandling(() => apiClient.post('/api/agent/recommendation', data, { headers: { 'X-Api-Key': apiKey } }), errorHandler);
  },
  chatWithAgent(apiKey, message, sessionId, earNumContext, imageData = null, errorHandler) {
    // 如果有圖片，使用 FormData
    if (imageData && imageData.file) {
      const formData = new FormData();
      formData.append('message', message);
      formData.append('session_id', sessionId);
      if (earNumContext) formData.append('ear_num_context', earNumContext);
      formData.append('image', imageData.file);
      
      return withErrorHandling(() => 
        apiClient.post('/api/agent/chat', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
            'X-Api-Key': apiKey
          }
        }), errorHandler);
    } else {
      // 沒有圖片時使用原來的 JSON 方式
      const payload = { message, session_id: sessionId, ear_num_context: earNumContext };
      return withErrorHandling(() => apiClient.post('/api/agent/chat', payload, { headers: { 'X-Api-Key': apiKey } }), errorHandler);
    }
  },

  // 儀表板 API
  getDashboardData(errorHandler) {
    return withErrorHandling(() => apiClient.get('/api/dashboard/data'), errorHandler);
  },
  getFarmReport(errorHandler) {
    return withErrorHandling(() => apiClient.get('/api/dashboard/farm_report'), errorHandler);
  },

  // 成本 / 收益管理 API
  listCostEntries(params = {}, errorHandler) {
    return withErrorHandling(() => apiClient.get('/api/finance/costs', { params }), errorHandler);
  },
  createCostEntry(data, errorHandler) {
    return withErrorHandling(() => apiClient.post('/api/finance/costs', data), errorHandler);
  },
  updateCostEntry(id, data, errorHandler) {
    return withErrorHandling(() => apiClient.put(`/api/finance/costs/${id}`, data), errorHandler);
  },
  deleteCostEntry(id, errorHandler) {
    return withErrorHandling(() => apiClient.delete(`/api/finance/costs/${id}`), errorHandler);
  },
  bulkImportCostEntries(entries, errorHandler) {
    return withErrorHandling(() => apiClient.post('/api/finance/costs/bulk-import', { entries }), errorHandler);
  },
  listRevenueEntries(params = {}, errorHandler) {
    return withErrorHandling(() => apiClient.get('/api/finance/revenues', { params }), errorHandler);
  },
  createRevenueEntry(data, errorHandler) {
    return withErrorHandling(() => apiClient.post('/api/finance/revenues', data), errorHandler);
  },
  updateRevenueEntry(id, data, errorHandler) {
    return withErrorHandling(() => apiClient.put(`/api/finance/revenues/${id}`, data), errorHandler);
  },
  deleteRevenueEntry(id, errorHandler) {
    return withErrorHandling(() => apiClient.delete(`/api/finance/revenues/${id}`), errorHandler);
  },
  bulkImportRevenueEntries(entries, errorHandler) {
    return withErrorHandling(() => apiClient.post('/api/finance/revenues/bulk-import', { entries }), errorHandler);
  },

  runCohortAnalysis(payload, errorHandler) {
    return withErrorHandling(() => apiClient.post('/api/bi/cohort-analysis', payload), errorHandler);
  },
  runCostBenefit(payload, errorHandler) {
    return withErrorHandling(() => apiClient.post('/api/bi/cost-benefit', payload), errorHandler);
  },
  generateAnalyticsReport(payload, apiKey, errorHandler) {
    const config = apiKey ? { headers: { 'X-Api-Key': apiKey } } : {};
    return withErrorHandling(() => apiClient.post('/api/agent/analytics-report', payload, config), errorHandler);
  },

  // 資料管理 API
  exportExcel(errorHandler) { 
    return withErrorHandling(() => apiClient.get('/api/data/export_excel', { responseType: 'blob' }), errorHandler); 
  },
  analyzeExcel(file, errorHandler) {
    const formData = new FormData();
    formData.append('file', file);
    return withErrorHandling(() => apiClient.post('/api/data/analyze_excel', formData, { 
      headers: { 'Content-Type': 'multipart/form-data' } 
    }), errorHandler);
  },
  requestAiImportMapping(file, apiKey, errorHandler) {
    const formData = new FormData();
    formData.append('file', file);
    const headers = { 'Content-Type': 'multipart/form-data' };
    if (apiKey) {
      headers['X-Api-Key'] = apiKey;
    }

    return withErrorHandling(() => apiClient.post('/api/data/ai_import_mapping', formData, {
      headers
    }), errorHandler);
  },
  processImport(file, isDefaultMode, mappingConfig = {}, errorHandler) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('is_default_mode', isDefaultMode);
    if (!isDefaultMode) {
      formData.append('mapping_config', JSON.stringify(mappingConfig));
    }
    return withErrorHandling(() => apiClient.post('/api/data/process_import', formData, { 
      headers: { 'Content-Type': 'multipart/form-data' } 
    }), errorHandler);
  },

  // 事件選項管理 API
  getEventOptions(errorHandler) { 
    return withErrorHandling(() => apiClient.get('/api/dashboard/event_options'), errorHandler); 
  },
  addEventType(name, errorHandler) { 
    return withErrorHandling(() => apiClient.post('/api/dashboard/event_types', { name }), errorHandler); 
  },
  deleteEventType(typeId, errorHandler) { 
    return withErrorHandling(() => apiClient.delete(`/api/dashboard/event_types/${typeId}`), errorHandler); 
  },
  addEventDescription(typeId, description, errorHandler) {
    return withErrorHandling(() => apiClient.post('/api/dashboard/event_descriptions', { 
      event_type_option_id: typeId, 
      description: description 
    }), errorHandler);
  },
  deleteEventDescription(descId, errorHandler) { 
    return withErrorHandling(() => apiClient.delete(`/api/dashboard/event_descriptions/${descId}`), errorHandler); 
  },

  // 羊隻生長預測 API
  getSheepPrediction(earTag, targetDays, apiKey, errorHandler) {
    return withErrorHandling(() => apiClient.get(`/api/prediction/goats/${earTag}/prediction?target_days=${targetDays}`, {
      headers: { 'X-Api-Key': apiKey }
    }), errorHandler);
  },
  getPredictionChartData(earTag, targetDays, apiKey, errorHandler) {
    return withErrorHandling(() => apiClient.get(`/api/prediction/goats/${earTag}/prediction/chart-data?target_days=${targetDays}`, {
      headers: { 'X-Api-Key': apiKey }
    }), errorHandler);
  },

  // 產銷履歷 API
  getTraceabilityBatches(includeDetails = false, errorHandler) {
    const params = includeDetails ? { include_details: true } : undefined;
    return withErrorHandling(() => apiClient.get('/api/traceability/batches', { params }), errorHandler);
  },
  createTraceabilityBatch(data, errorHandler) {
    return withErrorHandling(() => apiClient.post('/api/traceability/batches', data), errorHandler);
  },
  getTraceabilityBatch(batchId, errorHandler) {
    return withErrorHandling(() => apiClient.get(`/api/traceability/batches/${batchId}`), errorHandler);
  },
  updateTraceabilityBatch(batchId, data, errorHandler) {
    return withErrorHandling(() => apiClient.put(`/api/traceability/batches/${batchId}`, data), errorHandler);
  },
  deleteTraceabilityBatch(batchId, errorHandler) {
    return withErrorHandling(() => apiClient.delete(`/api/traceability/batches/${batchId}`), errorHandler);
  },
  replaceBatchSheepLinks(batchId, sheepLinks, errorHandler) {
    const payload = { sheep_links: sheepLinks };
    return withErrorHandling(() => apiClient.post(`/api/traceability/batches/${batchId}/sheep`, payload), errorHandler);
  },
  removeBatchSheep(batchId, sheepId, errorHandler) {
    return withErrorHandling(() => apiClient.delete(`/api/traceability/batches/${batchId}/sheep/${sheepId}`), errorHandler);
  },
  addProcessingStep(batchId, data, errorHandler) {
    return withErrorHandling(() => apiClient.post(`/api/traceability/batches/${batchId}/steps`, data), errorHandler);
  },
  updateProcessingStep(stepId, data, errorHandler) {
    return withErrorHandling(() => apiClient.put(`/api/traceability/steps/${stepId}`, data), errorHandler);
  },
  deleteProcessingStep(stepId, errorHandler) {
    return withErrorHandling(() => apiClient.delete(`/api/traceability/steps/${stepId}`), errorHandler);
  },
  getPublicTraceBatch(batchNumber, errorHandler) {
    return withErrorHandling(() => apiClient.get(`/api/traceability/public/${batchNumber}`), errorHandler);
  },
  verifyHashChain(params = {}, errorHandler) {
    return withErrorHandling(() => apiClient.get('/api/verify/chain', { params }), errorHandler);
  },

  // IoT 裝置與自動化規則 API
  getIotDevices(errorHandler) {
    return withErrorHandling(() => apiClient.get('/api/iot/devices'), errorHandler);
  },
  getIotDevice(deviceId, errorHandler) {
    return withErrorHandling(() => apiClient.get(`/api/iot/devices/${deviceId}`), errorHandler);
  },
  createIotDevice(data, errorHandler) {
    return withErrorHandling(() => apiClient.post('/api/iot/devices', data), errorHandler);
  },
  updateIotDevice(deviceId, data, errorHandler) {
    return withErrorHandling(() => apiClient.put(`/api/iot/devices/${deviceId}`, data), errorHandler);
  },
  deleteIotDevice(deviceId, errorHandler) {
    return withErrorHandling(() => apiClient.delete(`/api/iot/devices/${deviceId}`), errorHandler);
  },
  getDeviceSensorReadings(deviceId, params = {}, errorHandler) {
    return withErrorHandling(() => apiClient.get(`/api/iot/devices/${deviceId}/readings`, { params }), errorHandler);
  },
  getAutomationRules(errorHandler) {
    return withErrorHandling(() => apiClient.get('/api/iot/rules'), errorHandler);
  },
  createAutomationRule(data, errorHandler) {
    return withErrorHandling(() => apiClient.post('/api/iot/rules', data), errorHandler);
  },
  updateAutomationRule(ruleId, data, errorHandler) {
    return withErrorHandling(() => apiClient.put(`/api/iot/rules/${ruleId}`, data), errorHandler);
  },
  deleteAutomationRule(ruleId, errorHandler) {
    return withErrorHandling(() => apiClient.delete(`/api/iot/rules/${ruleId}`), errorHandler);
  },

  // 活動日誌 / 系統追蹤
  getActivityLogs(params = {}, errorHandler) {
    return withErrorHandling(() => apiClient.get('/api/activity/logs', { params }), errorHandler);
  },

  // 原始錯誤處理包裝函數，供外部使用
  withErrorHandling
};