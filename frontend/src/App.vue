<script setup>
import { computed, ref } from "vue";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8001";
const initialAssistantMessage = {
  id: "welcome",
  role: "assistant",
  text: "??????????????????????????????????",
};

function createSessionId() {
  return `session-${Math.random().toString(36).slice(2, 10)}`;
}

const sessionId = ref(createSessionId());
const draft = ref("");
const isLoading = ref(false);
const errorMessage = ref("");
const messages = ref([{ ...initialAssistantMessage }]);

const canSend = computed(() => draft.value.trim().length > 0 && !isLoading.value);

const suggestions = [
  "???????",
  "?? 300 ?????????",
  "????????????",
  "???????????",
];

async function sendMessage(text) {
  const content = text.trim();
  if (!content || isLoading.value) {
    return;
  }

  errorMessage.value = "";
  messages.value.push({
    id: `user-${Date.now()}`,
    role: "user",
    text: content,
  });
  draft.value = "";
  isLoading.value = true;

  try {
    const response = await fetch(`${apiBaseUrl}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text: content,
        session_id: sessionId.value,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    messages.value.push({
      id: `assistant-${Date.now()}`,
      role: "assistant",
      text: data.text || "?????????????????",
    });
  } catch (error) {
    console.error(error);
    errorMessage.value = "????????????????????";
  } finally {
    isLoading.value = false;
  }
}

function handleSubmit() {
  void sendMessage(draft.value);
}

function useSuggestion(text) {
  draft.value = text;
  void sendMessage(text);
}

function startNewChat() {
  sessionId.value = createSessionId();
  draft.value = "";
  errorMessage.value = "";
  messages.value = [{ ...initialAssistantMessage }];
}
</script>

<template>
  <div class="page-shell">
    <aside class="hero-panel">
      <p class="eyebrow">Foot Bath Copilot</p>
      <h1>???????</h1>
      <p class="hero-copy">
        ?? ChatGPT ?????????????????????????? LangChain RAG ????
      </p>
      <div class="hero-grid">
        <article>
          <span>????</span>
          <strong>LangChain + DeepSeek</strong>
        </article>
        <article>
          <span>????</span>
          <strong>Chroma ????</strong>
        </article>
        <article>
          <span>????</span>
          <strong>?? /chat ??</strong>
        </article>
        <article>
          <span>????</span>
          <strong>???????</strong>
        </article>
      </div>
    </aside>

    <main class="chat-panel">
      <header class="chat-header">
        <div>
          <h2>???????</h2>
          <p>??????????????</p>
        </div>
        <div class="header-actions">
          <button
            data-testid="new-chat"
            class="ghost-button"
            type="button"
            :disabled="isLoading"
            @click="startNewChat"
          >
            ????
          </button>
          <span class="status-pill" :class="{ busy: isLoading }">
            {{ isLoading ? "???" : "???" }}
          </span>
        </div>
      </header>

      <section class="suggestions-row">
        <button
          v-for="item in suggestions"
          :key="item"
          class="suggestion-chip"
          type="button"
          @click="useSuggestion(item)"
        >
          {{ item }}
        </button>
      </section>

      <section class="message-list">
        <article
          v-for="message in messages"
          :key="message.id"
          class="message-card"
          :class="message.role"
        >
          <span class="message-role">{{ message.role === "assistant" ? "??" : "?" }}</span>
          <p>{{ message.text }}</p>
        </article>

        <article v-if="isLoading" class="message-card assistant loading-card">
          <span class="message-role">??</span>
          <p>????????...</p>
        </article>
      </section>

      <p v-if="errorMessage" class="error-banner">{{ errorMessage }}</p>

      <form class="composer" @submit.prevent="handleSubmit">
        <textarea
          v-model="draft"
          rows="3"
          placeholder="???????????? 300 ??????????"
        />
        <div class="composer-actions">
          <span>???????????????</span>
          <button type="submit" :disabled="!canSend">??</button>
        </div>
      </form>
    </main>
  </div>
</template>
