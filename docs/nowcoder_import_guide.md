# 牛客资料导入指南

牛客内容经常需要登录、弹窗或动态加载，不建议让 GitHub Actions 直接爬取。最稳的方式是手动沉淀成 Markdown/TXT，再交给工具自动导入。

## 推荐目录

把资料放到：

```text
data/raw/real_interviews/nowcoder/
```

这个目录会被 `python -m src.main study` 自动递归扫描。

## 推荐格式

每篇面经一个文件，文件名带来源和主题：

```text
data/raw/real_interviews/nowcoder/nowcoder-ai-project-730.md
data/raw/real_interviews/nowcoder/nowcoder-tencent-testdev-2026.md
```

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
- 如果截图里是题目列表，优先手动整理成问题列表，工具抽题会更准。
