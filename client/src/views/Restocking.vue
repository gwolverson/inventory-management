<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="card budget-card">
      <div class="budget-row">
        <label class="budget-label" for="budget-slider">{{ t('restocking.budgetLabel') }}</label>
        <span class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
      </div>
      <input
        id="budget-slider"
        type="range"
        min="1000"
        max="80000"
        step="500"
        v-model.number="budget"
        @change="loadRecommendations"
        class="budget-slider"
      />
    </div>

    <div v-if="successMessage" class="success-banner">{{ successMessage }}</div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.title') }} ({{ recommendations.length }})</h3>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          {{ t('restocking.noRecommendations') }}
        </div>

        <div v-else class="table-container">
          <table class="restock-table">
            <thead>
              <tr>
                <th class="col-item-name">{{ t('restocking.table.itemName') }}</th>
                <th class="col-warehouse">{{ t('restocking.table.warehouse') }}</th>
                <th class="col-category">{{ t('restocking.table.category') }}</th>
                <th class="col-trend">{{ t('restocking.table.trend') }}</th>
                <th class="col-number">{{ t('restocking.table.deficit') }}</th>
                <th class="col-number">{{ t('restocking.table.unitCost') }}</th>
                <th class="col-number">{{ t('restocking.table.recommendedQty') }}</th>
                <th class="col-number">{{ t('restocking.table.lineCost') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations" :key="item.sku">
                <td>{{ translateProductName(item.name) }}</td>
                <td>{{ translateWarehouse(item.warehouse) }}</td>
                <td>{{ translateCategory(item.category) }}</td>
                <td>
                  <span :class="['badge', item.trend]">{{ t(`trends.${item.trend}`) }}</span>
                </td>
                <td>{{ item.deficit }}</td>
                <td>{{ currencySymbol }}{{ item.unit_cost.toFixed(2) }}</td>
                <td><strong>{{ item.recommended_quantity }}</strong></td>
                <td>{{ currencySymbol }}{{ item.line_cost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="summary-row">
          <div class="summary-item">
            <span class="summary-label">{{ t('restocking.totalCost') }}</span>
            <span class="summary-value">{{ currencySymbol }}{{ totalCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">{{ t('restocking.budgetLabel') }}</span>
            <span class="summary-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">{{ t('restocking.remainingBudget') }}</span>
            <span class="summary-value" :style="{ color: remainingBudgetColor }">
              {{ currencySymbol }}{{ remainingBudget.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
            </span>
          </div>
        </div>

        <button
          class="place-order-btn"
          :disabled="submitting || recommendations.length === 0"
          @click="placeOrder"
        >
          {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName, translateWarehouse } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const budget = ref(25000)
    const recommendations = ref([])
    const totalCost = ref(0)
    const remainingBudget = ref(0)
    const loading = ref(true)
    const error = ref(null)
    const submitting = ref(false)
    const successMessage = ref(null)

    const remainingBudgetColor = computed(() => {
      return remainingBudget.value >= 0 ? '#10b981' : '#ef4444'
    })

    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        const response = await api.getRestockRecommendations(budget.value)
        recommendations.value = response.items
        totalCost.value = response.total_cost
        remainingBudget.value = response.remaining_budget
      } catch (err) {
        error.value = 'Failed to load restock recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      try {
        submitting.value = true
        const payload = {
          budget: budget.value,
          items: recommendations.value.map(r => ({
            sku: r.sku,
            name: r.name,
            quantity: r.recommended_quantity,
            unit_cost: r.unit_cost
          }))
        }
        const result = await api.createRestockOrder(payload)
        successMessage.value = t('restocking.orderSuccess', {
          orderNumber: result.order_number,
          days: result.lead_time_days
        })
        await loadRecommendations()
      } catch (err) {
        error.value = 'Failed to place restock order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    const translateCategory = (category) => {
      const categoryMap = {
        'Circuit Boards': t('categories.circuitBoards'),
        'Sensors': t('categories.sensors'),
        'Actuators': t('categories.actuators'),
        'Controllers': t('categories.controllers'),
        'Power Supplies': t('categories.powerSupplies')
      }
      return categoryMap[category] || category
    }

    onMounted(loadRecommendations)

    return {
      t,
      budget,
      recommendations,
      totalCost,
      remainingBudget,
      remainingBudgetColor,
      loading,
      error,
      submitting,
      successMessage,
      loadRecommendations,
      placeOrder,
      currencySymbol,
      translateProductName,
      translateWarehouse,
      translateCategory
    }
  }
}
</script>

<style scoped>
.budget-card {
  padding: 1.25rem 1.5rem;
}

.budget-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.75rem;
}

.budget-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.budget-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-slider {
  width: 100%;
  accent-color: #2563eb;
  cursor: pointer;
}

.success-banner {
  background: #d1fae5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  font-size: 0.938rem;
  font-weight: 500;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

/* Fixed table layout to prevent column shifting */
.restock-table {
  table-layout: fixed;
  width: 100%;
}

.col-item-name {
  width: 220px;
}

.col-warehouse {
  width: 140px;
}

.col-category {
  width: 140px;
}

.col-trend {
  width: 110px;
}

.col-number {
  width: 120px;
}

.summary-row {
  display: flex;
  gap: 2rem;
  margin-top: 1.25rem;
  padding-top: 1.25rem;
  border-top: 1px solid #e2e8f0;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.summary-label {
  font-size: 0.813rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.summary-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
}

.place-order-btn {
  margin-top: 1.25rem;
  padding: 0.625rem 1.5rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}
</style>
