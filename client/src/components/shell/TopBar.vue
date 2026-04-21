<template>
  <header class="topbar">
    <!-- Left: hamburger (mobile) + page title -->
    <div class="topbar-left">
      <button
        class="hamburger"
        @click="onToggleDrawer"
        aria-label="Open navigation"
      >
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
          <path d="M3 5H17M3 10H17M3 15H17" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </button>
      <span v-if="currentCode" class="topbar-code">{{ currentCode }}</span>
      <h1 class="page-title">{{ pageTitle }}</h1>
    </div>

    <!-- Center: reserved -->
    <div class="topbar-center">
      <slot name="center" />
    </div>

    <!-- Right: LanguageSwitcher + ProfileMenu -->
    <div class="topbar-right">
      <slot name="right" />
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  routes: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['toggle-drawer'])

const route = useRoute()

const onToggleDrawer = () => emit('toggle-drawer')

const matchedRoute = computed(() => props.routes.find(r => r.path === route.path))

const pageTitle = computed(() => matchedRoute.value?.label || '')

const currentCode = computed(() => matchedRoute.value?.code || '')
</script>

<style scoped>
.topbar {
  height: var(--topbar-h);
  background: var(--paper-raised);
  border-bottom: 1px solid var(--rule-subtle);
  display: flex;
  align-items: center;
  padding: 0 var(--space-6);
  gap: var(--space-4);
  position: sticky;
  top: 0;
  z-index: 100;
  flex-shrink: 0;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex: 1;
  min-width: 0;
}

.topbar-center {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
}

.topbar-code {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--ink-muted);
  letter-spacing: var(--tracking-wider);
  margin-right: var(--space-2);
  padding: var(--space-1) var(--space-2);
  border: 1px solid var(--rule-subtle);
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}

.page-title {
  font-family: var(--font-display);
  font-weight: var(--weight-semibold);
  font-size: var(--text-md);
  color: var(--ink);
  letter-spacing: var(--tracking-tight);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Hamburger: only visible on mobile */
.hamburger {
  display: none;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  color: var(--ink-muted);
  cursor: pointer;
  flex-shrink: 0;
  transition: border-color var(--dur-fast) var(--ease-standard),
              background var(--dur-fast) var(--ease-standard),
              color var(--dur-fast) var(--ease-standard);
}

.hamburger:hover {
  border-color: var(--rule-subtle);
  background: var(--paper-bg-sub);
  color: var(--ink);
}

.hamburger:focus-visible {
  outline: none;
  box-shadow: var(--ring);
}

@media (max-width: 1023px) {
  .hamburger {
    display: flex;
  }
}
</style>
