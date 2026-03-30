import { mount, flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "../App.vue";

function buildFetchMock(overrides = {}) {
  const dashboardPayload = overrides.dashboardPayload ?? {
    summary: { total: 20, avg_price: 629.03 },
    charts: {
      brand_top: [
        { brand: "unknown-brand", count: 14 },
        { brand: "midea", count: 5 },
      ],
      price_band: [
        { band: "200-399", count: 8 },
        { band: "400+", count: 11 },
      ],
      feature_coverage: [
        { feature: "恒温", count: 9 },
        { feature: "按摩", count: 7 },
      ],
      shop_type_share: [{ shop_type: "flagship", count: 20 }],
    },
  };

  const chatQueue = [...(overrides.chatQueue ?? [{ text: "建议优先看恒温和排水设计。" }])];

  return vi.fn((url) => {
    if (String(url).includes("/dashboard/summary")) {
      return Promise.resolve({
        ok: overrides.dashboardOk ?? true,
        status: overrides.dashboardStatus ?? 200,
        json: async () => dashboardPayload,
      });
    }

    if (overrides.chatReject) {
      return Promise.reject(overrides.chatReject);
    }

    const nextResponse = chatQueue.shift() ?? { text: "建议优先看恒温和排水设计。" };
    return Promise.resolve({
      ok: true,
      status: 200,
      json: async () => nextResponse,
    });
  });
}

describe("App", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the chat title and starter message", async () => {
    vi.stubGlobal("fetch", buildFetchMock());
    const wrapper = mount(App);
    await flushPromises();

    expect(wrapper.text()).toContain("泡脚桶客服助手");
    expect(wrapper.text()).toContain("我可以帮你解答泡脚桶产品问题");
  });

  it("renders dashboard cards from the dashboard summary api", async () => {
    vi.stubGlobal("fetch", buildFetchMock());

    const wrapper = mount(App);
    await flushPromises();

    expect(wrapper.find('[data-testid="dashboard-total"]').text()).toContain("20");
    expect(wrapper.find('[data-testid="dashboard-avg-price"]').text()).toContain("629.03");
    expect(wrapper.find('[data-testid="dashboard-brand-top"]').text()).toContain("unknown-brand");
    expect(wrapper.find('[data-testid="dashboard-price-band"]').text()).toContain("200-399");
  });

  it("renders visual chart blocks for dashboard insights", async () => {
    vi.stubGlobal("fetch", buildFetchMock());

    const wrapper = mount(App);
    await flushPromises();

    expect(wrapper.findAll('[data-testid="brand-bar"]').length).toBe(2);
    expect(wrapper.findAll('[data-testid="price-column"]').length).toBe(2);
    expect(wrapper.find('[data-testid="shop-share-donut"]').exists()).toBe(true);
    expect(wrapper.findAll(".legend-item").length).toBe(1);
  });

  it("sends a question and shows the assistant answer", async () => {
    const fetchMock = buildFetchMock();
    vi.stubGlobal("fetch", fetchMock);

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.find("textarea").setValue("泡脚桶怎么选？");
    await wrapper.find("form").trigger("submit.prevent");
    await flushPromises();

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(wrapper.text()).toContain("泡脚桶怎么选？");
    expect(wrapper.text()).toContain("建议优先看恒温和排水设计。");
  });

  it("shows a loading state while waiting for the answer", async () => {
    let resolveChat;
    const fetchMock = vi.fn((url) => {
      if (String(url).includes("/dashboard/summary")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({
            summary: { total: 20, avg_price: 629.03 },
            charts: { brand_top: [], price_band: [], feature_coverage: [], shop_type_share: [] },
          }),
        });
      }
      return new Promise((resolve) => {
        resolveChat = resolve;
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.find("textarea").setValue("预算 300 元买什么类型？");
    await wrapper.find("form").trigger("submit.prevent");
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".loading-card").exists()).toBe(true);

    resolveChat({
      ok: true,
      status: 200,
      json: async () => ({ text: "300 元左右可以先看主力款。" }),
    });
    await flushPromises();
    expect(wrapper.find(".loading-card").exists()).toBe(false);
  });

  it("shows an error message when the request fails", async () => {
    vi.stubGlobal("fetch", buildFetchMock({ chatReject: new Error("network error") }));

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.find("textarea").setValue("有适合老人用的吗？");
    await wrapper.find("form").trigger("submit.prevent");
    await flushPromises();

    expect(wrapper.text()).toContain("连接机器人失败");
  });

  it("stores previous chats in the sidebar and can reopen them", async () => {
    vi.stubGlobal(
      "fetch",
      buildFetchMock({
        chatQueue: [
          { text: "建议优先看恒温和排水。" },
          { text: "300 元左右可以先看主力款。" },
        ],
      }),
    );

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.find("textarea").setValue("泡脚桶怎么选？");
    await wrapper.find("form").trigger("submit.prevent");
    await flushPromises();

    expect(wrapper.find('[data-testid="history-list"]').text()).toContain("泡脚桶怎么选？");

    await wrapper.find('[data-testid="new-chat"]').trigger("click");
    await wrapper.find("textarea").setValue("预算 300 元买什么类型？");
    await wrapper.find("form").trigger("submit.prevent");
    await flushPromises();

    const historyItems = wrapper.findAll('[data-testid="history-item"]');
    expect(historyItems.length).toBeGreaterThanOrEqual(2);
    await historyItems[1].trigger("click");

    expect(wrapper.find(".message-list").text()).toContain("泡脚桶怎么选？");
    expect(wrapper.find(".message-list").text()).toContain("建议优先看恒温和排水");
  });

  it("starts a new conversation and clears previous messages", async () => {
    vi.stubGlobal("fetch", buildFetchMock());

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.find("textarea").setValue("泡脚桶怎么选？");
    await wrapper.find("form").trigger("submit.prevent");
    await flushPromises();

    expect(wrapper.text()).toContain("泡脚桶怎么选？");

    await wrapper.find('[data-testid="new-chat"]').trigger("click");

    const cards = wrapper.findAll(".message-card");
    expect(cards).toHaveLength(1);
    expect(cards[0].text()).toContain("我可以帮你解答泡脚桶产品问题");
  });
});
