<template>
  <div class="chat-page">
    <h1 class="page-title">
      <el-icon><Service /></el-icon>
  羊博士問答
    </h1>

    <el-card shadow="never">
      <div class="chat-controls">
        <!-- 使用 el-select-v2 虛擬化選擇器 -->
        <el-select-v2
          v-model="selectedEarNum"
          :options="sheepOptions"
          placeholder="針對羊隻 (選填)"
          clearable
          filterable
          class="context-select"
          :loading="sheepStore.isLoading"
        />

        <el-input
          v-model="manualEarNumInput"
          placeholder="或手動輸入耳號查詢"
          clearable
          class="manual-input"
          @keyup.enter="handleManualSearch"
        >
          <template #append>
            <el-button :icon="Search" @click="handleManualSearch" />
          </template>
        </el-input>

        <el-button @click="chatStore.clearChat" :icon="Delete" class="clear-btn">清空對話</el-button>
      </div>

      <div class="chat-container" ref="chatContainerRef">
        <div
          v-for="(message, index) in chatStore.messages"
          :key="index"
          class="chat-message"
          :class="message.role"
        >
          <div v-if="message.role === 'user'" class="message-content">
            <!-- 顯示用戶上傳的圖片 -->
            <div v-if="message.image" class="message-image">
              <img :src="message.image.url" :alt="message.image.name" class="chat-image" />
              <p class="image-caption">{{ message.image.name }}</p>
            </div>
            <!-- 顯示用戶文字 -->
            <div v-if="message.content" v-text="message.content"></div>
          </div>
          <div v-else class="message-content" v-html="message.content"></div>
        </div>
        <div v-if="chatStore.isLoading" class="chat-message model">
          <div class="loading-dots">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>

      <div class="chat-input-area">
        <!-- 圖片預覽區域 -->
        <div v-if="selectedImage" class="image-preview">
          <div class="image-preview-container">
            <img :src="selectedImage.url" alt="預覽圖片" class="preview-image" />
            <el-button
              type="danger"
              :icon="Delete"
              circle
              size="small"
              class="remove-image-btn"
              @click="removeSelectedImage"
            />
          </div>
          <p class="image-name">{{ selectedImage.name }}</p>
        </div>
        
        <div class="input-controls">
          <el-input
            v-model="userInput"
            type="textarea"
            :rows="2"
            placeholder="輸入您的問題..."
            resize="none"
            @keyup.enter.prevent="handleSendMessage"
          />
          <div class="input-buttons">
            <!-- 照片上傳按鈕 -->
            <input
              ref="fileInputRef"
              type="file"
              accept="image/*"
              @change="handleImageSelect"
              style="display: none;"
            />
            <el-button
              type="info"
              :icon="Picture"
              @click="openFileSelector"
              :disabled="chatStore.isLoading"
              title="上傳山羊照片"
            >
              上傳照片
            </el-button>
            <el-button
              type="primary"
              @click="handleSendMessage"
              :loading="chatStore.isLoading"
              :disabled="!userInput.trim() && !selectedImage"
            >
              發送
            </el-button>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue';
import { Service, Delete, Search, Picture } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { useSettingsStore } from '../stores/settings';
import { useChatStore } from '../stores/chat';
import { useSheepStore } from '../stores/sheep';

const settingsStore = useSettingsStore();
const chatStore = useChatStore();
const sheepStore = useSheepStore();

const selectedEarNum = ref('');
const userInput = ref('');
const manualEarNumInput = ref('');
const chatContainerRef = ref(null);
const fileInputRef = ref(null);
const selectedImage = ref(null);

// 為 el-select-v2 準備符合其格式的選項陣列
const sheepOptions = computed(() => 
  sheepStore.sortedSheepList.map(sheep => ({
    value: sheep.EarNum,
    label: `${sheep.EarNum} (${sheep.Breed || '未知品種'})`
  }))
);

const scrollToBottom = () => {
  nextTick(() => {
    if (chatContainerRef.value) {
      chatContainerRef.value.scrollTop = chatContainerRef.value.scrollHeight;
    }
  });
};

watch(() => chatStore.messages, scrollToBottom, { deep: true });

const handleManualSearch = () => {
  const earNumToFind = manualEarNumInput.value.trim();
  if (!earNumToFind) {
    ElMessage.warning('請輸入要查詢的耳號');
    return;
  }
  
  const found = sheepStore.sheepList.some(sheep => sheep.EarNum === earNumToFind);
  
  if (found) {
    selectedEarNum.value = earNumToFind;
    ElMessage.success(`已成功定位到羊隻 ${earNumToFind}`);
    manualEarNumInput.value = '';
  } else {
    ElMessage.error(`在您的羊群中找不到耳號為 ${earNumToFind} 的羊隻`);
  }
};

const handleSendMessage = async () => {
  if (!userInput.value.trim() && !selectedImage.value) return;
  if (!settingsStore.hasApiKey) {
    ElMessage.error('請先在「系統設定」中設定並測試有效的 API 金鑰');
    return;
  }
  
  const messageToSend = userInput.value;
  const imageToSend = selectedImage.value;
  
  // 清空輸入
  userInput.value = '';
  selectedImage.value = null;
  
  await chatStore.sendMessage(settingsStore.apiKey, messageToSend, selectedEarNum.value, imageToSend);
};

const openFileSelector = () => {
  fileInputRef.value?.click();
};

const handleImageSelect = (event) => {
  const file = event.target.files[0];
  if (!file) return;
  
  // 檢查檔案類型
  if (!file.type.startsWith('image/')) {
    ElMessage.error('請選擇圖片檔案');
    return;
  }
  
  // 檢查檔案大小 (限制為 10MB)
  const maxSize = 10 * 1024 * 1024; // 10MB
  if (file.size > maxSize) {
    ElMessage.error('圖片檔案不能超過 10MB');
    return;
  }
  
  // 讀取檔案並創建預覽
  const reader = new FileReader();
  reader.onload = (e) => {
    selectedImage.value = {
      file: file,
      url: e.target.result,
      name: file.name,
      size: file.size,
      type: file.type
    };
  };
  reader.readAsDataURL(file);
  
  // 清空檔案輸入，允許重複選擇同一檔案
  event.target.value = '';
};

const removeSelectedImage = () => {
  selectedImage.value = null;
};

onMounted(() => {
  sheepStore.fetchSheepList();
  scrollToBottom();
});
</script>

<style scoped>
/* 樣式保持不變 */
.chat-page {
  animation: fadeIn 0.5s ease-out;
}
.page-title {
  font-size: 1.8em; color: #1e3a8a; margin-top: 0;
  margin-bottom: 20px; display: flex; align-items: center;
}
.page-title .el-icon {
  margin-right: 10px;
}
.chat-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 20px;
  align-items: center;
}
.context-select {
  flex: 1 1 250px;
}
.manual-input {
  flex: 1 1 200px;
}
.clear-btn {
  margin-left: auto;
}
.chat-container {
  height: calc(100vh - 420px);
  min-height: 300px;
  border: 1px solid #e5e7eb;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  background-color: #f9fafb;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.chat-message {
  display: flex;
  margin-bottom: 15px;
  max-width: 85%;
}
.chat-message.user {
  justify-content: flex-end;
  align-self: flex-end;
}
.chat-message.model {
  justify-content: flex-start;
  align-self: flex-start;
}
.message-content {
  padding: 12px 18px;
  border-radius: 12px;
  word-wrap: break-word;
  line-height: 1.6;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.chat-message.user .message-content {
  background-color: #3b82f6;
  color: white;
  border-bottom-right-radius: 3px;
}
.chat-message.model .message-content {
  background-color: #ffffff;
  color: #374151;
  border: 1px solid #e5e7eb;
  border-bottom-left-radius: 3px;
}
.chat-input-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.image-preview {
  padding: 12px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px dashed #d1d5db;
}
.image-preview-container {
  position: relative;
  display: inline-block;
}
.preview-image {
  max-width: 200px;
  max-height: 150px;
  border-radius: 6px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.remove-image-btn {
  position: absolute;
  top: -8px;
  right: -8px;
  background-color: #f56c6c;
  border-color: #f56c6c;
}
.image-name {
  margin: 8px 0 0 0;
  font-size: 0.85em;
  color: #6b7280;
}
.input-controls {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}
.input-controls .el-textarea {
  flex: 1;
}
.input-buttons {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}
.message-image {
  margin-bottom: 8px;
}
.chat-image {
  max-width: 250px;
  max-height: 200px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.image-caption {
  margin: 6px 0 0 0;
  font-size: 0.8em;
  color: #9ca3af;
  font-style: italic;
}
.loading-dots span {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #909399;
  margin: 0 2px;
  animation: bounce 1.4s infinite ease-in-out both;
}
.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1.0); }
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>