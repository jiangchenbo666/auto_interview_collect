# auto_interview_collect

## GitHub Actions 自动化流水线

仓库内置 `.github/workflows/daily-pipeline.yml`，每天北京时间 08:00 自动运行，也可以在 GitHub 的 Actions 页面手动点 `Run workflow`。

流水线会自动做这些事：

- 拉取 `config/real_sources.yaml` 中的公开真实来源
- 增量抽题并写入 SQLite，题目 hash 去重
- 调用 DeepSeek 生成答案；如果没配置 key，会退回本地模板答案
- 生成 `public/index.html`、`public/today.md`、`public/questions.md`
- 部署到 GitHub Pages
- 如果配置了钉钉机器人，会把 `today.md` 推送到手机
- 如果配置了 `OBSIDIAN_PAT`，会自动拉取私有 Obsidian 仓库到 `data/obsidian`

第一次使用需要在 GitHub 仓库配置：

1. `Settings -> Secrets and variables -> Actions -> New repository secret`
2. 新增 `DEEPSEEK_API_KEY`
3. 可选新增 `DINGTALK_WEBHOOK_URL`
4. 如果钉钉机器人开启了加签，再新增 `DINGTALK_SECRET`
5. 如果要让云端流水线读取你的私有 Obsidian 笔记，新增 `OBSIDIAN_PAT`
6. `Settings -> Pages -> Source` 选择 `GitHub Actions`

部署成功后，页面地址通常是：

```text
https://jiangchenbo666.github.io/auto_interview_collect/
```

注意：GitHub Actions 用 cache 保存 `data/interview.db`，能满足 MVP 的“每天不重复”需求，但它不是强数据库。后续如果要更稳，可以换成 Supabase、云端 SQLite 备份，或者把题库导出为 artifact。

### 私有 Obsidian 仓库接入

如果你的 Obsidian 已经通过 Git 自动同步到 `jiangchenbo666/Obsidian-Vault`，只需要再给本工具仓库一个只读访问令牌。

推荐使用 fine-grained Personal Access Token：

```text
GitHub -> Settings -> Developer settings -> Personal access tokens -> Fine-grained tokens
```

权限建议：

```text
Repository access: Only select repositories
Repository: jiangchenbo666/Obsidian-Vault
Contents: Read-only
```

然后回到 `auto_interview_collect` 仓库：

```text
Settings -> Secrets and variables -> Actions -> New repository secret
```

新增：

```text
OBSIDIAN_PAT=你的 fine-grained token
```

下一次 `Daily Interview Pipeline` 运行时，会自动执行：

```text
Checkout tool repository
Checkout Obsidian vault -> data/obsidian
Report Obsidian vault status
Build daily study page
```

这样 DeepSeek 生成答案时读到的就是你最新 push 到 GitHub 的 Obsidian 笔记。

测开/安全测试面经收集、自动整理和每日企业微信推送工具。

这个项目也叫 **TestDev Interview Agent**。它的定位是：帮测试开发/安全测试方向同学把零散面经整理成可复习、可推送、可包装成面试表达的本地知识库。

## MVP 能力

- 从 `.txt` / `.md` 文件导入面经文本
- 自动清洗文本并提取疑问句、编号题、标题题
- 使用 SQLite 存储题目并用 hash 去重
- 按测开岗位方向做规则分类
- 生成标准答案和结合项目经历的面试表达
- 每日抽取 3-5 道题，生成 Markdown 推送内容
- 支持企业微信群机器人 Webhook 推送

## 快速开始

先说明一句：项目自带的 `data/raw/sample_questions.md` 只是演示数据，不是真实面经。真实八股/面经需要你导入自己保存的材料。

最省事的方式：

```bash
python -m src.main demo
```

或者在 Windows 下双击：

```text
run_demo.bat
```

它会自动初始化数据库、导入样例题、生成答案，并导出：

- `data/exports/today.html`：浏览器版今日复习页面，会自动打开
- `data/exports/today.md`：今日复习内容
- `data/exports/questions.md`：完整题库导出

## 导入真实面经和八股文

把真实材料放到：

```text
data/raw/real_interviews/
```

支持 `.md` 和 `.txt`。例如：

```text
data/raw/real_interviews/nowcoder-字节测开一面.md
data/raw/real_interviews/github-测试开发八股.md
data/raw/real_interviews/blog-安全测试面试题.txt
```

然后执行：

```bash
python -m src.main import-folder data/raw/real_interviews
python -m src.main rebuild-answers --use-llm --limit 50
python -m src.main demo --use-llm
```

页面会显示每道题的来源路径。这样你能区分哪些题来自真实材料，哪些只是 demo。

## 从公开网页刷新真实来源

项目可以从 `config/real_sources.yaml` 中配置的公开 URL 拉取内容并抽题：

```bash
python -m src.main refresh-sources
python -m src.main process --use-llm --limit 50
python -m src.main daily --limit 5 --mark-reviewed
```

也可以临时导入一个 URL：

```bash
python -m src.main import-url "https://example.com/interview-note.html"
```

说明：

- 只建议配置公开、无需登录、允许浏览的页面。
- 牛客等需要登录或反爬的页面，建议手动保存为 `.md/.txt` 后导入。
- 系统使用题目 hash 去重，同一道题不会重复入库。

## 每日不重复和周日精选

推荐日常只运行这一条：

```bash
python -m src.main study --use-llm
```

它会自动：

- 刷新 `config/real_sources.yaml` 里的公开真实来源
- 导入 `data/raw/real_interviews/` 下的本地真实面经
- 处理新题目并结合 Obsidian/DeepSeek 生成答案
- 生成 `data/exports/today.html`
- 默认标记今日题目为已复习，降低明天重复概率
- 周日自动切换成“周日精选复习”

每日生成：

```bash
python -m src.main daily --limit 5 --mark-reviewed
```

`--mark-reviewed` 会把今天展示的题标记为已复习，后续普通每日题会优先选择未展示过的题。

每周日运行同一个命令时，会自动切换成“周日精选复习”，优先展示本周/近期已复习题和高频题，用来回顾。

## 接入 Obsidian 知识库

推荐把你的 Obsidian vault 放到：

```text
data/obsidian/
```

例如：

```text
data/obsidian/我的项目笔记/
data/obsidian/实习复盘/
data/obsidian/安全测试总结.md
```

然后检查是否识别到笔记：

```bash
python -m src.main vault-status
```

用一道题测试相关笔记检索：

```bash
python -m src.main vault-status --query "接口测试如何设计鉴权用例？"
```

如果你更新了 Obsidian 项目笔记，想让已有题目的“面试表达”重新结合笔记生成：

```bash
python -m src.main rebuild-answers --limit 50
python -m src.main demo
```

注意：`data/obsidian/` 已经被 `.gitignore` 忽略，不会把你的私人笔记提交到 GitHub。

## 使用 DeepSeek API 生成答案

默认情况下，项目使用本地模板 + Obsidian 检索片段，不需要 API key。

如果你想让所有答案调用 DeepSeek 模型生成：

1. 复制 `.env.example` 为 `.env`
2. 填入：

```text
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=你的 DeepSeek API key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-pro
```

然后运行：

```bash
python -m src.main rebuild-answers --use-llm --limit 20
python -m src.main demo --use-llm
```

没有 `--use-llm` 时，不会调用 API。`.env` 已经被 `.gitignore` 忽略，不会上传到 GitHub。

手动分步运行：

```bash
cd TestDev-Interview-Agent
python -m src.main init
python -m src.main import-file data/raw/sample_questions.md
python -m src.main import-folder data/raw/real_interviews
python -m src.main process --limit 20
python -m src.main daily --limit 3 --dry-run
```

如果要真实推送企业微信：

```bash
copy .env.example .env
```

然后在 `.env` 里填写：

```text
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
```

执行：

```bash
python -m src.main daily --limit 3
```

常驻每日推送：

```bash
python -m src.main serve-daily --time 08:30 --limit 3
```

## 常用命令

```bash
python -m src.main init
python -m src.main import-file <path>
python -m src.main list --status raw
python -m src.main process --limit 30
python -m src.main daily --limit 5 --dry-run --output data/exports/today.md
python -m src.main export-md data/exports/questions.md
```

## 目录速览

```text
config/      项目配置：分类表、数据源配置、后续给大模型用的 Prompt 模板
data/        本地数据：原始面经、处理后数据、SQLite 数据库、导出的 Markdown
docs/        项目文档：架构说明、目录导览、Agent 协议、MVP 计划、你的项目经历素材
src/         程序源码：CLI、题目处理、数据库、推送、每日任务
tasks/       Multi-Agent 协作材料：Worker Prompt 模板、任务单、审查记录
tests/       自动化测试：保证导入、分类、存储、每日推送这些主链路不被改坏
```

更详细的目录解释看 [docs/directory_guide.md](docs/directory_guide.md)。

## 主流程

```text
导入 md/txt 面经
  -> 抽取题目
  -> SQLite 去重入库
  -> 规则分类
  -> 生成标准答案
  -> 结合项目经历生成面试表达
  -> 每日企业微信 Markdown 推送
```
