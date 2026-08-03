# 牛客资料导入指南

牛客内容经常需要登录、弹窗或动态加载，不建议让 GitHub Actions 直接爬取。最稳的方式是手动沉淀成 Markdown/TXT，再交给工具自动导入。

## 推荐目录

最省事的方式：把复制粘贴的原始资料放到私有 Obsidian 仓库里。推荐用你现在新建的目录：

```text
Obsidian-Vault/面经资料-未整理/
```

兼容旧目录：

```text
Obsidian-Vault/面经资料/待整理/
```

保存成 `.txt`、`.md` 或截图文件都可以。Obsidian Git 会自动 push 到私有仓库，GitHub Actions 每天会拉取这些目录，并整理成规范 Markdown。

本地公开仓库也支持一个收件箱目录：

```text
data/raw/inbox/
```

但因为 `auto_interview_collect` 是公开仓库，不建议在这里放包含隐私、账号、截图 OCR 文本的资料。

整理后的 Markdown 会自动写到：

```text
data/raw/real_interviews/nowcoder/
```

这个目录会被 `python -m src.main study` 自动递归扫描并导入题库。

## 推荐格式

每篇面经一个文件，文件名带来源和主题：

```text
data/raw/real_interviews/nowcoder/nowcoder-ai-project-730.md
data/raw/real_interviews/nowcoder/nowcoder-tencent-testdev-2026.md
```

如果你懒得整理，直接在 `Obsidian-Vault/面经资料-未整理/` 下建一个 txt：

```text
2026-08-03-nowcoder-ai-project.txt
```

然后把牛客内容复制进去即可。工具会自动生成规范 md。

内容建议这样写：

```markdown
# 牛客 AI 项目面经

来源：https://www.nowcoder.com/...
岗位：测试开发 / AI 应用测试
公司：可选
日期：2026-08-03

1. 针对你的 AI 项目问了一大堆 AI 知识，应该怎么回答？
2. Harness 有了解吗？用它做什么？
3. 什么是 MVP？你这个项目怎么定义 MVP？
4. 如果模型回答不稳定，你怎么测试？
```

## 注意

- 不要把账号 Cookie、私信、个人手机号、面试官姓名等隐私写进去。
- 可以摘录问题和你自己的复盘，不建议整篇复制受限页面内容。
- 截图支持 `.png`、`.jpg`、`.jpeg`、`.webp`、`.bmp`。云端有 Kimi key 时会尝试视觉解析；没有 key 或解析失败时，会先生成“截图待解析”的资料卡，流水线不会中断。
- 如果截图里是题目列表，优先手动整理成问题列表，工具抽题会更准；截图适合你懒得转文字时先收进去。

## 手动测试

本地可以执行：

```bash
python -m src.main normalize-inbox
python -m src.main study --no-refresh-sources --no-open
```

如果你想本地立刻测试截图解析，并且 `.env` 里已经有 `KIMI_API_KEY`：

```bash
python -m src.main normalize-inbox --use-vision
```
