from __future__ import annotations


# Lightweight rule-based classifier for MVP.
# Later this can be replaced by a DeepSeek call while keeping the same function API.
CATEGORY_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("安全测试", ("sql注入", "注入", "xss", "csrf", "ssrf", "文件上传", "漏洞", "越权", "安全", "权限绕过")),
    ("接口测试", ("接口", "api", "http", "鉴权", "幂等", "token", "状态码")),
    ("自动化测试", ("自动化", "selenium", "pytest", "unittest", "框架", "脚本")),
    ("性能测试", ("性能", "压测", "并发", "响应慢", "吞吐", "qps", "tps", "瓶颈")),
    ("测试用例设计", ("用例", "边界值", "等价类", "场景", "异常", "测试点")),
    ("数据库", ("数据库", "mysql", "sql", "索引", "b+树", "b树", "哈希表", "回表", "最左前缀", "聚簇索引", "事务", "锁", "慢查询", "explain")),
    ("计算机网络", ("tcp", "udp", "http", "https", "三次握手", "四次挥手", "time_wait", "keep-alive", "证书", "网络")),
    ("操作系统", ("进程", "线程", "协程", "死锁", "内存", "上下文切换", "用户态", "内核态", "系统调用", "i/o")),
    ("Linux", ("linux", "shell", "grep", "awk", "sed", "chmod", "日志", "文件权限", "进程权限")),
    ("Python", ("python", "list", "tuple", "dict", "装饰器", "生成器", "gil")),
    ("Java", ("java", "jvm", "spring", "集合", "多线程")),
    ("数据结构与算法", ("算法", "复杂度", "链表", "数组", "栈", "队列", "树", "排序")),
    ("CI/CD", ("ci", "cd", "jenkins", "流水线", "持续集成", "gitlab")),
    ("Docker 与云原生", ("docker", "容器", "k8s", "kubernetes", "镜像", "namespace", "namespaces", "cgroup", "cgroups", "容器逃逸", "特权容器")),
    ("RAG 与 LLM 应用", ("rag", "llm", "大模型", "向量", "召回", "重排", "chunk", "prompt", "幻觉", "知识库", "证据链")),
    ("AI 工程", ("ai", "harness", "evaluation", "eval", "mvp", "golden set", "a/b", "模型版本", "回归评测")),
    ("项目经历", ("项目", "实习", "难点", "负责", "经历")),
    ("HR 与行为面", ("优缺点", "离职", "加班", "职业规划", "冲突")),
]


def classify_question(question: str) -> tuple[str, str]:
    """Return (category, difficulty) for one question."""
    lowered = question.lower().replace(" ", "")
    for category, keywords in CATEGORY_KEYWORDS:
        if any(keyword.lower().replace(" ", "") in lowered for keyword in keywords):
            return category, infer_difficulty(question, category)
    return "测试基础", infer_difficulty(question, "测试基础")


def infer_difficulty(question: str, category: str) -> str:
    """Infer a rough difficulty label used in daily review messages."""
    hard_markers = ("原理", "设计", "定位", "优化", "架构", "瓶颈", "源码")
    easy_markers = ("是什么", "区别", "流程", "概念")

    if category in {"安全测试", "性能测试", "自动化测试"} and any(
        marker in question for marker in hard_markers
    ):
        return "hard"
    if any(marker in question for marker in hard_markers):
        return "medium"
    if any(marker in question for marker in easy_markers):
        return "easy"
    return "medium"
