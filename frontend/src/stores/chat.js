import { defineStore } from 'pinia';
import { ref, reactive } from 'vue';
import api from '../api';

// 定義初始的歡迎訊息
const createInitialMessage = () => ({
  role: 'model',
  content: "<p>您好，我是領頭羊博士，請問有什麼可以為您服務的嗎？</p>"
});

export const useChatStore = defineStore('chat', () => {
  // --- State ---
  const sessionId = ref('session_' + Date.now());
  // 使用 reactive 來管理消息陣列，以便 Vue 能夠追蹤陣列內的變化
  const messages = reactive([createInitialMessage()]);
  const isLoading = ref(false);
  const error = ref('');

  // --- Actions ---

  // 發送訊息的 action
  async function sendMessage(apiKey, userMessage, earNumContext, imageData = null) {
    // 準備用戶訊息物件
    const userMessageObj = { 
      role: 'user', 
      content: userMessage || (imageData ? '請幫我分析這張山羊照片' : '')
    };
    
    // 如果有圖片，添加圖片資訊
    if (imageData) {
      userMessageObj.image = {
        url: imageData.url,
        name: imageData.name,
        type: imageData.type
      };
    }
    
    // 將用戶的訊息添加到歷史記錄中
    messages.push(userMessageObj);
    
    isLoading.value = true;
    error.value = '';

    try {
      const response = await api.chatWithAgent(
        apiKey,
        userMessage || '請幫我分析這張山羊照片',
        sessionId.value,
        earNumContext,
        imageData
      );
      // 將 AI 的回覆添加到歷史記錄中
      messages.push({ role: 'model', content: response.reply_html });
    } catch (err) {
      const errorMessage = err.error || err.message || 'AI 助理回覆時發生未知錯誤';
      error.value = errorMessage;
      // 將錯誤訊息也作為一條 AI 回覆添加到歷史記錄中
      messages.push({ role: 'model', content: `<p style="color:red;">助理回覆錯誤: ${errorMessage}</p>` });
    } finally {
      isLoading.value = false;
    }
  }

  // 清空對話歷史
  function clearChat() {
    sessionId.value = 'session_' + Date.now();
    // 清空陣列並重新加入初始訊息
    messages.length = 0;
    messages.push(createInitialMessage());
    isLoading.value = false;
    error.value = '';
  }

  return {
    sessionId,
    messages,
    isLoading,
    error,
    sendMessage,
    clearChat,
  };
});