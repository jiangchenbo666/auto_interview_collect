# raw 数据目录

这里放真实面经和八股材料。

## 推荐放法

```text
data/raw/real_interviews/
├── nowcoder-某公司测开面经.md
├── github-测试开发八股整理.md
└── blog-安全测试面试题.txt
```

然后执行：

```bash
python -m src.main import-folder data/raw/real_interviews
python -m src.main rebuild-answers --use-llm --limit 50
python -m src.main demo --use-llm
```

## 重要说明

- `sample_questions.md` 只是演示数据，不代表真实面经。
- 真实面经必须来自你保存的牛客、GitHub、博客、个人整理等来源。
- 页面里会显示每道题的来源路径，避免把演示题误当真实材料。
