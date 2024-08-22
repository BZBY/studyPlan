<template>
  <q-page padding>
    <q-card v-if="planDetails" class="q-mb-md">
      <q-card-section>
        <div class="text-h4">{{ planDetails.title }}</div>
        <div class="text-body1 text-secondary">{{ planDetails.goal }}</div>
      </q-card-section>
    </q-card>

    <div v-for="week in planDetails?.weeks" :key="week.week" class="q-mb-md">
      <q-card>
        <q-card-section>
          <div class="text-h5">Week {{ week.week }}: {{ week.title }}</div>
        </q-card-section>

        <q-list>
          <q-item v-for="day in week.days" :key="day.day" class="q-mb-sm">
            <q-item-section>
              <div class="text-h6">Day {{ day.day }}: {{ day.title }}</div>
              <TaskItem
                v-for="task in day.tasks"
                :key="task.task_id"
                :task="task"
                :planId="planDetails.plan_id"
              />
              <div class="text-caption text-secondary">
                Study Time: {{ day.study_time_hours }} hours
              </div>
            </q-item-section>
          </q-item>
        </q-list>
      </q-card>
    </div>

    <!-- Supplemental Resources -->
    <q-card v-if="planDetails?.resources" class="q-mb-md">
      <q-card-section>
        <div class="text-h5">Supplemental Resources</div>

        <!-- Book Resources -->
        <div v-if="planDetails?.resources.books.length">
          <div class="text-h6">Books</div>
          <ul>
            <li v-for="book in planDetails?.resources.books" :key="book.title">
              {{ book.title }} - {{ book.author }}
            </li>
          </ul>
        </div>

        <!-- Project Resources -->
        <div v-if="planDetails?.resources.projects.length" class="q-mt-md">
          <div class="text-h6">Projects</div>
          <ul>
            <li
              v-for="project in planDetails?.resources.projects"
              :key="project.description"
            >
              <a :href="project.url" target="_blank">{{ project.description }}</a>
              - {{ project.platform }}
            </li>
          </ul>
        </div>
      </q-card-section>
    </q-card>

  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { usePlanStore } from 'stores/planStore.js'
import { useQuasar } from 'quasar'
import { useRoute } from 'vue-router'
import TaskItem from 'components/TaskItem.vue' // 引入 TaskItem 组件

const planStore = usePlanStore()
const $q = useQuasar()
const route = useRoute()
const planDetails = ref(null)

const fetchPlanDetails = async () => {
  try {
    await planStore.fetchPlanDetails(route.params.planId)
    planDetails.value = planStore.planDetails
  } catch (error) {
    $q.notify({ type: 'negative', message: 'Failed to fetch plan details.' })
  }
}

onMounted(fetchPlanDetails)
</script>

<style scoped>
.full-save-button {
  margin-top: 20px;
  width: 100%;
}
</style>
