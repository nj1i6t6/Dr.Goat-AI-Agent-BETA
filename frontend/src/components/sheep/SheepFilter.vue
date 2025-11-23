<template>
  <el-card shadow="never" class="filter-card">
    <el-form :model="filterForm" label-position="top">
      <el-row :gutter="20">
        <!-- 新增：耳號搜尋框 -->
        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="耳號搜尋">
            <el-input
              v-model="filterForm.earNumSearch"
              placeholder="輸入部分或完整耳號"
              clearable
              @keyup.enter="emitFilter"
            />
          </el-form-item>
        </el-col>

        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="牧場編號">
            <el-select-v2
              v-model="filterForm.farmNum"
              :options="farmNumOptions"
              placeholder="所有牧場"
              clearable
              style="width: 100%;"
            />
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="品種">
            <el-select-v2
              v-model="filterForm.breed"
              :options="breedOptions"
              placeholder="所有品種"
              clearable
              filterable
              style="width: 100%;"
            />
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="性別">
            <el-select v-model="filterForm.sex" placeholder="所有性別" clearable style="width: 100%;">
               <el-option v-for="item in sexOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
           <el-form-item label="品種類別">
            <el-select v-model="filterForm.breedCategory" placeholder="所有類別" clearable style="width: 100%;">
              <el-option v-for="item in breedCategoryOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12" :md="10">
          <el-form-item label="出生日期範圍">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="開始日期"
              end-placeholder="結束日期"
              style="width: 100%;"
              value-format="YYYY-MM-DD"
            />
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="24" :md="8" class="action-buttons">
            <el-button type="primary" :icon="Search" @click="emitFilter">搜尋</el-button>
            <el-button @click="resetFilter">清除篩選</el-button>
        </el-col>
      </el-row>
    </el-form>
  </el-card>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue';
import { Search } from '@element-plus/icons-vue';
import { useSheepStore } from '../../stores/sheep';
import { sexOptions, breedCategoryOptions, statusOptions } from '../../utils';

const sheepStore = useSheepStore();
const emit = defineEmits(['filter']);

const createInitialFilter = () => ({
  earNumSearch: '', // 新增：耳號搜尋欄位的狀態
  farmNum: '',
  breed: '',
  sex: '',
  breedCategory: '',
  status: '',
  startDate: '',
  endDate: '',
});

const filterForm = reactive(createInitialFilter());
const dateRange = ref([]);

// 為 el-select-v2 準備選項格式
const farmNumOptions = computed(() => sheepStore.filterOptions.farmNums.map(val => ({ label: val, value: val })));
const breedOptions = computed(() => sheepStore.filterOptions.breeds.map(val => ({ label: val, value: val })));

watch(dateRange, (newRange) => {
  filterForm.startDate = newRange ? newRange[0] : '';
  filterForm.endDate = newRange ? newRange[1] : '';
});

const emitFilter = () => {
  emit('filter', { ...filterForm });
};

const resetFilter = () => {
  Object.assign(filterForm, createInitialFilter());
  dateRange.value = [];
  emitFilter();
};
</script>

<style scoped>
.filter-card {
  margin-bottom: 20px;
}
.action-buttons {
  display: flex;
  align-items: flex-end;
  padding-bottom: 18px; /* To align with form items */
}
</style>