<template>
  <Teleport to="body">
    <Transition name="po-modal">
      <div
        v-if="isOpen && backlogItem"
        class="modal-overlay"
        @click="close"
        @keydown.escape="close"
      >
        <div class="modal-container" @click.stop>
          <!-- Header -->
          <div class="modal-header">
            <div class="modal-header-left">
              <span class="section-eyebrow mono-label">§ PURCHASE ORDER</span>
              <h3 class="modal-title">
                <template v-if="mode === 'create'">New Purchase Order</template>
                <template v-else-if="fetchedPO">Purchase Order · <span class="mono">{{ fetchedPO.id }}</span></template>
                <template v-else>Purchase Order</template>
              </h3>
            </div>
            <button class="close-btn" @click="close" aria-label="Close modal">
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
                <path d="M13.5 4.5L4.5 13.5M4.5 4.5L13.5 13.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <!-- Body -->
          <div class="modal-body">
            <!-- Context card — always shown -->
            <div class="context-card">
              <div class="context-row">
                <span class="context-field">
                  <span class="mono-label">SKU</span>
                  <span class="mono context-value">{{ backlogItem.item_sku }}</span>
                </span>
                <span class="context-field">
                  <span class="mono-label">Item</span>
                  <span class="context-value">{{ backlogItem.item_name }}</span>
                </span>
                <span class="context-field">
                  <span class="mono-label">Shortage</span>
                  <span class="mono tabular context-value shortage">{{ shortage }} units</span>
                </span>
                <span class="context-field">
                  <span class="mono-label">Delayed</span>
                  <span class="mono tabular context-value">{{ backlogItem.days_delayed }}d</span>
                </span>
              </div>
            </div>

            <!-- Error block -->
            <div v-if="fetchError" class="error-block">
              {{ fetchError }}
            </div>

            <!-- View mode: loading state -->
            <div v-if="mode === 'view' && fetchLoading" class="loading-block">
              <span class="mono-label">Loading purchase order...</span>
            </div>

            <!-- View mode: PO detail -->
            <div v-else-if="mode === 'view' && fetchedPO" class="po-detail">
              <dl class="detail-grid">
                <div class="detail-item">
                  <dt class="mono-label">ID</dt>
                  <dd class="mono tabular">{{ fetchedPO.id }}</dd>
                </div>
                <div class="detail-item">
                  <dt class="mono-label">Supplier</dt>
                  <dd>{{ fetchedPO.supplier_name }}</dd>
                </div>
                <div class="detail-item">
                  <dt class="mono-label">Quantity</dt>
                  <dd class="mono tabular">{{ fetchedPO.quantity }}</dd>
                </div>
                <div class="detail-item">
                  <dt class="mono-label">Unit Cost</dt>
                  <dd class="mono tabular">${{ Number(fetchedPO.unit_cost).toFixed(2) }}</dd>
                </div>
                <div class="detail-item">
                  <dt class="mono-label">Expected Delivery</dt>
                  <dd class="mono">{{ formatDate(fetchedPO.expected_delivery_date) }}</dd>
                </div>
                <div class="detail-item">
                  <dt class="mono-label">Created</dt>
                  <dd class="mono">{{ formatDate(fetchedPO.created_date) }}</dd>
                </div>
                <div class="detail-item">
                  <dt class="mono-label">Status</dt>
                  <dd>
                    <span
                      class="badge"
                      :class="getStatusBadgeClass(fetchedPO.status)"
                    >{{ fetchedPO.status }}</span>
                  </dd>
                </div>
                <div v-if="fetchedPO.notes" class="detail-item detail-item--full">
                  <dt class="mono-label">Notes</dt>
                  <dd>{{ fetchedPO.notes }}</dd>
                </div>
              </dl>
            </div>

            <!-- Create mode: form -->
            <form v-else-if="mode === 'create'" class="po-form" @submit.prevent="submitForm">
              <!-- Submit error -->
              <div v-if="submitError" class="error-block">
                {{ submitError }}
              </div>

              <div class="form-field">
                <label for="po-supplier" class="mono-label">Supplier Name *</label>
                <input
                  id="po-supplier"
                  v-model="form.supplier_name"
                  type="text"
                  class="form-input"
                  required
                  placeholder="e.g. Acme Components Ltd."
                  autocomplete="off"
                />
              </div>

              <div class="form-row">
                <div class="form-field">
                  <label for="po-quantity" class="mono-label">Quantity *</label>
                  <input
                    id="po-quantity"
                    v-model.number="form.quantity"
                    type="number"
                    class="form-input mono tabular"
                    required
                    min="1"
                    step="1"
                  />
                </div>
                <div class="form-field">
                  <label for="po-unit-cost" class="mono-label">Unit Cost ($) *</label>
                  <input
                    id="po-unit-cost"
                    v-model.number="form.unit_cost"
                    type="number"
                    class="form-input mono tabular"
                    required
                    min="0"
                    step="0.01"
                    placeholder="0.00"
                  />
                </div>
              </div>

              <div class="form-field">
                <label for="po-delivery" class="mono-label">Expected Delivery Date *</label>
                <input
                  id="po-delivery"
                  v-model="form.expected_delivery_date"
                  type="date"
                  class="form-input mono"
                  required
                />
              </div>

              <div class="form-field">
                <label for="po-notes" class="mono-label">Notes</label>
                <textarea
                  id="po-notes"
                  v-model="form.notes"
                  class="form-input form-textarea"
                  rows="3"
                  placeholder="Optional notes for this purchase order"
                ></textarea>
              </div>
            </form>
          </div>

          <!-- Footer -->
          <div class="modal-footer">
            <template v-if="mode === 'create'">
              <button class="btn-ghost" type="button" @click="close">Cancel</button>
              <button
                class="btn-primary"
                type="button"
                :disabled="!formValid || submitting"
                @click="submitForm"
              >
                <template v-if="submitting">Creating...</template>
                <template v-else>Create Purchase Order</template>
              </button>
            </template>
            <template v-else>
              <button class="btn-ghost" type="button" @click="close">Close</button>
            </template>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api.js'

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  },
  backlogItem: {
    type: Object,
    default: null
  },
  mode: {
    type: String,
    default: 'create'
  }
})

const emit = defineEmits(['close', 'po-created'])

// ---------- computed helpers ----------
const shortage = computed(() => {
  if (!props.backlogItem) return 0
  return props.backlogItem.quantity_needed - props.backlogItem.quantity_available
})

// ---------- view mode state ----------
const fetchedPO = ref(null)
const fetchLoading = ref(false)
const fetchError = ref(null)

const fetchPO = async () => {
  if (!props.backlogItem) return
  fetchLoading.value = true
  fetchError.value = null
  try {
    fetchedPO.value = await api.getPurchaseOrderByBacklogItem(props.backlogItem.id)
  } catch (err) {
    fetchError.value = 'Failed to load purchase order.'
    console.error(err)
  } finally {
    fetchLoading.value = false
  }
}

// ---------- create mode state ----------
const defaultDeliveryDate = () => {
  const d = new Date()
  d.setDate(d.getDate() + 14)
  return d.toISOString().slice(0, 10)
}

const form = ref({
  supplier_name: '',
  quantity: 1,
  unit_cost: '',
  expected_delivery_date: defaultDeliveryDate(),
  notes: ''
})

const submitting = ref(false)
const submitError = ref(null)

const formValid = computed(() => {
  return (
    form.value.supplier_name.trim().length > 0 &&
    form.value.quantity >= 1 &&
    form.value.unit_cost !== '' &&
    Number(form.value.unit_cost) >= 0 &&
    form.value.expected_delivery_date.length > 0
  )
})

const resetState = () => {
  fetchedPO.value = null
  fetchLoading.value = false
  fetchError.value = null
  submitting.value = false
  submitError.value = null
  form.value = {
    supplier_name: '',
    quantity: shortage.value > 0 ? shortage.value : 1,
    unit_cost: '',
    expected_delivery_date: defaultDeliveryDate(),
    notes: ''
  }
}

// ---------- lifecycle ----------
watch(() => props.isOpen, (val) => {
  if (val) {
    resetState()
    if (props.mode === 'view') {
      fetchPO()
    } else {
      // pre-fill quantity from shortage
      form.value.quantity = shortage.value > 0 ? shortage.value : 1
    }
  } else {
    resetState()
  }
})

onMounted(() => {
  if (props.isOpen && props.mode === 'view') {
    fetchPO()
  }
})

// ---------- actions ----------
const close = () => emit('close')

const submitForm = async () => {
  if (!formValid.value || submitting.value) return
  submitting.value = true
  submitError.value = null
  try {
    const payload = {
      backlog_item_id: props.backlogItem.id,
      supplier_name: form.value.supplier_name.trim(),
      quantity: form.value.quantity,
      unit_cost: Number(form.value.unit_cost),
      expected_delivery_date: form.value.expected_delivery_date,
      notes: form.value.notes.trim() || null
    }
    const created = await api.createPurchaseOrder(payload)
    emit('po-created', created)
    emit('close')
  } catch (err) {
    submitError.value = err?.response?.data?.detail || 'Failed to create purchase order.'
    console.error(err)
  } finally {
    submitting.value = false
  }
}

// ---------- helpers ----------
const formatDate = (dateStr) => {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

const getStatusBadgeClass = (status) => {
  if (!status) return 'info'
  const s = status.toLowerCase()
  if (s === 'pending') return 'warning'
  if (s === 'delivered') return 'success'
  if (s === 'shipped') return 'info'
  return 'info'
}
</script>

<style scoped>
/* ── Overlay ─────────────────────────────────────────────────────── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(10, 10, 10, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: var(--space-4);
}

/* ── Container ───────────────────────────────────────────────────── */
.modal-container {
  background: var(--paper-raised);
  border: 1px solid var(--rule);
  box-shadow: var(--shadow-lg);
  max-width: 560px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  border-radius: var(--radius-sm);
}

/* ── Header ──────────────────────────────────────────────────────── */
.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--rule);
  flex-shrink: 0;
}

.modal-header-left {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.section-eyebrow {
  /* .mono-label utility already covers font/size/transform/tracking/color */
}

.modal-title {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: var(--weight-semibold);
  color: var(--ink);
  letter-spacing: var(--tracking-tight);
  line-height: var(--leading-tight);
}

.close-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  color: var(--ink-muted);
  cursor: pointer;
  transition:
    border-color var(--dur-fast) var(--ease-standard),
    color var(--dur-fast) var(--ease-standard),
    background var(--dur-fast) var(--ease-standard);
  margin-top: var(--space-1);
}

.close-btn:hover {
  border-color: var(--rule-subtle);
  color: var(--ink);
  background: var(--paper-bg-sub);
}

.close-btn:focus-visible {
  outline: none;
  box-shadow: var(--ring);
}

/* ── Body ────────────────────────────────────────────────────────── */
.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

/* ── Context card ────────────────────────────────────────────────── */
.context-card {
  background: var(--paper-bg-sub);
  border: 1px solid var(--rule-subtle);
  border-radius: var(--radius-sm);
  padding: var(--space-4);
}

.context-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-4) var(--space-6);
}

.context-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.context-value {
  font-size: var(--text-sm);
  color: var(--ink);
  font-weight: var(--weight-medium);
}

.context-value.shortage {
  color: var(--danger);
  font-weight: var(--weight-semibold);
}

/* ── Error / loading blocks ──────────────────────────────────────── */
.error-block {
  background: var(--danger-bg);
  border: 1px solid var(--danger);
  border-radius: var(--radius-sm);
  padding: var(--space-3) var(--space-4);
  font-size: var(--text-sm);
  color: var(--danger-ink);
  font-family: var(--font-body);
}

.loading-block {
  padding: var(--space-6) 0;
  text-align: center;
  color: var(--ink-muted);
}

/* ── View mode: PO detail ────────────────────────────────────────── */
.po-detail {
  flex: 1;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4) var(--space-6);
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.detail-item--full {
  grid-column: 1 / -1;
}

.detail-item dt {
  /* mono-label applied via class */
}

.detail-item dd {
  font-size: var(--text-sm);
  color: var(--ink);
  font-weight: var(--weight-medium);
}

/* ── Badge variants (view mode status) ───────────────────────────── */
/* Global .badge class applies base styles; these are semantic overrides */
/* (badge base is defined globally; we only layer semantic colours here) */

/* ── Create mode: form ───────────────────────────────────────────── */
.po-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.form-input {
  background: var(--paper-bg);
  border: 1px solid var(--rule-soft);
  border-radius: var(--radius-sm);
  padding: var(--space-2) var(--space-3);
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  color: var(--ink);
  width: 100%;
  transition: border-color var(--dur-fast) var(--ease-standard);
  appearance: none;
  -webkit-appearance: none;
}

.form-input:hover {
  border-color: var(--ink);
}

.form-input:focus-visible {
  outline: none;
  box-shadow: var(--ring);
  border-color: var(--accent);
}

.form-textarea {
  resize: vertical;
  min-height: 72px;
  font-family: var(--font-body);
}

/* ── Footer ──────────────────────────────────────────────────────── */
.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  border-top: 1px solid var(--rule-subtle);
  flex-shrink: 0;
}

.btn-ghost {
  background: transparent;
  border: 1px solid var(--rule-subtle);
  border-radius: var(--radius-sm);
  padding: var(--space-2) var(--space-4);
  font-family: var(--font-body);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--ink-soft);
  cursor: pointer;
  transition:
    border-color var(--dur-fast) var(--ease-standard),
    color var(--dur-fast) var(--ease-standard),
    background var(--dur-fast) var(--ease-standard);
}

.btn-ghost:hover {
  border-color: var(--rule);
  color: var(--ink);
  background: var(--paper-bg-sub);
}

.btn-ghost:focus-visible {
  outline: none;
  box-shadow: var(--ring);
}

.btn-primary {
  background: var(--accent);
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  padding: var(--space-2) var(--space-5);
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
  color: var(--accent-ink);
  cursor: pointer;
  transition:
    background var(--dur-fast) var(--ease-standard),
    opacity var(--dur-fast) var(--ease-standard);
}

.btn-primary:hover:not(:disabled) {
  background: var(--accent-hover);
}

.btn-primary:focus-visible {
  outline: none;
  box-shadow: var(--ring);
}

.btn-primary:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

/* ── Transition ──────────────────────────────────────────────────── */
.po-modal-enter-active,
.po-modal-leave-active {
  transition: opacity var(--dur-medium) var(--ease-standard);
}

.po-modal-enter-from,
.po-modal-leave-to {
  opacity: 0;
}

.po-modal-enter-active .modal-container,
.po-modal-leave-active .modal-container {
  transition: transform var(--dur-medium) var(--ease-standard);
}

.po-modal-enter-from .modal-container,
.po-modal-leave-to .modal-container {
  transform: scale(0.97) translateY(var(--space-2));
}
</style>
