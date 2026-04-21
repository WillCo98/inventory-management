<template>
  <div class="restocking">
    <div class="page-header">
      <div class="section-code">§ 04 · RESTOCKING</div>
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="budget-section card">
      <div class="budget-header">
        <span class="budget-label">{{ t('restocking.budget') }}</span>
        <span class="budget-value tabular" :class="{ 'over-budget': isOverBudget }">
          {{ formatCurrency(budget, currentCurrency) }}
        </span>
      </div>
      <div class="slider-wrapper">
        <span class="slider-endpoint mono tabular">$1K</span>
        <input
          type="range"
          v-model.number="budget"
          min="1000"
          max="1000000"
          step="1000"
          class="budget-slider"
        />
        <span class="slider-endpoint mono tabular">$1M</span>
      </div>
      <p class="budget-description">{{ t('restocking.budgetRange') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.totalRecommended') }}</div>
          <div class="stat-value tabular">{{ enrichedRecommendations.length }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.estimatedCost') }}</div>
          <div class="stat-value tabular">{{ formatCurrency(totalCost, currentCurrency) }}</div>
        </div>
        <div class="stat-card" :class="budgetRemaining >= 0 ? 'success' : 'danger'">
          <div class="stat-label">{{ t('restocking.budgetRemaining') }}</div>
          <div class="stat-value tabular">{{ formatCurrency(Math.abs(budgetRemaining), currentCurrency) }}{{ budgetRemaining < 0 ? ' over' : '' }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.trendBreakdown') }}</div>
          <div class="stat-value trend-breakdown-value">
            <span class="badge increasing tabular">{{ trendBreakdown.increasing }}</span>
            <span class="badge stable tabular">{{ trendBreakdown.stable }}</span>
            <span class="badge decreasing tabular">{{ trendBreakdown.decreasing }}</span>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }}</h3>
          <span v-if="isOverBudget" class="badge danger over-budget-badge">{{ t('restocking.overBudget') }}</span>
        </div>

        <div v-if="enrichedRecommendations.length === 0" class="no-data-row">
          {{ t('restocking.noRecommendations') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.currentDemand') }}</th>
                <th>{{ t('restocking.table.forecastedDemand') }}</th>
                <th>{{ t('restocking.table.demandGap') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.quantity') }}</th>
                <th>{{ t('restocking.table.lineCost') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in enrichedRecommendations" :key="item.item_sku">
                <td><strong class="mono">{{ item.item_sku }}</strong></td>
                <td>{{ item.item_name }}</td>
                <td>
                  <span :class="['badge', trendBadgeClass(item.trend)]">
                    {{ t('trends.' + item.trend) }}
                  </span>
                </td>
                <td class="tabular">{{ item.current_demand }}</td>
                <td><strong class="tabular">{{ item.forecasted_demand }}</strong></td>
                <td>
                  <span :class="['tabular', item.demand_gap > 0 ? 'gap-positive' : 'gap-neutral']">
                    {{ item.demand_gap > 0 ? '+' : '' }}{{ item.demand_gap }}
                  </span>
                </td>
                <td class="tabular">{{ formatCurrency(item.unit_cost, currentCurrency) }}</td>
                <td>
                  <input
                    type="number"
                    min="1"
                    :value="editableQuantities[item.item_sku]"
                    @input="updateQuantity(item.item_sku, $event.target.value)"
                    class="qty-input tabular"
                  />
                </td>
                <td>
                  <strong class="tabular" :class="{ 'over-budget-text': item.editedLineCost > budget }">
                    {{ formatCurrency(item.editedLineCost, currentCurrency) }}
                  </strong>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-if="enrichedRecommendations.length > 0" class="card order-summary-card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.orderSummary') }}</h3>
        </div>

        <div class="summary-body">
          <div class="summary-row">
            <span class="summary-label">{{ t('restocking.totalItems') }}</span>
            <span class="summary-val tabular">{{ enrichedRecommendations.length }}</span>
          </div>
          <div class="summary-row">
            <span class="summary-label">{{ t('restocking.totalCost') }}</span>
            <span class="summary-val tabular" :class="{ 'over-budget-text': isOverBudget }">
              {{ formatCurrency(totalCost, currentCurrency) }}
            </span>
          </div>
          <div class="summary-row lead-time-row">
            <span class="summary-label lead-time-note">{{ t('restocking.leadTime') }}</span>
          </div>
        </div>

        <div class="submit-area">
          <div v-if="submitSuccess" class="success-message">
            {{ t('restocking.orderSuccess') }}
          </div>
          <div v-if="submitError" class="error submit-error">
            {{ submitError }}
          </div>

          <button
            class="submit-btn"
            :disabled="!canSubmit"
            :class="{ 'btn-loading': submitting, 'btn-over-budget': isOverBudget }"
            @click="submitOrder"
          >
            <span v-if="submitting" class="btn-spinner"></span>
            {{ submitting ? t('common.loading') : t('restocking.placeOrder') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()
    const { } = useFilters()

    const budget = ref(50000)
    const recommendations = ref([])
    const editableQuantities = ref({})
    const loading = ref(false)
    const error = ref(null)
    const submitting = ref(false)
    const submitSuccess = ref(false)
    const submitError = ref(null)

    let debounceTimer = null

    const loadRecommendations = async () => {
      loading.value = true
      error.value = null
      submitSuccess.value = false
      try {
        const data = await api.getRestockingRecommendations(budget.value)
        recommendations.value = data

        // Initialize editable quantities from API response
        const quantities = {}
        for (const item of data) {
          quantities[item.item_sku] = item.recommended_quantity
        }
        editableQuantities.value = quantities
      } catch (err) {
        error.value = 'Failed to load restocking recommendations'
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    const updateQuantity = (sku, rawValue) => {
      const parsed = parseInt(rawValue, 10)
      if (!isNaN(parsed) && parsed >= 1) {
        editableQuantities.value = { ...editableQuantities.value, [sku]: parsed }
      }
    }

    const enrichedRecommendations = computed(() => {
      return recommendations.value.map(item => {
        const qty = editableQuantities.value[item.item_sku] ?? item.recommended_quantity
        return {
          ...item,
          editedQuantity: qty,
          editedLineCost: item.unit_cost * qty
        }
      })
    })

    const totalCost = computed(() =>
      enrichedRecommendations.value.reduce((sum, item) => sum + item.editedLineCost, 0)
    )

    const budgetRemaining = computed(() => budget.value - totalCost.value)

    const isOverBudget = computed(() => totalCost.value > budget.value)

    const canSubmit = computed(
      () => totalCost.value > 0 && totalCost.value <= budget.value && !submitting.value
    )

    const trendBreakdown = computed(() => {
      const counts = { increasing: 0, stable: 0, decreasing: 0 }
      for (const item of recommendations.value) {
        if (counts[item.trend] !== undefined) counts[item.trend]++
      }
      return counts
    })

    const trendBadgeClass = (trend) => {
      const map = { increasing: 'success', stable: 'info', decreasing: 'warning' }
      return map[trend] ?? 'info'
    }

    const submitOrder = async () => {
      submitting.value = true
      submitError.value = null
      try {
        const orderItems = enrichedRecommendations.value.map(item => ({
          item_sku: item.item_sku,
          item_name: item.item_name,
          quantity: editableQuantities.value[item.item_sku],
          unit_cost: item.unit_cost
        }))
        await api.submitRestockOrder({ items: orderItems, total_value: totalCost.value })
        submitSuccess.value = true
        recommendations.value = []
        editableQuantities.value = {}
      } catch (err) {
        submitError.value = t('restocking.orderError')
      } finally {
        submitting.value = false
      }
    }

    watch(budget, () => {
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        loadRecommendations()
      }, 300)
    })

    onMounted(() => loadRecommendations())

    return {
      t,
      currentCurrency,
      formatCurrency,
      budget,
      recommendations,
      editableQuantities,
      loading,
      error,
      submitting,
      submitSuccess,
      submitError,
      enrichedRecommendations,
      totalCost,
      budgetRemaining,
      isOverBudget,
      canSubmit,
      trendBreakdown,
      trendBadgeClass,
      updateQuantity,
      submitOrder
    }
  }
}
</script>

<style scoped>
/* Section-code eyebrow */
.section-code {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  color: var(--ink-muted);
  margin-bottom: var(--space-2);
}

/* ── Budget section ──────────────────────────────────────────── */
.budget-section {
  margin-bottom: var(--space-6);
}

.budget-header {
  display: flex;
  align-items: baseline;
  gap: var(--space-4);
  margin-bottom: var(--space-3);
}

.budget-label {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  color: var(--ink-muted);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
}

.budget-value {
  font-family: var(--font-mono);
  font-size: var(--text-3xl);
  font-weight: var(--weight-bold);
  color: var(--ink);
  letter-spacing: var(--tracking-tight);
  transition: color var(--dur-medium) var(--ease-standard);
}

.budget-value.over-budget {
  color: var(--danger);
}

.slider-wrapper {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.slider-endpoint {
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  color: var(--ink-muted);
  white-space: nowrap;
  flex-shrink: 0;
}

/* Rectangular industrial slider — square track, accent fill thumb */
.budget-slider {
  flex: 1;
  -webkit-appearance: none;
  appearance: none;
  height: 4px;
  border-radius: var(--radius-none);
  background: var(--paper-bg-sub);
  border: 1px solid var(--rule-subtle);
  outline: none;
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-standard);
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: var(--radius-none);
  background: var(--accent);
  cursor: pointer;
  border: 2px solid var(--paper-raised);
  box-shadow: 0 0 0 1px var(--accent);
  transition: background var(--dur-fast) var(--ease-standard);
}

.budget-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: var(--radius-none);
  background: var(--accent);
  cursor: pointer;
  border: 2px solid var(--paper-raised);
  box-shadow: 0 0 0 1px var(--accent);
  transition: background var(--dur-fast) var(--ease-standard);
}

.budget-slider:hover::-webkit-slider-thumb {
  background: var(--accent-hover);
  box-shadow: 0 0 0 1px var(--accent-hover);
}

.budget-slider:hover::-moz-range-thumb {
  background: var(--accent-hover);
  box-shadow: 0 0 0 1px var(--accent-hover);
}

.budget-description {
  margin-top: var(--space-2);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--ink-faint);
  letter-spacing: var(--tracking-wide);
}

/* ── Trend breakdown in stat card ────────────────────────────── */
.trend-breakdown-value {
  display: flex;
  gap: var(--space-2);
  align-items: center;
  flex-wrap: wrap;
  font-size: var(--text-base);
  margin-top: var(--space-2);
}

/* Over-budget badge in card header */
.over-budget-badge {
  /* inherits .badge .danger from globals — no extra rules needed */
}

/* No-data state */
.no-data-row {
  text-align: center;
  padding: var(--space-12);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
  color: var(--ink-muted);
}

/* Demand gap coloring */
.gap-positive {
  color: var(--success);
  font-weight: var(--weight-semibold);
}

.gap-neutral {
  color: var(--ink-muted);
}

/* Quantity input — mono, industrial */
.qty-input {
  width: 80px;
  padding: var(--space-1) var(--space-2);
  border: 1px solid var(--rule-soft);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  color: var(--ink);
  background: var(--paper-raised);
  outline: none;
  text-align: right;
  transition: border-color var(--dur-fast) var(--ease-standard);
}

.qty-input:focus {
  border-color: var(--ink);
  box-shadow: var(--ring);
}

.qty-input:hover:not(:focus) {
  border-color: var(--rule);
}

/* Over-budget text */
.over-budget-text {
  color: var(--danger);
}

/* Order summary card — accent left rule */
.order-summary-card {
  border-left: 3px solid var(--accent);
}

.summary-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-bottom: var(--space-5);
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-2) var(--space-3);
  background: var(--paper-bg-sub);
  border: 1px solid var(--rule-subtle);
  border-radius: var(--radius-sm);
}

.lead-time-row {
  background: var(--info-bg);
  border-color: var(--info);
}

.summary-label {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
  color: var(--ink-soft);
}

.lead-time-note {
  color: var(--info);
}

.summary-val {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  font-weight: var(--weight-bold);
  color: var(--ink);
}

/* ── Submit area ─────────────────────────────────────────────── */
.submit-area {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.submit-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-8);
  background: var(--accent);
  color: var(--accent-ink);
  border: none;
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-standard);
  align-self: flex-start;
}

.submit-btn:hover:not(:disabled) {
  background: var(--accent-hover);
}

.submit-btn:active:not(:disabled) {
  background: var(--accent-press);
}

.submit-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.submit-btn.btn-over-budget {
  background: var(--danger);
}

.submit-btn.btn-over-budget:hover:not(:disabled) {
  background: var(--danger-ink);
}

/* Spinner */
.btn-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.35);
  border-top-color: var(--accent-ink);
  border-radius: 50%;
  animation: spin var(--dur-slow) linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Success message */
.success-message {
  padding: var(--space-3) var(--space-4);
  background: var(--success-bg);
  border: 1px solid var(--success);
  color: var(--success);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.submit-error {
  margin: 0;
}
</style>
