/**
 * 測試環境設置檔案 - 針對 Vitest 3.x 優化
 * 提供所有測試共用的設定和模擬
 */

import { config } from '@vue/test-utils'
import { vi } from 'vitest'

// 設置全域測試環境
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// 模擬 ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// 模擬 IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Element Plus 組件 stub - 簡化但功能完整
config.global.stubs = {
  'el-divider': {
    name: 'ElDivider',
    template: '<hr class="el-divider" />',
    props: ['direction', 'content-position']
  },
  'el-card': {
    name: 'ElCard',
    template: '<div class="el-card"><slot /></div>',
    props: ['shadow']
  },
  'el-form': {
    name: 'ElForm',
    template: '<form class="el-form" @submit.prevent><slot /></form>',
    props: ['model', 'labelPosition', 'rules'],
    methods: {
      validate: () => Promise.resolve(true),
      resetFields: () => {},
      clearValidate: () => {}
    }
  },
  'el-form-item': {
    name: 'ElFormItem',
    template: '<div class="el-form-item"><label v-if="label">{{ label }}</label><slot /></div>',
    props: ['label', 'prop', 'required']
  },
  'el-row': {
    name: 'ElRow',
    template: '<div class="el-row" :style="{ gap: gutter + \'px\' }"><slot /></div>',
    props: ['gutter']
  },
  'el-col': {
    name: 'ElCol',  
    template: '<div class="el-col"><slot /></div>',
    props: ['xs', 'sm', 'md', 'lg', 'xl', 'span', 'offset']
  },
  'el-input': {
    name: 'ElInput',
    template: `
      <div class="el-input">
        <input 
          :value="modelValue" 
          :placeholder="placeholder"
          :type="type || 'text'"
          @input="$emit('update:modelValue', $event.target.value)" 
          @keyup.enter="$emit('keyup', $event)"
          @blur="$emit('blur', $event)"
          @focus="$emit('focus', $event)"
        />
        <span v-if="clearable && modelValue" @click="$emit('update:modelValue', '')">✕</span>
      </div>
    `,
    props: ['modelValue', 'placeholder', 'clearable', 'type', 'disabled'],
    emits: ['update:modelValue', 'keyup', 'blur', 'focus'],
  },
  'el-input-number': {
    name: 'ElInputNumber',
    template: `
      <div class="el-input-number">
        <input 
          type="number"
          :value="modelValue" 
          :min="min"
          :max="max"
          :step="step"
          @input="$emit('update:modelValue', parseFloat($event.target.value) || 0)"
          @change="$emit('change', parseFloat($event.target.value) || 0)"
        />
      </div>
    `,
    props: ['modelValue', 'min', 'max', 'step', 'precision'],
    emits: ['update:modelValue', 'change'],
  },
  'el-select': {
    name: 'ElSelect',
    template: `
      <div class="el-select">
        <select 
          :value="modelValue" 
          @change="$emit('update:modelValue', $event.target.value)"
        >
          <option value="" v-if="placeholder">{{ placeholder }}</option>
          <slot />
        </select>
      </div>
    `,
    props: ['modelValue', 'placeholder', 'clearable', 'multiple'],
    emits: ['update:modelValue', 'change'],
  },
  'el-select-v2': {
    name: 'ElSelectV2',
    template: `
      <div class="el-select-v2">
        <select 
          :value="modelValue" 
          @change="$emit('update:modelValue', $event.target.value)"
        >
          <option value="" v-if="placeholder">{{ placeholder }}</option>
          <option v-for="option in options" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </div>
    `,
    props: ['modelValue', 'options', 'placeholder', 'clearable', 'filterable'],
    emits: ['update:modelValue', 'change'],
  },
  'el-option': {
    name: 'ElOption',
    template: '<option class="el-option" :value="value">{{ label || $slots.default?.()[0]?.children }}</option>',
    props: ['value', 'label', 'disabled'],
  },
  'el-date-picker': {
    name: 'ElDatePicker',
    template: `
      <div class="el-date-picker">
        <input 
          type="date"
          :value="modelValue" 
          @input="$emit('update:modelValue', $event.target.value)" 
          @change="$emit('change', $event.target.value)"
          :placeholder="placeholder"
        />
      </div>
    `,
    props: ['modelValue', 'type', 'placeholder', 'format', 'valueFormat'],
    emits: ['update:modelValue', 'change'],
  },
  'el-button': {
    name: 'ElButton',
    template: `
      <button 
        class="el-button" 
        :type="nativeType || 'button'"
        :disabled="disabled || loading"
        @click="$emit('click', $event)"
      >
        <span v-if="loading">Loading...</span>
        <slot v-else />
      </button>
    `,
    props: ['type', 'nativeType', 'disabled', 'loading', 'size'],
    emits: ['click'],
  },
  'el-table': {
    name: 'ElTable',
    template: `
      <div class="el-table">
        <table>
          <slot />
        </table>
      </div>
    `,
    props: ['data', 'height', 'maxHeight', 'stripe', 'border'],
    methods: {
      clearSelection: () => {},
      toggleRowSelection: () => {},
      setCurrentRow: () => {},
    }
  },
  'el-table-column': {
    name: 'ElTableColumn',
    template: '<td class="el-table-column"><slot /></td>',
    props: ['prop', 'label', 'width', 'minWidth', 'fixed', 'sortable', 'type'],
  },
  'el-dialog': {
    name: 'ElDialog',
    template: `
      <div v-if="modelValue" class="el-dialog" @click.self="$emit('update:modelValue', false)">
        <div class="el-dialog__wrapper">
          <header class="el-dialog__header">
            <span class="el-dialog__title">{{ title }}</span>
            <button @click="$emit('update:modelValue', false)">✕</button>
          </header>
          <main class="el-dialog__body">
            <slot />
          </main>
          <footer class="el-dialog__footer">
            <slot name="footer" />
          </footer>
        </div>
      </div>
    `,
    props: ['modelValue', 'title', 'width', 'top', 'modal', 'closeOnClickModal'],
    emits: ['update:modelValue', 'close', 'open'],
  },
  'el-tabs': {
    name: 'ElTabs',
    template: `
      <div class="el-tabs">
        <div class="el-tabs__header">
          <div class="el-tabs__nav">
            <slot name="header" />
          </div>
        </div>
        <div class="el-tabs__content">
          <slot />
        </div>
      </div>
    `,
    props: ['modelValue', 'type', 'closable', 'addable'],
    emits: ['update:modelValue', 'tab-click', 'tab-remove', 'tab-add'],
  },
  'el-tab-pane': {
    name: 'ElTabPane',
    template: '<div class="el-tab-pane" v-if="name === $parent.modelValue"><slot /></div>',
    props: ['label', 'name', 'disabled', 'closable'],
  },
  'el-message': {
    name: 'ElMessage',
    template: '<div class="el-message"><slot /></div>',
  },
  'el-loading': {
    name: 'ElLoading',
    template: '<div class="el-loading"><slot /></div>',
  },
  'el-icon': {
    name: 'ElIcon',
    template: '<i class="el-icon"><slot /></i>',
    props: ['size', 'color'],
  },
  // 路由相關組件
  'router-link': {
    name: 'RouterLink',
    template: '<a class="router-link" :href="to"><slot /></a>',
    props: ['to', 'replace', 'append'],
  },
  'router-view': {
    name: 'RouterView',
    template: '<div class="router-view"><slot /></div>',
  },
}

// 全域模擬
config.global.mocks = {
  $t: (key) => key, // 模擬 i18n
  $route: {
    path: '/',
    params: {},
    query: {},
  },
  $router: {
    push: vi.fn(),
    replace: vi.fn(),
    go: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
  },
}

// 全域提供者
config.global.provide = {
  // 可以在這裡添加全域提供的依賴
}

// 設置預設的掛載選項
config.global.renderStubDefaultSlot = true
