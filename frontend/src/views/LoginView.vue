<template>
  <div class="login-page-body">
    <div class="login-container">
      <div class="login-logo">
        <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0OCIgaGVpZ2h0PSI0OCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiMzYjgyZjYiIHN0cm9rZS13aWR0aD0iMS41IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwYXRoIGQ9Ik05IDE1Yy0yLjUgMS41LTUuMjUgMi41LTggMyIvPjxwYXRoIGQ9Ik0zLjUgMjFjMS4yNS0xLjE3IDItNS41IDMtMTAuNWMwLTUuMzkgMS43Ny04LjUgMi41LTkuNWMxLTEuMjUgMi4yNS0xLjUgNC41LS41YzMuMzggMS41IDMuNSAzLjVjIDQuNSA5LjVjMCAuMzEgMCAxLjE5LS4wOCA1Ii8+PHBhdGggZD0iTTE4IDIxYzAgLTEuNDQtLjUtMy41LTEuNS01LjVjLTEtMi0yLjUtMy00LjUtMy41Ii8+PHBhdGggZD0iTTIyIDIwLjVjLTEuODEtMS4xNy0zLjc1LTEuNS01Ljg3LTEuNSIvPjxjaXJjbGUgY3g9IjEwIiBjeT0iMTAiIHI9IjEiLz48Y2lyY2xlIGN4PSIxNiIgY3k9IjEwIiByPSIxIi8+PC9zdmc+" alt="領頭羊博士 Logo">
        <h1>領頭羊博士</h1>
        <p>您的智能飼養顧問</p>
      </div>

      <el-tabs v-model="activeTab" class="form-toggle-tabs" stretch>
        <el-tab-pane label="登入" name="login"></el-tab-pane>
        <el-tab-pane label="註冊" name="register"></el-tab-pane>
      </el-tabs>

      <!-- 登入表單 -->
      <el-form
        v-if="activeTab === 'login'"
        ref="loginFormRef"
        :model="loginForm"
        :rules="formRules"
        label-position="top"
        @submit.prevent="handleLogin"
      >
        <el-form-item label="使用者名稱" prop="username">
          <el-input v-model="loginForm.username" placeholder="請輸入使用者名稱" size="large" />
        </el-form-item>
        <el-form-item label="密碼" prop="password">
          <el-input v-model="loginForm.password" type="password" placeholder="請輸入密碼" show-password size="large" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading" class="full-width-btn" size="large">登入</el-button>
        </el-form-item>
      </el-form>

      <!-- 註冊表單 -->
      <el-form
        v-if="activeTab === 'register'"
        ref="registerFormRef"
        :model="registerForm"
        :rules="formRules"
        label-position="top"
        @submit.prevent="handleRegister"
      >
        <el-form-item label="使用者名稱" prop="username">
          <el-input v-model="registerForm.username" placeholder="請設定您的使用者名稱" size="large" />
        </el-form-item>
        <el-form-item label="密碼" prop="password">
          <el-input v-model="registerForm.password" type="password" placeholder="請設定您的密碼 (至少6位)" show-password size="large" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading" class="full-width-btn" size="large">註冊並登入</el-button>
        </el-form-item>
      </el-form>
      
      <el-alert
        v-if="errorMessage"
        :title="errorMessage"
        type="error"
        show-icon
        :closable="false"
        style="margin-top: 20px;"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useAuthStore } from '../stores/auth';
import { ElMessage } from 'element-plus';

// 使用我們定義的 auth store
const authStore = useAuthStore();

// 組件內部狀態
const activeTab = ref('login');
const loading = ref(false);
const errorMessage = ref('');

// 登入表單的數據模型
const loginForm = reactive({
  username: '',
  password: '',
});
const loginFormRef = ref(null);

// 註冊表單的數據模型
const registerForm = reactive({
  username: '',
  password: '',
});
const registerFormRef = ref(null);

// 表單驗證規則
const formRules = {
  username: [{ required: true, message: '使用者名稱為必填項', trigger: 'blur' }],
  password: [
    { required: true, message: '密碼為必填項', trigger: 'blur' },
    { min: 6, message: '密碼長度不能少於 6 位', trigger: 'blur' },
  ],
};

// 處理登入的函數
const handleLogin = async () => {
  // 觸發表單驗證
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      errorMessage.value = '';
      try {
        await authStore.login(loginForm);
        ElMessage.success('登入成功！');
      } catch (error) {
        errorMessage.value = error.error || '登入時發生未知錯誤';
      } finally {
        loading.value = false;
      }
    }
  });
};

// 處理註冊的函數
const handleRegister = async () => {
  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      errorMessage.value = '';
      try {
        await authStore.register(registerForm);
        ElMessage.success('註冊成功！');
      } catch (error) {
        errorMessage.value = error.error || '註冊時發生未知錯誤';
      } finally {
        loading.value = false;
      }
    }
  });
};
</script>

<style scoped>
.login-page-body {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f0f4f8;
}

.login-container {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
  text-align: center;
}

.login-logo {
  margin-bottom: 25px;
}
.login-logo img {
  height: 50px;
  margin-bottom: 10px;
}
.login-logo h1 {
  margin: 0;
  font-size: 2em;
  color: #1e3a8a;
}
.login-logo p {
  margin-top: 5px;
  color: #64748b;
}

.full-width-btn {
  width: 100%;
}

/* 覆蓋 Element Plus Tabs 的一些樣式，使其更像我們舊的樣式 */
.form-toggle-tabs {
  margin-bottom: 25px;
}
.form-toggle-tabs .el-tabs__header {
  border-bottom: none;
  background-color: #eef1f5;
  border-radius: 8px;
  padding: 5px;
}
.form-toggle-tabs .el-tabs__nav-wrap::after {
  display: none;
}
.form-toggle-tabs .el-tabs__item {
  border: none;
  border-radius: 6px;
  transition: all 0.3s ease;
  color: #64748b;
}
.form-toggle-tabs .el-tabs__item.is-active {
  background-color: white;
  color: #409eff;
  box-shadow: 0 2px 5px rgba(0,0,0,0.08);
}
.form-toggle-tabs .el-tabs__active-bar {
  display: none;
}
</style>