<template>
  <div class="dashboard-page" v-loading="initialLoading">
    <div v-if="!initialLoading && !hasSheep" class="empty-state">
      <el-result
        icon="info"
        title="歡迎, 開始建立您的羊群檔案吧！"
        sub-title="系統中尚無羊隻資料。請前往「數據管理中心」導入您的第一批資料。"
      >
        <template #extra>
          <el-button type="primary" size="large" @click="$router.push('/data-management')">
            🚀 前往數據管理中心
          </el-button>
        </template>
      </el-result>
    </div>

    <div v-else-if="!initialLoading && hasSheep" class="dashboard-content">
      <BaseAuroraCard class="welcome-card" title="領頭羊博士的問候！">
        <div class="agent-tip" v-loading="settingsStore.agentTip.loading" v-html="safeAgentTipHtml"></div>
        <el-alert
          v-if="ragStatusVisible"
          :title="ragStatusTitle"
          :type="ragStatusType"
          :closable="false"
          show-icon
          class="rag-status-alert"
        >
          <template #default>
            <span>{{ ragStatusMessage }}</span>
          </template>
        </el-alert>
      </BaseAuroraCard>

      <section class="dashboard-grid">
        <BaseAuroraCard title="📅 任務與安全提醒">
          <el-empty
            v-if="!dashboardData.reminders || dashboardData.reminders.length === 0"
            description="暫無待辦事項"
          />
          <ul v-else class="capsule-list">
            <li v-for="(reminder, index) in dashboardData.reminders" :key="`reminder-${index}`" class="capsule-item">
              <div class="capsule-item__primary">
                <span class="ear-num-link">{{ reminder.ear_num }}</span>
                <span class="capsule-item__title">{{ reminder.type }}</span>
                <span class="capsule-item__meta">至 {{ reminder.due_date }}</span>
              </div>
              <el-tag :type="getTagType(reminder.status)" size="small" effect="light">{{ reminder.status }}</el-tag>
            </li>
          </ul>
        </BaseAuroraCard>

        <BaseAuroraCard title="❤️ 健康與福利警示">
          <el-empty
            v-if="!dashboardData.health_alerts || dashboardData.health_alerts.length === 0"
            description="羊群健康狀況良好"
          />
          <ul v-else class="capsule-list">
            <li v-for="(alert, index) in dashboardData.health_alerts" :key="`alert-${index}`" class="capsule-item">
              <div class="capsule-item__primary">
                <strong class="capsule-item__title">{{ alert.type }}</strong>
                <span class="ear-num-link">{{ alert.ear_num }}</span>
                <span class="capsule-item__meta">{{ alert.message }}</span>
              </div>
            </li>
          </ul>
        </BaseAuroraCard>
      </section>

      <section class="dashboard-grid">
        <BaseAuroraCard title="🐑 羊群狀態速覽">
          <el-empty
            v-if="!dashboardData.flock_status_summary || dashboardData.flock_status_summary.length === 0"
            description="暫無狀態數據"
          />
          <ul v-else class="summary-list">
            <li v-for="summary in dashboardData.flock_status_summary" :key="summary.status">
              <span class="summary-list__label">{{ getStatusText(summary.status) }}</span>
              <span class="summary-list__value">{{ summary.count }} 隻</span>
            </li>
          </ul>
        </BaseAuroraCard>

        <BaseAuroraCard title="🌿 ESG 指標速覽">
          <div v-if="dashboardData.esg_metrics" class="esg-card">
            <p>
              <strong>飼料轉換率 (FCR) 估算:</strong>
              <span v-if="dashboardData.esg_metrics.fcr" class="esg-value">
                {{ dashboardData.esg_metrics.fcr.toFixed(2) }}
              </span>
              <el-tag v-else type="info" size="small">數據不足</el-tag>
              <span class="form-note">(kg飼料/kg增重)</span>
            </p>
            <el-button type="success" :loading="reportLoading" @click="generateFarmReport">生成牧場報告</el-button>
          </div>
          <el-empty v-else description="暫無 ESG 數據" />
        </BaseAuroraCard>
      </section>

      <section class="activity-log-section">
        <VirtualizedLogTable />
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue';
import { useSettingsStore } from '../stores/settings';
import api from '../api';
import { ElMessage, ElMessageBox } from 'element-plus';
import VirtualizedLogTable from '@/components/tables/VirtualizedLogTable.vue';
import BaseAuroraCard from '@/components/common/BaseAuroraCard.vue';
import { sanitizeHtml } from '@/utils/sanitizeHtml';
import { escapeHtml } from '@/utils/text';

const settingsStore = useSettingsStore();

const safeAgentTipHtml = computed(() => sanitizeHtml(settingsStore.agentTip.html));
const ragStatusState = computed(() => settingsStore.ragStatus);
const ragStatusVisible = computed(() => ragStatusState.value.available !== null);
const ragStatusType = computed(() => (ragStatusState.value.available ? 'success' : 'warning'));
const ragStatusTitle = computed(() =>
  ragStatusState.value.available ? 'RAG 知識庫已啟用' : 'RAG 功能已降級'
);
const ragStatusMessage = computed(() =>
  ragStatusState.value.message ||
  (ragStatusState.value.available ? 'RAG 知識庫已啟用。' : 'RAG 功能已降級，系統將自動退回為一般模式。')
);

const initialLoading = ref(true);
const hasSheep = ref(false);
const reportLoading = ref(false);
const dashboardData = reactive({
  reminders: [],
  health_alerts: [],
  flock_status_summary: [],
  esg_metrics: {},
});

const statusMap = {
  maintenance: '維持期',
  growing_young: '生長前期',
  growing_finishing: '生長育肥期',
  gestating_early: '懷孕早期',
  gestating_late: '懷孕晚期',
  lactating_early: '泌乳早期',
  lactating_peak: '泌乳高峰期',
  lactating_mid: '泌乳中期',
  lactating_late: '泌乳晚期',
  dry_period: '乾乳期',
  breeding_male_active: '配種期公羊',
  breeding_male_non_active: '非配種期公羊',
  fiber_producing: '產毛期',
  other_status: '其他',
};
const getStatusText = (status) => statusMap[status] || status || '未分類';

const getTagType = (status) => {
  if (status === '已過期') return 'danger';
  if (status === '即將到期') return 'warning';
  if (status === '停藥中') return 'info';
  return 'primary';
};

async function fetchInitialData() {
  try {
    const sheepList = await api.getAllSheep();
    hasSheep.value = sheepList && sheepList.length > 0;

    if (hasSheep.value) {
      fetchDashboardContent();
    }
  } catch (error) {
    ElMessage.error('無法獲取羊群資料');
  } finally {
    initialLoading.value = false;
  }
}

async function fetchDashboardContent() {
  settingsStore.refreshRagStatus();
  settingsStore.fetchAndSetAgentTip();
  fetchDashboardData();
}

async function fetchDashboardData() {
  try {
    const data = await api.getDashboardData();
    Object.assign(dashboardData, data);
  } catch (error) {
    ElMessage.error(`載入儀表板數據失敗: ${error.error || error.message}`);
  }
}

async function generateFarmReport() {
  reportLoading.value = true;
  try {
    const report = await api.getFarmReport();
    const flockComposition = report.flock_composition || {};
    const productionSummary = report.production_summary || {};
    const healthSummary = report.health_summary || {};
    const breedList = (flockComposition.by_breed || [])
      .map((breed) => `<li>${escapeHtml(breed.name)}: ${escapeHtml(breed.count)} 隻</li>`)
      .join('');
    const sexList = (flockComposition.by_sex || [])
      .map((sexItem) => `<li>${escapeHtml(sexItem.name)}: ${escapeHtml(sexItem.count)} 隻</li>`)
      .join('');
    const diseaseList = (healthSummary.top_diseases || [])
      .map((disease) => `<li>${escapeHtml(disease.name)}: ${escapeHtml(disease.count)} 次</li>`)
      .join('');

    const reportHtml = `
      <h4>羊群結構 (總計: ${escapeHtml(flockComposition.total ?? '0')} 隻)</h4>
      <h5>品種分佈</h5>
      <ul>${breedList || '<li>暫無品種資料</li>'}</ul>
      <h5>性別分佈</h5>
      <ul>${sexList || '<li>暫無性別資料</li>'}</ul>
      <hr>
      <h4>生產性能摘要</h4>
      <ul>
        <li>平均出生體重: <strong>${escapeHtml(productionSummary.avg_birth_weight || 'N/A')} kg</strong></li>
        <li>平均窩仔數: <strong>${escapeHtml(productionSummary.avg_litter_size || 'N/A')} 隻</strong></li>
        <li>平均日產奶量 (有記錄者): <strong>${escapeHtml(productionSummary.avg_milk_yield || 'N/A')} kg/天</strong></li>
      </ul>
      <hr>
      <h4>健康狀況摘要 (最常見的5項疾病事件)</h4>
      <ul>${diseaseList || '<li>暫無疾病記錄</li>'}</ul>
    `;
    const sanitizedReportHtml = sanitizeHtml(reportHtml);

    ElMessageBox.alert(sanitizedReportHtml, '牧場年度報告摘要', {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '關閉',
    });
  } catch (error) {
    ElMessage.error(`生成報告失敗: ${error.error || error.message}`);
  } finally {
    reportLoading.value = false;
  }
}

onMounted(() => {
  fetchInitialData();
});
</script>

<style scoped>
.dashboard-page {
  animation: fadeIn 0.5s ease-out;
}

.empty-state {
  display: flex;
  justify-content: center;
  padding: 3rem 0;
}

.dashboard-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.welcome-card .agent-tip {
  font-size: 1rem;
  color: var(--aurora-text-secondary);
  font-style: italic;
  min-height: 24px;
}

.rag-status-alert {
  margin-top: 1rem;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}

.capsule-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.capsule-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 0.85rem 1rem;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.18);
  border: 1px solid rgba(148, 163, 184, 0.28);
  backdrop-filter: blur(12px);
  transition: transform var(--aurora-transition-base), box-shadow var(--aurora-transition-base);
}

.capsule-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.12);
}

.capsule-item__primary {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

.capsule-item__title {
  font-weight: 600;
  color: var(--aurora-text-primary);
}

.capsule-item__meta {
  font-size: 0.85rem;
  color: var(--aurora-text-muted);
}

.ear-num-link {
  font-weight: 600;
  color: var(--aurora-accent-strong);
}

.summary-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.summary-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.85rem 1rem;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.35);
  border: 1px solid rgba(148, 163, 184, 0.2);
  backdrop-filter: blur(10px);
}

.summary-list__label {
  font-weight: 600;
  color: var(--aurora-text-secondary);
}

.summary-list__value {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--aurora-accent-secondary);
}

.esg-card {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.esg-value {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--aurora-accent-secondary);
  margin: 0 0.5rem;
}

.form-note {
  font-size: 0.85rem;
  color: var(--aurora-text-muted);
}

.activity-log-section {
  margin-top: 0.5rem;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 640px) {
  .capsule-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .capsule-item__primary {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
