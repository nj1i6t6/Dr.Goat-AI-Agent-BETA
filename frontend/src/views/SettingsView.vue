<template>
  <div class="settings-page">
    <h1 class="page-title">
      <el-icon><Setting /></el-icon>
      系統設定
    </h1>

    <!-- 介面字體大小 -->
    <el-card shadow="never" class="font-card">
      <template #header><div class="card-header">介面字體大小</div></template>
      <p>
        針對視覺需求調整整體字級。預設值符合目前設計建議，選擇「大字級」或「超大字級」可於各頁面放大文字，方便熟齡使用者閱讀。
      </p>
      <el-radio-group v-model="fontScaleValue" class="font-scale-radio" size="large">
        <el-radio-button :label="FONT_SCALE.DEFAULT">預設字級（建議）</el-radio-button>
        <el-radio-button :label="FONT_SCALE.LARGE">大字級（放大 12.5%）</el-radio-button>
        <el-radio-button :label="FONT_SCALE.EXTRA_LARGE">超大字級（放大 25%）</el-radio-button>
      </el-radio-group>
      <div class="font-scale-preview" role="list" aria-label="字級預覽">
        <div
          role="listitem"
          class="preview-card preview-card--default"
          :class="{ active: fontScaleValue === FONT_SCALE.DEFAULT }"
        >
          <div class="preview-title">預設字級</div>
          <div class="preview-description">常用段落會以 16px 為基準。</div>
        </div>
        <div
          role="listitem"
          class="preview-card preview-card--large"
          :class="{ active: fontScaleValue === FONT_SCALE.LARGE }"
        >
          <div class="preview-title">大字級</div>
          <div class="preview-description">放大至約 18px，適合需要更高可讀性的使用情境。</div>
        </div>
        <div
          role="listitem"
          class="preview-card preview-card--extra-large"
          :class="{ active: fontScaleValue === FONT_SCALE.EXTRA_LARGE }"
        >
          <div class="preview-title">超大字級</div>
          <div class="preview-description">放大至約 20px，適合需要非常高可讀性的使用情境。</div>
        </div>
      </div>
      <p class="font-scale-hint">此設定會記住在瀏覽器中，重新整理或再次登入都會維持目前字級。</p>
    </el-card>

    <!-- API 金鑰設定 -->
    <el-card shadow="never">
      <template #header><div class="card-header">Gemini API 金鑰設定</div></template>
      <p>請在此輸入您的 Google Gemini API 金鑰。此金鑰將被儲存在您的瀏覽器本地，用於與領頭羊博士 AI 進行通訊。</p>
      <el-input v-model="apiKeyInput" placeholder="在此貼上您的 API 金鑰" show-password clearable />
      <div class="api-key-status" :class="apiKeyStatus.type">
        {{ apiKeyStatus.message }}
      </div>
      <el-button type="primary" :loading="testLoading" @click="handleTestAndSaveApiKey">
        測試並儲存金鑰
      </el-button>
    </el-card>

    <!-- 事件選項管理 -->
    <el-card shadow="never" class="event-options-card">
      <template #header><div class="card-header">事件選項管理</div></template>
      <p>您可以在這裡自訂事件記錄時的「事件類型」和對應的「簡要描述」選項。預設選項無法刪除。</p>
      
      <div class="add-type-form">
        <el-input v-model="newEventType" placeholder="輸入新的事件類型名稱" @keyup.enter="handleAddEventType" />
        <el-button type="success" :icon="Plus" @click="handleAddEventType">新增類型</el-button>
      </div>

      <el-collapse v-model="activeCollapseItems" v-loading="optionsLoading">
        <el-empty v-if="!eventOptions.length && !optionsLoading" description="尚未有任何事件選項" />
        <el-collapse-item v-for="type in eventOptions" :key="type.id" :name="type.id">
          <template #title>
            <span class="collapse-title">{{ type.name }}</span>
            <el-tag v-if="type.is_default" type="info" size="small" effect="plain" class="title-tag">預設</el-tag>
            <el-tag type="primary" size="small" effect="plain" class="title-tag">{{ type.descriptions.length }} 個描述</el-tag>
          </template>
          
          <div class="description-list">
            <div v-for="desc in type.descriptions" :key="desc.id" class="description-item">
              <span>{{ desc.description }}</span>
              <el-button
                v-if="!desc.is_default"
                type="danger"
                :icon="Delete"
                @click="handleDeleteDescription(desc.id)"
                size="small"
                circle
                plain
              />
            </div>
            <div class="add-description-form">
              <el-input v-model="newDescriptions[type.id]" placeholder="為此類型新增簡要描述" size="small" @keyup.enter="handleAddDescription(type.id)" />
              <el-button type="primary" @click="handleAddDescription(type.id)" size="small">新增描述</el-button>
            </div>
          </div>
          
          <div v-if="!type.is_default" class="type-actions">
            <el-popconfirm
              title="確定要刪除此類型嗎？其下所有描述將一併刪除。"
              @confirm="handleDeleteType(type.id)"
              width="250"
            >
              <template #reference>
                <el-button type="danger" plain size="small">刪除整個「{{ type.name }}」類型</el-button>
              </template>
            </el-popconfirm>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue';
import { Setting, Plus, Delete } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { useSettingsStore, FONT_SCALE } from '../stores/settings';
import api from '../api';

const settingsStore = useSettingsStore();

// API Key State
const apiKeyInput = ref('');
const testLoading = ref(false);
const apiKeyStatus = reactive({ type: 'info', message: '尚未設定 API 金鑰。' });

// Event Options State
const optionsLoading = ref(false);
const eventOptions = ref([]);
const newEventType = ref('');
const newDescriptions = reactive({});
const activeCollapseItems = ref([]);

const fontScaleValue = computed({
  get: () => settingsStore.fontScale,
  set: (value) => settingsStore.setFontScale(value),
});

const updateApiKeyStatus = () => {
  if (settingsStore.hasApiKey) {
    apiKeyStatus.type = 'success';
    apiKeyStatus.message = '已載入儲存的 API 金鑰。建議點擊測試以驗證其有效性。';
  } else {
    apiKeyStatus.type = 'error';
    apiKeyStatus.message = '尚未設定 API 金鑰。';
  }
};

const handleTestAndSaveApiKey = async () => {
  if (!apiKeyInput.value) {
    ElMessage.error('請輸入 API 金鑰');
    return;
  }
  testLoading.value = true;
  apiKeyStatus.type = 'info';
  apiKeyStatus.message = '正在測試金鑰...';
  try {
    await api.getAgentTip(apiKeyInput.value);
    settingsStore.setApiKey(apiKeyInput.value);
    apiKeyStatus.type = 'success';
    apiKeyStatus.message = 'API 金鑰驗證成功！已儲存。';
    ElMessage.success('API 金鑰已儲存');
  } catch (error) {
    settingsStore.clearApiKey();
    apiKeyStatus.type = 'error';
    apiKeyStatus.message = `金鑰驗證失敗: ${error.error || error.message}`;
    ElMessage.error('金鑰驗證失敗');
  } finally {
    testLoading.value = false;
  }
};

const fetchEventOptions = async () => {
  optionsLoading.value = true;
  try {
    const data = await api.getEventOptions();
    eventOptions.value = data;
    // 為每個類型初始化一個空的 newDescriptions 屬性
    data.forEach(type => {
      if (!newDescriptions[type.id]) {
        newDescriptions[type.id] = '';
      }
    });
  } catch (error) {
    ElMessage.error(`載入事件選項失敗: ${error.error || error.message}`);
  } finally {
    optionsLoading.value = false;
  }
};

const handleAddEventType = async () => {
  const name = newEventType.value.trim();
  if (!name) {
    ElMessage.warning('請輸入事件類型名稱');
    return;
  }
  try {
    await api.addEventType(name);
    ElMessage.success('事件類型新增成功');
    newEventType.value = '';
    await fetchEventOptions();
  } catch (error) {
    ElMessage.error(`新增失敗: ${error.error || error.message}`);
  }
};

const handleDeleteType = async (typeId) => {
  try {
    await api.deleteEventType(typeId);
    ElMessage.success('事件類型已刪除');
    await fetchEventOptions();
  } catch (error) {
    ElMessage.error(`刪除失敗: ${error.error || error.message}`);
  }
};

const handleAddDescription = async (typeId) => {
  const description = newDescriptions[typeId]?.trim();
  if (!description) {
    ElMessage.warning('請輸入簡要描述內容');
    return;
  }
  try {
    await api.addEventDescription(typeId, description);
    ElMessage.success('簡要描述新增成功');
    newDescriptions[typeId] = '';
    await fetchEventOptions();
  } catch (error) {
    ElMessage.error(`新增失敗: ${error.error || error.message}`);
  }
};

const handleDeleteDescription = async (descId) => {
  try {
    await api.deleteEventDescription(descId);
    ElMessage.success('簡要描述已刪除');
    await fetchEventOptions();
  } catch (error) {
    ElMessage.error(`刪除失敗: ${error.error || error.message}`);
  }
};

onMounted(() => {
  apiKeyInput.value = settingsStore.apiKey;
  updateApiKeyStatus();
  fetchEventOptions();
});
</script>

<style scoped>
.settings-page { animation: fadeIn 0.5s ease-out; }
.page-title {
  font-size: 1.75rem; color: #1e3a8a; margin-top: 0;
  margin-bottom: 1.25rem; display: flex; align-items: center;
}
.page-title .el-icon { margin-right: 0.625rem; }
.card-header { font-size: 1.125rem; font-weight: bold; }
.el-card { margin-bottom: 1.5rem; }

.api-key-status {
  margin: 0.625rem 0;
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
  font-size: 0.9375rem;
}
.api-key-status.info { background-color: #f4f4f5; color: #909399; }
.api-key-status.success { background-color: #f0f9eb; color: #67c23a; }
.api-key-status.error { background-color: #fef0f0; color: #f56c6c; }

.font-card p {
  margin-bottom: 0.5rem;
}


.font-scale-radio {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.font-scale-preview {
  margin-top: 1rem;
  display: grid;
  gap: 0.75rem;
  grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
}

.preview-card {
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  padding: 1rem;
  background: white;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.preview-card.active {
  border-color: #2563eb;
  box-shadow: 0 0.25rem 0.75rem rgba(37, 99, 235, 0.1);
}

.preview-card--default {
  font-size: 1rem;
}

.preview-card--large {
  font-size: 1.125rem;
}

.preview-card--extra-large {
  font-size: 1.25rem;
}

.preview-title {
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.preview-description {
  color: #475569;
  line-height: 1.6;
}

.font-scale-hint {
  margin-top: 0.75rem;
  font-size: 0.875rem;
  color: #64748b;
}

.add-type-form {
  display: flex;
  gap: 0.625rem;
  margin-bottom: 1.25rem;
}

.collapse-title {
  font-size: 1.0625rem;
  font-weight: 500;
}
.title-tag {
  margin-left: 0.625rem;
}

.description-list {
  padding: 0 0.625rem;
}
.description-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f0f2f5;
}
.add-description-form {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.9375rem;
}
.type-actions {
  margin-top: 0.9375rem;
  padding-top: 0.9375rem;
  border-top: 1px dashed #dcdfe6;
  text-align: right;
}
</style>
