# Agent 协作协议

## 角色

- 架构师 Agent：设计架构、拆任务、审查代码、控制范围
- Worker Agent：按任务单完成局部代码
- 本地环境：运行、测试、验证、保存产物

## 任务状态

```text
Drafted -> Assigned -> Implemented -> Reviewed -> Revision Required/Accepted -> Merged -> Verified
```

## Worker 任务单字段

- Task ID
- Goal
- Context
- Files Allowed To Modify
- Requirements
- Constraints
- Output Format

## 约束

Worker 不能随意改目录结构，不能实现未分配功能，不能硬编码密钥。
