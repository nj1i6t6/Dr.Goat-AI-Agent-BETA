<template>
  <div class="data-management-page">
    <h1 class="page-title">
      <el-icon><Upload /></el-icon>
      數據管理中心
    </h1>

    <!-- 資料匯出 -->
    <el-card shadow="never">
      <template #header><div class="card-header">資料匯出</div></template>
      <p>將您帳戶中所有的羊隻基礎資料、事件日誌、歷史數據及 AI 聊天記錄備份為一份完整的 Excel (.xlsx) 檔案。</p>
      <el-button type="primary" :loading="exportLoading" @click="handleExport" :icon="Download">
        匯出全部資料
      </el-button>
    </el-card>

    <!-- 資料導入 -->
    <h2 class="section-title">資料導入</h2>
    <el-tabs v-model="activeTab" type="border-card" class="import-tabs">
      <!-- 快速導入 -->
      <el-tab-pane label="快速導入 (使用標準範本)" name="default">
        <el-steps :active="defaultStep" finish-status="success" simple>
          <el-step title="下載範本" />
          <el-step title="上傳檔案" />
          <el-step title="執行導入" />
        </el-steps>
        <div class="step-content">
          <h4>步驟一：下載並填寫標準範本</h4>
          <p>請下載系統提供的標準 Excel 範本，並將您的數據按照範本的格式填寫。</p>
          <a href="/templates/goat_import_template.xlsx" download>
            <el-button type="success" :icon="Download">下載標準範本.xlsx</el-button>
          </a>
          <el-divider />
          <h4>步驟二：上傳已填寫的範本檔案</h4>
          <el-upload
            drag
            action="#"
            :auto-upload="false"
            :on-change="handleDefaultFileChange"
            :limit="1"
            :on-exceed="handleFileExceed"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">將檔案拖曳至此，或<em>點擊上傳</em></div>
          </el-upload>
          <el-divider />
          <h4>步驟三：執行導入</h4>
          <el-button type="primary" :disabled="!defaultFile" :loading="defaultImportLoading" @click="handleProcessImport(true)">
            執行快速導入
          </el-button>
          <div v-if="defaultImportResult" class="import-result" v-html="defaultImportResult"></div>
        </div>
      </el-tab-pane>

      <!-- 自訂導入 -->
      <el-tab-pane label="自訂導入 (使用我的格式)" name="custom">
        <el-steps :active="customStep" finish-status="success" simple>
          <el-step title="上傳檔案" />
          <el-step title="設定映射" />
          <el-step title="執行導入" />
        </el-steps>
        <div class="step-content">
          <h4>步驟一：上傳您的 Excel 檔案</h4>
          <el-upload
            drag
            action="#"
            :auto-upload="false"
            :on-change="handleCustomFileChange"
            :limit="1"
            :on-exceed="handleFileExceed"
            v-loading="customAnalysisLoading"
          >
             <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">將檔案拖曳至此，或<em>點擊上傳</em></div>
          </el-upload>
          <div v-if="customAnalyzedData">
            <el-divider />
            <h4>步驟二：設定工作表用途與欄位映射</h4>
            <SheetMappingConfigurator
              :sheets="customAnalyzedData.sheets"
              :mapping-state="mappingConfig"
              :sheet-purpose-options="sheetPurposeOptions"
              :system-field-mappings="systemFieldMappings"
              @update-mapping="handleCustomMappingUpdate"
            />
            <el-divider />
            <h4>步驟三：執行導入</h4>
            <el-button type="primary" :loading="customImportLoading" @click="handleProcessImport(false)">執行導入</el-button>
            <div v-if="customImportResult" class="import-result" v-html="customImportResult"></div>
          </div>
        </div>
      </el-tab-pane>

      <!-- AI 智慧導入 -->
      <el-tab-pane label="AI 智慧導入 (Beta)" name="ai">
        <el-steps :active="aiStep" finish-status="success" simple>
          <el-step title="上傳檔案" />
          <el-step title="AI 分析與審核" />
          <el-step title="執行導入" />
        </el-steps>
        <div class="step-content">
          <h4>步驟一：上傳您的 Excel 檔案</h4>
          <el-upload
            drag
            action="#"
            :auto-upload="false"
            :on-change="handleAiFileChange"
            :limit="1"
            :on-exceed="handleFileExceed"
            v-loading="aiAnalysisLoading"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">將檔案拖曳至此，或<em>點擊上傳</em></div>
          </el-upload>

          <div v-if="aiAnalysisLoading" class="ai-status">
            <el-alert title="AI 分析中，請稍候..." type="info" :closable="false" show-icon />
          </div>

          <div v-if="aiAnalyzedData">
            <el-divider />
            <h4>步驟二：審核 AI 建議</h4>
            <el-alert
              v-if="aiSummary"
              :title="aiSummary"
              type="success"
              show-icon
              :closable="false"
              class="ai-summary-alert"
            />
            <el-alert
              v-for="(warning, index) in aiWarnings"
              :key="`ai-warning-${index}`"
              :title="warning"
              type="warning"
              show-icon
              :closable="false"
              class="ai-warning-alert"
            />

            <SheetMappingConfigurator
              :sheets="aiAnalyzedData.sheets"
              :mapping-state="aiMappingConfig"
              :sheet-purpose-options="sheetPurposeOptions"
              :system-field-mappings="systemFieldMappings"
              :sheet-insights="aiInsights"
              @update-mapping="handleAiMappingUpdate"
            />

            <el-divider />
            <h4>步驟三：確認並執行導入</h4>
            <el-button
              type="primary"
              :disabled="!aiFile"
              :loading="aiImportLoading"
              @click="handleAiImport"
            >
              使用 AI 建議執行導入
            </el-button>
            <div v-if="aiImportResult" class="import-result" v-html="aiImportResult"></div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { Upload, Download, UploadFilled } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import api from '../api';
import SheetMappingConfigurator from '../components/common/SheetMappingConfigurator.vue';
import { sheetPurposeOptions, systemFieldMappings } from '../utils';
import { useSettingsStore } from '../stores/settings';

const activeTab = ref('default');
const exportLoading = ref(false);

const settingsStore = useSettingsStore();

// Default Import State
const defaultStep = ref(1);
const defaultFile = ref(null);
const defaultImportLoading = ref(false);
const defaultImportResult = ref('');

// Custom Import State
const customStep = ref(0);
const customFile = ref(null);
const customAnalysisLoading = ref(false);
const customAnalyzedData = ref(null);
const mappingConfig = reactive({});
const customImportLoading = ref(false);
const customImportResult = ref('');

// AI Import State
const aiStep = ref(0);
const aiFile = ref(null);
const aiAnalysisLoading = ref(false);
const aiAnalyzedData = ref(null);
const aiMappingConfig = reactive({});
const aiInsights = reactive({});
const aiWarnings = ref([]);
const aiSummary = ref('');
const aiImportLoading = ref(false);
const aiImportResult = ref('');

const getEffectiveApiKey = () => (
  (settingsStore.apiKey || localStorage.getItem('geminiApiKey') || localStorage.getItem('gemini_api_key') || '').trim()
);

const resetReactiveObject = (target) => {
  Object.keys(target).forEach((key) => delete target[key]);
};

const ensureSheetConfig = (target, sheetName) => {
  if (!target[sheetName]) {
    target[sheetName] = { purpose: '', columns: {} };
  }
  if (!target[sheetName].columns) {
    target[sheetName].columns = {};
  }
  return target[sheetName];
};

const updateMappingConfig = (target, payload) => {
  const { sheetName, purpose, fieldKey, column } = payload;
  if (!sheetName) return;

  const entry = ensureSheetConfig(target, sheetName);

  if (purpose !== undefined) {
    entry.purpose = purpose;
    if (!purpose || purpose === 'ignore') {
      entry.columns = {};
    }
  }

  if (fieldKey) {
    if (column) {
      entry.columns[fieldKey] = column;
    } else {
      delete entry.columns[fieldKey];
    }
  }
};

const handleCustomMappingUpdate = (payload) => updateMappingConfig(mappingConfig, payload);
const handleAiMappingUpdate = (payload) => updateMappingConfig(aiMappingConfig, payload);

const handleExport = async () => {
  exportLoading.value = true;
  try {
    const response = await api.exportExcel();
    const contentDisposition = response.headers['content-disposition'];
    let filename = 'goat_data_export.xlsx';
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="(.+)"/);
      if (filenameMatch && filenameMatch.length > 1) {
        filename = filenameMatch[1];
      }
    }
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    ElMessage.success('檔案已成功匯出');
  } catch (error) {
    ElMessage.error(`匯出失敗: ${error.error || error.message}`);
  } finally {
    exportLoading.value = false;
  }
};

const handleFileExceed = (files) => {
  ElMessage.warning(`一次只能上傳一個檔案，您已選擇 ${files.length} 個檔案`);
};

const handleDefaultFileChange = (file) => {
  defaultFile.value = file.raw;
  defaultStep.value = 2;
  defaultImportResult.value = '';
};

const handleCustomFileChange = async (file) => {
  customFile.value = file.raw;
  customStep.value = 1;
  customAnalysisLoading.value = true;
  customImportResult.value = '';
  customAnalyzedData.value = null;
  resetReactiveObject(mappingConfig);

  try {
    const result = await api.analyzeExcel(customFile.value);
    customAnalyzedData.value = result;
    if (result?.sheets) {
      Object.keys(result.sheets).forEach((sheetName) => {
        mappingConfig[sheetName] = { purpose: '', columns: {} };
      });
    }
    customStep.value = 2;
  } catch (error) {
    ElMessage.error(`檔案分析失敗: ${error.error || error.message}`);
    customStep.value = 0;
  } finally {
    customAnalysisLoading.value = false;
  }
};

const handleAiFileChange = async (file) => {
  aiFile.value = file.raw;
  aiStep.value = 1;
  aiImportResult.value = '';
  aiSummary.value = '';
  aiWarnings.value = [];
  aiAnalyzedData.value = null;
  resetReactiveObject(aiMappingConfig);
  resetReactiveObject(aiInsights);

  aiAnalysisLoading.value = true;
  try {
    const apiKey = getEffectiveApiKey();
    if (!apiKey) {
      throw { error: '請先在系統設定頁面儲存您的 Gemini API 金鑰。' };
    }

    const result = await api.requestAiImportMapping(aiFile.value, apiKey);
    aiAnalyzedData.value = result.analysis || null;

    const sheets = result.analysis?.sheets || {};
    const suggested = result.mapping_config?.sheets || {};
    const metadata = result.metadata || {};

    aiWarnings.value = Array.isArray(result.warnings) ? result.warnings.map((msg) => String(msg)) : [];
    if (Array.isArray(result.ai_notes)) {
      aiWarnings.value = [...aiWarnings.value, ...result.ai_notes.map((msg) => String(msg))];
    }
    aiSummary.value = typeof result.summary === 'string' ? result.summary : '';

    Object.keys(sheets).forEach((sheetName) => {
      const suggestion = suggested[sheetName] || {};
      aiMappingConfig[sheetName] = {
        purpose: suggestion.purpose || '',
        columns: { ...(suggestion.columns || {}) }
      };
      if (metadata[sheetName]) {
        aiInsights[sheetName] = metadata[sheetName];
      }
    });

    aiStep.value = 2;
  } catch (error) {
    ElMessage.error(`AI 分析失敗: ${error.error || error.message}`);
    aiStep.value = 0;
  } finally {
    aiAnalysisLoading.value = false;
  }
};

const handleProcessImport = async (isDefault, options = {}) => {
  const file = options.file ?? (isDefault ? defaultFile.value : customFile.value);
  if (!file) {
    ElMessage.error('請先上傳檔案');
    return;
  }

  const stepRef = options.stepRef ?? (isDefault ? defaultStep : customStep);
  const loadingRef = options.loadingRef ?? (isDefault ? defaultImportLoading : customImportLoading);
  const resultRef = options.resultRef ?? (isDefault ? defaultImportResult : customImportResult);
  const mappingSource = options.mapping ?? mappingConfig;
  const successMessage = options.successMessage || '導入操作完成';

  loadingRef.value = true;
  resultRef.value = '';

  try {
    const mappingPayload = isDefault ? {} : JSON.parse(JSON.stringify(mappingSource));
    const result = await api.processImport(file, isDefault, mappingPayload);
    let resultHtml = `<h4>導入報告</h4><p class="success">${result.message}</p>`;
    if (result.details && result.details.length > 0) {
      resultHtml += `<ul>${result.details.map(d => `<li><strong>${d.sheet}</strong>: ${d.message}</li>`).join('')}</ul>`;
    }

    resultRef.value = resultHtml;
    stepRef.value = 3;
    ElMessage.success(successMessage);

    if (typeof options.onSuccess === 'function') {
      options.onSuccess(result);
    }
  } catch (error) {
    const errorHtml = `<p class="error">導入失敗: ${error.error || error.message}</p>`;
    resultRef.value = errorHtml;
    ElMessage.error('導入過程中發生錯誤');
    if (typeof options.onError === 'function') {
      options.onError(error);
    }
  } finally {
    loadingRef.value = false;
  }
};

const handleAiImport = () => {
  handleProcessImport(false, {
    file: aiFile.value,
    mapping: aiMappingConfig,
    stepRef: aiStep,
    loadingRef: aiImportLoading,
    resultRef: aiImportResult,
    successMessage: 'AI 建議已成功導入'
  });
};
</script>

<style scoped>
.data-management-page { animation: fadeIn 0.5s ease-out; }
.page-title, .section-title {
  font-size: 1.8em; color: #1e3a8a; margin-top: 0;
  margin-bottom: 20px; display: flex; align-items: center;
}
.section-title { font-size: 1.5em; margin-top: 30px; }
.page-title .el-icon { margin-right: 10px; }
.card-header { font-size: 1.2em; font-weight: bold; }
.import-tabs { margin-top: 20px; }
.step-content { padding: 20px; }
.import-result {
  margin-top: 20px;
  padding: 15px;
  border-radius: 4px;
  background-color: #f4f4f5;
  border: 1px solid #e9e9eb;
}
.import-result :deep(p.success) { color: #67c23a; font-weight: bold; }
.import-result :deep(p.error) { color: #f56c6c; font-weight: bold; }
.import-result :deep(ul) { padding-left: 20px; }
.ai-status { margin-top: 16px; }
.ai-summary-alert { margin-bottom: 12px; }
.ai-warning-alert { margin-bottom: 10px; }
</style>