import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';

import { useIotStore } from '@/stores/iot';

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

const mockDevices = [
  { id: 1, name: '環境感測器', device_type: '舍內環境監控', category: 'sensor', status: 'online' },
  { id: 2, name: '降溫風扇', device_type: '自動風扇', category: 'actuator', status: 'offline' },
];

const mockRules = [
  { id: 10, name: '高溫啟動風扇', trigger_source_device_id: 1, action_target_device_id: 2, trigger_condition: {}, action_command: {}, is_enabled: true },
];

describe('iot Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('initial state should be correct', () => {
    const store = useIotStore();
    expect(store.devices).toEqual([]);
    expect(store.rules).toEqual([]);
    expect(store.sensorDevices).toEqual([]);
    expect(store.actuatorDevices).toEqual([]);
    expect(store.lastCreatedApiKey).toBeNull();
  });

  it('fetchDevices should populate device list', async () => {
    api.getIotDevices.mockResolvedValue(mockDevices);
    const store = useIotStore();

    await store.fetchDevices();

    expect(api.getIotDevices).toHaveBeenCalledTimes(1);
    expect(store.devices).toHaveLength(2);
    expect(store.sensorDevices[0].name).toBe('環境感測器');
  });

  it('createDevice should insert device and store api key once', async () => {
    const created = { id: 3, name: '新感測器', device_type: '舍內環境監控', category: 'sensor', api_key: 'secret' };
    api.createIotDevice.mockResolvedValue(created);
    const store = useIotStore();

    const result = await store.createDevice({ name: created.name, device_type: created.device_type, category: created.category });

    expect(api.createIotDevice).toHaveBeenCalledWith({ name: created.name, device_type: created.device_type, category: created.category });
    expect(store.devices[0].id).toBe(3);
    expect(store.devices[0]).not.toHaveProperty('api_key');
    expect(store.lastCreatedApiKey).toBe('secret');
    expect(result.api_key).toBe('secret');
  });

  it('updateDevice should replace existing entry', async () => {
    const store = useIotStore();
    store.devices = [...mockDevices];
    api.updateIotDevice.mockResolvedValue({ ...mockDevices[0], location: 'A 區' });

    const updated = await store.updateDevice(1, { location: 'A 區' });

    expect(api.updateIotDevice).toHaveBeenCalledWith(1, { location: 'A 區' });
    expect(updated.location).toBe('A 區');
    expect(store.devices[0].location).toBe('A 區');
  });

  it('deleteDevice should remove entry', async () => {
    const store = useIotStore();
    store.devices = [...mockDevices];
    api.deleteIotDevice.mockResolvedValue({ success: true });

    await store.deleteDevice(1);

    expect(api.deleteIotDevice).toHaveBeenCalledWith(1);
    expect(store.devices).toHaveLength(1);
    expect(store.devices[0].id).toBe(2);
  });

  it('fetchDeviceReadings caches readings per device', async () => {
    const store = useIotStore();
    api.getDeviceSensorReadings.mockResolvedValue([{ id: 1, data: { temperature: 30 }, created_at: '2024-08-20T00:00:00Z' }]);

    const readings = await store.fetchDeviceReadings(1, 10);

    expect(api.getDeviceSensorReadings).toHaveBeenCalledWith(1, { limit: 10 });
    expect(readings).toHaveLength(1);
    expect(store.readings[1]).toEqual(readings);
  });

  it('fetchRules should populate rules array', async () => {
    const store = useIotStore();
    api.getAutomationRules.mockResolvedValue(mockRules);

    await store.fetchRules();

    expect(api.getAutomationRules).toHaveBeenCalledTimes(1);
    expect(store.rules).toHaveLength(1);
    expect(store.rules[0].id).toBe(10);
  });

  it('createRule and updateRule should maintain rule list', async () => {
    const store = useIotStore();
    api.createAutomationRule.mockResolvedValue(mockRules[0]);
    api.updateAutomationRule.mockResolvedValue({ ...mockRules[0], name: '更新後規則' });

    await store.createRule({ name: '高溫啟動風扇' });
    expect(store.rules).toHaveLength(1);

    const updated = await store.updateRule(10, { name: '更新後規則' });
    expect(api.updateAutomationRule).toHaveBeenCalledWith(10, { name: '更新後規則' });
    expect(updated.name).toBe('更新後規則');
    expect(store.rules[0].name).toBe('更新後規則');
  });

  it('deleteRule should remove target rule', async () => {
    const store = useIotStore();
    store.rules = [...mockRules];
    api.deleteAutomationRule.mockResolvedValue({ success: true });

    await store.deleteRule(10);

    expect(api.deleteAutomationRule).toHaveBeenCalledWith(10);
    expect(store.rules).toEqual([]);
  });

  it('getCommandOptions should fallback to default commands', () => {
    const store = useIotStore();
    expect(store.getCommandOptions('自動風扇')).toContain('turn_on');
    expect(store.getCommandOptions('未知裝置')).toEqual(['turn_on', 'turn_off']);
  });
});
