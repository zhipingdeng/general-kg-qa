<template>
  <div class="flex flex-col h-screen bg-gray-50">
    <Header />
    
    <div class="flex-1 overflow-hidden flex flex-col">
      <!-- Welcome Section (when no messages) -->
      <div v-if="messages.length === 0" class="flex-1 flex items-center justify-center p-4">
        <div class="text-center max-w-2xl">
          <div class="w-20 h-20 bg-gradient-to-br from-primary-500 to-purple-500 rounded-3xl flex items-center justify-center mx-auto mb-6">
            <svg class="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 class="text-3xl font-bold text-gray-900 mb-3">通用百科知识问答</h2>
          <p class="text-gray-500 mb-8 text-lg">基于知识图谱的智能问答，输入任何问题开始探索</p>
          
          <!-- Recommended Questions -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-xl mx-auto">
            <button
              v-for="q in recommendedQuestions"
              :key="q"
              @click="sendMessage(q)"
              class="p-4 bg-white rounded-xl border border-gray-200 hover:border-primary-300 hover:shadow-md transition-all text-left text-sm text-gray-700 hover:text-primary-600"
            >
              <svg class="w-4 h-4 text-primary-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              {{ q }}
            </button>
          </div>
        </div>
      </div>

      <!-- Chat Messages -->
      <div v-else ref="chatContainer" class="flex-1 overflow-y-auto p-4 space-y-4">
        <div
          v-for="(msg, idx) in messages"
          :key="idx"
          class="flex"
          :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
        >
          <!-- Assistant Avatar -->
          <div v-if="msg.role === 'assistant'" class="flex-shrink-0 mr-3">
            <div class="w-8 h-8 bg-gradient-to-br from-primary-500 to-purple-500 rounded-full flex items-center justify-center">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
          </div>

          <!-- Message Bubble -->
          <div
            class="max-w-[70%] px-4 py-3"
            :class="msg.role === 'user' ? 'bubble-user' : 'bubble-assistant'"
          >
            <div class="whitespace-pre-wrap">{{ msg.content }}</div>
            
            <!-- Entities -->
            <div v-if="msg.entities && msg.entities.length > 0" class="mt-3 pt-3 border-t border-gray-200/50">
              <div class="text-xs text-gray-500 mb-1">识别到的实体：</div>
              <div class="flex flex-wrap gap-1">
                <span v-for="entity in msg.entities" :key="entity" class="entity-tag">
                  {{ entity }}
                </span>
              </div>
            </div>
          </div>

          <!-- User Avatar -->
          <div v-if="msg.role === 'user'" class="flex-shrink-0 ml-3">
            <div class="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
              <span class="text-sm font-medium text-primary-700">
                {{ authStore.user?.username?.charAt(0).toUpperCase() }}
              </span>
            </div>
          </div>
        </div>

        <!-- Loading Indicator -->
        <div v-if="loading" class="flex justify-start">
          <div class="flex-shrink-0 mr-3">
            <div class="w-8 h-8 bg-gradient-to-br from-primary-500 to-purple-500 rounded-full flex items-center justify-center">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
          </div>
          <div class="bubble-assistant px-4 py-3">
            <div class="flex space-x-2">
              <div class="w-2 h-2 bg-gray-400 rounded-full bounce-dot" />
              <div class="w-2 h-2 bg-gray-400 rounded-full bounce-dot" />
              <div class="w-2 h-2 bg-gray-400 rounded-full bounce-dot" />
            </div>
          </div>
        </div>
      </div>

      <!-- Input Area -->
      <div class="border-t border-gray-200 bg-white p-4">
        <form @submit.prevent="sendMessage(inputText)" class="flex space-x-3 max-w-4xl mx-auto">
          <input
            v-model="inputText"
            type="text"
            placeholder="输入您的问题..."
            :disabled="loading"
            class="flex-1 px-4 py-3 border border-gray-200 rounded-xl focus:border-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            :disabled="!inputText.trim() || loading"
            class="btn-primary text-white px-6 py-3 rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { qaApi } from '@/api/qa'
import type { ChatMessage } from '@/types'
import Header from '@/components/Header.vue'

const authStore = useAuthStore()
const messages = ref<ChatMessage[]>([])
const inputText = ref('')
const loading = ref(false)
const chatContainer = ref<HTMLElement>()

const recommendedQuestions = [
  '红色食品是什么？',
  '大龙湫在哪里？',
  '什么是人工智能？',
  '太阳系有哪些行星？'
]

async function sendMessage(text: string) {
  if (!text.trim() || loading.value) return
  
  const question = text.trim()
  inputText.value = ''
  
  // Add user message
  messages.value.push({
    role: 'user',
    content: question,
    timestamp: Date.now()
  })
  
  // Scroll to bottom
  await nextTick()
  scrollToBottom()
  
  // Send to API
  loading.value = true
  try {
    const result = await qaApi.ask({ question })
    messages.value.push({
      role: 'assistant',
      content: result.answer,
      entities: result.entities,
      timestamp: Date.now()
    })
  } catch (e: any) {
    messages.value.push({
      role: 'assistant',
      content: '抱歉，处理您的问题时出现了错误，请稍后重试。',
      timestamp: Date.now()
    })
  } finally {
    loading.value = false
    await nextTick()
    scrollToBottom()
  }
}

function scrollToBottom() {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

onMounted(() => {
  // Focus input on mount
  const input = document.querySelector('input[type="text"]') as HTMLInputElement
  input?.focus()
})
</script>
