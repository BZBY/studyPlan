<template>
  <q-dialog v-model="localVisible" maximized>
    <q-card>
      <q-card-section>
        <div class="text-h6">AI Conversation</div>
      </q-card-section>
      <q-separator />
      <q-card-section class="input-section" ref="inputSection">
        <div class="q-pa-md row justify-center">
          <div class="chat-container" ref="chatContainer">
            <q-chat-message
              v-for="(message, index) in combinedMessages"
              :key="index"
              :text="[message.text]"
              :sent="message.sent"
              :bg-color="message.sent ? 'primary' : 'amber'"
              text-color="white"
            >
              <template v-slot:name>{{ message.sent ? 'AI' : 'Me' }}</template>
              <template v-slot:stamp>{{ formatTimestamp(message.timestamp) }}</template>
              <template v-slot:avatar>
                <img
                  class="q-message-avatar"
                  :class="message.sent ? 'q-message-avatar--sent' : 'q-message-avatar--received'"
                  :src="message.sent ? 'https://avatars.githubusercontent.com/u/31246794?v=4' : 'https://avatars.githubusercontent.com/u/43779380?v=4'"
                />
              </template>
            </q-chat-message>
            <div v-if="loading" class="row justify-center q-my-sm">
              <q-spinner-dots color="primary" size="40px"/>
            </div>
            <div class="spacer"></div>
          </div>
        </div>
      </q-card-section>
      <q-separator />
      <q-card-section class="input-section" ref="inputSection">
        <q-input
          v-model="newComment"
          label="Your Comment"
          dense
          type="textarea"
          autogrow
          @input="adjustChatHeight"
          @keyup.enter="submitCommentAndGetFeedback"
        />
        <div class="q-mt-sm q-gutter-sm row justify-between">
          <q-btn label="Submit" color="primary" @click="submitCommentAndGetFeedback" />
          <q-btn label="Close" color="negative" @click="emitCloseDialog" />
        </div>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick } from 'vue'
import {useQuasar} from "quasar";
import {usePlanStore} from "stores/planStore.js";

const props = defineProps({
  isVisible: Boolean,
  task: Object,
  planId: String
})

const emit = defineEmits(['update:isVisible'])

const localVisible = ref(props.isVisible)

watch(() => props.isVisible, (newValue) => {
  localVisible.value = newValue
})

watch(localVisible, (newValue) => {
  emit('update:isVisible', newValue)
})

const newComment = ref('')
const loading = ref(false)
const chatContainer = ref(null)
const inputSection = ref(null)
const $q = useQuasar()
const planStore = usePlanStore()
const taskState = reactive({
  content: props.task.content,
  status: props.task.status,
  task_id: props.task.task_id || '',  // Ensure task_id is present
  comments: Array.isArray(props.task.comments) ? [...props.task.comments] : [],
  feedbacks: Array.isArray(props.task.feedbacks) ? [...props.task.feedbacks] : []
});
const combinedMessages = computed(() => {
  const messages = []
  const comments = taskState.comments
  const feedbacks = taskState.feedbacks

  const maxLength = Math.max(comments.length, feedbacks.length)

  for (let i = 0; i < maxLength; i++) {
    if (i < comments.length) {
      messages.push({
        text: comments[i].comment,
        timestamp: comments[i].timestamp,
        sent: false
      })
    }
    if (i < feedbacks.length) {
      messages.push({
        text: feedbacks[i].feedback,
        timestamp: feedbacks[i].timestamp,
        sent: true
      })
    }
  }

  return messages
})

const formatTimestamp = (timestamp) => {
  const date = new Date(timestamp)
  return `${date.getHours()}:${date.getMinutes()}`
}

const scrollToBottom = () => {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

const adjustChatHeight = () => {
  nextTick(() => {
    if (chatContainer.value && inputSection.value) {
      const inputHeight = inputSection.value.offsetHeight
      chatContainer.value.style.paddingBottom = `${inputHeight + 20}px`
      scrollToBottom()
    }
  })
}

const submitCommentAndGetFeedback = async () => {
  if (!newComment.value) {
    $q.notify({ type: 'warning', message: 'Comment cannot be empty.' })
    return
  }

  try {
    loading.value = true

    await planStore.submitComment(props.planId, props.task.task_id, newComment.value)
    taskState.comments.push({
      comment: newComment.value,
      timestamp: new Date().toISOString()
    })
    $q.notify({ type: 'positive', message: 'Comment submitted successfully.' })





    const feedback = await planStore.getFeedback(props.planId, props.task.task_id, newComment.value)
    taskState.feedbacks.push({
      feedback: feedback.feedback,
      timestamp: new Date().toISOString()
    })

    // 清空输入框
    newComment.value = ''
    $q.notify({ type: 'positive', message: 'AI feedback retrieved successfully.' })



    loading.value = false

    scrollToBottom()

  } catch (error) {
    loading.value = false
    $q.notify({ type: 'negative', message: 'Failed to submit comment or get AI feedback.' })
  }
}

const emitCloseDialog = () => {
  localVisible.value = false
}
</script>

<style scoped>
.chat-container {
  width: 100%;
  max-width: 80%;
  margin: 0 auto;
  overflow-y: scroll; /* Ensure the container is scrollable */
  max-height: calc(100vh - 150px); /* Adjust max-height for better scrolling */
  padding-bottom: 80px;
  box-sizing: border-box;
  transition: padding-bottom 0.2s ease;
  scrollbar-width: none; /* For Firefox */
  -ms-overflow-style: none;  /* For Internet Explorer and Edge */
}

.chat-container::-webkit-scrollbar {
  display: none; /* For Chrome, Safari, and Opera */
}

.input-section {
  background-color: white;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px;
  z-index: 1000;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
  transition: height 0.2s ease;
}

.q-chat-message {
  margin-bottom: 12px;
}

.spacer {
  height: 20px;
}
</style>
