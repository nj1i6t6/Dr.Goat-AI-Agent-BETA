<template>
  <el-form ref="formRef" :model="form" label-width="120px" class="rule-builder-form">
    <el-form-item label="規則名稱" prop="name" :rules="[{ required: true, message: '請輸入規則名稱' }]"><el-input v-model="form.name" /></el-form-item>

    <el-divider>IF 條件</el-divider>
    <el-form-item label="感測器裝置" prop="trigger_source_device_id" :rules="[{ required: true, message: '請選擇感測器' }]">
      <el-select v-model="form.trigger_source_device_id" placeholder="選擇感測器" @change="handleSensorChange">
        <el-option v-for="sensor in sensors" :key="sensor.id" :label="sensor.name" :value="sensor.id" />
      </el-select>
    </el-form-item>
    <el-form-item label="數據變數" prop="trigger_condition.variable" :rules="[{ required: true, message: '請選擇變數' }]">
      <el-select v-model="form.trigger_condition.variable" placeholder="選擇變數">
        <el-option v-for="option in variableOptions" :key="option.value" :label="option.label" :value="option.value" />
      </el-select>
    </el-form-item>
    <el-form-item label="運算子" prop="trigger_condition.operator" :rules="[{ required: true, message: '請選擇運算子' }]">
      <el-select v-model="form.trigger_condition.operator">
        <el-option v-for="operator in operators" :key="operator" :label="operator" :value="operator" />
      </el-select>
    </el-form-item>
    <el-form-item label="閾值" prop="trigger_condition.value" :rules="[{ required: true, message: '請輸入閾值' }]"><el-input v-model="form.trigger_condition.value" /></el-form-item>

    <el-divider>THEN 動作</el-divider>
    <el-form-item label="致動器裝置" prop="action_target_device_id" :rules="[{ required: true, message: '請選擇致動器' }]">
      <el-select v-model="form.action_target_device_id" placeholder="選擇致動器" @change="handleActuatorChange">
        <el-option v-for="actuator in actuators" :key="actuator.id" :label="actuator.name" :value="actuator.id" />
      </el-select>
    </el-form-item>
    <el-form-item label="指令" prop="action_command.command" :rules="[{ required: true, message: '請選擇指令' }]">
      <el-select v-model="form.action_command.command" placeholder="選擇指令">
        <el-option v-for="command in commandOptions" :key="command" :label="command" :value="command" />
      </el-select>
    </el-form-item>
    <el-form-item label="指令參數 (JSON)">
      <el-input v-model="rawParameters" type="textarea" :rows="3" placeholder='例如：{"duration_minutes": 30}' />
    </el-form-item>
    <el-form-item label="啟用規則"><el-switch v-model="form.is_enabled" /></el-form-item>

    <div class="builder-actions">
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="primary" @click="handleSubmit">儲存規則</el-button>
    </div>
  </el-form>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue';
import { ElMessage } from 'element-plus';

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      name: '',
      trigger_source_device_id: null,
      trigger_condition: { variable: '', operator: '>', value: '' },
      action_target_device_id: null,
      action_command: { command: '', parameters: {} },
      is_enabled: true,
    }),
  },
  sensors: {
    type: Array,
    default: () => [],
  },
  actuators: {
    type: Array,
    default: () => [],
  },
  deviceCommandOptions: {
    type: Function,
    required: true,
  },
});

const emit = defineEmits(['save', 'cancel']);

const formRef = ref();
const form = reactive(structuredClone(props.modelValue));
const rawParameters = ref(JSON.stringify(form.action_command.parameters || {}, null, 0));

const operators = ['>', '>=', '<', '<=', '=', '!='];

const SENSOR_VARIABLES = Object.freeze({
  '舍內環境監控': [
    { label: '溫度 (°C)', value: 'temperature' },
    { label: '相對濕度 (%)', value: 'humidity' },
    { label: '氨氣濃度 (ppm)', value: 'ammonia_ppm' },
    { label: '二氧化碳濃度 (ppm)', value: 'co2_ppm' },
    { label: '光照 (lux)', value: 'light_lux' },
    { label: '噪音 (dB)', value: 'noise_db' },
  ],
  '智慧頸圈/耳標': [
    { label: '體溫 (°C)', value: 'body_temperature' },
    { label: '活動指數', value: 'activity_index' },
    { label: '反芻時間 (分鐘)', value: 'rumination_minutes' },
    { label: '發情偵測', value: 'estrus_detected' },
  ],
  '自動體重計': [
    { label: '體重 (kg)', value: 'weight_kg' },
  ],
  '智慧採食槽': [
    { label: '採食量 (g)', value: 'feed_intake_grams' },
    { label: '採食時長 (秒)', value: 'feeding_duration_seconds' },
  ],
  '智慧飲水器': [
    { label: '飲水量 (ml)', value: 'water_intake_ml' },
    { label: '飲水頻次', value: 'drinking_frequency' },
  ],
  'AI 視覺攝影機': [
    { label: '跛行警報', value: 'lameness_detected_alert' },
    { label: '異常倒臥', value: 'abnormal_lying_alert' },
  ],
});

const variableOptions = computed(() => {
  const sensor = props.sensors.find(item => item.id === form.trigger_source_device_id);
  if (!sensor) return [];
  return SENSOR_VARIABLES[sensor.device_type] || [
    { label: '溫度 (°C)', value: 'temperature' },
    { label: '相對濕度 (%)', value: 'humidity' },
  ];
});

const commandOptions = computed(() => {
  const actuator = props.actuators.find(item => item.id === form.action_target_device_id);
  return actuator ? props.deviceCommandOptions(actuator.device_type) : [];
});

watch(
  () => props.modelValue,
  (value) => {
    Object.assign(form, structuredClone(value));
    rawParameters.value = JSON.stringify(form.action_command.parameters || {}, null, 0);
  },
  { deep: true }
);

watch(variableOptions, (options) => {
  if (options.length && !options.find(option => option.value === form.trigger_condition.variable)) {
    form.trigger_condition.variable = options[0].value;
  }
});

watch(commandOptions, (options) => {
  if (options.length && !options.includes(form.action_command.command)) {
    form.action_command.command = options[0];
  }
});

function handleSensorChange() {
  if (!variableOptions.value.find(option => option.value === form.trigger_condition.variable)) {
    form.trigger_condition.variable = variableOptions.value[0]?.value || '';
  }
}

function handleActuatorChange() {
  const options = commandOptions.value;
  if (!options.includes(form.action_command.command)) {
    form.action_command.command = options[0] || '';
  }
}

function parseParameters() {
  if (!rawParameters.value || !rawParameters.value.trim()) {
    return {};
  }
  try {
    return JSON.parse(rawParameters.value);
  } catch (error) {
    throw new Error('指令參數必須為有效的 JSON 字串');
  }
}

function handleSubmit() {
  formRef.value.validate(async (valid) => {
    if (!valid) return;
    try {
      form.action_command.parameters = parseParameters();
      emit('save', structuredClone(form));
    } catch (error) {
      ElMessage.error(error.message || String(error));
    }
  });
}

function handleCancel() {
  emit('cancel');
}
</script>

<style scoped>
.rule-builder-form {
  max-width: 640px;
}

.builder-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}
</style>
