import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import api from '../api';

export const useSheepStore = defineStore('sheep', () => {
  // --- State ---
  const sheepList = ref([]);
  const isLoading = ref(false);
  const hasLoaded = ref(false);

  // --- Getters ---
  const sortedSheepList = computed(() => {
    return [...sheepList.value].sort((a, b) => a.EarNum.localeCompare(b.EarNum, undefined, { numeric: true }));
  });
  
  const filterOptions = computed(() => {
    const farmNums = [...new Set(sheepList.value.map(s => s.FarmNum).filter(Boolean))].sort();
    const breeds = [...new Set(sheepList.value.map(s => s.Breed).filter(Boolean))].sort();
    return { farmNums, breeds };
  });

  // --- Actions ---
  async function fetchSheepList(force = false) {
    if (isLoading.value || (hasLoaded.value && !force)) {
      return;
    }
    isLoading.value = true;
    try {
      const data = await api.getAllSheep();
      sheepList.value = data;
      hasLoaded.value = true;
    } catch (error) {
      console.error("獲取羊群列表失敗:", error);
    } finally {
      isLoading.value = false;
    }
  }

  function addSheep(newSheep) {
    sheepList.value.push(newSheep);
  }

  function updateSheep(updatedSheep) {
    const index = sheepList.value.findIndex(s => s.id === updatedSheep.id);
    if (index !== -1) {
      sheepList.value[index] = updatedSheep;
    } else {
      // 如果找不到，可能是新增的羊，直接加入
      sheepList.value.push(updatedSheep);
    }
  }

  function removeSheep(earNum) {
    sheepList.value = sheepList.value.filter(s => s.EarNum !== earNum);
  }

  function refreshSheepList() {
    return fetchSheepList(true);
  }

  return {
    sheepList,
    isLoading,
    hasLoaded,
    sortedSheepList,
    filterOptions,
    fetchSheepList,
    addSheep,
    updateSheep,
    removeSheep,
    refreshSheepList,
  };
});