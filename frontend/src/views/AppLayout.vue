<template>
  <div class="app-layout">
    <header class="glass-nav">
      <div
        class="nav-brand"
        role="button"
        tabindex="0"
        @click="$router.push('/dashboard')"
        @keyup.enter="$router.push('/dashboard')"
      >
        <img class="nav-brand__logo" :src="logoUrl" alt="Aurora Navigation Logo" />
        <div class="nav-brand__label">
          <span class="nav-brand__title">領頭羊博士</span>
          <span class="nav-brand__subtitle">Dr.Goat AI Agent</span>
        </div>
      </div>

      <el-menu
        :default-active="$route.path"
        class="nav-links"
        mode="horizontal"
        :ellipsis="false"
        router
      >
        <el-menu-item index="/dashboard">AI Agent儀表盤</el-menu-item>
  <el-menu-item index="/consultation">營養與ESG建議</el-menu-item>
  <el-menu-item index="/chat">羊博士問答</el-menu-item>
  <el-menu-item index="/flock">羊群管理</el-menu-item>
        <el-menu-item index="/prediction">生長預測</el-menu-item>
  <el-menu-item index="/analytics">數據分析中心</el-menu-item>
        <el-menu-item index="/iot">智慧牧場 IoT</el-menu-item>
        <el-menu-item index="/traceability">產銷履歷管理</el-menu-item>
        <el-menu-item index="/data-management">數據管理</el-menu-item>
        <el-menu-item index="/settings">系統設定</el-menu-item>
      </el-menu>

      <div class="nav-actions">
        <div class="control-cluster">
          <el-tooltip :content="isDark ? '切換為淺色主題' : '切換為深色主題'">
            <el-button
              circle
              size="small"
              class="control-button"
              :aria-label="isDark ? '切換為淺色主題' : '切換為深色主題'"
              :aria-pressed="isDark"
              @click="toggleColorScheme"
            >
              <el-icon>
                <MoonNight v-if="isDark" />
                <Sunny v-else />
              </el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip :content="motionEnabled ? '停用 Aurora 動效' : '啟用 Aurora 動效'">
            <el-button
              circle
              size="small"
              class="control-button"
              :class="{ 'is-active': motionEnabled }"
              :aria-label="motionEnabled ? '停用 Aurora 動效' : '啟用 Aurora 動效'"
              :aria-pressed="motionEnabled"
              @click="toggleMotion"
            >
              <el-icon><MagicStick /></el-icon>
            </el-button>
          </el-tooltip>
        </div>

        <div class="user-panel">
          <div class="user-panel__details">
            <span class="user-panel__name">{{ authStore.username }}</span>
            <span class="user-panel__role">Aurora Admin</span>
          </div>
          <el-button class="user-panel__logout" size="small" plain type="danger" @click="handleLogout">
            登出
          </el-button>
        </div>

        <div class="hamburger-menu" @click="drawerVisible = true">
          <el-icon><Menu /></el-icon>
        </div>
      </div>
    </header>

    <el-drawer
      v-model="drawerVisible"
      title="導航選單"
      direction="rtl"
      :with-header="true"
      size="260px"
    >
      <el-menu
        :default-active="$route.path"
        class="drawer-menu"
        router
        @select="drawerVisible = false"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>AI Agent儀表盤</span>
        </el-menu-item>
        <el-menu-item index="/consultation">
          <el-icon><HelpFilled /></el-icon>
          <span>營養與ESG建議</span>
        </el-menu-item>
        <el-menu-item index="/chat">
          <el-icon><Service /></el-icon>
          <span>羊博士問答</span>
        </el-menu-item>
        <el-menu-item index="/flock">
          <el-icon><Tickets /></el-icon>
          <span>羊群管理</span>
        </el-menu-item>
        <el-menu-item index="/prediction">
          <el-icon><TrendCharts /></el-icon>
          <span>生長預測</span>
        </el-menu-item>
        <el-menu-item index="/analytics">
          <el-icon><DataAnalysis /></el-icon>
          <span>數據分析中心</span>
        </el-menu-item>
        <el-menu-item index="/iot">
          <el-icon><Cpu /></el-icon>
          <span>智慧牧場 IoT</span>
        </el-menu-item>
        <el-menu-item index="/traceability">
          <el-icon><Collection /></el-icon>
          <span>產銷履歷管理</span>
        </el-menu-item>
        <el-menu-item index="/data-management">
          <el-icon><Upload /></el-icon>
          <span>數據管理</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系統設定</span>
        </el-menu-item>
      </el-menu>
    </el-drawer>

    <main class="main-content">
      <div class="main-content__surface aurora-scrollbar">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useAuthStore } from '../stores/auth';
import { ElMessage, ElMessageBox } from 'element-plus';
import {
  Menu,
  DataAnalysis,
  HelpFilled,
  Service,
  Tickets,
  Upload,
  Setting,
  TrendCharts,
  Collection,
  Cpu,
  Sunny,
  MoonNight,
  MagicStick,
} from '@element-plus/icons-vue';
import { useTheme } from '@/composables/useTheme';
import logoUrl from '@/assets/images/logo.svg';

const authStore = useAuthStore();
const drawerVisible = ref(false);
const { isDark, motionEnabled, toggleColorScheme, toggleMotion } = useTheme();

const handleLogout = () => {
  ElMessageBox.confirm('您確定要登出嗎？', '提示', {
    confirmButtonText: '確定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(async () => {
      await authStore.logout();
      ElMessage({ type: 'success', message: '您已成功登出' });
    })
    .catch(() => {});
};
</script>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.glass-nav {
  position: sticky;
  top: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 0 28px;
  height: 72px;
  background: linear-gradient(115deg, rgba(20, 184, 166, 0.22), rgba(59, 130, 246, 0.28));
  backdrop-filter: blur(18px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.25);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.18);
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  cursor: pointer;
  color: inherit;
  text-decoration: none;
}

.nav-brand:focus-visible {
  outline: 2px solid rgba(59, 130, 246, 0.75);
  outline-offset: 4px;
  border-radius: 999px;
}

.nav-brand__logo {
  height: 40px;
  width: 40px;
  filter: drop-shadow(0 4px 8px rgba(15, 23, 42, 0.35));
}

.nav-brand__label {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
}

.nav-brand__title {
  font-size: 1.35rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: #f8fafc;
}

.nav-brand__subtitle {
  font-size: 0.75rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(241, 245, 249, 0.78);
}

.nav-links {
  flex: 1;
  background: transparent;
  border-bottom: none;
  height: 100%;
  --el-menu-active-color: #ffffff;
}

.nav-links :deep(.el-menu-item) {
  color: rgba(241, 245, 249, 0.78);
  font-weight: 500;
  background: transparent !important;
  border-bottom: 3px solid transparent !important;
  transition: color var(--aurora-transition-base), border-color var(--aurora-transition-base);
}

.nav-links :deep(.el-menu-item:hover),
.nav-links :deep(.el-menu-item.is-active) {
  color: #ffffff !important;
  border-bottom-color: rgba(255, 255, 255, 0.8) !important;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.control-cluster {
  display: flex;
  gap: 0.55rem;
}

.control-button {
  background: rgba(255, 255, 255, 0.24);
  border: 1px solid rgba(255, 255, 255, 0.4);
  color: #0f172a;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25);
  transition: transform var(--aurora-transition-base), box-shadow var(--aurora-transition-base),
    background var(--aurora-transition-base);
}

.control-button:hover {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, 0.34);
}

.control-button.is-active {
  background: rgba(59, 130, 246, 0.35);
  color: #0f172a;
}

.user-panel {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  padding: 0.45rem 0.85rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.32);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.user-panel__details {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
  color: #f8fafc;
}

.user-panel__name {
  font-weight: 600;
  font-size: 0.95rem;
}

.user-panel__role {
  font-size: 0.7rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(226, 232, 240, 0.75);
}

.user-panel__logout {
  --el-button-bg-color: rgba(255, 255, 255, 0.2);
  --el-button-hover-bg-color: rgba(248, 113, 113, 0.18);
  --el-button-hover-text-color: #fee2e2;
  border-radius: 999px;
  font-weight: 600;
}

.hamburger-menu {
  display: none;
  cursor: pointer;
  color: #f8fafc;
  font-size: 1.5rem;
}

.main-content {
  flex: 1;
  width: 100%;
  padding: 28px 32px 48px;
  box-sizing: border-box;
  display: flex;
  justify-content: center;
}

.main-content__surface {
  width: 100%;
  max-width: 1360px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.28);
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.12);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.4);
  padding: 32px;
  box-sizing: border-box;
}

.main-content__surface :deep(> *) {
  width: 100%;
}

.drawer-menu {
  border-right: none;
}

:deep(.control-button .el-icon) {
  color: inherit;
}

@media (max-width: 1200px) {
  .nav-links {
    display: none;
  }

  .hamburger-menu {
    display: block;
  }
}

@media (max-width: 960px) {
  .user-panel {
    display: none;
  }
}

@media (max-width: 768px) {
  .glass-nav {
    padding: 0 18px;
    gap: 1rem;
  }

  .main-content {
    padding: 20px 18px 36px;
  }

  .main-content__surface {
    padding: 20px;
  }
}
</style>
