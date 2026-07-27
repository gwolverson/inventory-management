import { ref, computed } from 'vue'
import en from '../locales/en'
import ja from '../locales/ja'

const translations = {
  en,
  ja
}

// Load saved locale from localStorage, default to 'en'
const savedLocale = localStorage.getItem('app-locale') || 'en'
const currentLocale = ref(savedLocale)

// Currency is automatically set based on locale (en -> USD, ja -> JPY)
const currentCurrency = computed(() => {
  return currentLocale.value === 'ja' ? 'JPY' : 'USD'
})

export function useI18n() {
  const t = (key, params = {}) => {
    const keys = key.split('.')
    let value = translations[currentLocale.value]

    for (const k of keys) {
      if (value && typeof value === 'object') {
        value = value[k]
      } else {
        // If translation not found, try English as fallback
        if (currentLocale.value !== 'en') {
          let fallback = translations.en
          for (const fk of keys) {
            if (fallback && typeof fallback === 'object') {
              fallback = fallback[fk]
            } else {
              break
            }
          }
          if (fallback && typeof fallback === 'string') {
            return replacePlaceholders(fallback, params)
          }
        }
        // If still not found, return the key itself
        return key
      }
    }

    if (typeof value === 'string') {
      return replacePlaceholders(value, params)
    }

    return key
  }

  const replacePlaceholders = (text, params) => {
    return text.replace(/\{(\w+)\}/g, (match, key) => {
      return params[key] !== undefined ? params[key] : match
    })
  }

  const setLocale = (locale) => {
    if (translations[locale]) {
      currentLocale.value = locale
      localStorage.setItem('app-locale', locale)
    }
  }

  const availableLocales = computed(() => Object.keys(translations))

  const localeName = computed(() => {
    const names = {
      en: 'English',
      ja: '日本語'
    }
    return names[currentLocale.value] || currentLocale.value
  })

  // Translate product names
  const translateProductName = (productName) => {
    if (currentLocale.value === 'ja' && translations.ja.productNames[productName]) {
      return translations.ja.productNames[productName]
    }
    return productName
  }

  // Translate customer names
  const translateCustomerName = (customerName) => {
    if (currentLocale.value === 'ja' && translations.ja.customerNames[customerName]) {
      return translations.ja.customerNames[customerName]
    }
    return customerName
  }

  // Translate warehouse names
  const translateWarehouse = (warehouseName) => {
    if (currentLocale.value === 'ja') {
      // Handle city names
      const cityMap = {
        'San Francisco': 'サンフランシスコ',
        'London': 'ロンドン',
        'Tokyo': '東京'
      }

      if (cityMap[warehouseName]) {
        return cityMap[warehouseName]
      }

      // Handle "Warehouse X-##" pattern
      if (warehouseName.startsWith('Warehouse ')) {
        return warehouseName.replace('Warehouse ', '倉庫')
      }

      return warehouseName
    }
    return warehouseName
  }

  // Translate product/spending categories
  const translateCategory = (category) => {
    // First try spending categories
    const spendingCategoryMap = {
      'Raw Materials': t('spendingCategories.rawMaterials'),
      'Components': t('spendingCategories.components'),
      'Equipment': t('spendingCategories.equipment'),
      'Consumables': t('spendingCategories.consumables')
    }

    // Then try product categories
    const productCategoryMap = {
      'Circuit Boards': t('categories.circuitBoards'),
      'Sensors': t('categories.sensors'),
      'Actuators': t('categories.actuators'),
      'Controllers': t('categories.controllers'),
      'Power Supplies': t('categories.powerSupplies')
    }

    return spendingCategoryMap[category] || productCategoryMap[category] || category
  }

  // Translate month abbreviations (Jan..Dec)
  const translateMonth = (month) => {
    const monthMap = {
      'Jan': t('months.jan'),
      'Feb': t('months.feb'),
      'Mar': t('months.mar'),
      'Apr': t('months.apr'),
      'May': t('months.may'),
      'Jun': t('months.jun'),
      'Jul': t('months.jul'),
      'Aug': t('months.aug'),
      'Sep': t('months.sep'),
      'Oct': t('months.oct'),
      'Nov': t('months.nov'),
      'Dec': t('months.dec')
    }
    return monthMap[month] || month
  }

  // Translate priority (accepts lower or capitalized case)
  const translatePriority = (priority) => {
    const priorityMap = {
      'high': t('priority.high'),
      'medium': t('priority.medium'),
      'low': t('priority.low'),
      'High': t('priority.high'),
      'Medium': t('priority.medium'),
      'Low': t('priority.low')
    }
    return priorityMap[priority] || priority
  }

  // Translate stock level labels
  const translateStockLevel = (stockLevel) => {
    const stockMap = {
      'In Stock': t('status.inStock'),
      'Low Stock': t('status.lowStock')
    }
    return stockMap[stockLevel] || stockLevel
  }

  return {
    t,
    setLocale,
    currentLocale: computed(() => currentLocale.value),
    currentCurrency,
    availableLocales,
    localeName,
    translateProductName,
    translateCustomerName,
    translateWarehouse,
    translateCategory,
    translateMonth,
    translatePriority,
    translateStockLevel
  }
}
