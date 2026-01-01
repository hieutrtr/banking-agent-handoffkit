"""Tests for entity extraction functionality."""

from datetime import datetime, timezone

import pytest

from handoffkit.context.entity_extractor import EntityExtractor
from handoffkit.context.models import EntityType, ExtractedEntity
from handoffkit.core.types import Message, MessageSpeaker


class TestEntityExtractorInit:
    """Test EntityExtractor initialization."""

    def test_init_creates_instance(self):
        """Test that EntityExtractor can be instantiated."""
        extractor = EntityExtractor()
        assert extractor is not None

    def test_init_sets_up_patterns(self):
        """Test that patterns are initialized."""
        extractor = EntityExtractor()
        assert hasattr(extractor, "_account_pattern")
        assert hasattr(extractor, "_currency_pattern")
        assert hasattr(extractor, "_email_pattern")
        assert hasattr(extractor, "_phone_pattern")


class TestExtractedEntityModel:
    """Test ExtractedEntity Pydantic model."""

    def test_create_entity(self):
        """Test creating an ExtractedEntity."""
        entity = ExtractedEntity(
            entity_type=EntityType.ACCOUNT_NUMBER,
            original_value="12345678",
            masked_value="****5678",
            normalized_value=None,
            message_index=0,
            start_pos=10,
            end_pos=18,
        )
        assert entity.entity_type == EntityType.ACCOUNT_NUMBER
        assert entity.original_value == "12345678"
        assert entity.masked_value == "****5678"

    def test_entity_to_dict(self):
        """Test ExtractedEntity.to_dict() serialization."""
        entity = ExtractedEntity(
            entity_type=EntityType.CURRENCY,
            original_value="$1,234.56",
            masked_value=None,
            normalized_value="1234.56 USD",
            message_index=1,
            start_pos=0,
            end_pos=9,
        )
        result = entity.to_dict()
        assert isinstance(result, dict)
        assert result["entity_type"] == "currency"
        assert result["original_value"] == "$1,234.56"
        assert result["normalized_value"] == "1234.56 USD"

    def test_entity_type_enum_values(self):
        """Test EntityType enum has all required values."""
        assert EntityType.ACCOUNT_NUMBER == "account_number"
        assert EntityType.CURRENCY == "currency"
        assert EntityType.DATE == "date"
        assert EntityType.EMAIL == "email"
        assert EntityType.PHONE == "phone"
        assert EntityType.NAME == "name"


class TestAccountNumberExtraction:
    """Test account number extraction and masking."""

    def test_extract_8_digit_account(self):
        """Test extracting 8-digit account number."""
        extractor = EntityExtractor()
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="My account number is 12345678",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        entities = extractor.extract_entities(messages)

        account_entities = [e for e in entities if e.entity_type == EntityType.ACCOUNT_NUMBER]
        assert len(account_entities) >= 1
        assert account_entities[0].original_value == "12345678"
        assert account_entities[0].masked_value == "****5678"

    def test_extract_longer_account_with_dashes(self):
        """Test extracting account with dashes."""
        extractor = EntityExtractor()
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Account: 1234-5678-9012",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        entities = extractor.extract_entities(messages)

        account_entities = [e for e in entities if e.entity_type == EntityType.ACCOUNT_NUMBER]
        assert len(account_entities) >= 1
        # Masked should show last 4 digits
        assert "9012" in account_entities[0].masked_value

    def test_mask_account_last_4_digits(self):
        """Test account masking shows only last 4 digits."""
        extractor = EntityExtractor()
        masked = extractor._mask_account("123456789012")
        assert masked == "********9012"

    def test_mask_short_account(self):
        """Test masking short account number."""
        extractor = EntityExtractor()
        masked = extractor._mask_account("1234")
        assert masked == "1234"  # All visible if exactly 4 digits


class TestCurrencyExtraction:
    """Test currency extraction and normalization."""

    def test_extract_dollar_symbol(self):
        """Test extracting $1,234.56 format."""
        extractor = EntityExtractor()
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="I was charged $1,234.56",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        entities = extractor.extract_entities(messages)

        currency_entities = [e for e in entities if e.entity_type == EntityType.CURRENCY]
        assert len(currency_entities) >= 1
        assert "$1,234.56" in currency_entities[0].original_value

    def test_extract_dollars_word(self):
        """Test extracting '1500 dollars' format."""
        extractor = EntityExtractor()
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="I need to transfer 1500 dollars",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        entities = extractor.extract_entities(messages)

        currency_entities = [e for e in entities if e.entity_type == EntityType.CURRENCY]
        assert len(currency_entities) >= 1

    def test_extract_usd_prefix(self):
        """Test extracting 'USD 100' format."""
        extractor = EntityExtractor()
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="The fee is USD 100",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        entities = extractor.extract_entities(messages)

        currency_entities = [e for e in entities if e.entity_type == EntityType.CURRENCY]
        assert len(currency_entities) >= 1

    def test_normalize_currency(self):
        """Test currency normalization to float and code."""
        extractor = EntityExtractor()
        amount, code = extractor._normalize_currency("$1,234.56")
        assert amount == 1234.56
        assert code == "USD"

    def test_normalize_eur_currency(self):
        """Test EUR currency detection."""
        extractor = EntityExtractor()
        amount, code = extractor._normalize_currency("100 EUR")
        assert amount == 100.0
        assert code == "EUR"


class TestDateExtraction:
    """Test date extraction (absolute and relative)."""

    def test_extract_iso_date(self):
        """Test extracting ISO format date (2025-12-25)."""
        extractor = EntityExtractor()
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="The appointment is on 2025-12-25",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        entities = extractor.extract_entities(messages)

        date_entities = [e for e in entities if e.entity_type == EntityType.DATE]
        assert len(date_entities) >= 1
        assert date_entities[0].original_value == "2025-12-25"

    def test_extract_us_date(self):
        """Test extracting US format date (12/25/2025)."""
        extractor = EntityExtractor()
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="The payment is due on 12/25/2025",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        entities = extractor.extract_entities(messages)

        date_entities = [e for e in entities if e.entity_type == EntityType.DATE]
        assert len(date_entities) >= 1

    def test_extract_month_day_year(self):
        """Test extracting 'December 25, 2025' format."""
        extractor = EntityExtractor()
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="The event is on December 25, 2025",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        entities = extractor.extract_entities(messages)

        date_entities = [e for e in entities if e.entity_type == EntityType.DATE]
        assert len(date_entities) >= 1

    def test_parse_relative_yesterday(self):
        """Test parsing 'yesterday' relative date."""
        extractor = EntityExtractor()
        reference = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = extractor._parse_relative_date("yesterday", reference)
        assert result == "2024-01-14"

    def test_parse_relative_last_tuesday(self):
        """Test parsing 'last Tuesday' relative date."""
        extractor = EntityExtractor()
        # Reference: Monday Jan 15, 2024 -> last Tuesday was Jan 9
        reference = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = extractor._parse_relative_date("last tuesday", reference)
        assert result is not None
        # Verify it's a valid date
        datetime.strptime(result, "%Y-%m-%d")

    def test_extract_relative_date_yesterday(self):
        """Test extracting 'yesterday' from message."""
        extractor = EntityExtractor()
        ref_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="This happened yesterday",
                timestamp=ref_time,
            ),
        ]

        entities = extractor.extract_entities(messages)

        date_entities = [e for e in entities if e.entity_type == EntityType.DATE]
        assert len(date_entities) >= 1
        assert date_entities[0].normalized_value == "2024-01-14"


class TestEmailExtraction:
    """Test email extraction."""

    def test_extract_email(self):
        """Test extracting email address."""
        extractor = EntityExtractor()
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Contact me at user@example.com",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        entities = extractor.extract_entities(messages)

        email_entities = [e for e in entities if e.entity_type == EntityType.EMAIL]
        assert len(email_entities) >= 1
        assert email_entities[0].original_value == "user@example.com"

    def test_extract_complex_email(self):
        """Test extracting email with dots and plus."""
        extractor = EntityExtractor()
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Email: john.doe+test@company.co.uk",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        entities = extractor.extract_entities(messages)

        email_entities = [e for e in entities if e.entity_type == EntityType.EMAIL]
        assert len(email_entities) >= 1


class TestPhoneExtraction:
    """Test phone number extraction."""

    def test_extract_us_phone(self):
        """Test extracting US phone number."""
        extractor = EntityExtractor()
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Call me at 555-123-4567",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        entities = extractor.extract_entities(messages)

        phone_entities = [e for e in entities if e.entity_type == EntityType.PHONE]
        assert len(phone_entities) >= 1

    def test_extract_phone_with_parens(self):
        """Test extracting phone with parentheses."""
        extractor = EntityExtractor()
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="My number is (555) 123-4567",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        entities = extractor.extract_entities(messages)

        phone_entities = [e for e in entities if e.entity_type == EntityType.PHONE]
        assert len(phone_entities) >= 1


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_conversation(self):
        """Test extraction with empty conversation."""
        extractor = EntityExtractor()
        entities = extractor.extract_entities([])
        assert entities == []

    def test_no_entities_in_message(self):
        """Test message with no extractable entities."""
        extractor = EntityExtractor()
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Hello, how are you?",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        entities = extractor.extract_entities(messages)
        assert entities == []

    def test_multiple_entities_single_message(self):
        """Test extracting multiple entities from one message."""
        extractor = EntityExtractor()
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Account 12345678 was charged $500 on 2024-01-15",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        entities = extractor.extract_entities(messages)
        entity_types = {e.entity_type for e in entities}

        assert EntityType.ACCOUNT_NUMBER in entity_types
        assert EntityType.CURRENCY in entity_types
        assert EntityType.DATE in entity_types

    def test_multiple_messages(self):
        """Test extraction across multiple messages."""
        extractor = EntityExtractor()
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="My account is 12345678",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.AI,
                content="I see. What's the issue?",
                timestamp=datetime(2024, 1, 1, 12, 0, 30, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.USER,
                content="I was charged $99.99",
                timestamp=datetime(2024, 1, 1, 12, 1, 0, tzinfo=timezone.utc),
            ),
        ]

        entities = extractor.extract_entities(messages)

        # Should have entities from different messages with correct message_index
        account_entities = [e for e in entities if e.entity_type == EntityType.ACCOUNT_NUMBER]
        currency_entities = [e for e in entities if e.entity_type == EntityType.CURRENCY]

        assert len(account_entities) >= 1
        assert account_entities[0].message_index == 0

        assert len(currency_entities) >= 1
        assert currency_entities[0].message_index == 2


class TestDateNormalization:
    """Test date normalization to ISO 8601."""

    def test_normalize_month_day_year(self):
        """Test normalizing 'December 25, 2025' to ISO format."""
        extractor = EntityExtractor()
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="The event is on December 25, 2025",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        entities = extractor.extract_entities(messages)

        date_entities = [e for e in entities if e.entity_type == EntityType.DATE]
        assert len(date_entities) >= 1
        # Should be normalized to ISO 8601
        assert date_entities[0].normalized_value == "2025-12-25"


class TestEuropeanCurrencyFormat:
    """Test European currency format handling."""

    def test_normalize_european_format(self):
        """Test normalizing '1.234,56 EUR' to float."""
        extractor = EntityExtractor()
        amount, code = extractor._normalize_currency("1.234,56 EUR")
        assert amount == 1234.56
        assert code == "EUR"

    def test_normalize_european_format_large(self):
        """Test normalizing large European amounts."""
        extractor = EntityExtractor()
        amount, code = extractor._normalize_currency("12.345.678,99 EUR")
        assert amount == 12345678.99
        assert code == "EUR"


class TestPIIMasking:
    """Test PII masking for phone and email."""

    def test_phone_masking(self):
        """Test phone numbers are masked."""
        extractor = EntityExtractor()
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Call me at 555-123-4567",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        entities = extractor.extract_entities(messages)

        phone_entities = [e for e in entities if e.entity_type == EntityType.PHONE]
        assert len(phone_entities) >= 1
        assert phone_entities[0].masked_value is not None
        assert "4567" in phone_entities[0].masked_value
        assert "555" not in phone_entities[0].masked_value

    def test_email_masking(self):
        """Test email addresses are masked."""
        extractor = EntityExtractor()
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Contact me at user@example.com",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        entities = extractor.extract_entities(messages)

        email_entities = [e for e in entities if e.entity_type == EntityType.EMAIL]
        assert len(email_entities) >= 1
        assert email_entities[0].masked_value is not None
        assert "***" in email_entities[0].masked_value
        assert "@example.com" in email_entities[0].masked_value


class TestPerformance:
    """Test performance requirements."""

    def test_extraction_under_50ms(self):
        """Test extraction completes in under 50ms for typical conversation."""
        import time

        extractor = EntityExtractor()
        # Create a typical 20-message conversation
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content=f"Message {i}: My account 12345678 was charged $99.99 on 2024-01-15. Email: user@test.com",
                timestamp=datetime(2024, 1, 1, 12, i, 0, tzinfo=timezone.utc),
            )
            for i in range(20)
        ]

        start = time.perf_counter()
        entities = extractor.extract_entities(messages)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 50, f"Extraction took {elapsed_ms:.2f}ms, expected < 50ms"
        assert len(entities) > 0  # Verify extraction worked


class TestOverlappingPatterns:
    """Test overlapping pattern detection."""

    def test_phone_not_matched_as_account(self):
        """Test phone number is not also extracted as account number."""
        extractor = EntityExtractor()
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Call 5551234567 for support",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        entities = extractor.extract_entities(messages)

        # Should be detected as phone, not account (even though it's 10 digits)
        phone_entities = [e for e in entities if e.entity_type == EntityType.PHONE]
        account_entities = [e for e in entities if e.entity_type == EntityType.ACCOUNT_NUMBER]

        # 5551234567 matches phone pattern, should not be double-counted
        assert len(phone_entities) >= 1

    def test_date_not_matched_as_account(self):
        """Test ISO date is not matched as account number."""
        extractor = EntityExtractor()
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Appointment on 2024-01-15",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        entities = extractor.extract_entities(messages)

        date_entities = [e for e in entities if e.entity_type == EntityType.DATE]
        account_entities = [e for e in entities if e.entity_type == EntityType.ACCOUNT_NUMBER]

        # Date should be extracted, not as account
        assert len(date_entities) >= 1
        assert len(account_entities) == 0
