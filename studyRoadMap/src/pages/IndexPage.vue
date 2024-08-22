<template>
  <q-page class="q-pa-md">
    <div class="row justify-between">
      <div class="text-h6">Weekly Schedule Overview</div>
      <q-btn-group>
        <q-btn label="Week 1" @click="setCurrentWeek(1)" :flat="currentWeek !== 1" />
        <q-btn label="Week 2" @click="setCurrentWeek(2)" :flat="currentWeek !== 2" />
        <q-btn label="Week 3" @click="setCurrentWeek(3)" :flat="currentWeek !== 3" />
      </q-btn-group>
    </div>

    <div class="row justify-between q-mt-md">

      <q-btn label="Base (1-3)" @click="setCurrentRange(1)" :flat="currentRange !== 1" />
      <q-btn label="Improve (4-6)" @click="setCurrentRange(2)" :flat="currentRange !== 2" />
      <q-btn label="Project Work (7)" @click="setCurrentRange(3)" :flat="currentRange !== 3" />

    <q-select
        v-model="selectedPlanId"
        :options="planOptions"
        label="Filter by Plan"
        outlined
        class="q-ml-md"
        clearable
        clear-icon="clear"
      />

    </div>

    <!-- Display a card for project work if the range is 3 -->
    <div v-if="currentRange === 3" class="q-pa-md q-gutter-md row">
      <div class="col" v-for="planId in filteredPlanIds" :key="planId">
        <div class="text-h6">{{ planId }}</div>
        <div class="q-gutter-md">
          <q-card
            v-for="task in filteredTasksByPlan(planId)"
            :key="task.task_id"
            class="my-card"
            :style="{ backgroundColor: getPlanColor(task.plan_id) , height: '200px' }"
          >
            <q-card-section>
              <q-tooltip anchor="top middle" self="bottom middle">
                <span>{{ task.content }}</span>
              </q-tooltip>
              <div class="text-h6" style="padding-top: 0%;padding-bottom: 20%">{{ task.content.slice(0, 12) }}...</div>
              <div class="text-subtitle2">{{ task.plan_id }}</div>
            </q-card-section>
            <q-separator dark></q-separator>
            <q-card-actions style="background: white">
              <q-btn flat @click="navigateToPlan(task.plan_id)">Go</q-btn>
              <q-btn
                outline
                :color="getStatusColor(task.status)"
                class="q-ml-sm cursor-pointer"
                icon="flag"
                @click="cycleTaskStatus(task)"
              >
                {{ task.status }}
              </q-btn>
            </q-card-actions>
          </q-card>
        </div>
      </div>
    </div>

    <div class="row q-mt-md">
      <div class="col" v-for="(dayTasks, index) in filteredWeekData" :key="index">
        <div class="text-h6">{{ dayNames[index] }}</div>
        <q-timeline class="q-mt-sm">
          <q-timeline-entry
            v-for="task in filteredTasks(dayTasks.tasks)"
            :key="task.task_id"
            style="min-height:180px;"
            :subtitle="task.plan_id"
            :side-color="getPlanColor(task.plan_id)"
          >
            <q-chip
              :style="{ color: getPlanColor(task.plan_id) }"
              outline
              class="q-mt-xs q-chip-content"
              style="position: relative;font-size: 13px;"
            >
              {{ task.content.slice(0, 25) }}...

            </q-chip>
            <q-btn
              flat
              @click="navigateToPlan(task.plan_id)"
            >
              {{ task.plan_title.slice(5, -5) }}
            </q-btn>

            <q-btn
              outline
              :color="getStatusColor(task.status)"
              class="q-ml-sm cursor-pointer"
              icon="flag"
              @click="cycleTaskStatus(task)"
              style="position: absolute;top:80px;right: 0px; "
            >
              {{ task.status }}
            </q-btn>
            <q-tooltip anchor="top middle" self="bottom middle">
              <span>{{ task.content }}</span>
            </q-tooltip>
          </q-timeline-entry>
        </q-timeline>
      </div>
    </div>

  </q-page>
</template>
<script setup>
import { ref, onMounted, computed } from 'vue';
import {useRoute, useRouter} from "vue-router";
import {usePlanStore} from "stores/planStore.js";
const planStore = usePlanStore();
const currentWeek = ref(1);
const currentRange = ref(1);
const weekData = ref([
  { day: 1, tasks: [] },
  { day: 2, tasks: [] },
  { day: 3, tasks: [] },
  { day: 4, tasks: [] },
  { day: 5, tasks: [] },
  { day: 6, tasks: [] },
  { day: 7, tasks: [] }
]);

const dayNames = ['First', 'Second', 'Third', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const filteredPlanIds = computed(() => {
  const ids = new Set();
  projectWorkTasks.value.forEach(task => ids.add(task.plan_id));
  return [...ids];
});
const filteredTasksByPlan = (planId) => {
  return projectWorkTasks.value.filter(task => task.plan_id === planId);
};
const fetchWeekTasks = async (weekNumber) => {
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/weeks/${weekNumber}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch tasks for week ${weekNumber}: ${response.statusText}`);
    }

    const data = await response.json();

    // Normalize the data to fit into the 7-day structure
    data.days.forEach(day => {
      while (day.day > 7) {
        day.day -= 7;
      }
      weekData.value[day.day - 1].tasks = day.tasks; // Adjust for zero-based index
    });
  } catch (error) {
    console.error(`Failed to fetch tasks for week ${weekNumber}:`, error);
  }
};
const selectedPlanId = ref(null);
const planOptions = computed(() => {
  const uniquePlanIds = new Set();
  weekData.value.forEach(day => {
    day.tasks.forEach(task => uniquePlanIds.add(task.plan_id));
  });
  return [...uniquePlanIds].map(planId => ({ label: planId, value: planId }));
});

const filteredTasks = (tasks) => {
  if (!selectedPlanId.value) return tasks;
  console.log(tasks[0].plan_id,selectedPlanId.value.value)
  return tasks.filter(task => task.plan_id === selectedPlanId.value.value);
};


const planColors = ref({});
const getPlanColor = (planId) => {

  const colors = [
    '#f14242', // Darker Red
    '#ff2a7e', // Darker Pink
    '#8600cd', // Darker Purple
    '#6e4aca', // Darker Deep Purple
    '#3550ea', // Darker Indigo
    '#00ffdf', // Darker Blue
    '#009fff', // Darker Light Blue
    '#0eeaff', // Darker Cyan
    '#92f83a', // Darker Light Green
    '#FBC02D', // Darker Yellow
    '#ddff00', // Darker Amber
  ];
  if (!planColors.value[planId]) {
    planColors.value[planId] = colors[Math.floor(Math.random() * colors.length)];
  }
  return planColors.value[planId];
};

const getStatusColor = (status) => {
  switch (status) {
    case 'Pending':
      return 'grey';
    case 'Processing':
      return 'light-blue';
    case 'Completed':
      return 'green';
    default:
      return 'black';
  }
};

const cycleTaskStatus = (task) => {
  const statusOptions = ['Pending', 'Processing', 'Completed'];
  const currentIndex = statusOptions.indexOf(task.status);
  const nextIndex = (currentIndex + 1) % statusOptions.length;
  task.status = statusOptions[nextIndex];
  planStore.updateTaskStatus(task)
};



const setCurrentWeek = (weekNumber) => {
  currentWeek.value = weekNumber;
  fetchWeekTasks(weekNumber);
};

const setCurrentRange = (range) => {
  currentRange.value = range;
};

const filteredWeekData = computed(() => {
  if (currentRange.value === 1) {
    return weekData.value.slice(0, 3).filter(day => day.tasks.length > 0);
  } else if (currentRange.value === 2) {
    return weekData.value.slice(3, 6).filter(day => day.tasks.length > 0);
  } else if (currentRange.value === 3) {
    return weekData.value.slice(6, 7).filter(day => day.tasks.length > 0);
  }
  return [];
});

const projectWorkTasks = computed(() => {
  if (currentRange.value === 3) {
    return weekData.value[6].tasks;
  }
  return [];
});
const router = useRouter();

const navigateToPlan = (planId) => {
  router.push(`/plan/${planId}`);
};

onMounted(() => {
  fetchWeekTasks(currentWeek.value); // Fetch data for the first week by default
});
</script>

<style scoped>
.q-chip-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.q-chip {
  width: 100%;
  text-align: left;
  font-size: 12px;
  margin-bottom: 12px;
}

.q-timeline {
  margin-left: 0 !important;
  margin-right: 0 !important;
}

.row {
  display: flex;
  justify-content: space-between;
}

.col {
  flex: 1;
  padding: 0 10px;
}

.bg-white {
  background-color: #ffffff !important;
}

.bg-light-blue {
  background-color: #e0f7fa !important;
}

.bg-blue-purple {
  background-color: #b39ddb !important;
}

.my-card {
  width: 100%;
  max-width: 250px;
}
</style>
