<template>
  <div class="iot-management">
    <div class="header">
      <h1><el-icon><Cpu /></el-icon> IoT 裝置管理</h1>
      <div class="header-actions">
        <el-button type="primary" :icon="Plus" @click="openDeviceDialog()">新增裝置</el-button>
        <el-button :icon="Refresh" @click="handleRefresh" :loading="iotStore.deviceLoading">重新整理</el-button>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :xs="24" :md="14">
        <el-card shadow="never" class="device-card">
          <template #header>
            <div class="card-header">
              <span>裝置列表</span>
              <el-tag type="info">{{ iotStore.devices.length }} 台裝置</el-tag>
            </div>
          </template>
          <el-table :data="iotStore.devices" v-loading="iotStore.deviceLoading" @row-click="handleRowClick" class="device-table" highlight-current-row>
            <el-table-column prop="name" label="名稱" min-width="140" />
            <el-table-column prop="device_type" label="裝置類型" min-width="160" />
            <el-table-column prop="category" label="分類" width="110">
              <template #default="scope">
                <el-tag :type="scope.row.category === 'sensor' ? 'success' : 'warning'">{{ scope.row.category === 'sensor' ? '感測器' : '致動器' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="location" label="位置" min-width="120" />
            <el-table-column prop="status" label="狀態" width="120">
              <template #default="scope">
                <el-tag :type="statusTagType(scope.row.status)">{{ formatStatus(scope.row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="last_seen" label="最後通訊" min-width="180">
              <template #default="scope">
                {{ scope.row.last_seen ? formatDateTime(scope.row.last_seen) : '尚未連線' }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160">
              <template #default="scope">
                <el-button type="primary" link @click.stop="openDeviceDialog(scope.row)">編輯</el-button>
                <el-popconfirm title="確定要刪除此裝置嗎？" @confirm="handleDeleteDevice(scope.row.id)">
                  <template #reference>
                    <el-button type="danger" link>刪除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="10">
        <el-card shadow="never" class="rule-card">
          <template #header>
            <div class="card-header">
              <span>自動化規則</span>
              <el-button type="primary" link :icon="Plus" @click="openRuleDialog()">新增規則</el-button>
            </div>
          </template>
          <el-table :data="iotStore.rules" v-loading="iotStore.ruleLoading" class="rule-table" empty-text="尚未建立規則">
            <el-table-column prop="name" label="規則名稱" min-width="160" />
            <el-table-column label="狀態" width="120">
              <template #default="scope">
                <el-switch v-model="scope.row.is_enabled" size="small" @change="value => toggleRule(scope.row, value)" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160">
              <template #default="scope">
                <el-button type="primary" link @click="openRuleDialog(scope.row)">編輯</el-button>
                <el-popconfirm title="確定要刪除此規則嗎？" @confirm="handleDeleteRule(scope.row.id)">
                  <template #reference>
                    <el-button type="danger" link>刪除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-drawer v-model="drawerVisible" size="40%" :title="selectedDevice?.name || '裝置詳情'" destroy-on-close>
      <template v-if="selectedDevice">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="裝置類型">{{ selectedDevice.device_type }}</el-descriptions-item>
          <el-descriptions-item label="分類">{{ selectedDevice.category === 'sensor' ? '感測器' : '致動器' }}</el-descriptions-item>
          <el-descriptions-item label="位置">{{ selectedDevice.location || '未設定' }}</el-descriptions-item>
          <el-descriptions-item label="狀態">{{ formatStatus(selectedDevice.status) }}</el-descriptions-item>
          <el-descriptions-item label="API Key">
            <span class="one-time-secret">僅在建立裝置時提供一次，請妥善保存。</span>
          </el-descriptions-item>
          <el-descriptions-item label="數據上傳 URL">{{ ingestUrl }}</el-descriptions-item>
          <el-descriptions-item v-if="selectedDevice.control_url" label="控制指令 URL">{{ selectedDevice.control_url }}</el-descriptions-item>
        </el-descriptions>

        <div class="chart-section">
          <h3>最近讀數</h3>
          <div v-if="readingLoading" class="chart-loading"><el-icon><Loading /></el-icon></div>
          <el-empty v-else-if="!selectedReadings.length" description="尚無讀數" />
          <Line v-else :data="chartData" :options="chartOptions" :key="chartKey" class="sensor-chart" />
        </div>
      </template>
    </el-drawer>

    <el-dialog v-model="deviceDialogVisible" :title="deviceDialogTitle" width="520px" destroy-on-close>
      <el-form ref="deviceFormRef" :model="deviceForm" label-width="120px">
        <el-form-item label="名稱" prop="name" :rules="[{ required: true, message: '請輸入名稱' }]">
          <el-input v-model="deviceForm.name" />
        </el-form-item>
        <el-form-item label="裝置類型" prop="device_type" :rules="[{ required: true, message: '請選擇裝置類型' }]">
          <el-select v-model="deviceForm.device_type" placeholder="選擇裝置類型">
            <el-option v-for="option in iotStore.deviceTypeOptions" :key="option.label" :label="option.label" :value="option.label" />
          </el-select>
        </el-form-item>
        <el-form-item label="分類" prop="category" :rules="[{ required: true, message: '請選擇分類' }]">
          <el-select v-model="deviceForm.category">
            <el-option label="感測器" value="sensor" />
            <el-option label="致動器" value="actuator" />
          </el-select>
        </el-form-item>
        <el-form-item label="安裝地點"><el-input v-model="deviceForm.location" /></el-form-item>
        <el-form-item v-if="deviceForm.category === 'actuator'" label="控制 URL" :rules="[{ required: true, message: '請輸入控制 URL' }]">
          <el-input v-model="deviceForm.control_url" placeholder="http://example.com/cmd" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="deviceDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="deviceSubmitting" @click="handleSubmitDevice">{{ deviceDialogSubmitLabel }}</el-button>
      </template>
      <el-alert
        v-if="iotStore.lastCreatedApiKey && !isEditingDevice"
        type="success"
        :closable="false"
        class="api-key-alert"
        title="API Key 僅顯示一次，請立即複製"
      >
        <code class="api-key-value">{{ iotStore.lastCreatedApiKey }}</code>
      </el-alert>
    </el-dialog>

    <el-dialog v-model="ruleDialogVisible" :title="ruleDialogTitle" width="640px" destroy-on-close>
      <automation-rule-builder
        :model-value="ruleForm"
        :sensors="iotStore.sensorDevices"
        :actuators="iotStore.actuatorDevices"
        :device-command-options="iotStore.getCommandOptions"
        @save="handleSaveRule"
        @cancel="() => (ruleDialogVisible = false)"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, reactive, ref, watch } from 'vue';
import { useIotStore } from '../stores/iot';
import AutomationRuleBuilder from '../components/iot/AutomationRuleBuilder.vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Cpu, Loading, Plus, Refresh } from '@element-plus/icons-vue';
import { Line } from 'vue-chartjs';
import {
  CategoryScale,
  Chart,
  Legend,
  LineController,
  LineElement,
  LinearScale,
  PointElement,
  TimeScale,
  Title,
  Tooltip,
} from 'chart.js';
import 'chartjs-adapter-date-fns';

Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, TimeScale, Legend, Tooltip, Title);

const iotStore = useIotStore();

const deviceDialogVisible = ref(false);
const deviceSubmitting = ref(false);
const isEditingDevice = ref(false);
const deviceFormRef = ref();
const deviceForm = reactive({
  id: null,
  name: '',
  device_type: '',
  category: 'sensor',
  location: '',
  control_url: '',
});

const ruleDialogVisible = ref(false);
const ruleForm = ref({});
const drawerVisible = ref(false);
const selectedDeviceId = ref(null);
const readingLoading = ref(false);

const deviceDialogTitle = computed(() => (isEditingDevice.value ? '編輯裝置' : '新增裝置'));
const deviceDialogSubmitLabel = computed(() => (isEditingDevice.value ? '儲存變更' : '建立裝置'));
const ruleDialogTitle = computed(() => (ruleForm.value?.id ? '編輯規則' : '新增規則'));

const selectedDevice = computed(() => iotStore.devices.find(device => device.id === selectedDeviceId.value));
const selectedReadings = computed(() => {
  if (!selectedDeviceId.value) return [];
  return iotStore.readings[selectedDeviceId.value] || [];
});

const ingestUrl = computed(() => (typeof window !== 'undefined' ? `${window.location.origin}/api/iot/ingest` : '/api/iot/ingest'));

const chartKey = computed(() => `${selectedDeviceId.value}-${selectedReadings.value.length}`);

const chartData = computed(() => {
  const labels = selectedReadings.value.map(reading => new Date(reading.created_at));
  const datasetMap = new Map();

  selectedReadings.value.forEach((reading, index) => {
    Object.entries(reading.data || {}).forEach(([key, value]) => {
      if (typeof value !== 'number') return;
      if (!datasetMap.has(key)) {
        datasetMap.set(key, new Array(selectedReadings.value.length).fill(null));
      }
      datasetMap.get(key)[index] = value;
    });
  });

  const datasets = Array.from(datasetMap.entries()).map(([key, values], idx) => ({
    label: key,
    data: values,
    tension: 0.3,
    borderWidth: 2,
    backgroundColor: `hsla(${(idx * 80) % 360}, 70%, 60%, 0.2)`,
    borderColor: `hsl(${(idx * 80) % 360}, 70%, 45%)`,
  }));

  return { labels, datasets };
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    x: {
      type: 'time',
      time: { tooltipFormat: 'yyyy-MM-dd HH:mm' },
      ticks: { autoSkip: true, maxRotation: 0 },
    },
    y: {
      beginAtZero: false,
      ticks: { precision: 2 },
    },
  },
};

function formatStatus(status) {
  if (!status) return '未知';
  if (status === 'online') return '在線';
  if (status === 'offline') return '離線';
  return status;
}

function statusTagType(status) {
  switch (status) {
    case 'online':
      return 'success';
    case 'error':
      return 'danger';
    case 'maintenance':
      return 'warning';
    default:
      return 'info';
  }
}

function formatDateTime(value) {
  if (!value) return '';
  const date = new Date(value);
  return `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
}

function resetDeviceForm(device = null) {
  deviceForm.id = device?.id || null;
  deviceForm.name = device?.name || '';
  deviceForm.device_type = device?.device_type || '';
  deviceForm.category = device?.category || 'sensor';
  deviceForm.location = device?.location || '';
  deviceForm.control_url = device?.control_url || '';
}

function openDeviceDialog(device = null) {
  isEditingDevice.value = Boolean(device);
  resetDeviceForm(device);
  deviceDialogVisible.value = true;
  iotStore.lastCreatedApiKey = null;
}

async function handleSubmitDevice() {
  deviceFormRef.value.validate(async (valid) => {
    if (!valid) return;
    deviceSubmitting.value = true;
    try {
      const payload = {
        name: deviceForm.name,
        device_type: deviceForm.device_type,
        category: deviceForm.category,
        location: deviceForm.location,
        control_url: deviceForm.category === 'actuator' ? deviceForm.control_url : null,
      };
      if (isEditingDevice.value && deviceForm.id) {
        await iotStore.updateDevice(deviceForm.id, payload);
        ElMessage.success('裝置更新成功');
        deviceDialogVisible.value = false;
      } else {
        const created = await iotStore.createDevice(payload);
        if (created.api_key) {
          ElMessage.success('裝置建立成功，請立即複製 API Key');
        } else {
          deviceDialogVisible.value = false;
        }
      }
    } catch (error) {
      ElMessage.error(error?.response?.data?.error || error.message || '操作失敗');
    } finally {
      deviceSubmitting.value = false;
    }
  });
}

function handleDeleteDevice(deviceId) {
  ElMessageBox.confirm('刪除後將無法復原，是否繼續？', '提醒', {
    confirmButtonText: '刪除',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    await iotStore.deleteDevice(deviceId);
    ElMessage.success('裝置已刪除');
    if (selectedDeviceId.value === deviceId) {
      drawerVisible.value = false;
      selectedDeviceId.value = null;
    }
  }).catch(() => {});
}

function handleRowClick(row) {
  selectedDeviceId.value = row.id;
  drawerVisible.value = true;
}

async function fetchReadings(deviceId) {
  if (!deviceId) return;
  readingLoading.value = true;
  try {
    await iotStore.fetchDeviceReadings(deviceId, 50);
  } finally {
    readingLoading.value = false;
  }
}

watch(selectedDeviceId, (value) => {
  if (value) {
    fetchReadings(value);
  }
});

watch(deviceDialogVisible, (visible) => {
  if (!visible) {
    iotStore.lastCreatedApiKey = null;
  }
});

function handleRefresh() {
  iotStore.fetchDevices(true);
  iotStore.fetchRules(true);
  if (selectedDeviceId.value) {
    fetchReadings(selectedDeviceId.value);
  }
}

function openRuleDialog(rule = null) {
  ruleForm.value = rule
    ? structuredClone(rule)
    : {
        name: '',
        trigger_source_device_id: iotStore.sensorDevices[0]?.id || null,
        trigger_condition: { variable: '', operator: '>', value: '' },
        action_target_device_id: iotStore.actuatorDevices[0]?.id || null,
        action_command: { command: '', parameters: {} },
        is_enabled: true,
      };
  ruleDialogVisible.value = true;
}

async function handleSaveRule(payload) {
  try {
    if (payload.id) {
      await iotStore.updateRule(payload.id, payload);
      ElMessage.success('規則已更新');
    } else {
      await iotStore.createRule(payload);
      ElMessage.success('規則建立成功');
    }
    ruleDialogVisible.value = false;
  } catch (error) {
    ElMessage.error(error?.response?.data?.error || error.message || '儲存失敗');
  }
}

async function handleDeleteRule(ruleId) {
  await iotStore.deleteRule(ruleId);
  ElMessage.success('規則已刪除');
}

async function toggleRule(rule, value) {
  try {
    await iotStore.updateRule(rule.id, { is_enabled: value });
    ElMessage.success(value ? '規則已啟用' : '規則已停用');
  } catch (error) {
    rule.is_enabled = !value;
    ElMessage.error(error?.response?.data?.error || error.message || '更新狀態失敗');
  }
}

onMounted(async () => {
  await Promise.all([iotStore.fetchDevices(), iotStore.fetchRules()]);
});

onBeforeUnmount(() => {
  iotStore.lastCreatedApiKey = null;
});
</script>

<style scoped>
.iot-management {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.header h1 {
  font-size: 1.8rem;
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.device-card,
.rule-card {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.device-table ::v-deep(.el-table__row) {
  cursor: pointer;
}

.chart-section {
  margin-top: 20px;
  height: 280px;
}

.sensor-chart {
  height: 260px;
}

.chart-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 240px;
  color: #909399;
}

.api-key-alert {
  margin-top: 16px;
}

.api-key-alert .api-key-value {
  display: inline-block;
  margin-top: 8px;
  padding: 4px 8px;
  background: #1f2d3d;
  color: #fff;
  border-radius: 4px;
  font-family: 'Fira Code', 'Consolas', monospace;
  letter-spacing: 0.5px;
}

.one-time-secret {
  color: #909399;
}

@media (max-width: 768px) {
  .header {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
