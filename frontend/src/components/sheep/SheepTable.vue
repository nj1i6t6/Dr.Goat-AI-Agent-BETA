<template>
  <div class="table-container" v-loading="loading">
    <el-auto-resizer>
      <template #default="{ height, width }">
        <el-table-v2
          :columns="columns"
          :data="sortedData"
          :width="width"
          :height="height"
          :sort-by="sortState"
          @column-sort="onSort"
          fixed
        >
          <template #empty>
             <el-empty description="尚無羊隻資料，或沒有任何羊隻符合目前的篩選條件。" />
          </template>
        </el-table-v2>
      </template>
    </el-auto-resizer>
  </div>
</template>

<script setup>
import { ref, computed, h } from 'vue';
import { ElButton, ElTooltip } from 'element-plus';
import { statusOptions } from '../../utils';

const props = defineProps({
  sheepData: { type: Array, required: true },
  loading: { type: Boolean, default: false },
});

const emit = defineEmits(['edit', 'delete', 'viewLog', 'consult']);

// Sort state: key is the dataKey of the column, order is 'asc' or 'desc'
const sortState = ref({
  key: 'EarNum',
  order: 'asc',
});

// Helper functions for rendering
const formatDate = (dateStr) => dateStr ? new Date(dateStr).toLocaleDateString() : 'N/A';
const getStatusText = (status) => statusOptions.find(s => s.value === status)?.label || status || '未指定';

const getReminders = (sheep) => {
  const reminders = [];
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const sevenDaysFromNow = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);
  
  const reminderFields = [
    { field: 'next_vaccination_due_date', text: '疫苗', icon: '💉' },
    { field: 'next_deworming_due_date', text: '驅蟲', icon: '💊' },
    { field: 'expected_lambing_date', text: '產仔', icon: '🐑' },
  ];

  reminderFields.forEach(r => {
    if (sheep[r.field]) {
      const dueDate = new Date(sheep[r.field]);
      if (!isNaN(dueDate.getTime())) {
        const isOverdue = dueDate < today;
        if (isOverdue || dueDate <= sevenDaysFromNow) {
          reminders.push({ ...r, isOverdue, dueDate });
        }
      }
    }
  });
  return reminders;
};

// Define columns for el-table-v2
const columns = [
  { key: 'EarNum', dataKey: 'EarNum', title: '耳號', width: 150, sortable: true },
  { key: 'Breed', dataKey: 'Breed', title: '品種', width: 150, sortable: true },
  { key: 'Sex', dataKey: 'Sex', title: '性別', width: 100, sortable: true },
  { 
    key: 'BirthDate', 
    dataKey: 'BirthDate', 
    title: '出生日期', 
    width: 150, 
    sortable: true,
    cellRenderer: ({ cellData }) => formatDate(cellData)
  },
  { 
    key: 'status', 
    dataKey: 'status', 
    title: '狀態/提醒', 
    width: 200, 
    sortable: true,
    cellRenderer: ({ rowData }) => {
      const reminders = getReminders(rowData);
      const reminderNodes = reminders.map(r => 
        h(ElTooltip, { 
          content: `${formatDate(r.dueDate)} ${r.text}${r.isOverdue ? '已過期' : '即將到期'}`, 
          placement: 'top'
        }, () => h('span', { class: ['reminder-icon', { overdue: r.isOverdue }] }, r.icon))
      );
      return h('div', null, [
        h('span', null, getStatusText(rowData.status)),
        ...reminderNodes
      ]);
    }
  },
  {
    key: 'operations',
    title: '操作',
    width: 280,
    align: 'center',
    cellRenderer: ({ rowData }) => [
      h(ElButton, { type: 'success', size: 'small', onClick: () => emit('consult', rowData.EarNum) }, () => '諮詢'),
      h(ElButton, { type: 'primary', size: 'small', onClick: () => emit('edit', rowData.EarNum) }, () => '編輯'),
      h(ElButton, { type: 'info', size: 'small', onClick: () => emit('viewLog', rowData.EarNum) }, () => '日誌'),
      h(ElButton, { type: 'danger', size: 'small', onClick: () => emit('delete', rowData.EarNum) }, () => '刪除'),
    ]
  }
];

// Sorting logic
const onSort = ({ key, order }) => {
  sortState.value = { key, order };
};

const sortedData = computed(() => {
  const data = [...props.sheepData];
  const { key, order } = sortState.value;
  if (!key || !order) return data;
  
  return data.sort((a, b) => {
    let valA = a[key] || '';
    let valB = b[key] || '';
    
    if (key === 'BirthDate') {
      valA = valA ? new Date(valA).getTime() : 0;
      valB = valB ? new Date(valB).getTime() : 0;
    }

    const modifier = order === 'asc' ? 1 : -1;

    if (typeof valA === 'string' && typeof valB === 'string') {
        // Use localeCompare for more natural string sorting (e.g., handles numbers in strings better)
        return valA.localeCompare(valB, undefined, { numeric: true }) * modifier;
    }
    
    if (valA < valB) return -1 * modifier;
    if (valA > valB) return 1 * modifier;
    return 0;
  });
});
</script>

<style scoped>
.table-container {
  width: 100%;
  height: calc(100vh - 400px); /* Adjust height based on your layout */
  min-height: 400px;
}
:deep(.reminder-icon) {
  margin-left: 5px;
  cursor: help;
}
:deep(.reminder-icon.overdue) {
  color: #f56c6c;
}
</style>