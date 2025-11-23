import { defineStore } from 'pinia';
import { ref, reactive, toRaw } from 'vue';
import api from '../api';

// Helper function to create a clean, initial state for the form
const createInitialFormState = () => ({
  EarNum: '', Breed: '', Sex: '', BirthDate: '',
  Body_Weight_kg: null, Age_Months: null,
  breed_category: 'Dairy', status: 'maintenance', status_description: '',
  target_average_daily_gain_g: null, milk_yield_kg_day: null,
  milk_fat_percentage: null, number_of_fetuses: null,
  activity_level: 'confined', other_remarks: '',
  optimization_goal: 'balanced',
});


export const useConsultationStore = defineStore('consultation', () => {
  // --- State ---
  // 將表單數據本身也作為 store 的一部分
  const form = reactive(createInitialFormState());

  const isLoading = ref(false);
  const resultHtml = ref('');
  const error = ref('');
  
  // --- Actions ---

  // Action to update the form with new data (e.g., from loading a sheep)
  function setFormData(data) {
    // Reset form to initial state first to clear old values
    Object.assign(form, createInitialFormState());
    // Assign new values
    Object.keys(form).forEach(key => {
      if (data[key] !== undefined) {
        form[key] = data[key];
      }
    });
    // When new data is loaded, clear the previous AI result
    resultHtml.value = '';
    error.value = '';
  }

  // Action to get recommendation
  async function getRecommendation(apiKey) {
    // We use the form state stored within this store
    const formData = toRaw(form);

    isLoading.value = true;
    resultHtml.value = ''; // Clear previous result before fetching new one
    error.value = '';

    try {
      const response = await api.getRecommendation(apiKey, formData);
      resultHtml.value = response.recommendation_html;
    } catch (err) {
      const errorMessage = err.error || err.message || '獲取建議時發生未知錯誤';
      error.value = errorMessage;
      resultHtml.value = `<div style="color:red;">獲取建議失敗: ${errorMessage}</div>`;
    } finally {
      isLoading.value = false;
    }
  }

  // Action to reset everything
  function reset() {
    Object.assign(form, createInitialFormState());
    isLoading.value = false;
    resultHtml.value = '';
    error.value = '';
  }

  return {
    form,
    isLoading,
    resultHtml,
    error,
    setFormData,
    getRecommendation,
    reset,
  };
});