<template>
  <q-card class="q-mb-sm task-card" :class="taskStatusClass" flat bordered>
    <q-card-section>
      <div class="row justify-between items-center">
        <div class="row items-center">
          <q-icon :name="isEditing ? 'close' : 'edit'" class="q-mr-sm cursor-pointer" @click="toggleTaskEdit" />
          <span>{{ taskState.content }}</span>
        </div>
        <div class="row items-center">
          <q-chip
            outline
            :color="taskStatusColor"
            class="q-ml-sm cursor-pointer"
            icon="flag"

          >
           <a @click="cycleTaskStatus"> {{ taskState.status }}</a>
          </q-chip>

          <q-btn flat icon="chat" @click="showAiChatDialog = true" />
        </div>
      </div>
    </q-card-section>

    <q-slide-transition>
      <q-card v-if="isEditing" flat bordered class="q-pa-md q-mt-md">
        <q-form @submit.prevent="submitEdit">
          <q-input
            v-model="taskState.content"
            label="Edit Task Content"
            filled
            dense
            type="textarea"
            autogrow
            class="q-mb-md"
          />
          <q-select
            v-model="taskState.status"
            :options="statusOptions"
            label="Task Status"
            filled
            dense
            class="q-mb-md"
          />
          <div class="row justify-between">
            <q-btn label="Submit" color="primary" type="submit" />
            <q-btn label="Cancel" flat color="negative" @click="cancelEdit" />
          </div>
        </q-form>
      </q-card>
    </q-slide-transition>

    <AiChatDialog v-model:isVisible="showAiChatDialog" :task="taskState" :plan-id="props.planId" />
  </q-card>
</template>

<script setup>
import {ref, reactive, watch, computed} from 'vue'
import {useQuasar} from 'quasar'
import AiChatDialog from 'src/components/AiChatDialog.vue'
import {usePlanStore} from 'src/stores/planStore.js'

const props = defineProps({
  task: Object,
  planId: String
})

const taskState = reactive({
  content: props.task.content,
  status: props.task.status || 'Pending',  // Default to 'Pending'
  task_id: props.task.task_id || '',
  comments: Array.isArray(props.task.comments) ? [...props.task.comments] : [],
  feedbacks: Array.isArray(props.task.feedbacks) ? [...props.task.feedbacks] : []
})

watch(() => props.task, (newTask) => {
  taskState.content = newTask.content
  taskState.status = newTask.status || 'Pending'
  taskState.task_id = newTask.task_id || ''  // Update task_id
  taskState.comments = Array.isArray(newTask.comments) ? [...newTask.comments] : []
  taskState.feedbacks = Array.isArray(newTask.feedbacks) ? [...newTask.feedbacks] : []
}, {deep: true})

const isEditing = ref(false)
const showAiChatDialog = ref(false)

const statusOptions = ['Pending', 'Processing', 'Completed']

const taskStatusClass = computed(() => {
  switch (taskState.status) {
    case 'Pending':
      return 'bg-white'
    case 'Processing':
      return 'bg-light-blue'
    case 'Completed':
      return 'bg-blue-purple'
    default:
      return ''
  }
})

const taskStatusColor = computed(() => {
  switch (taskState.status) {
    case 'Pending':
      return 'grey'
    case 'Processing':
      return 'light-blue'
    case 'Completed':
      return 'blue-purple'
    default:
      return 'grey'
  }
})

const cycleTaskStatus = () => {
  const currentIndex = statusOptions.indexOf(taskState.status)
  const nextIndex = (currentIndex + 1) % statusOptions.length
  taskState.status = statusOptions[nextIndex]
  submitEdit();
}

const toggleTaskEdit = () => {
  isEditing.value = !isEditing.value
}

const $q = useQuasar()
const planStore = usePlanStore()

const submitEdit = async () => {
  try {
    await planStore.editTask(props.planId, taskState.task_id, taskState.status, taskState.content)
    isEditing.value = false
    $q.notify({type: 'positive', message: 'Task edited successfully.'})
  } catch (error) {
    $q.notify({type: 'negative', message: 'Failed to edit task.'})
  }
}

const cancelEdit = () => {
  taskState.content = props.task.content
  isEditing.value = false
}
</script>

<style scoped>
.bg-white {
  background-color: #ffffff !important;
}

.bg-light-blue {
  background-color: #e0f7fa !important; /* Light Blue */
}

.bg-blue-purple {
  background-color: #b39ddb !important; /* Blue with a hint of purple */
}

.task-card {
  border: 1px solid #e0e0e0; /* Light grey border for better separation */
  border-radius: 8px; /* Slight rounding of the corners for a modern look */
}

.q-mr-sm {
  margin-right: 8px;
}

.q-ml-sm {
  margin-left: 8px;
}

.row {
  display: flex;
  align-items: center;
}

.q-btn {
  font-size: 14px;
}

.q-chat-message {
  margin-bottom: 12px;
}

.q-gutter-sm {
  margin-top: 16px;
}
</style>
