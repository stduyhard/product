import { mount, flushPromises } from "@vue/test-utils";
import { describe, expect, it, vi, beforeEach } from "vitest";
import App from "../App.vue";

describe("App", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the chat title and starter message", () => {
    const wrapper = mount(App);

    expect(wrapper.text()).toContain("???????");
    expect(wrapper.text()).toContain("??????????????");
  });

  it("sends a question and shows the assistant answer", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ text: "?????????????" }),
      }),
    );

    const wrapper = mount(App);
    await wrapper.find('textarea').setValue("???????");
    await wrapper.find('form').trigger('submit.prevent');
    await flushPromises();

    expect(fetch).toHaveBeenCalledTimes(1);
    expect(wrapper.text()).toContain("???????");
    expect(wrapper.text()).toContain("?????????????");
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
    await wrapper.find('textarea').setValue("?? 300 ???????");
    await wrapper.find('form').trigger('submit.prevent');
    await wrapper.vm.$nextTick();

    expect(wrapper.find('.loading-card').exists()).toBe(true);

    resolveFetch({ ok: true, json: async () => ({ text: "300 ??????????" }) });
    await flushPromises();
    expect(wrapper.find('.loading-card').exists()).toBe(false);
  });

  it("shows an error message when the request fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network error")));

    const wrapper = mount(App);
    await wrapper.find('textarea').setValue("?????????");
    await wrapper.find('form').trigger('submit.prevent');
    await flushPromises();

    expect(wrapper.text()).toContain("???????");
  });


  it("starts a new conversation and clears previous messages", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ text: "????????????" }),
      }),
    );

    const wrapper = mount(App);
    await wrapper.find('textarea').setValue("???????");
    await wrapper.find('form').trigger('submit.prevent');
    await flushPromises();

    expect(wrapper.text()).toContain("???????");

    await wrapper.find('[data-testid="new-chat"]').trigger('click');

    const cards = wrapper.findAll('.message-card');
    expect(cards).toHaveLength(1);
    expect(cards[0].text()).toContain("??????????????");
  });
});
