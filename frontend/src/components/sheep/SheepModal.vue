<template>
  <el-dialog
    v-model="dialogVisible"
    :title="title"
    width="70%"
    :before-close="handleClose"
    top="5vh"
    class="sheep-modal"
  >
    <div v-loading="loading">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="基本資料" name="basicInfoTab">
          <BasicInfoTab v-if="activeTab === 'basicInfoTab'" :sheep-data="sheepData" @data-updated="handleDataUpdated" @close="handleClose" />
        </el-tab-pane>
        <el-tab-pane label="事件日誌" name="eventsLogTab" :disabled="isNewSheep">
          <EventsLogTab v-if="activeTab === 'eventsLogTab' && !isNewSheep" :ear-num="earNum" />
        </el-tab-pane>
        <el-tab-pane label="歷史數據" name="historyTab" :disabled="isNewSheep">
          <HistoryTab v-if="activeTab === 'historyTab' && !isNewSheep" :ear-num="earNum" />
        </el-tab-pane>
      </el-tabs>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { ElMessage } from 'element-plus';
import api from '../../api';
import BasicInfoTab from './tabs/BasicInfoTab.vue';
import EventsLogTab from './tabs/EventsLogTab.vue';
import HistoryTab from './tabs/HistoryTab.vue';

const props = defineProps({
  earNum: {
    type: String,
    default: null,
  },
  initialTab: {
    type: String,
    default: 'basicInfoTab',
  },
});

const emit = defineEmits(['close', 'data-updated']);

const dialogVisible = ref(true);
const loading = ref(false);
const activeTab = ref(props.initialTab);
const sheepData = ref(null);

const isNewSheep = computed(() => !props.earNum);
const title = computed(() => isNewSheep.value ? '新增羊隻資料' : `管理羊隻資料 (耳號: ${props.earNum})`);

const fetchSheepDetails = async () => {
  if (isNewSheep.value) return;
  loading.value = true;
  try {
    sheepData.value = await api.getSheepDetails(props.earNum);
  } catch (error) {
    ElMessage.error(`載入羊隻資料失敗: ${error.error || error.message}`);
    handleClose();
  } finally {
    loading.value = false;
  }
};

const handleClose = () => {
  emit('close');
};

const handleDataUpdated = () => {
  emit('data-updated');
};

onMounted(() => {
  fetchSheepDetails();
});
</script>

<style>
/* Global style for this modal, not scoped */
.sheep-modal .el-dialog__body {
  padding-top: 10px;
  max-height: 75vh;
  overflow-y: auto;
}
</style>