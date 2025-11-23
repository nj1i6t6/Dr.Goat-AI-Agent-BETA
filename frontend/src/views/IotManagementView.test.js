import { describe, it, expect, beforeEach, vi } from 'vitest';
import { shallowMount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import { useIotStore } from '@/stores/iot';

vi.mock('vue-chartjs', () => ({
  Line: { name: 'LineChartStub', render: () => null },
}));

vi.mock('@element-plus/icons-vue', () => ({
  Cpu: { name: 'CpuIcon', render: () => null },
  Loading: { name: 'LoadingIcon', render: () => null },
  Plus: { name: 'PlusIcon', render: () => null },
  Refresh: { name: 'RefreshIcon', render: () => null },
}));

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
  },
  ElMessageBox: {
    confirm: vi.fn(() => Promise.resolve()),
  },
}));

vi.mock('@/api', () => ({
  default: {
    getIotDevices: vi.fn(),
    createIotDevice: vi.fn(),
    updateIotDevice: vi.fn(),
    deleteIotDevice: vi.fn(),
    getDeviceSensorReadings: vi.fn(),
    getAutomationRules: vi.fn(),
    createAutomationRule: vi.fn(),
    updateAutomationRule: vi.fn(),
    deleteAutomationRule: vi.fn(),
  },
}));

import api from '@/api';
import IotManagementView from '@/views/IotManagementView.vue';

const mockDevices = [
  { id: 1, name: '環境感測器', device_type: '舍內環境監控', category: 'sensor', status: 'online' },
  { id: 2, name: '降溫風扇', device_type: '自動風扇', category: 'actuator', status: 'offline' },
];

const mockRules = [
  {
    id: 10,
    name: '高溫啟動風扇',
    trigger_source_device_id: 1,
    action_target_device_id: 2,
    trigger_condition: { variable: 'temperature', operator: '>', value: 28 },
    action_command: { command: 'turn_on' },
    is_enabled: true,
  },
];

const globalStubs = {
  'el-row': true,
  'el-col': true,
  'el-card': true,
  'el-table': true,
  'el-table-column': true,
  'el-button': true,
  'el-dialog': true,
  'el-drawer': true,
  'el-popconfirm': true,
  'el-switch': true,
  'el-tag': true,
  'el-icon': true,
  'el-tooltip': true,
  'el-empty': true,
  'el-descriptions': true,
  'el-descriptions-item': true,
  'el-form': true,
  'el-form-item': true,
  'el-select': true,
  'el-option': true,
  'el-input': true,
  'el-alert': true,
  'automation-rule-builder': { template: '<div />' },
};

describe('IotManagementView', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    api.getIotDevices.mockResolvedValue(mockDevices);
    api.getAutomationRules.mockResolvedValue(mockRules);
    api.getDeviceSensorReadings.mockResolvedValue([
      { id: 100, data: { temperature: 30 }, created_at: '2024-08-20T00:00:00Z' },
    ]);
  });

  const mountView = () =>
    shallowMount(IotManagementView, {
      global: {
        stubs: globalStubs,
      },
    });

  it('loads devices and rules on mount', async () => {
    const wrapper = mountView();
    await flushPromises();

    const store = useIotStore();
    expect(store.devices).toEqual(mockDevices);
    expect(store.rules).toEqual(mockRules);

    wrapper.unmount();
  });

  it('opens device dialog via helper', async () => {
    const wrapper = mountView();
    await flushPromises();

    expect(wrapper.vm.deviceDialogVisible).toBe(false);
    wrapper.vm.openDeviceDialog();
    await wrapper.vm.$nextTick();

    expect(wrapper.vm.deviceDialogVisible).toBe(true);
    expect(wrapper.vm.isEditingDevice).toBe(false);

    wrapper.unmount();
  });

  it('fetches readings when selecting a device', async () => {
    const wrapper = mountView();
    await flushPromises();

    await wrapper.vm.handleRowClick(mockDevices[0]);
    await flushPromises();

    expect(api.getDeviceSensorReadings).toHaveBeenCalledWith(1, { limit: 50 });
    expect(wrapper.vm.drawerVisible).toBe(true);

    wrapper.unmount();
  });
});
