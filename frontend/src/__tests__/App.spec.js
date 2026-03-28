
import { mount, flushPromises } from "@vue/test-utils";
import { describe, expect, it, vi, beforeEach } from "vitest";
import App from "../App.vue";

describe("App", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the chat title and starter message", () => {
    const wrapper = mount(App);

    expect(wrapper.text()).toContain("泡脚桶客服助手");
    expect(wrapper.text()).toContain("我可以帮你解答泡脚桶产品问题");
  });

  it("sends a question and shows the assistant answer", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ text: "建议优先看恒温和排水设计。" }),
      }),
    );

    const wrapper = mount(App);
    await wrapper.find("textarea").setValue("泡脚桶怎么选？");
    await wrapper.find("form").trigger("submit.prevent");
    await flushPromises();

    expect(fetch).toHaveBeenCalledTimes(1);
    expect(wrapper.text()).toContain("泡脚桶怎么选？");
    expect(wrapper.text()).toContain("建议优先看恒温和排水设计。");
  });

  it("shows a loading state while waiting for the answer", async () => {
    let resolveFetch;
    vi.stubGlobal(
      "fetch",
      vi.fn(
        () =>
          new Promise((resolve) => {
            resolveFetch = resolve;
          }),
      ),
    );

    const wrapper = mount(App);
    await wrapper.find("textarea").setValue("预算 300 元买什么类型？");
    await wrapper.find("form").trigger("submit.prevent");
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".loading-card").exists()).toBe(true);

    resolveFetch({ ok: true, json: async () => ({ text: "300 元左右可以先看主力款。" }) });
    await flushPromises();
    expect(wrapper.find(".loading-card").exists()).toBe(false);
  });

  it("shows an error message when the request fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network error")));

    const wrapper = mount(App);
    await wrapper.find("textarea").setValue("有适合老人用的吗？");
    await wrapper.find("form").trigger("submit.prevent");
    await flushPromises();

    expect(wrapper.text()).toContain("连接机器人失败");
  });

  it("stores previous chats in the sidebar and can reopen them", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ text: "建议优先看恒温和排水。" }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ text: "300 元左右可以先看主力款。" }),
        }),
    );

    const wrapper = mount(App);
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
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ text: "建议先看恒温和排水设计。" }),
      }),
    );

    const wrapper = mount(App);
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
