import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

// 使用 defineStore 來定義一個 store
// 第一個參數是 store 的唯一 ID
export const useAuthStore = defineStore('auth', () => {
  
  // --- State (狀態) ---
  // 使用 ref 來定義響應式狀態，類似於 Vue 組件中的 data
  const getUserFromStorage = () => {
    try {
      const userStr = localStorage.getItem('user');
      return userStr ? JSON.parse(userStr) : null;
    } catch (error) {
      console.warn('解析 localStorage 中的用戶資料失敗:', error);
      localStorage.removeItem('user');
      return null;
    }
  };
  const user = ref(getUserFromStorage())
  const isLoggingOut = ref(false) // 添加登出狀態標誌

  // --- Getters (計算屬性) ---
  // 使用 computed 來定義計算屬性，類似於 Vue 組件中的 computed
  const isAuthenticated = computed(() => !!user.value)
  const username = computed(() => user.value?.username || '訪客')

  // --- Actions (方法) ---
  // 定義可以用來修改狀態的函數
  async function login(credentials) {
    try {
      const response = await api.login(credentials);
      if (response.success) {
        // 登入成功，更新 user 狀態
        user.value = response.user;
        // 將用戶資訊存儲到 localStorage，以便刷新頁面後保持登入狀態
        localStorage.setItem('user', JSON.stringify(response.user));
        // 登入成功後跳轉到儀表板頁面 - 使用動態導入避免循環依賴
        const { default: router } = await import('../router')
        await router.push({ name: 'Dashboard' });
      }
      return response;
    } catch (error) {
      console.error('登入失敗:', error);
      // 將錯誤拋出，讓組件可以處理
      throw error;
    }
  }

  async function register(credentials) {
    try {
      const response = await api.register(credentials);
      if (response.success) {
        user.value = response.user;
        localStorage.setItem('user', JSON.stringify(response.user));
        // 使用動態導入避免循環依賴
        const { default: router } = await import('../router')
        await router.push({ name: 'Dashboard' });
      }
      return response;
    } catch (error) {
      console.error('註冊失敗:', error);
      throw error;
    }
  }

  async function logout() {
    // 防止重複登出
    if (isLoggingOut.value) {
      console.log('正在登出中，跳過重複請求');
      return;
    }
    
    isLoggingOut.value = true;
    
    try {
      // 即使後端請求失敗，前端也要完成登出操作
      await api.logout();
    } catch (error) {
      console.error("登出請求失敗，但將繼續執行前端登出流程:", error);
    } finally {
      // 清空狀態和 localStorage
      user.value = null;
      localStorage.removeItem('user');
      isLoggingOut.value = false;
      
      // 跳轉到登入頁面 - 使用動態導入避免循環依賴
      // 使用 replace 防止用戶透過瀏覽器返回鍵回到需要登入的頁面
      const { default: router } = await import('../router')
      await router.replace({ name: 'Login' });
    }
  }

  // 返回 state, getters, actions，讓外部可以訪問
  return {
    user,
    isAuthenticated,
    username,
    login,
    register,
    logout,
  }
})