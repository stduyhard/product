<script setup>
import { computed, onMounted, ref } from "vue";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8001";

const labels = {
  heroTitle: "\u6ce1\u811a\u6876\u5ba2\u670d\u52a9\u624b",
  heroCopy:
    "\u7c7b\u4f3c ChatGPT \u7684\u672c\u5730\u95ee\u7b54\u754c\u9762\uff0c\u540c\u65f6\u628a\u722c\u53d6\u5546\u54c1\u751f\u6210\u7684\u5e02\u573a\u8c03\u7814\u7ed3\u679c\u6c47\u603b\u6210\u524d\u7aef\u4eea\u8868\u76d8\u3002",
  welcome:
    "\u6211\u53ef\u4ee5\u5e2e\u4f60\u89e3\u7b54\u6ce1\u811a\u6876\u4ea7\u54c1\u95ee\u9898\uff0c\u4e5f\u4f1a\u7ed3\u5408\u672c\u5730\u77e5\u8bc6\u5e93\u548c\u5e02\u573a\u8c03\u7814\u6570\u636e\u7ed9\u51fa\u5efa\u8bae\u3002",
  newChat: "\u65b0\u5efa\u5bf9\u8bdd",
  dashboardTitle: "\u5e02\u573a\u8c03\u7814\u4eea\u8868\u76d8",
  dashboardLoading: "\u52a0\u8f7d\u4e2d",
  dashboardReady: "\u5df2\u5c31\u7eea",
  totalLabel: "\u5546\u54c1\u6837\u672c\u6570",
  avgPriceLabel: "\u5e73\u5747\u4ef7\u683c",
  brandTop: "\u54c1\u724c Top",
  priceBand: "\u4ef7\u683c\u5e26\u5206\u5e03",
  featureCoverage: "\u529f\u80fd\u8986\u76d6",
  shopType: "\u5e97\u94fa\u7c7b\u578b",
  botTitle: "\u6ce1\u811a\u6876\u987e\u95ee\u673a\u5668\u4eba",
  botSubTitle: "\u652f\u6301\u57fa\u4e8e\u672c\u5730\u77e5\u8bc6\u5e93\u7684\u591a\u8f6e\u5bf9\u8bdd\u3002",
  answering: "\u56de\u7b54\u4e2d",
  idle: "\u5f85\u547d\u4e2d",
  history: "\u5386\u53f2\u4f1a\u8bdd",
  historyUnit: "\u6761",
  assistant: "\u52a9\u624b",
  user: "\u7528\u6237",
  composing: "\u6b63\u5728\u6574\u7406\u56de\u590d...",
  send: "\u53d1\u9001",
  promptHint: "\u673a\u5668\u4eba\u4f1a\u4f18\u5148\u4f7f\u7528\u77e5\u8bc6\u5e93\u548c\u8c03\u7814\u6570\u636e\u56de\u7b54\u3002",
  placeholder: "\u8bf7\u8f93\u5165\u95ee\u9898\uff0c\u4f8b\u5982\uff1a\u9884\u7b97 300 \u5143\u6709\u4ec0\u4e48\u63a8\u8350\uff1f",
  fallbackAnswer: "\u6682\u65f6\u6ca1\u6709\u62ff\u5230\u56de\u7b54\uff0c\u8bf7\u7a0d\u540e\u518d\u8bd5\u3002",
  error: "\u8fde\u63a5\u673a\u5668\u4eba\u5931\u8d25\uff0c\u8bf7\u786e\u8ba4\u540e\u7aef\u670d\u52a1\u5df2\u542f\u52a8\u3002",
  sessionTitle: "\u65b0\u5bf9\u8bdd",
  chartEmpty: "\u6682\u65f6\u65e0\u6570\u636e",
};

const suggestions = [
  "\u6ce1\u811a\u6876\u600e\u4e48\u9009\uff1f",
  "\u9884\u7b97 300 \u5143\u6709\u4ec0\u4e48\u63a8\u8350\uff1f",
  "\u6052\u6e29\u548c\u6309\u6469\u54ea\u4e2a\u66f4\u91cd\u8981\uff1f",
  "\u9002\u5408\u8001\u4eba\u4f7f\u7528\u7684\u6b3e\u5f0f\u6709\u54ea\u4e9b\uff1f",
];

const chartPalette = ["#9f4d24", "#d4864e", "#e5a96b", "#f1d0a7"];
const donutPalette = ["#2f6c63", "#9f4d24", "#c88b5d", "#eadfc5"];

function defaultDashboard() {
  return {
    summary: { total: 0, avg_price: 0 },
    charts: {
      brand_top: [],
      price_band: [],
      feature_coverage: [],
      shop_type_share: [],
    },
  };
}

function createSessionId() {
  return `session-${Math.random().toString(36).slice(2, 10)}`;
}

function createWelcomeMessage() {
  return {
    id: `assistant-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
    role: "assistant",
    text: labels.welcome,
  };
}

function createSession(label = labels.sessionTitle) {
  return {
    id: createSessionId(),
    title: label,
    preview: labels.welcome,
    updatedAt: Date.now(),
    messages: [createWelcomeMessage()],
  };
}

const draft = ref("");
const isLoading = ref(false);
const errorMessage = ref("");
const sessions = ref([createSession()]);
const currentSessionId = ref(sessions.value[0].id);
const dashboardLoading = ref(true);
const dashboard = ref(defaultDashboard());

const currentSession = computed(() => {
  return sessions.value.find((session) => session.id === currentSessionId.value) ?? sessions.value[0];
});

const canSend = computed(() => draft.value.trim().length > 0 && !isLoading.value);
const avgPriceText = computed(() => Number(dashboard.value.summary?.avg_price || 0).toFixed(2));

const brandBars = computed(() => buildBarSeries(dashboard.value.charts.brand_top, "brand"));
const featureBars = computed(() => buildBarSeries(dashboard.value.charts.feature_coverage, "feature"));
const priceColumns = computed(() => buildColumnSeries(dashboard.value.charts.price_band, "band"));
const shopSegments = computed(() => buildDonutSegments(dashboard.value.charts.shop_type_share, "shop_type"));
const shopDonutStyle = computed(() => ({
  background: buildConicGradient(shopSegments.value),
}));

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

function normalizeDashboard(payload) {
  return {
    summary: {
      total: payload?.summary?.total ?? 0,
      avg_price: payload?.summary?.avg_price ?? 0,
    },
    charts: {
      brand_top: payload?.charts?.brand_top ?? [],
      price_band: payload?.charts?.price_band ?? [],
      feature_coverage: payload?.charts?.feature_coverage ?? [],
      shop_type_share: payload?.charts?.shop_type_share ?? [],
    },
  };
}

function buildBarSeries(items, labelKey) {
  const safeItems = Array.isArray(items) ? items : [];
  const max = Math.max(...safeItems.map((item) => Number(item.count || 0)), 0);
  return safeItems.map((item, index) => ({
    label: item[labelKey],
    count: Number(item.count || 0),
    width: max > 0 ? `${(Number(item.count || 0) / max) * 100}%` : "0%",
    color: chartPalette[index % chartPalette.length],
  }));
}

function buildColumnSeries(items, labelKey) {
  const safeItems = Array.isArray(items) ? items : [];
  const max = Math.max(...safeItems.map((item) => Number(item.count || 0)), 0);
  return safeItems.map((item, index) => ({
    label: item[labelKey],
    count: Number(item.count || 0),
    height: max > 0 ? `${Math.max((Number(item.count || 0) / max) * 100, 8)}%` : "0%",
    color: chartPalette[index % chartPalette.length],
  }));
}

function buildDonutSegments(items, labelKey) {
  const safeItems = Array.isArray(items) ? items : [];
  const total = safeItems.reduce((sum, item) => sum + Number(item.count || 0), 0);
  let cursor = 0;
  return safeItems.map((item, index) => {
    const count = Number(item.count || 0);
    const percentage = total > 0 ? (count / total) * 100 : 0;
    const segment = {
      label: item[labelKey],
      count,
      percentage,
      start: cursor,
      end: cursor + percentage,
      color: donutPalette[index % donutPalette.length],
    };
    cursor += percentage;
    return segment;
  });
}

function buildConicGradient(segments) {
  if (!segments.length) {
    return "conic-gradient(#eadfc5 0deg 360deg)";
  }
  const stops = segments.map(
    (segment) =>
      `${segment.color} ${segment.start.toFixed(2)}% ${segment.end.toFixed(2)}%`,
  );
  return `conic-gradient(${stops.join(", ")})`;
}

async function loadDashboard() {
  dashboardLoading.value = true;
  try {
    const response = await fetch(`${apiBaseUrl}/dashboard/summary`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    dashboard.value = normalizeDashboard(await response.json());
  } catch (error) {
    console.error(error);
    dashboard.value = defaultDashboard();
  } finally {
    dashboardLoading.value = false;
  }
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
    title: session.title === labels.sessionTitle ? summarizeTitle(content) : session.title,
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
    const answer = data.text || labels.fallbackAnswer;
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
    errorMessage.value = labels.error;
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

onMounted(() => {
  void loadDashboard();
});
</script>

<template>
  <div class="page-shell">
    <aside class="hero-panel">
      <div>
        <p class="eyebrow">Foot Bath Copilot</p>
        <h1>{{ labels.heroTitle }}</h1>
        <p class="hero-copy">{{ labels.heroCopy }}</p>
      </div>

      <section class="dashboard-panel">
        <div class="dashboard-header">
          <div>
            <p class="eyebrow">Market Dashboard</p>
            <h3>{{ labels.dashboardTitle }}</h3>
          </div>
          <span class="status-pill" :class="{ busy: dashboardLoading }">
            {{ dashboardLoading ? labels.dashboardLoading : labels.dashboardReady }}
          </span>
        </div>

        <div class="dashboard-summary-grid">
          <article class="metric-card" data-testid="dashboard-total">
            <span>{{ labels.totalLabel }}</span>
            <strong>{{ dashboard.summary.total }}</strong>
          </article>
          <article class="metric-card" data-testid="dashboard-avg-price">
            <span>{{ labels.avgPriceLabel }}</span>
            <strong>{{ avgPriceText }}</strong>
          </article>
        </div>

        <div class="dashboard-charts">
          <article class="chart-card" data-testid="dashboard-brand-top">
            <h4>{{ labels.brandTop }}</h4>
            <div v-if="brandBars.length" class="bar-chart">
              <div
                v-for="item in brandBars"
                :key="`${item.label}-${item.count}`"
                class="bar-row"
                data-testid="brand-bar"
              >
                <div class="chart-meta">
                  <span>{{ item.label }}</span>
                  <strong>{{ item.count }}</strong>
                </div>
                <div class="bar-track">
                  <div class="bar-fill" :style="{ width: item.width, background: item.color }"></div>
                </div>
              </div>
            </div>
            <p v-else class="chart-empty">{{ labels.chartEmpty }}</p>
          </article>

          <article class="chart-card" data-testid="dashboard-price-band">
            <h4>{{ labels.priceBand }}</h4>
            <div v-if="priceColumns.length" class="column-chart">
              <div
                v-for="item in priceColumns"
                :key="`${item.label}-${item.count}`"
                class="column-item"
                data-testid="price-column"
              >
                <div class="column-track">
                  <div class="column-fill" :style="{ height: item.height, background: item.color }"></div>
                </div>
                <strong>{{ item.count }}</strong>
                <span>{{ item.label }}</span>
              </div>
            </div>
            <p v-else class="chart-empty">{{ labels.chartEmpty }}</p>
          </article>

          <article class="chart-card">
            <h4>{{ labels.featureCoverage }}</h4>
            <div v-if="featureBars.length" class="bar-chart compact">
              <div
                v-for="item in featureBars"
                :key="`${item.label}-${item.count}`"
                class="bar-row"
              >
                <div class="chart-meta">
                  <span>{{ item.label }}</span>
                  <strong>{{ item.count }}</strong>
                </div>
                <div class="bar-track">
                  <div class="bar-fill" :style="{ width: item.width, background: item.color }"></div>
                </div>
              </div>
            </div>
            <p v-else class="chart-empty">{{ labels.chartEmpty }}</p>
          </article>

          <article class="chart-card">
            <h4>{{ labels.shopType }}</h4>
            <div v-if="shopSegments.length" class="donut-wrap">
              <div class="donut-chart" data-testid="shop-share-donut" :style="shopDonutStyle"></div>
              <div class="donut-legend">
                <div
                  v-for="item in shopSegments"
                  :key="`${item.label}-${item.count}`"
                  class="legend-item"
                >
                  <span class="legend-dot" :style="{ background: item.color }"></span>
                  <span>{{ item.label }}</span>
                  <strong>{{ item.count }}</strong>
                </div>
              </div>
            </div>
            <p v-else class="chart-empty">{{ labels.chartEmpty }}</p>
          </article>
        </div>
      </section>
    </aside>

    <main class="chat-panel">
      <header class="chat-header">
        <div>
          <h2>{{ labels.botTitle }}</h2>
          <p>{{ labels.botSubTitle }}</p>
        </div>
        <div class="header-actions">
          <button
            data-testid="new-chat"
            class="ghost-button"
            type="button"
            :disabled="isLoading"
            @click="startNewChat"
          >
            {{ labels.newChat }}
          </button>
          <span class="status-pill" :class="{ busy: isLoading }">
            {{ isLoading ? labels.answering : labels.idle }}
          </span>
        </div>
      </header>

      <div class="chat-body">
        <aside class="history-panel">
          <div class="history-header">
            <h3>{{ labels.history }}</h3>
            <span>{{ sessions.length }} {{ labels.historyUnit }}</span>
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
              <span class="message-role">{{ message.role === "assistant" ? labels.assistant : labels.user }}</span>
              <p>{{ message.text }}</p>
            </article>

            <article v-if="isLoading" class="message-card assistant loading-card">
              <span class="message-role">{{ labels.assistant }}</span>
              <p>{{ labels.composing }}</p>
            </article>
          </section>

          <p v-if="errorMessage" class="error-banner">{{ errorMessage }}</p>

          <form class="composer" @submit.prevent="handleSubmit">
            <textarea
              v-model="draft"
              rows="3"
              :placeholder="labels.placeholder"
            />
            <div class="composer-actions">
              <span>{{ labels.promptHint }}</span>
              <button type="submit" :disabled="!canSend">{{ labels.send }}</button>
            </div>
          </form>
        </section>
      </div>
    </main>
  </div>
</template>
