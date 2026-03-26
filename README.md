# 泡脚桶产品调研与本地 AI 客服 MVP

这是一个围绕 `泡脚桶` 产品搭建的 MVP 项目，包含两条主线：

1. 电商数据采集与市场调研
2. 本地 AI 客服机器人

当前版本已经支持：

- 京东泡脚桶商品小样本采集
- 飞书多维表写入
- 自动生成市场调研报告
- 自动生成汇报简版与仪表盘摘要
- 生成本地知识库
- 基于 `LangChain RAG + DeepSeek` 的本地客服机器人

## 目录说明

- `run_mvp.py`：主流程入口
- `app/collector/`：京东/天猫采集与清洗
- `app/sync/`：飞书多维表同步
- `app/analysis/`：统计分析与 AI 总结
- `app/report/`：报告、汇报简版、仪表盘数据生成
- `app/bot/`：本地机器人、知识库、RAG 问答服务
- `config/keywords.json`：默认关键词
- `output/`：报告与仪表盘输出目录
- `data/knowledge_base.json`：本地知识库文件

## 环境准备

建议 Python 3.13。

安装依赖：

```powershell
python -m pip install -r requirements.txt
python -m playwright install chromium
```

## 环境变量

项目通过 `.env` 读取配置。你至少需要准备以下内容：

### 1. 飞书多维表

- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `FEISHU_APP_TOKEN`
- `FEISHU_TABLE_PRODUCTS`
- `FEISHU_TABLE_JOBS`
- `FEISHU_USE_CN_FIELDS=1`

### 2. 京东浏览器抓取

- `COLLECTOR_MODE=web`
- `COLLECTOR_PLATFORMS=jd`
- `COLLECTOR_PER_PLATFORM_LIMIT=20`
- `KEYWORDS_OVERRIDE=泡脚桶`
- `USE_BROWSER_COLLECTOR=1`
- `BROWSER_HEADLESS=0`
- `BROWSER_CDP_PORT=9222`

### 3. DeepSeek / LangChain

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`
- `BOT_VECTOR_CACHE_PATH`

说明：

- 当前项目使用 `langchain-openai` 的 `ChatOpenAI` 兼容 DeepSeek。
- 只要 `OPENAI_BASE_URL` 和 `OPENAI_API_KEY` 配好，就能跑 AI 分析与机器人问答。
- `BOT_VECTOR_CACHE_PATH` 用于持久化本地 Chroma 向量库，机器人重启时可直接复用。

## 京东抓取前准备

为了提高京东页面抓取成功率，建议先用调试端口启动 Chrome：

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="D:\chrome-cdp-profile"
```

然后在这个 Chrome 里：

1. 登录京东
2. 打开泡脚桶搜索页
3. 确认能看到商品列表

推荐页面：

[https://search.jd.com/Search?keyword=%E6%B3%A1%E8%84%9A%E6%A1%B6](https://search.jd.com/Search?keyword=%E6%B3%A1%E8%84%9A%E6%A1%B6)

## 运行市场调研主流程

执行：

```powershell
python run_mvp.py
```

成功后会输出：

- 市场报告：[`output/market_report.md`](D:\python-code\produtct_ai\output\market_report.md)
- 汇报简版：[`output/executive_brief.md`](D:\python-code\produtct_ai\output\executive_brief.md)
- 仪表盘摘要：[`output/dashboard_summary.json`](D:\python-code\produtct_ai\output\dashboard_summary.json)
- 本地知识库：[`data/knowledge_base.json`](D:\python-code\produtct_ai\data\knowledge_base.json)

同时会将商品记录与任务日志同步到飞书多维表。

## 启动本地机器人

执行：

```powershell
python -m uvicorn app.bot.server:app --host 127.0.0.1 --port 8001
```

健康检查：

```powershell
curl http://127.0.0.1:8001/health
```

## 本地问答接口

### 推荐：直接使用 `/chat`

请求：

```powershell
curl -Method POST http://127.0.0.1:8001/chat `
  -ContentType "application/json" `
  -Body '{"text":"泡脚桶怎么选？"}'
```

返回格式：

```json
{"text":"..."}
```

### 兼容接口：`/feishu/webhook`

如果仍需要兼容飞书事件格式，可以继续调用：

```powershell
curl -Method POST http://127.0.0.1:8001/feishu/webhook `
  -ContentType "application/json" `
  -Body '{"token":"dev-token","event":{"text":"泡脚桶怎么选？"}}'
```

## 机器人技术栈

当前机器人不是简单的请求转发，而是标准的 `LangChain RAG` 结构：

- 本地知识库
- Retriever
- Embeddings
- Chroma
- ChatPromptTemplate
- DeepSeek（通过 `ChatOpenAI` 接入）
- StrOutputParser

也就是说，当前问答链路是：

`Knowledge Base -> Retriever -> Prompt -> LLM -> Answer`

## 建议演示顺序

1. 启动带 `9222` 的 Chrome 并打开京东搜索页
2. 运行 `python run_mvp.py`
3. 打开飞书多维表查看商品数据
4. 打开报告文件查看市场结论
5. 启动本地机器人
6. 用 `/chat` 提问演示产品咨询问答

## 当前已完成能力

- 京东泡脚桶商品采集
- 飞书多维表写入
- 市场调研报告生成
- 汇报简版生成
- 仪表盘摘要生成
- 本地知识库生成
- LangChain RAG 本地客服机器人
- 本地 `/chat` 问答接口

## 已知限制

- 当前演示主线聚焦京东，小样本为主
- 京东网页结构可能变化，抓取依赖当前页面可见性
- 飞书表字段读取权限可能受到 Base 内部权限限制
- 当前向量库使用本地 `Chroma` 持久化目录，适合单机演示与本地复用

## 后续可继续增强

1. 增加多轮对话记忆与会话管理
2. 接入天猫真实抓取
3. 增强品牌、价格带、卖点交叉分析
4. 增加更适合汇报的可视化页面
