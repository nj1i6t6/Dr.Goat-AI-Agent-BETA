<template>
  <div v-loading="loading">
    <el-row :gutter="20">
      <el-col :md="10">
        <h4>數據列表</h4>
        <el-table :data="historyData" stripe height="400">
          <el-table-column prop="record_date" label="日期" width="120" />
          <el-table-column prop="record_type" label="類型">
            <template #default="{ row }">{{ historyTypeMap[row.record_type] || row.record_type }}</template>
          </el-table-column>
          <el-table-column prop="value" label="數值" />
          <el-table-column label="操作" width="90">
            <template #default="{ row }">
              <el-button type="danger" size="small" @click="handleDelete(row.id)">刪除</el-button>
            </template>
          </el-table-column>
          <template #empty>
            <el-empty description="此羊隻尚無歷史數據" />
          </template>
        </el-table>
      </el-col>
      <el-col :md="14">
        <h4>數據圖表</h4>
        <el-select v-model="selectedChartType" placeholder="選擇圖表數據" style="width:100%; margin-bottom: 10px;">
          <el-option v-for="type in availableChartTypes" :key="type" :label="historyTypeMap[type] || type" :value="type" />
        </el-select>
        <div class="chart-container">
          <Line v-if="chartData.datasets[0]?.data.length > 0" :data="chartData" :options="chartOptions" />
          <el-empty v-else description="選擇的類型無數據可供繪製圖表" />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import api from '../../../api';
import { Line } from 'vue-chartjs';
import { Chart as ChartJS, Title, Tooltip, Legend, LineElement, CategoryScale, LinearScale, PointElement, TimeScale } from 'chart.js';
import 'chartjs-adapter-date-fns';

ChartJS.register(Title, Tooltip, Legend, LineElement, CategoryScale, LinearScale, PointElement, TimeScale);

const props = defineProps({
  earNum: { type: String, required: true },
});

const loading = ref(false);
const historyData = ref([]);
const selectedChartType = ref('');

const historyTypeMap = {
  'Body_Weight_kg': '體重 (公斤)',
  'milk_yield_kg_day': '日產奶量 (公斤/天)',
  'milk_fat_percentage': '乳脂率 (%)'
};

const availableChartTypes = computed(() => [...new Set(historyData.value.map(d => d.record_type))]);

const chartData = computed(() => {
  const filtered = historyData.value.filter(d => d.record_type === selectedChartType.value);
  return {
    datasets: [{
      label: historyTypeMap[selectedChartType.value] || selectedChartType.value,
      data: filtered.map(d => ({ x: new Date(d.record_date).getTime(), y: d.value })),
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59, 130, 246, 0.2)',
      tension: 0.1,
      fill: true,
    }],
  };
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    x: { type: 'time', time: { unit: 'day' } },
    y: { beginAtZero: false }
  }
};

const fetchHistory = async () => {
  loading.value = true;
  try {
    historyData.value = await api.getSheepHistory(props.earNum);
    if (availableChartTypes.value.length > 0) {
      selectedChartType.value = availableChartTypes.value[0];
    }
  } catch (error) {
    ElMessage.error(`載入歷史數據失敗: ${error.error || error.message}`);
  } finally {
    loading.value = false;
  }
};

const handleDelete = async (recordId) => {
  try {
    await ElMessageBox.confirm('確定要刪除這條歷史數據嗎？', '警告', { type: 'warning' });
    await api.deleteSheepHistory(recordId);
    ElMessage.success('刪除成功');
    await fetchHistory();
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(`刪除失敗: ${error.error || error.message}`);
    }
  }
};

onMounted(() => {
  fetchHistory();
});
</script>

<style scoped>
.chart-container {
  height: 350px;
  position: relative;
}
</style>