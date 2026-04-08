"""Tests for Chinese memory extraction in general_extractor."""

from mempalace.general_extractor import extract_memories


class TestChineseDecisionExtraction:
    def test_chinese_decision(self):
        text = "经过讨论，我们决定使用 GraphQL 而不是 REST API。这个方案更适合我们的需求。"
        memories = extract_memories(text, min_confidence=0.1)
        types = [m["memory_type"] for m in memories]
        assert "decision" in types

    def test_traditional_decision(self):
        text = "經過討論，我們決定使用 GraphQL 而不是 REST API。這個方案更適合我們的需求。"
        memories = extract_memories(text, min_confidence=0.1)
        types = [m["memory_type"] for m in memories]
        assert "decision" in types


class TestChinesePreferenceExtraction:
    def test_chinese_preference(self):
        text = "我偏好函数式风格，总是用不可变数据结构。千万不要用全局变量。"
        memories = extract_memories(text, min_confidence=0.1)
        types = [m["memory_type"] for m in memories]
        assert "preference" in types


class TestChineseMilestoneExtraction:
    def test_chinese_milestone(self):
        text = "终于成功了！经过三天的努力，我们实现了完整的搜索功能。这是一个重大突破。"
        memories = extract_memories(text, min_confidence=0.1)
        types = [m["memory_type"] for m in memories]
        assert "milestone" in types


class TestChineseProblemExtraction:
    def test_chinese_problem(self):
        text = "系统出现了严重的错误，数据库崩溃导致服务失败。根本原因是内存泄漏。"
        memories = extract_memories(text, min_confidence=0.1)
        types = [m["memory_type"] for m in memories]
        assert "problem" in types


class TestChineseEmotionExtraction:
    def test_chinese_emotion(self):
        text = "我真的很开心，这个项目让我感到骄傲。我觉得团队做得非常好，我很感恩。"
        memories = extract_memories(text, min_confidence=0.1)
        types = [m["memory_type"] for m in memories]
        assert "emotional" in types


class TestEnglishUnchanged:
    def test_english_extraction_still_works(self):
        text = "We decided to use PostgreSQL because it has better JSON support. The trade-off was worth it."
        memories = extract_memories(text, min_confidence=0.1)
        types = [m["memory_type"] for m in memories]
        assert "decision" in types
