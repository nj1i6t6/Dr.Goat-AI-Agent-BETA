<template>
  <div class="sheet-mapping-wrapper">
    <div
      v-for="(sheet, name) in sheets"
      :key="name"
      class="sheet-mapping-item"
    >
      <div class="sheet-header">
        <div class="sheet-title">
          <p><strong>工作表: {{ name }}</strong> (共 {{ sheet.rows || 0 }} 筆資料)</p>
          <p v-if="sheet.columns && sheet.columns.length" class="sheet-columns">
            欄位：{{ sheet.columns.join(', ') }}
          </p>
        </div>
        <div v-if="sheetInsights[name] && (sheetInsights[name].confidence !== undefined || sheetInsights[name].notes)" class="sheet-insight">
          <el-tag v-if="formatConfidence(sheetInsights[name].confidence)" size="small" type="info">
            AI 信心 {{ formatConfidence(sheetInsights[name].confidence) }}
          </el-tag>
          <el-tooltip
            v-if="sheetInsights[name].notes"
            effect="light"
            placement="top"
          >
            <template #content>
              <span>{{ sheetInsights[name].notes }}</span>
            </template>
            <el-icon class="sheet-insight-icon"><InfoFilled /></el-icon>
          </el-tooltip>
        </div>
      </div>

      <el-select
        class="sheet-purpose-select"
        :model-value="mappingState[name]?.purpose || ''"
        placeholder="請選擇此工作表的用途"
        @change="value => emitUpdate({ sheetName: name, purpose: value || '' })"
      >
        <el-option
          v-for="opt in sheetPurposeOptions"
          :key="opt.value"
          :label="opt.text"
          :value="opt.value"
        />
      </el-select>

      <div v-if="systemFieldMappings[mappingState[name]?.purpose]" class="fields-container">
        <div
          v-for="field in systemFieldMappings[mappingState[name]?.purpose]"
          :key="field.key"
          class="field-mapping-row"
        >
          <span class="system-field-label">
            {{ field.label }}
            <el-tag v-if="field.required" type="danger" size="small">必填</el-tag>
          </span>
          <el-select
            :model-value="mappingState[name]?.columns?.[field.key] || ''"
            placeholder="對應您的欄位"
            clearable
            filterable
            @change="value => emitUpdate({ sheetName: name, fieldKey: field.key, column: value || '' })"
          >
            <el-option
              v-for="col in (sheet.columns || [])"
              :key="col"
              :label="col"
              :value="col"
            />
          </el-select>
        </div>
      </div>

      <div v-if="sheet.preview && sheet.preview.length" class="sheet-preview">
        <p class="sheet-preview-title">資料範例 (前 {{ sheet.preview.length }} 筆)</p>
        <el-table
          :data="sheet.preview"
          size="small"
          border
          style="width: 100%"
          :header-row-class-name="() => 'sheet-preview-header'"
          :row-class-name="() => 'sheet-preview-row'"
          max-height="220"
        >
          <el-table-column
            v-for="col in (sheet.columns || [])"
            :key="col"
            :prop="col"
            :label="col"
            show-overflow-tooltip
          />
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { InfoFilled } from '@element-plus/icons-vue';

const props = defineProps({
  sheets: {
    type: Object,
    required: true
  },
  mappingState: {
    type: Object,
    required: true
  },
  sheetPurposeOptions: {
    type: Array,
    required: true
  },
  systemFieldMappings: {
    type: Object,
    required: true
  },
  sheetInsights: {
    type: Object,
    default: () => ({})
  }
});

const emit = defineEmits(['update-mapping']);

const emitUpdate = (payload) => {
  emit('update-mapping', payload);
};

const formatConfidence = (value) => {
  if (value === undefined || value === null || value === '') return '';
  const numeric = Number(value);
  if (Number.isNaN(numeric)) return '';
  return `${Math.round(numeric * 100)}%`;
};

</script>

<style scoped>
.sheet-mapping-wrapper {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.sheet-mapping-item {
  border: 1px solid #dcdfe6;
  padding: 16px;
  border-radius: 6px;
  background-color: #fff;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sheet-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
}

.sheet-title {
  max-width: 75%;
}

.sheet-columns {
  margin: 4px 0 0;
  color: #606266;
  font-size: 0.85rem;
  word-break: break-all;
}

.sheet-insight {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sheet-insight-icon {
  cursor: pointer;
  color: #409eff;
}

.sheet-purpose-select {
  width: 100%;
}

.fields-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field-mapping-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 10px;
  background-color: #fafafa;
  border-radius: 4px;
}

.system-field-label {
  flex-basis: 38%;
  flex-shrink: 0;
  font-weight: 500;
  font-size: 0.95rem;
  display: flex;
  align-items: center;
  gap: 6px;
}

.sheet-preview {
  margin-top: 4px;
  border-top: 1px dashed #ebeef5;
  padding-top: 12px;
}

.sheet-preview-title {
  font-size: 0.9rem;
  color: #606266;
  margin-bottom: 8px;
}

.sheet-preview-header {
  background-color: #f5f7fa !important;
}

.sheet-preview-row:nth-child(odd) {
  background-color: #fcfcfc;
}

.sheet-preview-row:nth-child(even) {
  background-color: #f8f9fb;
}
</style>
