
<script setup>
import { computed, ref } from "vue";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8001";
const welcomeText = "我可以帮你解答泡脚桶产品问题，比如容量、恒温、按摩、预算和使用人群。";

function createSessionId() {
  return `session-${Math.random().toString(36).slice(2, 10)}`;
}

function createWelcomeMessage() {
  return {
    id: `assistant-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
    role: "assistant",
    text: welcomeText,
  };
}

function createSession(label = "新对话") {
  return {
    id: createSessionId(),
    title: label,
    preview: welcomeText,
    updatedAt: Date.now(),
    messages: [createWelcomeMessage()],
  };
}

const draft = ref("");
const isLoading = ref(false);
const errorMessage = ref("");
const sessions = ref([createSession()]);
const currentSessionId = ref(sessions.value[0].id);

const suggestions = [
  "泡脚桶怎么选？",
  "预算 300 元左右买什么类型？",
  "老人使用更看重哪些功能？",
  "恒温和按摩哪个更重要？",
];

const currentSession = computed(() => {
  return sessions.value.find((session) => session.id === currentSessionId.value) ?? sessions.value[0];
});

const canSend = computed(() => draft.value.trim().length > 0 && !isLoading.value);

function updateSession(sessionId, updater) {
  sessions.value = sessions.value.map((session) => {
    if (session.id !== sessionId) {
      return session;
    }
    return updater(session);
  });
}

function reorderSessions(sessionId) {
  const target = sessions.value.find((session) => session.id === sessionId);
  if (!target) {
    return;
  }
  sessions.value = [target, ...sessions.value.filter((session) => session.id !== sessionId)];
}

function summarizeTitle(text) {
  return text.length > 18 ? `${text.slice(0, 18)}...` : text;
}

async function sendMessage(text) {
  const content = text.trim();
  if (!content || isLoading.value) {
    return;
  }

  const sessionId = currentSessionId.value;
  errorMessage.value = "";
  draft.value = "";
  isLoading.value = true;

  updateSession(sessionId, (session) => ({
    ...session,
    title: session.title === "新对话" ? summarizeTitle(content) : session.title,
    preview: content,
    updatedAt: Date.now(),
    messages: [
      ...session.messages,
      {
        id: `user-${Date.now()}`,
        role: "user",
        text: content,
      },
    ],
  }));
  reorderSessions(sessionId);

  try {
    const response = await fetch(`${apiBaseUrl}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text: content,
        session_id: sessionId,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    const answer = data.text || "暂时没有拿到有效回复，请稍后再试。";
    updateSession(sessionId, (session) => ({
      ...session,
      preview: answer,
      updatedAt: Date.now(),
      messages: [
        ...session.messages,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          text: answer,
        },
      ],
    }));
    reorderSessions(sessionId);
  } catch (error) {
    console.error(error);
    errorMessage.value = "连接机器人失败，请确认本地服务已经启动。";
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
  const session = createSession();
  sessions.value = [session, ...sessions.value];
  currentSessionId.value = session.id;
  draft.value = "";
  errorMessage.value = "";
}

function switchSession(sessionId) {
  currentSessionId.value = sessionId;
  errorMessage.value = "";
}
</script>

<template>
  <div class="page-shell">
    <aside class="hero-panel">
      <div>
        <p class="eyebrow">Foot Bath Copilot</p>
        <h1>泡脚桶客服助手</h1>
        <p class="hero-copy">
          类似 ChatGPT 的本地客服界面，面向泡脚桶产品咨询，直接连接你当前的 LangChain RAG 机器人。
        </p>
      </div>

      <div class="hero-grid">
        <article>
          <span>接入能力</span>
          <strong>LangChain + DeepSeek</strong>
        </article>
        <article>
          <span>知识底座</span>
          <strong>Chroma 向量检索</strong>
        </article>
        <article>
          <span>交互方式</span>
          <strong>本地 /chat 问答</strong>
        </article>
        <article>
          <span>会话体验</span>
          <strong>多轮上下文记忆</strong>
        </article>
      </div>
    </aside>

    <main class="chat-panel">
      <header class="chat-header">
        <div>
          <h2>泡脚桶客服助手</h2>
          <p>我可以帮你解答泡脚桶产品问题</p>
        </div>
        <div class="header-actions">
          <button
            data-testid="new-chat"
            class="ghost-button"
            type="button"
            :disabled="isLoading"
            @click="startNewChat"
          >
            新建对话
          </button>
          <span class="status-pill" :class="{ busy: isLoading }">
            {{ isLoading ? "思考中" : "已连接" }}
          </span>
        </div>
      </header>

      <div class="chat-body">
        <aside class="history-panel">
          <div class="history-header">
            <h3>历史会话</h3>
            <span>{{ sessions.length }} 个会话</span>
          </div>

          <div class="history-list" data-testid="history-list">
            <button
              v-for="session in sessions"
              :key="session.id"
              data-testid="history-item"
              type="button"
              class="history-item"
              :class="{ active: session.id === currentSession.id }"
              @click="switchSession(session.id)"
            >
              <strong>{{ session.title }}</strong>
              <span>{{ session.preview }}</span>
            </button>
          </div>
        </aside>

        <section class="chat-column">
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
              v-for="message in currentSession.messages"
              :key="message.id"
              class="message-card"
              :class="message.role"
            >
              <span class="message-role">{{ message.role === "assistant" ? "助手" : "你" }}</span>
              <p>{{ message.text }}</p>
            </article>

            <article v-if="isLoading" class="message-card assistant loading-card">
              <span class="message-role">助手</span>
              <p>正在思考，请稍等...</p>
            </article>
          </section>

          <p v-if="errorMessage" class="error-banner">{{ errorMessage }}</p>

          <form class="composer" @submit.prevent="handleSubmit">
            <textarea
              v-model="draft"
              rows="3"
              placeholder="输入你的问题，比如：预算 300 元左右怎么选泡脚桶？"
            />
            <div class="composer-actions">
              <span>已启用会话记忆与本地知识库检索</span>
              <button type="submit" :disabled="!canSend">发送</button>
            </div>
          </form>
        </section>
      </div>
    </main>
  </div>
</template>
