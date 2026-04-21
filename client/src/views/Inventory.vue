<template>
  <div class="inventory">
    <div class="page-header">
      <div class="section-code">§ 02 · INVENTORY</div>
      <h2>{{ t('inventory.title') }}</h2>
      <p>{{ t('inventory.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('inventory.stockLevels') }} (<span class="tabular">{{ filteredItems.length }}</span> {{ t('inventory.skus') }})</h3>
          <div class="search-box">
            <span class="search-label">SEARCH</span>
            <span class="search-divider" aria-hidden="true"></span>
            <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd" />
            </svg>
            <input
              v-model="searchQuery"
              type="text"
              :placeholder="t('inventory.searchPlaceholder')"
              class="search-input"
            />
            <button
              v-if="searchQuery"
              @click="searchQuery = ''"
              class="clear-search"
              :title="t('inventory.clearSearch')"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('inventory.table.sku') }}</th>
                <th>{{ t('inventory.table.itemName') }}</th>
                <th>{{ t('inventory.table.category') }}</th>
                <th>{{ t('inventory.table.quantityOnHand') }}</th>
                <th>{{ t('inventory.table.reorderPoint') }}</th>
                <th>{{ t('inventory.table.unitCost') }}</th>
                <th>{{ t('inventory.table.totalValue') }}</th>
                <th>{{ t('inventory.table.location') }}</th>
                <th>{{ t('inventory.table.status') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in filteredItems"
                :key="item.id"
                class="clickable-row"
                @click="showItemDetail(item)"
              >
                <td><strong class="mono">{{ item.sku }}</strong></td>
                <td>{{ translateProductName(item.name) }}</td>
                <td>{{ translateCategory(item.category) }}</td>
                <td><strong class="tabular">{{ item.quantity_on_hand }}</strong></td>
                <td class="tabular">{{ item.reorder_point }}</td>
                <td class="tabular">{{ currencySymbol }}{{ item.unit_cost.toFixed(2) }}</td>
                <td><strong class="tabular">{{ currencySymbol }}{{ (item.quantity_on_hand * item.unit_cost).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) }}</strong></td>
                <td>{{ translateWarehouse(item.location) }}</td>
                <td>
                  <span :class="['badge', getStockStatusClass(item)]">
                    {{ getStockStatus(item) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <InventoryDetailModal
      :is-open="showItemModal"
      :inventory-item="selectedItem"
      @close="showItemModal = false"
    />
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import InventoryDetailModal from '../components/InventoryDetailModal.vue'

export default {
  name: 'Inventory',
  components: {
    InventoryDetailModal
  },
  setup() {
    const { t, currentCurrency, translateProductName, translateWarehouse } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)
    const items = ref([])
    const searchQuery = ref('')

    // Modal state
    const showItemModal = ref(false)
    const selectedItem = ref(null)

    // Use shared filters
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    // Stock status order for sorting (using status keys)
    const STATUS_ORDER = { 'lowStock': 0, 'adequate': 1, 'inStock': 2 }

    // Get stock status key (for sorting and translation)
    const getStockStatusKey = (item) => {
      if (item.quantity_on_hand <= item.reorder_point) {
        return 'lowStock'
      } else if (item.quantity_on_hand <= item.reorder_point * 1.5) {
        return 'adequate'
      } else {
        return 'inStock'
      }
    }

    // Computed property to filter items by search query and sort by stock status
    const filteredItems = computed(() => {
      let filtered = items.value

      // Apply search filter if query exists
      if (searchQuery.value.trim()) {
        const query = searchQuery.value.toLowerCase().trim()
        filtered = filtered.filter(item =>
          item.name.toLowerCase().includes(query)
        )
      }

      // Sort by stock status: Low Stock first, then Adequate, then In Stock
      // Always create a copy to avoid mutating the original array
      return filtered.slice().sort((a, b) => {
        const statusA = getStockStatusKey(a)
        const statusB = getStockStatusKey(b)
        return STATUS_ORDER[statusA] - STATUS_ORDER[statusB]
      })
    })

    const loadInventory = async () => {
      try {
        loading.value = true
        const filters = getCurrentFilters()
        // Inventory doesn't support month/status filters, only warehouse and category
        items.value = await api.getInventory({
          warehouse: filters.warehouse,
          category: filters.category
        })
      } catch (err) {
        error.value = 'Failed to load inventory: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Watch for filter changes and reload data
    watch([selectedLocation, selectedCategory], () => {
      loadInventory()
    })

    const getStockStatus = (item) => {
      const key = getStockStatusKey(item)
      return t(`status.${key}`)
    }

    const getStockStatusClass = (item) => {
      if (item.quantity_on_hand <= item.reorder_point) {
        return 'danger'
      } else if (item.quantity_on_hand <= item.reorder_point * 1.5) {
        return 'warning'
      } else {
        return 'success'
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

    const showItemDetail = (item) => {
      selectedItem.value = item
      showItemModal.value = true
    }

    onMounted(loadInventory)

    return {
      t,
      loading,
      error,
      items,
      searchQuery,
      filteredItems,
      getStockStatus,
      getStockStatusClass,
      translateCategory,
      showItemModal,
      selectedItem,
      showItemDetail,
      currencySymbol,
      translateProductName,
      translateWarehouse
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

/* card-header: flex layout with search aligned right */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-6);
}

/* Search box — mono industrial style */
.search-box {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0;
  border: 1px solid var(--rule-soft);
  border-radius: var(--radius-sm);
  background: var(--paper-raised);
  overflow: hidden;
  min-width: 300px;
  transition: border-color var(--dur-fast) var(--ease-standard);
}

.search-box:focus-within {
  border-color: var(--ink);
}

.search-label {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
  color: var(--ink-muted);
  padding: var(--space-2) var(--space-3);
  white-space: nowrap;
  flex-shrink: 0;
  background: var(--paper-bg-sub);
  border-right: 1px solid var(--rule-soft);
}

.search-divider {
  /* handled by .search-label border-right */
  display: none;
}

.search-icon {
  position: absolute;
  left: calc(/* label approx */ 68px + var(--space-2));
  width: 14px;
  height: 14px;
  color: var(--ink-faint);
  pointer-events: none;
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  padding: var(--space-2) var(--space-8) var(--space-2) var(--space-7);
  border: none;
  background: transparent;
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  color: var(--ink);
  outline: none;
  min-width: 0;
}

.search-input::placeholder {
  color: var(--ink-faint);
  font-family: var(--font-mono);
}

.clear-search {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-1);
  margin-right: var(--space-1);
  background: transparent;
  border: none;
  color: var(--ink-muted);
  cursor: pointer;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  transition: color var(--dur-fast) var(--ease-standard),
              background var(--dur-fast) var(--ease-standard);
}

.clear-search:hover {
  background: var(--paper-bg-sub);
  color: var(--ink);
}

.clear-search svg {
  width: 14px;
  height: 14px;
}

/* Clickable row — use token background, no hex */
.clickable-row {
  cursor: pointer;
}

.clickable-row:hover {
  background: var(--accent-soft) !important;
}
</style>
