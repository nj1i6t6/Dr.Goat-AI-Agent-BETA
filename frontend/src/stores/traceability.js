import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import api from '../api';

export const useTraceabilityStore = defineStore('traceability', () => {
  const batches = ref([]);
  const isLoading = ref(false);
  const selectedBatch = ref(null);
  const isSaving = ref(false);

  const sortedBatches = computed(() => {
    return [...batches.value].sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
  });

  async function fetchBatches(includeDetails = false) {
    if (isLoading.value) return;
    isLoading.value = true;
    try {
      const data = await api.getTraceabilityBatches(includeDetails);
      batches.value = data || [];
      return data;
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchBatch(batchId) {
    const data = await api.getTraceabilityBatch(batchId);
    selectedBatch.value = data;
    const index = batches.value.findIndex(b => b.id === data.id);
    if (index !== -1) {
      batches.value[index] = data;
    } else {
      batches.value.unshift(data);
    }
    return data;
  }

  async function createBatch(payload) {
    isSaving.value = true;
    try {
      const created = await api.createTraceabilityBatch(payload);
      batches.value.unshift(created);
      return created;
    } finally {
      isSaving.value = false;
    }
  }

  async function updateBatch(batchId, payload) {
    isSaving.value = true;
    try {
      const updated = await api.updateTraceabilityBatch(batchId, payload);
      const index = batches.value.findIndex(b => b.id === updated.id);
      if (index !== -1) {
        batches.value[index] = updated;
      }
      selectedBatch.value = updated;
      return updated;
    } finally {
      isSaving.value = false;
    }
  }

  async function deleteBatch(batchId) {
    await api.deleteTraceabilityBatch(batchId);
    batches.value = batches.value.filter(b => b.id !== batchId);
    if (selectedBatch.value?.id === batchId) {
      selectedBatch.value = null;
    }
  }

  async function replaceSheepLinks(batchId, sheepLinks) {
    isSaving.value = true;
    try {
      const updated = await api.replaceBatchSheepLinks(batchId, sheepLinks);
      selectedBatch.value = updated;
      const index = batches.value.findIndex(b => b.id === updated.id);
      if (index !== -1) {
        batches.value[index] = updated;
      }
      return updated;
    } finally {
      isSaving.value = false;
    }
  }

  async function addProcessingStep(batchId, payload) {
    const step = await api.addProcessingStep(batchId, payload);
    if (selectedBatch.value && selectedBatch.value.id === batchId) {
      selectedBatch.value.steps = selectedBatch.value.steps || [];
      selectedBatch.value.steps.push(step);
    }
    return step;
  }

  async function updateProcessingStep(stepId, payload) {
    const step = await api.updateProcessingStep(stepId, payload);
    if (selectedBatch.value?.steps) {
      const index = selectedBatch.value.steps.findIndex(s => s.id === step.id);
      if (index !== -1) {
        selectedBatch.value.steps[index] = step;
      }
    }
    return step;
  }

  async function deleteProcessingStep(stepId) {
    await api.deleteProcessingStep(stepId);
    if (selectedBatch.value?.steps) {
      selectedBatch.value.steps = selectedBatch.value.steps.filter(s => s.id !== stepId);
    }
  }

  return {
    batches,
    sortedBatches,
    selectedBatch,
    isLoading,
    isSaving,
    fetchBatches,
    fetchBatch,
    createBatch,
    updateBatch,
    deleteBatch,
    replaceSheepLinks,
    addProcessingStep,
    updateProcessingStep,
    deleteProcessingStep,
  };
});
