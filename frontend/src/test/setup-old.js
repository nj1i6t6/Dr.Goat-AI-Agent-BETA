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

// Element Plus 組件 stub - 修復後的版本
config.global.stubs = {
  'el-alert': {
    name: 'ElAlert',
    template: '<div v-if="modelValue !== false" class="el-alert"><slot /></div>',
    props: ['modelValue', 'type', 'title', 'description', 'closable', 'showIcon'],
    emits: ['close'],
  },
  'el-button': {
    name: 'ElButton',
    template: '<button class="el-button" :disabled="disabled || loading" @click="$emit(\'click\', $event)"><slot /></button>',
    props: ['type', 'size', 'disabled', 'loading', 'icon', 'plain', 'round', 'circle'],
    emits: ['click'],
  },
  'el-card': {
    name: 'ElCard',
    template: '<div class="el-card"><slot /></div>',
    props: ['header', 'bodyStyle', 'shadow'],
  },
  'el-form': {
    name: 'ElForm',
    template: '<form class="el-form" @submit.prevent="$emit(\'submit\', $event)"><slot /></form>',
    props: ['model', 'rules', 'labelPosition', 'labelWidth', 'inline', 'disabled'],
    emits: ['submit'],
    methods: {
      validate: vi.fn(() => Promise.resolve(true)),
      validateField: vi.fn(() => Promise.resolve(true)),
      resetFields: vi.fn(),
      clearValidation: vi.fn(),
    },
  },
  'el-form-item': {
    name: 'ElFormItem',
    template: '<div class="el-form-item"><label v-if="label" class="el-form-item__label">{{ label }}</label><div class="el-form-item__content"><slot /></div></div>',
    props: ['label', 'prop', 'required', 'rules', 'error'],
  },
  'el-input': {
    name: 'ElInput',
    template: '<div class="el-input"><input class="el-input__inner" :value="modelValue" :placeholder="placeholder" @input="$emit(\'update:modelValue\', $event.target.value)" @keyup.enter="$emit(\'keyup\', $event)" /><div v-if="$slots.append" class="el-input-group__append"><slot name="append" /></div></div>',
    props: ['modelValue', 'placeholder', 'clearable', 'type', 'disabled'],
    emits: ['update:modelValue', 'keyup', 'blur', 'focus'],
  },
  'el-input-number': {
    name: 'ElInputNumber',
    template: '<div class="el-input-number"><input type="number" :value="modelValue" :min="min" :max="max" :step="step" @input="$emit(\'update:modelValue\', parseFloat($event.target.value) || 0)" /></div>',
    props: ['modelValue', 'min', 'max', 'step', 'precision'],
    emits: ['update:modelValue', 'change'],
  },
  'el-select': {
    name: 'ElSelect',
    template: '<div class="el-select"><select :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><option value="" v-if="placeholder">{{ placeholder }}</option><slot /></select></div>',
    props: ['modelValue', 'placeholder', 'clearable', 'multiple'],
    emits: ['update:modelValue', 'change'],
  },
  'el-option': {
    name: 'ElOption',
    template: '<option :value="value">{{ label }}</option>',
    props: ['label', 'value', 'disabled'],
  },
  'el-date-picker': {
    name: 'ElDatePicker',
    template: '<div class="el-date-picker"><input type="date" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" /></div>',
    props: ['modelValue', 'type', 'placeholder', 'format', 'valueFormat'],
    emits: ['update:modelValue', 'change'],
  },
  'el-checkbox': {
    name: 'ElCheckbox',
    template: '<label class="el-checkbox"><input type="checkbox" :checked="modelValue" @change="$emit(\'update:modelValue\', $event.target.checked)" /> <span>{{ label }}<slot /></span></label>',
    props: ['modelValue', 'label', 'disabled'],
    emits: ['update:modelValue', 'change'],
  },
  'el-radio': {
    name: 'ElRadio',
    template: '<label class="el-radio"><input type="radio" :value="value" :checked="modelValue === value" @change="$emit(\'update:modelValue\', value)" /> <span>{{ label }}<slot /></span></label>',
    props: ['modelValue', 'label', 'value', 'disabled'],
    emits: ['update:modelValue', 'change'],
  },
  'el-radio-group': {
    name: 'ElRadioGroup',
    template: '<div class="el-radio-group"><slot /></div>',
    props: ['modelValue', 'disabled'],
    emits: ['update:modelValue', 'change'],
  },
  'el-switch': {
    name: 'ElSwitch',
    template: '<div class="el-switch"><input type="checkbox" :checked="modelValue" @change="$emit(\'update:modelValue\', $event.target.checked)" /></div>',
    props: ['modelValue', 'disabled'],
    emits: ['update:modelValue', 'change'],
  },
  'el-table': {
    name: 'ElTable',
    template: '<div class="el-table"><table><thead><slot name="header" /></thead><tbody><slot /></tbody></table></div>',
    props: ['data', 'height', 'maxHeight', 'stripe', 'border', 'size'],
    emits: ['select', 'select-all', 'selection-change'],
  },
  'el-table-column': {
    name: 'ElTableColumn',
    template: '<td class="el-table-column">{{ prop ? row[prop] : "" }}<slot /></td>',
    props: ['prop', 'label', 'width', 'minWidth', 'fixed', 'sortable', 'type'],
  },
  'el-pagination': {
    name: 'ElPagination',
    template: '<div class="el-pagination"><button @click="$emit(\'current-change\', currentPage - 1)">Previous</button><span>{{ currentPage }}</span><button @click="$emit(\'current-change\', currentPage + 1)">Next</button></div>',
    props: ['currentPage', 'pageSize', 'total', 'layout'],
    emits: ['current-change', 'size-change'],
  },
  'el-dialog': {
    name: 'ElDialog',
    template: '<div v-if="modelValue" class="el-dialog"><div class="el-dialog__header"><slot name="header" /></div><div class="el-dialog__body"><slot /></div><div class="el-dialog__footer"><slot name="footer" /></div></div>',
    props: ['modelValue', 'title', 'width', 'fullscreen', 'modal', 'closeOnClickModal'],
    emits: ['update:modelValue', 'close'],
  },
  'el-drawer': {
    name: 'ElDrawer',
    template: '<div v-if="modelValue" class="el-drawer"><slot /></div>',
    props: ['modelValue', 'title', 'size', 'direction'],
    emits: ['update:modelValue', 'close'],
  },
  'el-tabs': {
    name: 'ElTabs',
    template: '<div class="el-tabs"><div class="el-tabs__nav"><slot name="nav" /></div><div class="el-tabs__content"><slot /></div></div>',
    props: ['modelValue', 'type', 'position'],
    emits: ['update:modelValue', 'tab-click'],
  },
  'el-tab-pane': {
    name: 'ElTabPane',
    template: '<div class="el-tab-pane" v-if="name === $parent.modelValue || !$parent.modelValue"><slot /></div>',
    props: ['label', 'name', 'disabled'],
  },
  'el-collapse': {
    name: 'ElCollapse',
    template: '<div class="el-collapse"><slot /></div>',
    props: ['modelValue', 'accordion'],
    emits: ['update:modelValue', 'change'],
  },
  'el-collapse-item': {
    name: 'ElCollapseItem',
    template: '<div class="el-collapse-item"><div class="el-collapse-item__header" @click="toggle">{{ title }}</div><div v-if="isOpen" class="el-collapse-item__content"><slot /></div></div>',
    props: ['name', 'title', 'disabled'],
    data() {
      return { isOpen: false }
    },
    methods: {
      toggle() { this.isOpen = !this.isOpen }
    }
  },
  'el-tooltip': {
    name: 'ElTooltip',
    template: '<div class="el-tooltip"><slot /></div>',
    props: ['content', 'placement', 'disabled'],
  },
  'el-popover': {
    name: 'ElPopover',
    template: '<div class="el-popover"><slot name="reference" /><div class="el-popover__content"><slot /></div></div>',
    props: ['content', 'title', 'trigger', 'placement'],
  },
  'el-divider': {
    name: 'ElDivider',
    template: '<div class="el-divider"><span v-if="$slots.default" class="el-divider__text"><slot /></span></div>',
    props: ['direction', 'contentPosition'],
  },
  'el-row': {
    name: 'ElRow',
    template: '<div class="el-row"><slot /></div>',
    props: ['gutter', 'type', 'justify', 'align'],
  },
  'el-col': {
    name: 'ElCol',
    template: '<div class="el-col"><slot /></div>',
    props: ['span', 'offset', 'push', 'pull', 'xs', 'sm', 'md', 'lg', 'xl'],
  },
  'el-icon': {
    name: 'ElIcon',
    template: '<i class="el-icon"><slot /></i>',
    props: ['size', 'color'],
  },
  'el-loading': {
    name: 'ElLoading',
    template: '<div class="el-loading"><slot /></div>',
    directives: {
      loading: {
        mounted() {},
        updated() {},
        unmounted() {}
      }
    }
  },
  'el-upload': {
    name: 'ElUpload',
    template: '<div class="el-upload"><slot /></div>',
    props: ['action', 'method', 'data', 'name', 'withCredentials', 'headers', 'multiple', 'accept', 'autoUpload'],
    emits: ['change', 'success', 'error'],
  },
  'el-progress': {
    name: 'ElProgress',
    template: '<div class="el-progress"><div class="el-progress__text">{{ percentage }}%</div></div>',
    props: ['percentage', 'type', 'strokeWidth', 'textInside', 'status'],
  },
  'el-result': {
    name: 'ElResult',
    template: '<div class="el-result"><div class="el-result__title">{{ title }}</div><div class="el-result__subtitle">{{ subTitle }}</div><slot /></div>',
    props: ['icon', 'title', 'subTitle'],
  },
  'el-empty': {
    name: 'ElEmpty',
    template: '<div class="el-empty"><div class="el-empty__description">{{ description || "暫無數據" }}</div><slot /></div>',
    props: ['description'],
  },
  // 指令支持  
  'v-loading': true,
  'el-select-v2': {
    name: 'ElSelectV2', 
    template: '<div class="el-select-v2"><select :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><option v-for="item in options" :key="item.value" :value="item.value">{{ item.label }}</option></select></div>',
    props: ['modelValue', 'options', 'placeholder', 'clearable', 'multiple'],
    emits: ['update:modelValue', 'change'],
  },
}

// 全域屬性
config.global.mocks = {
  $t: (key) => key, // i18n mock
  $route: {
    path: '/',
    name: 'Dashboard',
    params: {},
    query: {},
    meta: {}
  },
  $router: {
    push: vi.fn(),
    replace: vi.fn(),
    go: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    currentRoute: {
      value: {
        path: '/',
        name: 'Dashboard', 
        params: {},
        query: {},
        meta: {}
      }
    }
  }
}

// 全域指令 mock
config.global.directives = {
  loading: {
    mounted() {},
    updated() {},
    unmounted() {}
  }
}

// Element Plus Message mock
global.ElMessage = {
  error: vi.fn(),
  success: vi.fn(),
  warning: vi.fn(),
  info: vi.fn()
}

// Element Plus MessageBox mock  
global.ElMessageBox = {
  alert: vi.fn().mockResolvedValue('confirm'),
  confirm: vi.fn().mockResolvedValue('confirm'),
  prompt: vi.fn().mockResolvedValue({ value: 'test' })
}

// Element Plus Notification mock
global.ElNotification = {
  error: vi.fn(),
  success: vi.fn(),
  warning: vi.fn(),
  info: vi.fn()
}

// Mock window.location
Object.defineProperty(window, 'location', {
  value: {
    href: 'http://localhost:3000',
    origin: 'http://localhost:3000',
    protocol: 'http:',
    host: 'localhost:3000',
    hostname: 'localhost',
    port: '3000',
    pathname: '/',
    search: '',
    hash: '',
    assign: vi.fn(),
    reload: vi.fn(),
    replace: vi.fn()
  },
  writable: true
})

// Mock localStorage and sessionStorage
const createStorageMock = () => ({
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn()
})

Object.defineProperty(window, 'localStorage', {
  value: createStorageMock(),
  writable: true
})

Object.defineProperty(window, 'sessionStorage', {
  value: createStorageMock(),
  writable: true
})

// Console 警告過濾
const originalWarn = console.warn
console.warn = (...args) => {
  const msg = args[0]
  if (typeof msg === 'string') {
    // 過濾 Element Plus 相關警告
    if (
      msg.includes('Failed to resolve component') ||
      msg.includes('Invalid prop') ||
      msg.includes('Vue warn')
    ) {
      return
    }
  }
  originalWarn.apply(console, args)
}

// 設置測試超時
vi.setConfig({
  testTimeout: 10000,
  hookTimeout: 10000
})
      </div>
    `,
    props: ['type', 'title', 'description', 'closable', 'showIcon', 'modelValue'],
    emits: ['close', 'update:modelValue'],
  },
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
  'el-radio': {
    name: 'ElRadio',
    template: `
      <label class="el-radio">
        <input 
          type="radio" 
          :value="label" 
          :checked="modelValue === label"
          @change="$emit('update:modelValue', label)"
        />
        <span class="el-radio__label">{{ label || $slots.default?.[0]?.children }}</span>
      </label>
    `,
    props: ['modelValue', 'label'],
    emits: ['update:modelValue'],
  },
  'el-radio-group': {
    name: 'ElRadioGroup',
    template: `
      <div class="el-radio-group">
        <slot />
      </div>
    `,
    props: ['modelValue'],
    emits: ['update:modelValue'],
  },
  'el-radio-button': {
    name: 'ElRadioButton',
    template: `
      <label class="el-radio-button">
        <input 
          type="radio" 
          :value="label" 
          :checked="modelValue === label"
          @change="$emit('update:modelValue', label)"
        />
        <span class="el-radio-button__inner">{{ label || $slots.default?.[0]?.children }}</span>
      </label>
    `,
    props: ['modelValue', 'label'],
    emits: ['update:modelValue'],
  },
  'el-steps': {
    name: 'ElSteps',
    template: '<div class="el-steps"><slot /></div>',
    props: ['active', 'align-center', 'direction', 'space', 'finish-status', 'process-status']
  },
  'el-step': {
    name: 'ElStep',
    template: '<div class="el-step"><div class="el-step__title"><slot /></div></div>',
    props: ['title', 'description', 'icon', 'status']
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
}

// 註冊全域指令模擬
config.global.directives = {
  loading: {
    mounted(el, binding) {
      if (binding.value) {
        el.classList.add('el-loading-mask')
      }
    },
    updated(el, binding) {
      if (binding.value) {
        el.classList.add('el-loading-mask')
      } else {
        el.classList.remove('el-loading-mask')
      }
    }
  }
}

// 額外的 Element Plus 組件
Object.assign(config.global.components, {
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
})

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
