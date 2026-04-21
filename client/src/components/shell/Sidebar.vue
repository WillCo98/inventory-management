<template>
  <aside
    class="sidebar"
    :class="{ collapsed: sidebarCollapsed, open: sidebarOpen }"
    aria-label="Main navigation"
  >
    <!-- Brand block -->
    <div class="sidebar-brand">
      <div class="brand-mark" aria-hidden="true">
        {{ brand ? brand.charAt(0) : 'C' }}
      </div>
      <div v-if="!sidebarCollapsed" class="brand-text">
        <span class="brand-name">{{ brand }}</span>
        <span class="brand-subtitle">{{ subtitle }}</span>
      </div>
      <button
        v-if="!sidebarCollapsed"
        class="collapse-toggle"
        @click="onToggleCollapsed"
        :aria-label="'Collapse sidebar'"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <path d="M10 4L6 8L10 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
      <button
        v-else
        class="collapse-toggle collapse-toggle--expand"
        @click="onToggleCollapsed"
        :aria-label="'Expand sidebar'"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <path d="M6 4L10 8L6 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>

    <!-- Nav groups -->
    <nav class="sidebar-nav" role="navigation">
      <template v-for="group in groupedRoutes" :key="group.name">
        <div class="nav-group">
          <span v-if="!sidebarCollapsed" class="nav-group-label">{{ group.name }}</span>
          <ul class="nav-list" role="list">
            <li v-for="route in group.routes" :key="route.path">
              <router-link
                :to="route.path"
                class="nav-item"
                :class="{ 'nav-item--active': isActive(route.path) }"
              >
                <!-- Icon (always visible) -->
                <span class="nav-icon" aria-hidden="true">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  >
                    <template v-if="route.icon">
                      <component
                        v-for="(shape, si) in route.icon"
                        :key="si"
                        :is="shape.tag"
                        v-bind="shape.attrs"
                      />
                    </template>
                  </svg>
                </span>
                <!-- Expanded: numeric code + label -->
                <span v-if="!sidebarCollapsed" class="nav-code" aria-hidden="true">{{ route.code }}</span>
                <span v-if="!sidebarCollapsed" class="nav-label">{{ route.label }}</span>
                <!-- Collapsed: tiny code under icon -->
                <span v-else class="nav-code-mini" aria-hidden="true">{{ route.code }}</span>
              </router-link>
            </li>
          </ul>
        </div>
      </template>
    </nav>

    <!-- Footer slot -->
    <div class="sidebar-footer">
      <slot name="footer" />
    </div>
  </aside>

  <!-- Mobile scrim -->
  <div
    v-if="sidebarOpen"
    class="sidebar-scrim"
    @click="onToggleDrawer"
    aria-hidden="true"
  />
</template>

<script setup>
import { inject, computed } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
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

const emit = defineEmits(['toggle-drawer', 'toggle-collapsed'])

const sidebarOpen = inject('sidebarOpen')
const sidebarCollapsed = inject('sidebarCollapsed')

const route = useRoute()

const isActive = (path) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

const onToggleDrawer = () => emit('toggle-drawer')
const onToggleCollapsed = () => emit('toggle-collapsed')

const groupedRoutes = computed(() => {
  const groups = {}
  const order = []

  for (const r of props.routes) {
    if (!groups[r.group]) {
      groups[r.group] = []
      order.push(r.group)
    }
    groups[r.group].push(r)
  }

  return order.map(name => ({ name, routes: groups[name] }))
})
</script>

<style scoped>
.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  width: var(--sidebar-w);
  background: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  overflow-x: hidden;
  transition: width var(--dur-medium) var(--ease-standard);
  flex-shrink: 0;
  z-index: 200;
}

.sidebar.collapsed {
  width: var(--sidebar-w-collapsed);
}

/* ── Brand block ─────────────────────────────────────────────── */
.sidebar-brand {
  height: var(--topbar-h);
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 0 var(--space-3);
  border-bottom: 1px solid var(--sidebar-rule);
  flex-shrink: 0;
}

.brand-mark {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  background: var(--accent);
  color: var(--accent-ink);
  font-family: var(--font-mono);
  font-weight: var(--weight-bold);
  font-size: var(--text-xs);
  display: flex;
  align-items: center;
  justify-content: center;
  text-transform: uppercase;
  letter-spacing: 0;
}

.sidebar.collapsed .sidebar-brand {
  justify-content: center;
  padding: 0;
}

.brand-text {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
  overflow: hidden;
}

.brand-name {
  font-family: var(--font-display);
  font-weight: var(--weight-bold);
  font-size: var(--text-sm);
  color: var(--ink-reverse);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: var(--tracking-tight);
}

.brand-subtitle {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--sidebar-text-muted);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.collapse-toggle {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: transparent;
  border: none;
  color: var(--sidebar-text-muted);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: color var(--dur-fast) var(--ease-standard),
              background var(--dur-fast) var(--ease-standard);
}

.collapse-toggle:hover {
  color: var(--ink-reverse);
  background: var(--sidebar-bg-hover);
}

.collapse-toggle:focus-visible {
  outline: none;
  box-shadow: var(--ring-dark);
}

/* ── Nav ─────────────────────────────────────────────────────── */
.sidebar-nav {
  flex: 1;
  padding: var(--space-3) var(--space-2);
  overflow-y: auto;
  overflow-x: hidden;
}

.nav-group {
  margin-bottom: var(--space-4);
}

.nav-group-label {
  display: block;
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  color: var(--sidebar-text-muted);
  padding: var(--space-3) var(--space-3) var(--space-2);
}

.nav-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  text-decoration: none;
  transition: background var(--dur-fast) var(--ease-standard),
              color var(--dur-fast) var(--ease-standard);
  color: var(--sidebar-text);
  outline: none;
  white-space: nowrap;
}

.nav-item:hover {
  background: var(--sidebar-bg-hover);
  color: #fff;
}

.nav-item:hover .nav-code,
.nav-item:hover .nav-code-mini {
  color: var(--accent);
}

.nav-item:hover .nav-icon {
  color: var(--accent);
}

.nav-item:focus-visible {
  box-shadow: var(--ring-dark);
}

.nav-item--active {
  background: var(--sidebar-active-bg);
  color: #fff;
}

.nav-item--active::before {
  content: '';
  position: absolute;
  left: 0;
  top: var(--space-1);
  bottom: var(--space-1);
  width: 3px;
  background: var(--accent);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}

.nav-item--active .nav-code,
.nav-item--active .nav-code-mini {
  color: var(--accent);
}

.nav-item--active .nav-icon {
  color: var(--accent);
}

/* ── Icon ──────────────────────────────────────────────────────── */
.nav-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--sidebar-text-muted);
  transition: color var(--dur-fast) var(--ease-standard);
}

.nav-icon svg {
  width: 20px;
  height: 20px;
  display: block;
}

/* ── Numeric code (expanded) ───────────────────────────────────── */
.nav-code {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--sidebar-text-muted);
  letter-spacing: var(--tracking-wider);
  width: 20px;
  flex-shrink: 0;
  transition: color var(--dur-fast) var(--ease-standard);
}

/* ── Tiny code below icon (collapsed only) ─────────────────────── */
.nav-code-mini {
  font-family: var(--font-mono);
  /* 9px: no token matches this ultra-small size; intentional literal */
  font-size: 9px;
  color: var(--sidebar-text-muted);
  letter-spacing: var(--tracking-wider);
  margin-top: var(--space-1);
  line-height: 1;
  transition: color var(--dur-fast) var(--ease-standard);
}

.nav-label {
  font-family: var(--font-body);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: inherit;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Collapsed nav items: column layout, icon + mini code centered */
.sidebar.collapsed .nav-item {
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-2) 0;
  gap: var(--space-1);
}

.sidebar.collapsed .nav-group-label {
  display: none;
}

/* ── Footer ──────────────────────────────────────────────────── */
.sidebar-footer {
  margin-top: auto;
  border-top: 1px solid var(--sidebar-rule);
  padding: var(--space-3) var(--space-2);
}

/* ── Mobile: off-canvas drawer ───────────────────────────────── */
@media (max-width: 1023px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    height: 100vh;
    transform: translateX(-100%);
    transition: transform var(--dur-medium) var(--ease-standard),
                width var(--dur-medium) var(--ease-standard);
    box-shadow: none;
    z-index: 300;
    width: var(--sidebar-w);
  }

  .sidebar.open {
    transform: translateX(0);
    box-shadow: var(--shadow-lg);
  }

  .sidebar.collapsed {
    width: var(--sidebar-w);
  }
}

.sidebar-scrim {
  display: none;
}

@media (max-width: 1023px) {
  .sidebar-scrim {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(10, 10, 10, 0.5);
    z-index: 299;
  }
}
</style>
