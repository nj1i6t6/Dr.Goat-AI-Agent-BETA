<template>
  <el-card class="form-card" shadow="never">
    <template #header>
      <span>{{ title }}</span>
    </template>
    <el-form ref="formRef" :model="form" :rules="rules" label-width="90px" class="finance-form">
      <el-form-item label="日期" prop="recorded_at">
        <el-date-picker v-model="form.recorded_at" type="date" value-format="YYYY-MM-DD" placeholder="選擇日期" />
      </el-form-item>
      <el-form-item label="分類" prop="category">
        <el-input v-model="form.category" :placeholder="categoryPlaceholder" />
      </el-form-item>
      <el-form-item label="金額" prop="amount">
        <el-input-number v-model="form.amount" :min="0" :precision="2" />
      </el-form-item>
      <el-form-item label="備註">
        <el-input v-model="form.notes" type="textarea" :rows="2" />
      </el-form-item>
      <el-button :type="buttonType" :loading="loading" @click="handleSubmit">{{ submitLabel }}</el-button>
    </el-form>
  </el-card>
</template>

<script setup>
import { ref } from 'vue'

const form = defineModel('form', { type: Object, required: true })

defineProps({
  title: {
    type: String,
    required: true,
  },
  submitLabel: {
    type: String,
    required: true,
  },
  buttonType: {
    type: String,
    default: 'primary',
  },
  loading: {
    type: Boolean,
    default: false,
  },
  rules: {
    type: Object,
    required: true,
  },
  categoryPlaceholder: {
    type: String,
    default: '例如：feed',
  },
})

const emit = defineEmits(['submit'])

const formRef = ref()

const handleSubmit = () => {
  formRef.value?.validate((valid) => {
    if (valid) {
      emit('submit')
    }
  })
}

const clearValidation = () => {
  formRef.value?.clearValidate()
}

const focusFirstField = () => {
  const input = formRef.value?.$el?.querySelector('input')
  input?.focus()
}

defineExpose({ clearValidation, focusFirstField })
</script>
