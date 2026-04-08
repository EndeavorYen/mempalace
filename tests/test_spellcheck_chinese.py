"""Tests for Chinese handling in spellcheck."""

from mempalace.spellcheck import spellcheck_user_text, _should_skip


class TestChineseSpellcheck:
    def test_chinese_text_skipped(self):
        """Chinese-dominant text should be returned unchanged."""
        text = "这是中文内容，不需要拼写检查"
        assert spellcheck_user_text(text) == text

    def test_chinese_token_skipped(self):
        """Individual Chinese tokens should be skipped by _should_skip."""
        assert _should_skip("中文", set()) is True
        assert _should_skip("数据库", set()) is True

    def test_english_text_still_works(self):
        """English text should still go through spellcheck."""
        # Without autocorrect installed, text is returned as-is
        text = "This is normal English text"
        result = spellcheck_user_text(text)
        assert isinstance(result, str)

    def test_mixed_text_with_chinese_majority(self):
        """Mixed text with Chinese majority should skip spellcheck."""
        text = "我们今天讨论了很多关于系统架构的问题，包括 database 的选择"
        assert spellcheck_user_text(text) == text
