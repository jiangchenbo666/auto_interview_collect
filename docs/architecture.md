# TestDev Interview Agent 架构设计

## 目标

第一阶段先做本地闭环：导入面经文本，提取题目，分类，生成答案，包装成面试表达，每天推送。

## 模块

- `storage`: SQLite 初始化和题目 CRUD
- `processors`: 清洗、抽取、分类、答案生成、项目包装
- `push`: 企业微信 Markdown 消息构建和发送
- `scheduler`: 每日任务编排
- `agents`: Agent 任务协议定义
- `main.py`: CLI 入口

## 代码阅读顺序

建议按下面顺序看代码：

1. `src/main.py`：先看命令行提供了哪些能力。
2. `src/storage/db.py` 和 `src/storage/repository.py`：理解题目怎么入库、怎么去重、怎么流转状态。
3. `src/processors/extractor.py`：理解从面经文本里怎么提取题目。
4. `src/processors/classifier.py`：理解规则分类。
5. `src/scheduler/daily_job.py`：理解“处理题目 -> 生成推送”的主链路。
6. `src/push/wecom_bot.py`：理解企业微信推送。

## 数据状态

- `raw`: 原始导入
- `classified`: 已分类
- `answered`: 已生成标准答案
- `packaged`: 已生成项目化回答
- `pushed`: 已推送
- `mastered`: 已掌握

## 后续演进

- 接入 DeepSeek API 生成更高质量答案
- 支持 GitHub raw 和博客 URL 导入
- 增加 FTS5 全文搜索
- 增加错题复习和间隔重复
- 增加 Worker Agent 自动任务分派
