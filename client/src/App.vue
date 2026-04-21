<template>
  <AppShell
    :routes="routes"
    :brand="t('nav.companyName')"
    :subtitle="t('nav.subtitle')"
  >
    <template #topbar-right>
      <LanguageSwitcher />
      <ProfileMenu
        @show-profile-details="showProfileDetails = true"
        @show-tasks="showTasks = true"
      />
    </template>

    <template #filter>
      <FilterBar />
    </template>

    <router-view />
  </AppShell>

  <ProfileDetailsModal
    :is-open="showProfileDetails"
    @close="showProfileDetails = false"
  />

  <TasksModal
    :is-open="showTasks"
    :tasks="tasks"
    @close="showTasks = false"
    @add-task="addTask"
    @delete-task="deleteTask"
    @toggle-task="toggleTask"
  />
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import AppShell from './components/shell/AppShell.vue'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

export default {
  name: 'App',
  components: {
    AppShell,
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    // ── Nav icons: 24×24 monoline SVG shape descriptors ──────────────────────
    // Each entry is an array of { tag, attrs } objects rendered via v-for/<component>
    // in Sidebar.vue — avoids v-html and keeps template parsing safe.
    const ICONS = {
      // 01 Overview — 2×2 dashboard grid
      overview: [
        { tag: 'rect', attrs: { x: '3', y: '3', width: '8', height: '8' } },
        { tag: 'rect', attrs: { x: '13', y: '3', width: '8', height: '8' } },
        { tag: 'rect', attrs: { x: '3', y: '13', width: '8', height: '8' } },
        { tag: 'rect', attrs: { x: '13', y: '13', width: '8', height: '8' } }
      ],
      // 02 Inventory — stacked boxes
      inventory: [
        { tag: 'rect', attrs: { x: '3', y: '3', width: '8', height: '8' } },
        { tag: 'rect', attrs: { x: '13', y: '3', width: '8', height: '8' } },
        { tag: 'rect', attrs: { x: '8', y: '13', width: '8', height: '8' } }
      ],
      // 03 Orders — clipboard / document list
      orders: [
        { tag: 'rect', attrs: { x: '5', y: '4', width: '14', height: '17' } },
        { tag: 'line', attrs: { x1: '8', y1: '2', x2: '16', y2: '2' } },
        { tag: 'line', attrs: { x1: '8', y1: '2', x2: '8', y2: '6' } },
        { tag: 'line', attrs: { x1: '16', y1: '2', x2: '16', y2: '6' } },
        { tag: 'line', attrs: { x1: '8', y1: '10', x2: '16', y2: '10' } },
        { tag: 'line', attrs: { x1: '8', y1: '14', x2: '16', y2: '14' } },
        { tag: 'line', attrs: { x1: '8', y1: '18', x2: '13', y2: '18' } }
      ],
      // 04 Restocking — loop/refresh arrows
      restocking: [
        { tag: 'path', attrs: { d: 'M4 8 L4 4 L8 4' } },
        { tag: 'path', attrs: { d: 'M4 4 L20 4 L20 11' } },
        { tag: 'path', attrs: { d: 'M20 16 L20 20 L16 20' } },
        { tag: 'path', attrs: { d: 'M20 20 L4 20 L4 13' } }
      ],
      // 05 Finance — vertical bar chart
      finance: [
        { tag: 'line', attrs: { x1: '4', y1: '20', x2: '20', y2: '20' } },
        { tag: 'rect', attrs: { x: '6', y: '12', width: '3', height: '8' } },
        { tag: 'rect', attrs: { x: '11', y: '8', width: '3', height: '12' } },
        { tag: 'rect', attrs: { x: '16', y: '4', width: '3', height: '16' } }
      ],
      // 06 Demand — trend arrow up-right
      demand: [
        { tag: 'polyline', attrs: { points: '3 17 9 11 13 15 21 7' } },
        { tag: 'polyline', attrs: { points: '15 7 21 7 21 13' } }
      ],
      // 07 Reports — document with fold + lines
      reports: [
        { tag: 'path', attrs: { d: 'M6 3 L14 3 L19 8 L19 21 L6 21 Z' } },
        { tag: 'polyline', attrs: { points: '14 3 14 8 19 8' } },
        { tag: 'line', attrs: { x1: '9', y1: '13', x2: '16', y2: '13' } },
        { tag: 'line', attrs: { x1: '9', y1: '17', x2: '16', y2: '17' } }
      ]
    }

    // Routes array as computed so it reacts to locale changes
    const routes = computed(() => [
      { path: '/',           label: t('nav.overview'),       group: 'OPERATIONS', code: '01', icon: ICONS.overview },
      { path: '/inventory',  label: t('nav.inventory'),      group: 'OPERATIONS', code: '02', icon: ICONS.inventory },
      { path: '/orders',     label: t('nav.orders'),         group: 'OPERATIONS', code: '03', icon: ICONS.orders },
      { path: '/restocking', label: t('nav.restocking'),     group: 'OPERATIONS', code: '04', icon: ICONS.restocking },
      { path: '/spending',   label: t('nav.finance'),        group: 'ANALYSIS',   code: '05', icon: ICONS.finance },
      { path: '/demand',     label: t('nav.demandForecast'), group: 'ANALYSIS',   code: '06', icon: ICONS.demand },
      { path: '/reports',    label: 'Reports',               group: 'ANALYSIS',   code: '07', icon: ICONS.reports },
    ])

    return {
      t,
      routes,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>
