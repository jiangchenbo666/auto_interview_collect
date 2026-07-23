# 目录导览

这份文档是给第一次打开项目的人看的。你可以把它当作“项目地图”。

## 根目录

```text
TestDev-Interview-Agent/
├── README.md
├── requirements.txt
├── .env.example
├── config/
├── data/
├── docs/
├── src/
├── tasks/
└── tests/
```

## `config/`

放配置，不放核心业务代码。

- `categories.yaml`：测开/安全测试面试题分类体系。
- `sources.yaml`：数据源配置，后续接 GitHub、博客、牛客时会用到。
- `prompts/`：给大模型用的 Prompt 模板。当前 MVP 先用规则和模板，后续接 DeepSeek 时再读取这些模板。

## `data/`

放本地运行产生的数据。

- `raw/`：原始面经文本，比如你从牛客、博客、GitHub 复制下来的 `.md` / `.txt`。
- `processed/`：后续可放清洗后的中间文件。
- `exports/`：导出的 Markdown 题库。
- `interview.db`：SQLite 数据库，运行 `init` 后生成。

## `docs/`

放项目说明和协作规范。

- `architecture.md`：系统整体架构。
- `agent_protocol.md`：架构师 Agent 和 Worker Agent 如何交接任务。
- `mvp_plan.md`：第一阶段 MVP 的目标和边界。
- `project_profile.md`：你的实习/项目经历素材，答案包装模块会读取它。
- `directory_guide.md`：当前这份目录说明。

## `src/`

放真正运行的源码。

- `main.py`：命令行入口，所有命令都从这里进来。
- `config_loader.py`：读取 `.env` 和默认数据库路径。
- `storage/`：SQLite 建表、连接、增删改查。
- `processors/`：文本清洗、题目抽取、分类、答案生成、项目经历包装。
- `push/`：企业微信消息格式和 Webhook 发送。
- `scheduler/`：每日处理和推送任务。
- `crawlers/`：预留爬虫模块，当前 MVP 优先使用本地文件导入。
- `agents/`：Multi-Agent 任务协议的数据结构。
- `utils/`：通用工具函数，比如题目 hash。

## `tasks/`

放给 Worker Agent 的任务材料。

- `worker_prompt_template.md`：以后交给 DeepSeek 的通用 Worker Prompt。
- `worker_tasks/`：具体任务单。
- `reviews/`：架构师 Agent 的代码审查记录。

## `tests/`

放 pytest 测试。

- `test_storage.py`：数据库初始化、去重、状态更新。
- `test_processors.py`：题目抽取、分类、答案模板。
- `test_daily_job.py`：每日处理和 dry-run 推送链路。
