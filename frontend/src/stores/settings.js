import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import api from '../api'; // 導入 api 模組

export const FONT_SCALE = Object.freeze({
  DEFAULT: 'default',
  LARGE: 'large',
  EXTRA_LARGE: 'extra-large',
});

const FONT_SCALE_STORAGE_KEY = 'uiFontScale';

function normaliseFontScale(value) {
  return Object.values(FONT_SCALE).includes(value) ? value : FONT_SCALE.DEFAULT;
}

function applyFontScale(scale) {
  if (typeof document === 'undefined') return;
  const htmlEl = document.documentElement;
  const normalised = normaliseFontScale(scale);
  htmlEl.setAttribute('data-font-scale', normalised);
}

export const useSettingsStore = defineStore('settings', () => {
  // --- State ---
  const apiKey = ref(localStorage.getItem('geminiApiKey') || '');
  const fontScale = ref(normaliseFontScale(localStorage.getItem(FONT_SCALE_STORAGE_KEY)));
  // 新增：用於緩存 AI 每日提示的狀態
  const agentTip = ref({
    html: '',       // 提示的 HTML 內容
    loading: false, // 是否正在加載
    loaded: false,  // 是否已經成功加載過
  });
  const ragStatus = ref({
    available: null,
    message: '',
    detail: null,
  });

  applyFontScale(fontScale.value);

  // --- Getters ---
  const hasApiKey = computed(() => !!apiKey.value);

  // --- Actions ---
  function setApiKey(newKey) {
    apiKey.value = newKey;
    localStorage.setItem('geminiApiKey', newKey);
  }

  function clearApiKey() {
    apiKey.value = '';
    localStorage.removeItem('geminiApiKey');
  }

  function setFontScale(newScale) {
    const normalised = normaliseFontScale(newScale);
    fontScale.value = normalised;
    localStorage.setItem(FONT_SCALE_STORAGE_KEY, normalised);
    applyFontScale(normalised);
  }

  function ensureFontScaleApplied() {
    applyFontScale(fontScale.value);
  }

  // 新增：獲取並緩存 AI 每日提示的 action
  async function refreshRagStatus() {
    if (!hasApiKey.value) {
      ragStatus.value = { available: null, message: '', detail: null };
      return;
    }

    try {
      const response = await api.getAgentStatus(apiKey.value);
      ragStatus.value = {
        available: Boolean(response.rag_enabled),
        message: response.message || '',
        detail: response.detail ?? null,
      };
    } catch (error) {
      ragStatus.value = {
        available: false,
        message: `無法取得 RAG 狀態: ${error.error || error.message}`,
        detail: null,
      };
    }
  }

  async function fetchAndSetAgentTip() {
    if (agentTip.value.loading) {
      return;
    }

    if (!hasApiKey.value) {
      ragStatus.value = { available: null, message: '', detail: null };
      if (!agentTip.value.loaded) {
        agentTip.value.html = "請先在「系統設定」中設定有效的API金鑰以獲取提示。";
      }
      return;
    }

    const statusPromise = refreshRagStatus();

    if (agentTip.value.loaded) {
      await statusPromise;
      return;
    }

    agentTip.value.loading = true;
    try {
      const response = await api.getAgentTip(apiKey.value);
      agentTip.value.html = response.tip_html;
      agentTip.value.loaded = true; // 標記為已成功加載
      await statusPromise;
    } catch (error) {
      agentTip.value.html = `<span style="color:red;">無法獲取提示: ${error.error || error.message}</span>`;
      agentTip.value.loaded = true;
      await statusPromise;
    } finally {
      agentTip.value.loading = false;
    }
  }

  return {
    apiKey,
    fontScale,
    hasApiKey,
    agentTip, // 導出 agentTip 狀態
    ragStatus,
    setApiKey,
    clearApiKey,
    setFontScale,
    ensureFontScaleApplied,
    refreshRagStatus,
    fetchAndSetAgentTip, // 導出新的 action
  };
});