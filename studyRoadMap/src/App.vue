<template>
  <router-view />
</template>

<script setup>
import { usePlanStore } from 'src/stores/planStore'
import { onMounted } from 'vue'

// Ensure the store is used after Pinia is initialized
const planStore = usePlanStore()

onMounted(() => {
  planStore.fetchPlans()
})
</script>
