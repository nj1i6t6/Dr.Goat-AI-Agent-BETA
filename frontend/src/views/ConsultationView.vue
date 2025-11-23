<template>
  <div class="consultation-page">
    <h1 class="page-title">
      <el-icon><HelpFilled /></el-icon>
  營養與ESG建議
    </h1>

    <el-card shadow="never">
      <div class="search-area">
        <el-input
          v-model="earNumInput"
          placeholder="在此輸入耳號以載入資料"
          clearable
          @keyup.enter="loadSheepData"
        >
          <template #append>
            <el-button :icon="Search" @click="loadSheepData" :loading="formLoading" />
          </template>
        </el-input>
      </div>

      <!-- 表單現在直接綁定 consultationStore.form -->
      <el-form
        ref="formRef"
        :model="consultationStore.form"
        :rules="rules"
        label-position="top"
        v-loading="formLoading"
      >
        <el-divider content-position="left"><h4>羊隻資料</h4></el-divider>
        <el-row :gutter="20">
          <el-col :sm="12" :md="6"><el-form-item label="諮詢耳號" prop="EarNum"><el-input v-model="consultationStore.form.EarNum" /></el-form-item></el-col>
          <el-col :sm="12" :md="6"><el-form-item label="品種名稱" prop="Breed"><el-input v-model="consultationStore.form.Breed" /></el-form-item></el-col>
          <el-col :sm="12" :md="6"><el-form-item label="性別" prop="Sex"><el-select v-model="consultationStore.form.Sex" placeholder="請選擇性別" style="width:100%;"><el-option v-for="item in sexOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select></el-form-item></el-col>
          <el-col :sm="12" :md="6"><el-form-item label="出生日期" prop="BirthDate"><el-date-picker v-model="consultationStore.form.BirthDate" type="date" placeholder="選擇日期" style="width:100%;" value-format="YYYY-MM-DD" /></el-form-item></el-col>
        </el-row>
        
        <el-divider content-position="left"><h4>當前狀態與生產參數</h4></el-divider>
        <el-row :gutter="20">
          <el-col :sm="12" :md="8"><el-form-item label="體重 (kg)" prop="Body_Weight_kg"><el-input-number v-model="consultationStore.form.Body_Weight_kg" :min="0" :precision="1" controls-position="right" style="width:100%;" /></el-form-item></el-col>
          <el-col :sm="12" :md="8"><el-form-item label="月齡" prop="Age_Months"><el-input-number v-model="consultationStore.form.Age_Months" :min="0" controls-position="right" style="width:100%;" /></el-form-item></el-col>
          <el-col :sm="24" :md="8"><el-form-item label="品種類別" prop="breed_category"><el-select v-model="consultationStore.form.breed_category" placeholder="請選擇品種類別" style="width:100%;"><el-option v-for="item in breedCategoryOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select></el-form-item></el-col>
        </el-row>
        <el-form-item label="生理狀態" prop="status">
          <el-select v-model="consultationStore.form.status" placeholder="請選擇生理狀態" style="width:100%;"><el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select>
        </el-form-item>
        <el-form-item v-if="consultationStore.form.status === 'other_status'" label="請描述其他生理狀態" prop="status_description"><el-input v-model="consultationStore.form.status_description" /></el-form-item>
        
        <el-row :gutter="20" v-if="showProductionParams">
          <el-col :sm="12" v-if="isGrowing"><el-form-item label="目標日增重 (克/天)" prop="target_average_daily_gain_g"><el-input-number v-model="consultationStore.form.target_average_daily_gain_g" :min="0" controls-position="right" style="width:100%;" /></el-form-item></el-col>
          <el-col :sm="12" v-if="isLactating"><el-form-item label="日產奶量 (公斤/天)" prop="milk_yield_kg_day"><el-input-number v-model="consultationStore.form.milk_yield_kg_day" :min="0" :precision="1" controls-position="right" style="width:100%;" /></el-form-item></el-col>
          <el-col :sm="12" v-if="isLactating"><el-form-item label="乳脂率 (%)" prop="milk_fat_percentage"><el-input-number v-model="consultationStore.form.milk_fat_percentage" :min="0" :precision="1" controls-position="right" style="width:100%;" /></el-form-item></el-col>
          <el-col :sm="12" v-if="isGestating"><el-form-item label="胎兒數 (1, 2, 3+)" prop="number_of_fetuses"><el-input-number v-model="consultationStore.form.number_of_fetuses" :min="1" controls-position="right" style="width:100%;" /></el-form-item></el-col>
        </el-row>
        
        <el-form-item label="活動量" prop="activity_level">
          <el-select v-model="consultationStore.form.activity_level" placeholder="請選擇活動量" style="width:100%;"><el-option v-for="item in activityLevelOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select>
        </el-form-item>
        <el-form-item label="使用者備註 (給AI)" prop="other_remarks"><el-input v-model="consultationStore.form.other_remarks" type="textarea" :rows="3" /></el-form-item>

        <el-divider content-position="left"><h4>AI 建議設定</h4></el-divider>
        <el-form-item label="優化目標" prop="optimization_goal">
          <el-radio-group v-model="consultationStore.form.optimization_goal">
            <el-radio-button label="balanced">均衡營養 (預設)</el-radio-button>
            <el-radio-button label="esg_focused">最低環境衝擊</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" size="large" @click="handleGetRecommendation" :loading="consultationStore.isLoading">獲取永續飼養建議</el-button>
          <el-button size="large" @click="handleResetForm">重設表單</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" class="results-area" v-if="consultationStore.resultHtml || consultationStore.isLoading">
      <h3 class="results-title">領頭羊博士的綜合建議</h3>
      <div v-loading="consultationStore.isLoading" class="recommendation-content" v-html="consultationStore.resultHtml"></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { HelpFilled, Search } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { useSettingsStore } from '../stores/settings';
import { useConsultationStore } from '../stores/consultation';
import api from '../api';
import { sexOptions, breedCategoryOptions, statusOptions, activityLevelOptions, formatDateForInput } from '../utils';

const route = useRoute();
const router = useRouter();
const settingsStore = useSettingsStore();
const consultationStore = useConsultationStore();

const earNumInput = ref('');
const formRef = ref(null);
const formLoading = ref(false);

const rules = {
  EarNum: [{ required: true, message: '請輸入耳號', trigger: 'blur' }],
  Body_Weight_kg: [{ required: true, type: 'number', message: '請輸入體重', trigger: 'blur' }],
  Age_Months: [{ required: true, type: 'number', message: '請輸入月齡', trigger: 'blur' }],
  breed_category: [{ required: true, message: '請選擇品種類別', trigger: 'change' }],
  status: [{ required: true, message: '請選擇生理狀態', trigger: 'change' }],
};

const isGrowing = computed(() => consultationStore.form.status?.includes('growing'));
const isLactating = computed(() => consultationStore.form.status?.includes('lactating'));
const isGestating = computed(() => consultationStore.form.status?.includes('gestating'));
const showProductionParams = computed(() => isGrowing.value || isLactating.value || isGestating.value);

const loadSheepData = async () => {
  if (!earNumInput.value) {
    ElMessage.warning('請輸入要查詢的耳號');
    return;
  }
  formLoading.value = true;
  try {
    const data = await api.getSheepDetails(earNumInput.value);
    const formattedData = { ...data, BirthDate: formatDateForInput(data.BirthDate) };
    // 使用 store action 來更新表單數據和清空舊結果
    consultationStore.setFormData(formattedData);
    ElMessage.success(`已成功載入耳號 ${data.EarNum} 的資料`);
  } catch (error) {
    ElMessage.error(`載入資料失敗: ${error.error || error.message}`);
    // 即使失敗也重置 store，但保留用戶輸入的耳號
    consultationStore.reset();
    consultationStore.form.EarNum = earNumInput.value;
  } finally {
    formLoading.value = false;
  }
};

const handleGetRecommendation = async () => {
  if (!settingsStore.hasApiKey) {
    ElMessage.error('請先在「系統設定」中設定並測試有效的 API 金鑰');
    return;
  }
  await formRef.value.validate(async (valid) => {
    if (valid) {
      consultationStore.getRecommendation(settingsStore.apiKey);
    } else {
      ElMessage.warning('請檢查表單必填項是否已填寫');
    }
  });
};

const handleResetForm = () => {
  earNumInput.value = '';
  consultationStore.reset();
};

onMounted(() => {
  if (route.query.earNum) {
    earNumInput.value = route.query.earNum;
    loadSheepData();
    router.replace({ query: {} });
  }
});
</script>

<style scoped>
/* 樣式保持不變 */
.consultation-page {
  animation: fadeIn 0.5s ease-out;
}
.page-title {
  font-size: 1.8em; color: #1e3a8a; margin-top: 0;
  margin-bottom: 20px; display: flex; align-items: center;
}
.page-title .el-icon {
  margin-right: 10px;
}
.search-area {
  margin-bottom: 20px;
  max-width: 500px;
}
.results-area {
  margin-top: 20px;
}
.results-title {
  color: #1e40af;
  margin-bottom: 15px;
}
.recommendation-content {
  min-height: 100px;
  line-height: 1.7;
}
.recommendation-content :deep(h1),
.recommendation-content :deep(h2),
.recommendation-content :deep(h3) {
  color: #1e3a8a;
  border-bottom: 1px solid #eee;
  padding-bottom: 5px;
  margin-top: 20px;
}
.recommendation-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 15px 0;
}
.recommendation-content :deep(th),
.recommendation-content :deep(td) {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}
.recommendation-content :deep(th) {
  background-color: #f2f6fc;
}
.recommendation-content :deep(code) {
  background-color: #f0f4f8;
  padding: 2px 5px;
  border-radius: 4px;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>