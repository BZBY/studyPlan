<template>
  <q-layout view="hHh lpR fFf">
    <q-header>
      <q-toolbar>
        <q-btn flat round dense icon="menu" @click="toggleDrawer" aria-label="Toggle Sidebar" />
        <q-toolbar-title>Teaching Plan Management</q-toolbar-title>
        <q-btn flat round dense icon="home" @click="goHome" aria-label="Go Home" />
      </q-toolbar>
    </q-header>

    <PlanSidebar :drawer-open="drawerOpen" @close="drawerOpen = false" />


  </q-layout>
</template>

<script setup>
import {ref} from 'vue'
import {useRouter} from 'vue-router'
import PlanSidebar from 'src/components/PlanSidebar.vue'

const drawerOpen = ref(false)
const router = useRouter()

const toggleDrawer = () => {
  drawerOpen.value = !drawerOpen.value
}

const goHome = () => {
  router.push('/')
}
</script>

<style scoped>
.with-sidebar {
  margin-left: 250px;
  transition: margin-left 0.3s ease; /* Animation for main content shift */
}
</style>
