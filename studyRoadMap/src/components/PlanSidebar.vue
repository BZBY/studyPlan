<template>
  <q-layout view="hHh lpR fFf">
    <q-header>
      <q-toolbar>
        <q-btn flat icon="menu" @click="toggleDrawer" />
        <q-toolbar-title>Teaching Plan Management</q-toolbar-title>
      </q-toolbar>
    </q-header>

    <q-drawer
      v-model="localDrawerOpen"
      show-if-above
      side="left"
      bordered
      :overlay="overlay"
      @close="closeDrawer"
      content-class="animated-sidebar"
      class="q-pa-md"
    >
      <q-scroll-area style="height: 100%;">
        <q-list>
          <q-item clickable @click="goHome">
            <q-item-section>
              <q-icon name="home" />
              <q-item-label>Home</q-item-label>
            </q-item-section>
          </q-item>

          <q-item-label header>Plans</q-item-label>
          <q-item v-for="plan in plans" :key="plan.plan_id" clickable @click="selectPlan(plan)">
            <q-item-section>{{ plan.title }}</q-item-section>
          </q-item>

          <q-item clickable @click="showAddPlanDialog = true">
            <q-item-section>
              <q-icon name="add" />
              <q-item-label>Add New Plan</q-item-label>
            </q-item-section>
          </q-item>

          <q-item v-if="currentPlan" clickable @click="deleteCurrentPlan">
            <q-item-section>
              <q-icon name="delete" />
              <q-item-label>Delete Current Plan</q-item-label>
            </q-item-section>
          </q-item>
        </q-list>
      </q-scroll-area>

      <!-- Add Plan Dialog -->
      <q-dialog v-model="showAddPlanDialog">
        <q-card>
          <q-card-section>
            <q-input v-model="newPlanJson" label="Plan JSON" type="textarea" />
          </q-card-section>
          <q-card-actions align="right">
            <q-btn label="Add" color="primary" @click="addPlan" />
            <q-btn label="Cancel" flat @click="showAddPlanDialog = false" />
          </q-card-actions>
        </q-card>
      </q-dialog>
    </q-drawer>

    <q-page-container :class="{ 'collapsed': !localDrawerOpen }" class="content-container">
      <router-view :key="$route.fullPath" />
    </q-page-container>
  </q-layout>
</template>

<script setup>
import {ref, computed, watch} from 'vue';
import {usePlanStore} from 'src/stores/planStore';
import {useRouter, useRoute} from 'vue-router';

const props = defineProps({
  drawerOpen: Boolean,
});

const emit = defineEmits(['close']);

const localDrawerOpen = ref(props.drawerOpen);
const showAddPlanDialog = ref(false);
const newPlanJson = ref('');
const planStore = usePlanStore();
const router = useRouter();
const route = useRoute();

const plans = computed(() => planStore.plans);
const currentPlan = ref(null);

planStore.fetchPlans();

watch(() => route.params.plan_id, (newPlanId) => {
  currentPlan.value = plans.value.find(plan => plan.plan_id === newPlanId) || null;
});

watch(() => props.drawerOpen, (newVal) => {
  localDrawerOpen.value = newVal;
});

const overlay = computed(() => window.innerWidth < 1024);

const closeDrawer = () => {
  emit('close');
};

const goHome = () => {
  closeDrawer();
  router.push('/');
};

const addPlan = async () => {
  try {
    const parsedJson = JSON.parse(newPlanJson.value);
    await planStore.addPlan(parsedJson);
    showAddPlanDialog.value = false;
    newPlanJson.value = '';
  } catch (error) {
    console.error('Failed to add plan:', error);
    alert('Invalid JSON format');
  }
};

const deleteCurrentPlan = async () => {
  if (currentPlan.value) {
    try {
      await planStore.deletePlan(currentPlan.value.plan_id);
      router.push('/');
      planStore.fetchPlans(); // Refresh the plans after deletion
    } catch (error) {
      console.error('Failed to delete plan:', error);
    }
  }
};

const selectPlan = (plan) => {
  currentPlan.value = plan;
  router.push(`/plan/${plan.plan_id}`);
  if (window.innerWidth < 1024) {
    closeDrawer();
  }
};

const toggleDrawer = () => {
  localDrawerOpen.value = !localDrawerOpen.value;
};

currentPlan.value = plans.value.find(plan => plan.plan_id === route.params.plan_id) || null;
</script>

<style scoped>
.animated-sidebar {
  transition: transform 0.3s ease-in-out; /* Smooth transition for the sidebar */
  border-right: 2px solid #ddd; /* Add right border to sidebar */
}

.content-container {
  transition: margin-left 0.3s ease-in-out, width 0.3s ease-in-out; /* Smooth transition for the main content area */
  margin-left: 100px; /* Default margin when the sidebar is open */
  overflow-y: auto; /* Independent scrolling for the content */
  height: calc(100vh - 64px); /* Ensure full height minus header */
}

.collapsed {
  margin-left: 0 !important; /* Adjust margin when the sidebar is collapsed */
}

.q-drawer {
  width: 100px;
}

.q-drawer.collapsed {
  width: 0;
}

@media (max-width: 1024px) {
  .content-container {
    margin-left: 0; /* No margin when the sidebar is overlaying the content */
  }
}
</style>
