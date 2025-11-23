<template>
  <div v-loading="loading">
    <h4>新增/編輯事件</h4>
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-row :gutter="20">
        <el-col :span="6"><el-form-item label="事件日期" prop="event_date"><el-date-picker v-model="form.event_date" type="date" value-format="YYYY-MM-DD" style="width:100%"/></el-form-item></el-col>
        <el-col :span="6">
          <el-form-item label="事件類型" prop="event_type">
            <el-select v-model="form.event_type" filterable allow-create placeholder="選擇或輸入類型" style="width:100%">
              <el-option v-for="item in eventOptions" :key="item.id" :label="item.name" :value="item.name"/>
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="簡要描述" prop="description">
            <el-autocomplete
              v-model="form.description"
              :fetch-suggestions="descriptionSuggestions"
              placeholder="輸入簡要描述"
              style="width:100%"
            />
          </el-form-item>
        </el-col>
      </el-row>
      <div v-if="showMedicationFields">
        <el-row :gutter="20">
          <el-col :span="12"><el-form-item label="用藥名稱"><el-input v-model="form.medication"/></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="停藥天數 (日)"><el-input-number v-model="form.withdrawal_days" :min="0" style="width:100%"/></el-form-item></el-col>
        </el-row>
      </div>
      <el-form-item label="詳細備註"><el-input v-model="form.notes" type="textarea" :rows="2"/></el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSubmit" :loading="saving">{{ isEditing ? '更新此事件' : '新增此事件' }}</el-button>
        <el-button v-if="isEditing" @click="resetForm">取消編輯</el-button>
      </el-form-item>
    </el-form>

    <el-divider />
    <h4>事件列表</h4>
    <el-table :data="events" stripe>
      <el-table-column prop="event_date" label="日期" width="120" />
      <el-table-column prop="event_type" label="類型" width="150" />
      <el-table-column label="描述/用藥">
        <template #default="{ row }">
          <div>{{ row.description }}</div>
          <div v-if="row.medication || row.withdrawal_days" class="medication-info">
            <el-tag size="small" v-if="row.medication">{{ row.medication }}</el-tag>
            <el-tag size="small" type="warning" v-if="row.withdrawal_days">停藥 {{ row.withdrawal_days }} 天</el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="notes" label="備註" />
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="handleEdit(row)">編輯</el-button>
          <el-button type="danger" size="small" @click="handleDelete(row.id)">刪除</el-button>
        </template>
      </el-table-column>
       <template #empty>
        <el-empty description="此羊隻尚無事件記錄" />
      </template>
    </el-table>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import api from '../../../api';

const props = defineProps({
  earNum: { type: String, required: true },
});

const loading = ref(false);
const saving = ref(false);
const events = ref([]);
const eventOptions = ref([]);

const formRef = ref(null);
const createInitialForm = () => ({
  id: null,
  event_date: new Date().toISOString().split('T')[0],
  event_type: '',
  description: '',
  notes: '',
  medication: '',
  withdrawal_days: null,
});
const form = reactive(createInitialForm());

const rules = {
  event_date: [{ required: true, message: '請選擇事件日期', trigger: 'change' }],
  event_type: [{ required: true, message: '請選擇或輸入事件類型', trigger: 'change' }],
};

const isEditing = computed(() => !!form.id);
const showMedicationFields = computed(() => form.event_type === '疾病治療');

const descriptionSuggestions = (queryString, cb) => {
  const selectedType = eventOptions.value.find(opt => opt.name === form.event_type);
  if (selectedType && selectedType.descriptions) {
    const results = selectedType.descriptions
      .map(d => ({ value: d.description }))
      .filter(item => item.value.toLowerCase().includes(queryString.toLowerCase()));
    cb(results);
  } else {
    cb([]);
  }
};

const fetchEvents = async () => {
  loading.value = true;
  try {
    events.value = await api.getSheepEvents(props.earNum);
  } catch (error) {
    ElMessage.error(`載入事件失敗: ${error.error || error.message}`);
  } finally {
    loading.value = false;
  }
};

const fetchEventOptions = async () => {
  try {
    eventOptions.value = await api.getEventOptions();
  } catch (error) {
    ElMessage.error(`載入事件選項失敗: ${error.error || error.message}`);
  }
};

const resetForm = () => {
  Object.assign(form, createInitialForm());
};

const handleEdit = (event) => {
  Object.assign(form, event);
};

const handleSubmit = async () => {
  await formRef.value.validate(async (valid) => {
    if (valid) {
      saving.value = true;
      try {
        if (isEditing.value) {
          await api.updateSheepEvent(form.id, form);
          ElMessage.success('事件更新成功');
        } else {
          await api.addSheepEvent(props.earNum, form);
          ElMessage.success('事件新增成功');
        }
        resetForm();
        await fetchEvents();
      } catch (error) {
        ElMessage.error(`操作失敗: ${error.error || error.message}`);
      } finally {
        saving.value = false;
      }
    }
  });
};

const handleDelete = async (eventId) => {
  try {
    await ElMessageBox.confirm('確定要刪除這條事件記錄嗎？', '警告', { type: 'warning' });
    await api.deleteSheepEvent(eventId);
    ElMessage.success('刪除成功');
    await fetchEvents();
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(`刪除失敗: ${error.error || error.message}`);
    }
  }
};

onMounted(() => {
  fetchEvents();
  fetchEventOptions();
});
</script>

<style scoped>
.medication-info {
  margin-top: 5px;
  display: flex;
  gap: 5px;
}
</style>