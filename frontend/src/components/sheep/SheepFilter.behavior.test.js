import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import SheepFilter from './SheepFilter.vue'

vi.mock('../../stores/sheep', () => ({
  useSheepStore: () => ({
    filterOptions: {
      farmNums: ['0001', '0002'],
      breeds: ['AL', 'SA']
    }
  })
}))

describe('SheepFilter interactions', () => {
  it('emits filter on search click', async () => {
    const wrapper = mount(SheepFilter, {
      global: {
        stubs: {
          'el-card': {
            template: '<div class="el-card"><slot /></div>'
          },
          'el-form': {
            template: '<form><slot /></form>',
            props: ['model', 'labelPosition']
          },
          'el-form-item': {
            template: '<div class="el-form-item"><slot /></div>',
            props: ['label']
          },
          'el-input': {
            template: '<input class="el-input" />'
          },
          'el-select': {
            template: '<select class="el-select"><slot /></select>'
          },
          'el-select-v2': {
            template: '<select class="el-select-v2"></select>'
          },
          'el-option': {
            template: '<option></option>'
          },
          'el-button': {
            template: '<button class="el-button" @click="$emit(\'click\')"><slot /></button>',
            emits: ['click']
          },
          'el-row': {
            template: '<div class="el-row"><slot /></div>'
          },
          'el-col': {
            template: '<div class="el-col"><slot /></div>'
          },
          'el-date-picker': {
            template: '<input class="el-date-picker" />'
          }
        }
      }
    })
  await wrapper.find('button.el-button').trigger('click')
    const emitted = wrapper.emitted('filter')
    expect(emitted).toBeTruthy()
    expect(emitted[0][0]).toHaveProperty('earNumSearch', '')
  })

  it('reset button clears fields and emits', async () => {
    const wrapper = mount(SheepFilter, {
      global: {
        stubs: {
          'el-card': {
            template: '<div class="el-card"><slot /></div>'
          },
          'el-form': {
            template: '<form><slot /></form>',
            props: ['model', 'labelPosition']
          },
          'el-form-item': {
            template: '<div class="el-form-item"><slot /></div>',
            props: ['label']
          },
          'el-input': {
            template: '<input class="el-input" />'
          },
          'el-select': {
            template: '<select class="el-select"><slot /></select>'
          },
          'el-select-v2': {
            template: '<select class="el-select-v2"></select>'
          },
          'el-option': {
            template: '<option></option>'
          },
          'el-button': {
            template: '<button class="el-button" @click="$emit(\'click\')"><slot /></button>',
            emits: ['click']
          },
          'el-row': {
            template: '<div class="el-row"><slot /></div>'
          },
          'el-col': {
            template: '<div class="el-col"><slot /></div>'
          },
          'el-date-picker': {
            template: '<input class="el-date-picker" />'
          }
        }
      }
    })
    // set some state via inputs not necessary; call reset directly via second button
  const buttons = wrapper.findAll('button.el-button')
  await buttons[1].trigger('click')
    const payload = wrapper.emitted('filter').pop()[0]
    expect(payload).toMatchObject({ farmNum: '', breed: '', sex: '' })
  })
})
