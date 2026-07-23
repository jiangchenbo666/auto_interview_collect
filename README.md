# auto_interview_collect

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
DEEPSEEK_MODEL=deepseek-v4-flash
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
