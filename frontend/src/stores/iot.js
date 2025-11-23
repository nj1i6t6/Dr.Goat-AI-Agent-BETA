import { defineStore } from 'pinia';
import { computed, reactive, ref } from 'vue';
import api from '../api';

const DEVICE_TYPE_CATALOG = Object.freeze([
  { label: '舍內環境監控', category: 'sensor' },
  { label: '智慧頸圈/耳標', category: 'sensor' },
  { label: '電子藥丸/瘤胃監測器', category: 'sensor' },
  { label: '自動體重計', category: 'sensor' },
  { label: '自動化擠乳系統', category: 'sensor' },
  { label: '智慧採食槽', category: 'sensor' },
  { label: '智慧飲水器', category: 'sensor' },
  { label: '飼料/草料庫存感測器', category: 'sensor' },
  { label: 'GPS 定位項圈', category: 'sensor' },
  { label: 'AI 視覺攝影機', category: 'sensor' },
  { label: '自動分群門', category: 'actuator' },
  { label: '自動風扇', category: 'actuator' },
  { label: '霧化降溫系統', category: 'actuator' },
  { label: '遮陽網/窗簾控制器', category: 'actuator' },
  { label: '電磁閥', category: 'actuator' },
  { label: '自動噴霧/消毒系統', category: 'actuator' },
]);

const DEFAULT_COMMANDS = Object.freeze({
  '自動風扇': ['turn_on', 'turn_off', 'set_speed'],
  '霧化降溫系統': ['start_misting', 'stop_misting'],
  '自動分群門': ['open', 'close'],
  '智慧採食槽': ['start_feeding', 'stop_feeding'],
  '電磁閥': ['open_valve', 'close_valve'],
  '自動噴霧/消毒系統': ['start_sanitize', 'stop_sanitize'],
});

export const useIotStore = defineStore('iot', () => {
  const devices = ref([]);
  const deviceLoading = ref(false);
  const rules = ref([]);
  const ruleLoading = ref(false);
  const readings = reactive({});
  const readingLoading = ref(false);
  const lastCreatedApiKey = ref(null);

  const sensorDevices = computed(() => devices.value.filter(device => device.category === 'sensor'));
  const actuatorDevices = computed(() => devices.value.filter(device => device.category === 'actuator'));
  const deviceTypeOptions = computed(() => DEVICE_TYPE_CATALOG);

  function getCommandOptions(deviceType) {
    return DEFAULT_COMMANDS[deviceType] || ['turn_on', 'turn_off'];
  }

  async function fetchDevices(force = false) {
    if (deviceLoading.value && !force) return;
    deviceLoading.value = true;
    try {
      const data = await api.getIotDevices();
      devices.value = data;
    } finally {
      deviceLoading.value = false;
    }
  }

  async function createDevice(payload) {
    const created = await api.createIotDevice(payload);
    const { api_key: apiKey, ...device } = created;
    devices.value = [device, ...devices.value.filter(existing => existing.id !== device.id)];
    lastCreatedApiKey.value = apiKey || null;
    return { ...device, api_key: apiKey };
  }

  async function updateDevice(deviceId, payload) {
    const updated = await api.updateIotDevice(deviceId, payload);
    const index = devices.value.findIndex(device => device.id === updated.id);
    if (index !== -1) {
      devices.value.splice(index, 1, updated);
    }
    return updated;
  }

  async function deleteDevice(deviceId) {
    await api.deleteIotDevice(deviceId);
    devices.value = devices.value.filter(device => device.id !== deviceId);
  }

  async function fetchDeviceReadings(deviceId, limit = 100) {
    readingLoading.value = true;
    try {
      const data = await api.getDeviceSensorReadings(deviceId, { limit });
      readings[deviceId] = data;
      return data;
    } finally {
      readingLoading.value = false;
    }
  }

  async function fetchRules(force = false) {
    if (ruleLoading.value && !force) return;
    ruleLoading.value = true;
    try {
      const data = await api.getAutomationRules();
      rules.value = data;
    } finally {
      ruleLoading.value = false;
    }
  }

  async function createRule(payload) {
    const rule = await api.createAutomationRule(payload);
    rules.value = [rule, ...rules.value.filter(existing => existing.id !== rule.id)];
    return rule;
  }

  async function updateRule(ruleId, payload) {
    const rule = await api.updateAutomationRule(ruleId, payload);
    const index = rules.value.findIndex(existing => existing.id === rule.id);
    if (index !== -1) {
      rules.value.splice(index, 1, rule);
    }
    return rule;
  }

  async function deleteRule(ruleId) {
    await api.deleteAutomationRule(ruleId);
    rules.value = rules.value.filter(rule => rule.id !== ruleId);
  }

  return {
    devices,
    deviceLoading,
    rules,
    ruleLoading,
    readings,
    readingLoading,
    lastCreatedApiKey,
    sensorDevices,
    actuatorDevices,
    deviceTypeOptions,
    getCommandOptions,
    fetchDevices,
    createDevice,
    updateDevice,
    deleteDevice,
    fetchDeviceReadings,
    fetchRules,
    createRule,
    updateRule,
    deleteRule,
  };
});
