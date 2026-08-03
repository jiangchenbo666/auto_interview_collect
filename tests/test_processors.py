from __future__ import annotations

from src.processors.answer_generator import generate_standard_answer
from src.processors.classifier import classify_question
from src.processors.extractor import extract_questions, is_noise_question


def test_extract_questions_from_markdown():
    text = """
    # 面经
    1. 接口测试用例应该如何设计？
    2. 普通描述，不一定是题目
    - 什么是 SQL 注入？
    """

    questions = extract_questions(text)

    assert "接口测试用例应该如何设计？" in questions
    assert "什么是 SQL 注入？" in questions


def test_extract_questions_filters_page_titles():
    text = """
    # 测试开发面试题全攻略 | 小林coding
    ## 06｜架构设计面试篇
    1. 接口测试用例应该如何设计？
    """

    questions = extract_questions(text)

    assert "接口测试用例应该如何设计？" in questions
    assert all("全攻略" not in question for question in questions)
    assert is_noise_question("06｜架构设计面试篇")
    assert is_noise_question("系统设计面试题")
    assert is_noise_question("业务测试：地基不牢，地动山摇")
    assert is_noise_question("业务测试")
    assert is_noise_question("框架设计")
    assert is_noise_question("很多同学在准备面试的时候会发现，面试官问的东西特别杂，有时候问你一个登录功能怎么测，有时候又问你 RestAssured 和 HttpClient 有什么区别。")
    assert not is_noise_question("并发测试怎么做")


def test_classify_security_and_interface():
    assert classify_question("什么是 SQL 注入，如何测试？")[0] == "安全测试"
    assert classify_question("接口测试用例应该如何设计？")[0] == "接口测试"


def test_classify_foundation_topics():
    assert classify_question("MySQL 索引为什么常用 B+ 树？")[0] == "数据库"
    assert classify_question("Linux 用户态和内核态有什么区别？")[0] == "操作系统"
    assert classify_question("TCP 三次握手为什么不是两次？")[0] == "计算机网络"
    assert classify_question("Docker Namespace 和 Cgroups 分别解决什么问题？")[0] == "Docker 与云原生"


def test_classify_ai_engineering_topics():
    assert classify_question("LLM evaluation harness 应该怎么设计？")[0] == "RAG 与 LLM 应用"
    assert classify_question("AI 面试助手的 MVP 应该验证哪些假设？")[0] == "AI 工程"


def test_generate_answer_contains_question():
    answer = generate_standard_answer("接口测试用例应该如何设计？", "接口测试")
    assert "接口测试" in answer
    assert "接口测试用例应该如何设计" in answer
