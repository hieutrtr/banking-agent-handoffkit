"""Tests for KeywordTrigger.

This module tests the critical keyword monitoring trigger which identifies
when users mention fraud, emergencies, or other urgent matters requiring
immediate human attention.
"""

import time

import pytest

from handoffkit.core.types import Message, TriggerResult, TriggerType
from handoffkit.triggers.keyword import KeywordTrigger

# Note: TriggerType.CRITICAL_KEYWORD is the actual enum value


class TestKeywordTriggerBasic:
    """Basic tests for KeywordTrigger evaluate method."""

    @pytest.fixture
    def trigger(self) -> KeywordTrigger:
        """Create a KeywordTrigger instance."""
        return KeywordTrigger()

    @pytest.mark.asyncio
    async def test_returns_trigger_result(self, trigger: KeywordTrigger):
        """Test that evaluate returns a TriggerResult."""
        message = Message(speaker="user", content="Hello")
        result = await trigger.evaluate(message)

        assert isinstance(result, TriggerResult)

    @pytest.mark.asyncio
    async def test_normal_message_does_not_trigger(self, trigger: KeywordTrigger):
        """Test that normal messages don't trigger."""
        message = Message(speaker="user", content="What is my account balance?")
        result = await trigger.evaluate(message)

        assert result.triggered is False
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_trigger_type_is_keyword(self, trigger: KeywordTrigger):
        """Test that trigger_type is KEYWORD when triggered (AC #1)."""
        message = Message(speaker="user", content="There is fraud on my account")
        result = await trigger.evaluate(message)

        assert result.triggered is True
        assert result.trigger_type == TriggerType.CRITICAL_KEYWORD


class TestDefaultKeywords:
    """Tests for default keyword detection (AC #2)."""

    @pytest.fixture
    def trigger(self) -> KeywordTrigger:
        """Create a KeywordTrigger instance."""
        return KeywordTrigger()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("keyword", [
        "fraud",
        "emergency",
        "locked out",
        "dispute",
        "unauthorized",
        "stolen",
    ])
    async def test_default_keywords_trigger(self, trigger: KeywordTrigger, keyword: str):
        """Test that default critical keywords trigger (AC #2)."""
        message = Message(speaker="user", content=f"I have a {keyword} issue")
        result = await trigger.evaluate(message)

        assert result.triggered is True, f"Failed to detect keyword: '{keyword}'"
        assert result.trigger_type == TriggerType.CRITICAL_KEYWORD

    @pytest.mark.asyncio
    @pytest.mark.parametrize("keyword", [
        # Financial
        "fraud",
        "unauthorized",
        "stolen",
        "dispute",
        "chargeback",
        # Safety
        "emergency",
        "threat",
        "danger",
        "harm",
        "suicide",
        "crisis",
        # Legal
        "lawsuit",
        "attorney",
        "lawyer",
        "sue",
        # Urgency
        "urgent",
        "immediately",
        "asap",
        "critical",
    ])
    async def test_all_default_keywords(self, trigger: KeywordTrigger, keyword: str):
        """Test all default keywords trigger."""
        message = Message(speaker="user", content=f"This is about {keyword}")
        result = await trigger.evaluate(message)

        assert result.triggered is True, f"Failed to detect keyword: '{keyword}'"

    @pytest.mark.asyncio
    async def test_fraud_with_unauthorized_transaction(self, trigger: KeywordTrigger):
        """Test fraud or unauthorized transaction triggers (AC #1)."""
        message = Message(speaker="user", content="I see an unauthorized transaction on my account")
        result = await trigger.evaluate(message)

        assert result.triggered is True
        assert result.trigger_type == TriggerType.CRITICAL_KEYWORD

    @pytest.mark.asyncio
    async def test_priority_is_immediate(self, trigger: KeywordTrigger):
        """Test that priority is set to immediate in metadata (AC #1)."""
        message = Message(speaker="user", content="There is fraud on my account")
        result = await trigger.evaluate(message)

        assert result.triggered is True
        assert result.metadata.get("priority") == "immediate"


class TestMultiWordPhrases:
    """Tests for multi-word phrase detection."""

    @pytest.fixture
    def trigger(self) -> KeywordTrigger:
        """Create a KeywordTrigger instance."""
        return KeywordTrigger()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("phrase", [
        "locked out",
        "legal action",
        "right now",
        "locked account",
        "cannot access",
    ])
    async def test_multi_word_phrases_trigger(self, trigger: KeywordTrigger, phrase: str):
        """Test multi-word phrases are detected correctly."""
        message = Message(speaker="user", content=f"I am {phrase} of my account")
        result = await trigger.evaluate(message)

        assert result.triggered is True, f"Failed to detect phrase: '{phrase}'"


class TestCaseInsensitivity:
    """Tests for case insensitivity (AC #5)."""

    @pytest.fixture
    def trigger(self) -> KeywordTrigger:
        """Create a KeywordTrigger instance."""
        return KeywordTrigger()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("variant", [
        "FRAUD",
        "Fraud",
        "fraud",
        "FrAuD",
    ])
    async def test_case_insensitive_matching(self, trigger: KeywordTrigger, variant: str):
        """Test case insensitivity for keywords (AC #5)."""
        message = Message(speaker="user", content=f"There is {variant} on my account")
        result = await trigger.evaluate(message)

        assert result.triggered is True, f"Failed with case variant: '{variant}'"

    @pytest.mark.asyncio
    async def test_case_sensitive_mode(self):
        """Test case sensitive mode only matches exact case."""
        trigger = KeywordTrigger(case_sensitive=True)

        # Lowercase should match (assuming default keywords are lowercase)
        message1 = Message(speaker="user", content="There is fraud on my account")
        result1 = await trigger.evaluate(message1)
        assert result1.triggered is True

        # Uppercase should NOT match in case-sensitive mode
        message2 = Message(speaker="user", content="There is FRAUD on my account")
        result2 = await trigger.evaluate(message2)
        assert result2.triggered is False


class TestCustomKeywords:
    """Tests for custom keyword configuration (AC #3)."""

    @pytest.mark.asyncio
    async def test_custom_keywords_trigger(self):
        """Test custom keywords trigger (AC #3)."""
        custom_keywords = ["regulation E", "FDIC complaint"]
        trigger = KeywordTrigger(keywords=custom_keywords)

        message = Message(speaker="user", content="I want to file a regulation E dispute")
        result = await trigger.evaluate(message)

        assert result.triggered is True

    @pytest.mark.asyncio
    async def test_fdic_complaint_keyword(self):
        """Test FDIC complaint custom keyword (AC #3)."""
        custom_keywords = ["regulation E", "FDIC complaint"]
        trigger = KeywordTrigger(keywords=custom_keywords)

        message = Message(speaker="user", content="I will file an FDIC complaint")
        result = await trigger.evaluate(message)

        assert result.triggered is True

    @pytest.mark.asyncio
    async def test_custom_keywords_replace_defaults(self):
        """Test that custom keywords replace default keywords."""
        custom_keywords = ["custom_word"]
        trigger = KeywordTrigger(keywords=custom_keywords)

        # Default keyword should NOT trigger
        message1 = Message(speaker="user", content="There is fraud on my account")
        result1 = await trigger.evaluate(message1)
        assert result1.triggered is False

        # Custom keyword should trigger
        message2 = Message(speaker="user", content="This is a custom_word situation")
        result2 = await trigger.evaluate(message2)
        assert result2.triggered is True


class TestNoFalsePositives:
    """Tests for avoiding false positives."""

    @pytest.fixture
    def trigger(self) -> KeywordTrigger:
        """Create a KeywordTrigger instance."""
        return KeywordTrigger()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("message_text", [
        "What is my account balance?",
        "How do I reset my password?",
        "Can you explain the fees?",
        "Thanks for your help!",
        "I have a question about payments",
    ])
    async def test_normal_messages_no_false_positive(self, trigger: KeywordTrigger, message_text: str):
        """Test that normal messages don't trigger false positives."""
        message = Message(speaker="user", content=message_text)
        result = await trigger.evaluate(message)

        assert result.triggered is False, f"False positive for: '{message_text}'"

    @pytest.mark.asyncio
    async def test_partial_match_no_trigger(self, trigger: KeywordTrigger):
        """Test that partial word matches don't trigger (e.g., 'defraud' shouldn't match 'fraud')."""
        message = Message(speaker="user", content="He tried to defraud the company")
        result = await trigger.evaluate(message)

        # 'defraud' contains 'fraud' but should NOT trigger due to word boundaries
        assert result.triggered is False


class TestPerformance:
    """Tests for performance requirements (AC #4)."""

    @pytest.fixture
    def trigger(self) -> KeywordTrigger:
        """Create a KeywordTrigger instance."""
        return KeywordTrigger()

    @pytest.mark.asyncio
    async def test_evaluation_under_50ms(self, trigger: KeywordTrigger):
        """Test that evaluation completes in <50ms (AC #4)."""
        message = Message(speaker="user", content="There is fraud on my account")

        start_time = time.perf_counter()
        result = await trigger.evaluate(message)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        assert elapsed_ms < 50, f"Evaluation took {elapsed_ms:.2f}ms, expected <50ms"
        assert result.triggered is True

    @pytest.mark.asyncio
    async def test_duration_in_metadata(self, trigger: KeywordTrigger):
        """Test that duration_ms is included in result metadata."""
        message = Message(speaker="user", content="Hello there")
        result = await trigger.evaluate(message)

        assert "duration_ms" in result.metadata
        assert isinstance(result.metadata["duration_ms"], float)
        assert result.metadata["duration_ms"] >= 0

    @pytest.mark.asyncio
    async def test_multiple_evaluations_fast(self, trigger: KeywordTrigger):
        """Test that 100 evaluations complete quickly."""
        messages = [
            Message(speaker="user", content=f"Test message {i}")
            for i in range(100)
        ]

        start_time = time.perf_counter()
        for message in messages:
            await trigger.evaluate(message)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # 100 evaluations should complete in <500ms (5ms each on average)
        assert elapsed_ms < 500, f"100 evaluations took {elapsed_ms:.2f}ms"


class TestMetadata:
    """Tests for metadata in trigger results."""

    @pytest.fixture
    def trigger(self) -> KeywordTrigger:
        """Create a KeywordTrigger instance."""
        return KeywordTrigger()

    @pytest.mark.asyncio
    async def test_matched_keyword_in_metadata(self, trigger: KeywordTrigger):
        """Test that matched_keyword is included in metadata."""
        message = Message(speaker="user", content="There is fraud on my account")
        result = await trigger.evaluate(message)

        assert result.triggered is True
        assert "matched_keyword" in result.metadata
        assert result.metadata["matched_keyword"] == "fraud"

    @pytest.mark.asyncio
    async def test_confidence_is_high(self, trigger: KeywordTrigger):
        """Test that confidence is 0.95 for keyword matches."""
        message = Message(speaker="user", content="This is an emergency")
        result = await trigger.evaluate(message)

        assert result.triggered is True
        assert result.confidence == 0.95


class TestTriggerProperties:
    """Tests for trigger properties."""

    def test_trigger_name(self):
        """Test that trigger_name property returns correct value."""
        trigger = KeywordTrigger()
        assert trigger.trigger_name == "keyword"

    def test_default_keywords_exist(self):
        """Test that default keywords are populated."""
        trigger = KeywordTrigger()
        assert len(trigger._keywords) > 0

    def test_case_sensitive_default_false(self):
        """Test that case_sensitive defaults to False."""
        trigger = KeywordTrigger()
        assert trigger._case_sensitive is False

    def test_custom_keywords_parameter(self):
        """Test that custom keywords parameter is accepted."""
        custom_keywords = ["test1", "test2"]
        trigger = KeywordTrigger(keywords=custom_keywords)
        assert trigger._keywords == custom_keywords
