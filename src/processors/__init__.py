"""Question processing pipeline.

processors 的职责是把“原始文本”一步步变成“可复习内容”：
cleaner -> extractor -> classifier -> answer_generator -> project_adapter
"""
