<template>
  <div class="app-shell" :class="{ collapsed: sidebarCollapsed }">
    <Sidebar
      :routes="routes"
      :brand="brand"
      :subtitle="subtitle"
      @toggle-drawer="toggleDrawer"
      @toggle-collapsed="toggleCollapsed"
    >
      <template #footer>
        <slot name="sidebar-footer" />
      </template>
    </Sidebar>

    <div class="app-main">
      <TopBar :routes="routes" @toggle-drawer="toggleDrawer">
        <template #right>
          <slot name="topbar-right" />
        </template>
        <template #center>
          <slot name="topbar-center" />
        </template>
      </TopBar>

      <div class="filter-strip">
        <slot name="filter" />
      </div>

      <main class="app-content">
        <div class="app-content-inner">
          <slot />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, provide, onMounted, onUnmounted, watch } from 'vue'
import Sidebar from './Sidebar.vue'
import TopBar from './TopBar.vue'

defineProps({
  routes: {
    type: Array,
    default: () => []
  },
  brand: {
    type: String,
    default: ''
  },
  subtitle: {
    type: String,
    default: ''
  }
})

const sidebarOpen = ref(false)
const sidebarCollapsed = ref(false)

// Tracks whether the user has explicitly toggled collapse state.
// When true, auto-collapse based on window width is suppressed.
const userToggledCollapse = ref(false)

const windowWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1280)

const AUTO_COLLAPSE_BREAKPOINT = 1280

const handleResize = () => {
  windowWidth.value = window.innerWidth
}

onMounted(() => {
  window.addEventListener('resize', handleResize, { passive: true })
  // Set initial state based on current width
  if (!userToggledCollapse.value) {
    sidebarCollapsed.value = window.innerWidth < AUTO_COLLAPSE_BREAKPOINT
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

// Auto-collapse when width crosses the threshold, unless user has manually toggled.
watch(windowWidth, (w) => {
  if (!userToggledCollapse.value) {
    sidebarCollapsed.value = w < AUTO_COLLAPSE_BREAKPOINT
  }
})

provide('sidebarOpen', sidebarOpen)
provide('sidebarCollapsed', sidebarCollapsed)

const toggleDrawer = () => {
  sidebarOpen.value = !sidebarOpen.value
}

const toggleCollapsed = () => {
  userToggledCollapse.value = true
  sidebarCollapsed.value = !sidebarCollapsed.value
}
</script>

<style scoped>
.app-shell {
  display: grid;
  grid-template-columns: var(--sidebar-w) 1fr;
  min-height: 100vh;
  transition: grid-template-columns var(--dur-medium) var(--ease-standard);
}

.app-shell.collapsed {
  grid-template-columns: var(--sidebar-w-collapsed) 1fr;
}

.app-main {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  min-width: 0;
  overflow: hidden;
}

.filter-strip {
  /* FilterBar handles its own sticky positioning */
}

.app-content {
  flex: 1;
  min-width: 0;
}

.app-content-inner {
  max-width: var(--content-max-w);
  margin: 0 auto;
  padding: var(--space-6) var(--space-8);
}

/* ── Mobile: single column, sidebar is off-canvas ──────────── */
@media (max-width: 1023px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .app-shell.collapsed {
    grid-template-columns: 1fr;
  }

  .app-content-inner {
    padding: var(--space-4) var(--space-4);
  }
}
</style>
