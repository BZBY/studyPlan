<template>
  <q-page class="q-pa-md">
    <div>
      <input type="file" @change="handleFileUpload" />
      <div v-if="tasks.length">
        <h3>任务列表</h3>
        <ul>
          <li v-for="(task, index) in tasks" :key="index">
            <h4 @click="selectTask(index)">{{ task.title }}</h4>
            <ul>
              <li v-for="(subtask, subIndex) in task.subtasks" :key="subIndex">
                {{ subtask }}
              </li>
            </ul>
          </li>
        </ul>
      </div>
      <div v-if="selectedTask">
        <h3>{{ selectedTask.title }}</h3>
        <ul>
          <li v-for="(subtask, index) in selectedTask.subtasks" :key="index">
            {{ subtask }}
          </li>
        </ul>
        <textarea v-model="comment" placeholder="写评论..." class="q-mt-md q-pa-md" rows="4"></textarea>
        <q-btn @click="submitComment" color="primary" class="q-mt-md">提交评论</q-btn>
        <div v-if="aiFeedback" class="q-mt-md">
          <h4>AI 反馈</h4>
          <p>{{ aiFeedback }}</p>
        </div>
        <div v-if="aiSuggestions" class="q-mt-md">
          <h4>AI 建议</h4>
          <p>{{ aiSuggestions }}</p>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import {ref, onMounted, watch} from 'vue'
import {useRoute} from 'vue-router'
import axios from 'axios'

const tasks = ref([])
const selectedTask = ref(null)
const comment = ref('')
const aiFeedback = ref('')
const aiSuggestions = ref('')
const route = useRoute()

const fetchTasks = async (schemeId) => {
  const response = await axios.get(`http://127.0.0.1:8000/api/schemes/${schemeId}/tasks`)
  tasks.value = response.data.tasks
}

const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  const reader = new FileReader()
  reader.onload = async (e) => {
    const content = e.target.result
    await saveMarkdown(content)
    parseMarkdown(content)
  }
  reader.readAsText(file)
}

const saveMarkdown = async (content) => {
  const schemeId = route.params.id
  await axios.post('http://127.0.0.1:8000/api/save_markdown', {content, id: schemeId})
}

const parseMarkdown = (content) => {
  const lines = content.split('\n')
  let currentTask = null

  lines.forEach((line) => {
    if (line.startsWith('### ')) {
      if (currentTask) tasks.value.push(currentTask)
      currentTask = {title: line.replace('### ', ''), subtasks: []}
    } else if (currentTask && line.startswith('- ')) {
      currentTask.subtasks.push(line.replace('- ', ''))
    }
  })

  if (currentTask) tasks.value.push(currentTask)
}

const selectTask = (index) => {
  selectedTask.value = tasks.value[index]
}

const submitComment = async () => {
  const markdownContent = await axios.get('http://127.0.0.1:8000/api/get_markdown')
  const updatedContent = await updateTeachingContent(comment.value, markdownContent.data.content)
  const feedback = await getAIFeedback(comment.value)
  aiFeedback.value = updatedContent
  aiSuggestions.value = feedback
}

const updateTeachingContent = async (commentContent, markdownContent) => {
  const response = await axios.post('http://127.0.0.1:8000/api/chat', {
    model: 'llama3.1',
    messages: [
      {role: 'user', content: commentContent},
      {role: 'system', content: markdownContent}
    ]
  });
  return response.data.response;
}

const getAIFeedback = async (commentContent) => {
  const response = await axios.post('http://127.0.0.1:8000/api/chat', {
    model: 'llama3.1',
    messages: [{role: 'user', content: commentContent}]
  });
  return response.data.response;
}

watch(() => route.params.id, (id) => {
  if (id) fetchTasks(id)
})

onMounted(() => {
  if (route.params.id) fetchTasks(route.params.id)
})
</script>

<style>
textarea {
  width: 100%;
  resize: none;
}
</style>
