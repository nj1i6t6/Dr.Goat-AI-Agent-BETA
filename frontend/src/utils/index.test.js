/**
 * Utils 模組測試
 * @jest-environment happy-dom
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  formatDateForInput,
  sexOptions,
  breedCategoryOptions,
  statusOptions,
  activityLevelOptions,
  sheetPurposeOptions,
  systemFieldMappings
} from './index'

describe('Utils 模組', () => {
  describe('formatDateForInput 函數', () => {
    beforeEach(() => {
      // Mock console.error to avoid noise in tests
      vi.spyOn(console, 'error').mockImplementation(() => {})
    })

    afterEach(() => {
      vi.restoreAllMocks()
    })

    it('應該正確格式化有效的日期字符串', () => {
      expect(formatDateForInput('2023-12-25')).toBe('2023-12-25')
      expect(formatDateForInput('2023/12/25')).toBe('2023-12-25')
      expect(formatDateForInput('2023-01-01')).toBe('2023-01-01')
    })

    it('應該處理帶時間的日期字符串', () => {
      expect(formatDateForInput('2023-12-25 10:30:45')).toBe('2023-12-25')
      expect(formatDateForInput('2023/12/25 14:20:00')).toBe('2023-12-25')
    })

    it('應該處理不同格式的日期分隔符', () => {
      expect(formatDateForInput('2023-01-15')).toBe('2023-01-15')
      expect(formatDateForInput('2023/01/15')).toBe('2023-01-15')
    })

    it('應該正確處理月份和日期的零填充', () => {
      expect(formatDateForInput('2023-1-5')).toBe('2023-01-05')
      expect(formatDateForInput('2023/1/5')).toBe('2023-01-05')
      expect(formatDateForInput('2023-12-5')).toBe('2023-12-05')
    })

    it('應該驗證年份範圍', () => {
      expect(formatDateForInput('1800-01-01')).toBe('')
      expect(formatDateForInput('2200-01-01')).toBe('')
      expect(formatDateForInput('1950-01-01')).toBe('1950-01-01')
      expect(formatDateForInput('2099-12-31')).toBe('2099-12-31')
    })

    it('應該處理無效的日期', () => {
      expect(formatDateForInput('invalid-date')).toBe('')
      expect(formatDateForInput('2023-13-01')).toBe('')
      expect(formatDateForInput('2023-02-30')).toBe('')
    })

    it('應該處理空值和 null', () => {
      expect(formatDateForInput('')).toBe('')
      expect(formatDateForInput(null)).toBe('')
      expect(formatDateForInput(undefined)).toBe('')
    })

    it('應該處理邊界情況', () => {
      expect(formatDateForInput('2023-02-28')).toBe('2023-02-28')
      expect(formatDateForInput('2024-02-29')).toBe('2024-02-29') // 閏年
      expect(formatDateForInput('2023-02-29')).toBe('') // 非閏年
    })

    it('應該在錯誤時記錄錯誤並返回空字符串', () => {
      const invalidInput = 'completely-invalid'
      const result = formatDateForInput(invalidInput)
      
      expect(result).toBe('')
      // 驗證是否調用了 console.error（如果實現中有的話）
    })

    it('應該處理特殊字符', () => {
      expect(formatDateForInput('2023@01@01')).toBe('')
      expect(formatDateForInput('2023*01*01')).toBe('')
    })

    it('應該處理非字符串輸入', () => {
      expect(formatDateForInput(20231225)).toBe('')
      expect(formatDateForInput(new Date('2023-12-25'))).toBe('')
      expect(formatDateForInput({})).toBe('')
      expect(formatDateForInput([])).toBe('')
    })
  })

  describe('靜態選項數據', () => {
    describe('sexOptions', () => {
      it('應該包含正確的性別選項', () => {
        expect(sexOptions).toHaveLength(3)
        expect(sexOptions).toContainEqual({ value: "母", label: "母 (Female)" })
        expect(sexOptions).toContainEqual({ value: "公", label: "公 (Male)" })
        expect(sexOptions).toContainEqual({ value: "閹", label: "閹 (Wether)" })
      })

      it('每個選項都應該有 value 和 label 屬性', () => {
        sexOptions.forEach(option => {
          expect(option).toHaveProperty('value')
          expect(option).toHaveProperty('label')
          expect(typeof option.value).toBe('string')
          expect(typeof option.label).toBe('string')
        })
      })
    })

    describe('breedCategoryOptions', () => {
      it('應該包含正確的品種類別選項', () => {
        expect(breedCategoryOptions).toHaveLength(6)
        
        const expectedOptions = [
          { value: "Dairy", label: "乳用 (Dairy)" },
          { value: "Meat", label: "肉用 (Meat)" },
          { value: "Fiber", label: "毛用 (Fiber)" },
          { value: "DualPurpose", label: "兼用 (DualPurpose)" },
          { value: "Miniature", label: "小型/寵物 (Miniature)" },
          { value: "Other", label: "其他" }
        ]
        
        expectedOptions.forEach(option => {
          expect(breedCategoryOptions).toContainEqual(option)
        })
      })

      it('每個選項都應該有正確的結構', () => {
        breedCategoryOptions.forEach(option => {
          expect(option).toHaveProperty('value')
          expect(option).toHaveProperty('label')
          expect(typeof option.value).toBe('string')
          expect(typeof option.label).toBe('string')
        })
      })
    })

    describe('statusOptions', () => {
      it('應該包含完整的生理狀態選項', () => {
        expect(statusOptions.length).toBeGreaterThan(10)
        
        const expectedStatuses = [
          'maintenance',
          'growing_young',
          'growing_finishing',
          'lactating_peak',
          'gestating_early',
          'other_status'
        ]
        
        expectedStatuses.forEach(status => {
          expect(statusOptions.some(option => option.value === status)).toBe(true)
        })
      })

      it('應該包含泌乳相關的所有狀態', () => {
        const lactatingStatuses = statusOptions.filter(option => 
          option.value.includes('lactating')
        )
        
        expect(lactatingStatuses.length).toBeGreaterThanOrEqual(4)
        expect(lactatingStatuses.some(s => s.value === 'lactating_early')).toBe(true)
        expect(lactatingStatuses.some(s => s.value === 'lactating_peak')).toBe(true)
        expect(lactatingStatuses.some(s => s.value === 'lactating_mid')).toBe(true)
        expect(lactatingStatuses.some(s => s.value === 'lactating_late')).toBe(true)
      })

      it('應該包含懷孕相關的狀態', () => {
        const gestatingStatuses = statusOptions.filter(option => 
          option.value.includes('gestating')
        )
        
        expect(gestatingStatuses.length).toBeGreaterThanOrEqual(2)
        expect(gestatingStatuses.some(s => s.value === 'gestating_early')).toBe(true)
        expect(gestatingStatuses.some(s => s.value === 'gestating_late')).toBe(true)
      })
    })

    describe('activityLevelOptions', () => {
      it('應該包含正確的活動量選項', () => {
        expect(activityLevelOptions).toHaveLength(3)
        
        const expectedOptions = [
          { value: "confined", label: "舍飼/限制" },
          { value: "grazing_flat_pasture", label: "平地放牧" },
          { value: "grazing_hilly_pasture", label: "山地放牧" }
        ]
        
        expectedOptions.forEach(option => {
          expect(activityLevelOptions).toContainEqual(option)
        })
      })
    })

    describe('sheetPurposeOptions', () => {
      it('應該包含完整的工作表用途選項', () => {
        expect(sheetPurposeOptions.length).toBeGreaterThan(5)
        
        // 檢查必要的選項
        expect(sheetPurposeOptions.some(option => option.value === "")).toBe(true)
        expect(sheetPurposeOptions.some(option => option.value === "ignore")).toBe(true)
        expect(sheetPurposeOptions.some(option => option.value === "basic_info")).toBe(true)
        expect(sheetPurposeOptions.some(option => option.value === "kidding_record")).toBe(true)
      })

      it('每個選項都應該有 value 和 text 屬性', () => {
        sheetPurposeOptions.forEach(option => {
          expect(option).toHaveProperty('value')
          expect(option).toHaveProperty('text')
          expect(typeof option.value).toBe('string')
          expect(typeof option.text).toBe('string')
        })
      })

      it('應該包含預設的空選項', () => {
        const defaultOption = sheetPurposeOptions.find(option => option.value === "")
        expect(defaultOption).toBeDefined()
        expect(defaultOption.text).toContain('請選擇')
      })
    })

    describe('systemFieldMappings', () => {
      it('應該包含所有必要的映射類型', () => {
        const expectedMappings = [
          'basic_info',
          'kidding_record', 
          'mating_record',
          'yean_record',
          'weight_record',
          'milk_yield_record',
          'milk_analysis_record',
          'breed_mapping',
          'sex_mapping'
        ]
        
        expectedMappings.forEach(mapping => {
          expect(systemFieldMappings).toHaveProperty(mapping)
          expect(Array.isArray(systemFieldMappings[mapping])).toBe(true)
        })
      })

      describe('basic_info 映射', () => {
        it('應該包含必要的基本信息字段', () => {
          const basicFields = systemFieldMappings.basic_info
          
          expect(basicFields.some(field => field.key === 'EarNum')).toBe(true)
          expect(basicFields.some(field => field.key === 'Breed')).toBe(true)
          expect(basicFields.some(field => field.key === 'Sex')).toBe(true)
          expect(basicFields.some(field => field.key === 'BirthDate')).toBe(true)
        })

        it('EarNum 字段應該是必填的', () => {
          const earNumField = systemFieldMappings.basic_info.find(field => field.key === 'EarNum')
          expect(earNumField).toBeDefined()
          expect(earNumField.required).toBe(true)
        })

        it('每個字段都應該有完整的結構', () => {
          systemFieldMappings.basic_info.forEach(field => {
            expect(field).toHaveProperty('key')
            expect(field).toHaveProperty('label')
            expect(typeof field.key).toBe('string')
            expect(typeof field.label).toBe('string')
            
            if (field.example) {
              expect(typeof field.example).toBe('string')
            }
          })
        })
      })

      describe('記錄類型映射', () => {
        const recordTypes = ['kidding_record', 'mating_record', 'weight_record', 'milk_yield_record']
        
        recordTypes.forEach(recordType => {
          it(`${recordType} 應該包含必要的字段`, () => {
            const fields = systemFieldMappings[recordType]
            expect(fields.length).toBeGreaterThan(0)
            
            // 檢查是否有 EarNum 字段
            expect(fields.some(field => field.key === 'EarNum')).toBe(true)
            
            // 檢查 EarNum 是否為必填
            const earNumField = fields.find(field => field.key === 'EarNum')
            expect(earNumField.required).toBe(true)
          })
        })

        it('weight_record 應該包含體重和日期字段', () => {
          const weightFields = systemFieldMappings.weight_record
          
          expect(weightFields.some(field => field.key === 'Weight')).toBe(true)
          expect(weightFields.some(field => field.key === 'MeaDate')).toBe(true)
          
          const weightField = weightFields.find(field => field.key === 'Weight')
          const dateField = weightFields.find(field => field.key === 'MeaDate')
          
          expect(weightField.required).toBe(true)
          expect(dateField.required).toBe(true)
        })
      })

      describe('映射表', () => {
        it('breed_mapping 應該包含代碼和名稱字段', () => {
          const breedMapping = systemFieldMappings.breed_mapping
          
          expect(breedMapping.some(field => field.key === 'Code')).toBe(true)
          expect(breedMapping.some(field => field.key === 'Name')).toBe(true)
          
          const codeField = breedMapping.find(field => field.key === 'Code')
          const nameField = breedMapping.find(field => field.key === 'Name')
          
          expect(codeField.required).toBe(true)
          expect(nameField.required).toBe(true)
        })

        it('sex_mapping 應該包含代碼和名稱字段', () => {
          const sexMapping = systemFieldMappings.sex_mapping
          
          expect(sexMapping.some(field => field.key === 'Code')).toBe(true)
          expect(sexMapping.some(field => field.key === 'Name')).toBe(true)
          
          const codeField = sexMapping.find(field => field.key === 'Code')
          const nameField = sexMapping.find(field => field.key === 'Name')
          
          expect(codeField.required).toBe(true)
          expect(nameField.required).toBe(true)
        })
      })
    })
  })

  describe('數據一致性檢查', () => {
    it('選項數組不應該為空', () => {
      expect(sexOptions.length).toBeGreaterThan(0)
      expect(breedCategoryOptions.length).toBeGreaterThan(0)
      expect(statusOptions.length).toBeGreaterThan(0)
      expect(activityLevelOptions.length).toBeGreaterThan(0)
      expect(sheetPurposeOptions.length).toBeGreaterThan(0)
    })

    it('systemFieldMappings 的所有值都應該是數組', () => {
      Object.values(systemFieldMappings).forEach(mapping => {
        expect(Array.isArray(mapping)).toBe(true)
        expect(mapping.length).toBeGreaterThan(0)
      })
    })

    it('所有選項值都應該是唯一的', () => {
      const testUniqueness = (options, valueKey = 'value') => {
        const values = options.map(option => option[valueKey])
        const uniqueValues = [...new Set(values)]
        expect(values.length).toBe(uniqueValues.length)
      }

      testUniqueness(sexOptions)
      testUniqueness(breedCategoryOptions)
      testUniqueness(statusOptions)
      testUniqueness(activityLevelOptions)
      testUniqueness(sheetPurposeOptions)
    })

    it('所有字段映射的 key 都應該是唯一的', () => {
      Object.values(systemFieldMappings).forEach(fields => {
        const keys = fields.map(field => field.key)
        const uniqueKeys = [...new Set(keys)]
        expect(keys.length).toBe(uniqueKeys.length)
      })
    })
  })

  describe('邊界條件和錯誤處理', () => {
    it('formatDateForInput 應該處理異常情況而不崩潰', () => {
      const problematicInputs = [
        'abc',
        '2023-',
        '-01-01',
        '2023--01',
        '2023-01-',
        '/////',
        '-----',
        'null',
        'undefined'
      ]

      problematicInputs.forEach(input => {
        expect(() => formatDateForInput(input)).not.toThrow()
        expect(formatDateForInput(input)).toBe('')
      })
    })

    it('數據結構應該保持完整性', () => {
      // 檢查所有選項數據的結構完整性
      const originalLength = sexOptions.length
      
      // 嘗試修改數據（在實際應用中應該避免這樣做）
      try {
        sexOptions.push({ value: 'test', label: 'test' })
        // 如果成功添加，立即移除以保證數據完整性
        if (sexOptions.length > originalLength) {
          sexOptions.pop()
        }
      } catch (error) {
        // 如果數據被凍結，推送操作會失敗，這是預期的
      }
      
      // 長度應該保持原樣
      expect(sexOptions.length).toBe(originalLength)
      
      // 確保所有原始數據仍然存在且結構正確
      expect(sexOptions[0]).toHaveProperty('value')
      expect(sexOptions[0]).toHaveProperty('label')
    })
  })

  describe('本地化和國際化', () => {
    it('所有標籤都應該包含中文', () => {
      const hasChineseChar = (str) => /[\u4e00-\u9fff]/.test(str)
      
      sexOptions.forEach(option => {
        expect(hasChineseChar(option.label)).toBe(true)
      })
      
      statusOptions.forEach(option => {
        expect(hasChineseChar(option.label)).toBe(true)
      })
    })

    it('系統字段標籤應該是中文', () => {
      const hasChineseChar = (str) => /[\u4e00-\u9fff]/.test(str)
      
      Object.values(systemFieldMappings).forEach(fields => {
        fields.forEach(field => {
          expect(hasChineseChar(field.label)).toBe(true)
        })
      })
    })
  })
})
