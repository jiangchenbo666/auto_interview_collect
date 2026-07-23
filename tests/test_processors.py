from __future__ import annotations

from src.processors.answer_generator import generate_standard_answer
from src.processors.classifier import classify_question
from src.processors.extractor import extract_questions


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


def test_classify_security_and_interface():
    assert classify_question("什么是 SQL 注入，如何测试？")[0] == "安全测试"
    assert classify_question("接口测试用例应该如何设计？")[0] == "接口测试"


def test_generate_answer_contains_question():
    answer = generate_standard_answer("接口测试用例应该如何设计？", "接口测试")
    assert "接口测试" in answer
    assert "接口测试用例应该如何设计" in answer
