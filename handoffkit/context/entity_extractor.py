"""Entity extraction from conversation messages."""

import re
from datetime import datetime, timedelta
from typing import Optional

from handoffkit.context.models import EntityType, ExtractedEntity
from handoffkit.core.types import Message
from handoffkit.utils.logging import get_logger

# Relative date patterns mapping to day offsets
_RELATIVE_DATES: dict[str, int] = {
    "today": 0,
    "yesterday": -1,
    "tomorrow": 1,
    "last week": -7,
    "next week": 7,
}

# Weekday names for relative date parsing
_WEEKDAYS: list[str] = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


class EntityExtractor:
    """Extract entities from conversation messages.

    This class extracts various entity types from conversation text including:
    - Account numbers (with masking for PII protection)
    - Currency amounts (with normalization)
    - Dates (absolute and relative)
    - Email addresses
    - Phone numbers

    Example:
        >>> extractor = EntityExtractor()
        >>> entities = extractor.extract_entities(messages)
        >>> for entity in entities:
        ...     print(f"{entity.entity_type}: {entity.masked_value or entity.original_value}")
    """

    def __init__(self) -> None:
        """Initialize entity extractor with compiled regex patterns.

        Example:
            >>> extractor = EntityExtractor()
        """
        self._logger = get_logger("context.entities")
        self._setup_patterns()

    def _setup_patterns(self) -> None:
        """Initialize compiled regex patterns for entity extraction."""
        # Account numbers: 8-17 digits, may have spaces/dashes
        # Pattern 1: Pure digits (8-17)
        # Pattern 2: Digits with dashes/spaces (total 8-17 digits)
        self._account_pattern = re.compile(
            r"\b(\d{8,17})\b|"  # Pure digits
            r"\b(\d{2,5}[-\s]\d{2,5}[-\s]\d{2,5})\b"  # With separators like 1234-5678-9012
        )

        # Currency: $1,234.56 or 1500 dollars or USD 100
        self._currency_pattern = re.compile(
            r"(\$[\d,]+\.?\d*)|"
            r"([\d,]+\.?\d*\s*(?:dollars?|USD|EUR|GBP))|"
            r"((?:USD|EUR|GBP)\s*[\d,]+\.?\d*)",
            re.IGNORECASE,
        )

        # Dates: Various formats
        self._date_patterns = [
            re.compile(r"\b(\d{4}-\d{2}-\d{2})\b"),  # ISO: 2025-12-25
            re.compile(r"\b(\d{1,2}/\d{1,2}/\d{2,4})\b"),  # US: 12/25/2025
            re.compile(
                r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b",
                re.IGNORECASE,
            ),
        ]

        # Relative date patterns
        self._relative_date_pattern = re.compile(
            r"\b(yesterday|today|tomorrow|last\s+(?:week|"
            + "|".join(_WEEKDAYS)
            + r")|next\s+(?:week|"
            + "|".join(_WEEKDAYS)
            + r"))\b",
            re.IGNORECASE,
        )

        # Email
        self._email_pattern = re.compile(
            r"\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b"
        )

        # Phone: US and international formats
        self._phone_pattern = re.compile(
            r"\b(\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})\b"
        )

    def extract_entities(
        self,
        conversation: list[Message],
    ) -> list[ExtractedEntity]:
        """Extract all entities from conversation messages.

        Args:
            conversation: List of Message objects

        Returns:
            List of ExtractedEntity objects found in the conversation

        Example:
            >>> extractor = EntityExtractor()
            >>> messages = [Message(speaker="user", content="Account 12345678")]
            >>> entities = extractor.extract_entities(messages)
            >>> len(entities) >= 1
            True
        """
        self._logger.info(
            "Starting entity extraction",
            extra={"conversation_length": len(conversation)},
        )

        entities: list[ExtractedEntity] = []

        for idx, msg in enumerate(conversation):
            message_entities = self._extract_from_message(
                msg.content, idx, msg.timestamp
            )
            entities.extend(message_entities)

        self._logger.info(
            "Entity extraction completed",
            extra={
                "total_entities": len(entities),
                "entity_types": list({e.entity_type.value for e in entities}),
            },
        )

        return entities

    def _extract_from_message(
        self,
        content: str,
        message_index: int,
        reference_time: datetime,
    ) -> list[ExtractedEntity]:
        """Extract entities from a single message.

        Args:
            content: Message text content
            message_index: Index of this message in the conversation
            reference_time: Timestamp for relative date calculations

        Returns:
            List of ExtractedEntity objects found in this message
        """
        entities: list[ExtractedEntity] = []

        # Track extracted positions to avoid overlaps
        extracted_positions: set[tuple[int, int]] = set()

        # Extract in priority order: dates and phones first to avoid
        # false matches from account pattern with dashes
        entities.extend(
            self._extract_dates(content, message_index, reference_time, extracted_positions)
        )
        entities.extend(
            self._extract_phones(content, message_index, extracted_positions)
        )
        entities.extend(
            self._extract_accounts(content, message_index, extracted_positions)
        )
        entities.extend(
            self._extract_currency(content, message_index, extracted_positions)
        )
        entities.extend(
            self._extract_emails(content, message_index, extracted_positions)
        )

        return entities

    def _is_overlapping(
        self,
        start: int,
        end: int,
        extracted_positions: set[tuple[int, int]],
    ) -> bool:
        """Check if a position range overlaps with already extracted entities."""
        for ex_start, ex_end in extracted_positions:
            if start < ex_end and end > ex_start:
                return True
        return False

    def _extract_accounts(
        self,
        content: str,
        message_index: int,
        extracted_positions: set[tuple[int, int]],
    ) -> list[ExtractedEntity]:
        """Extract account numbers from message content.

        Args:
            content: Message text
            message_index: Index of the message
            extracted_positions: Set of already extracted position ranges

        Returns:
            List of account number entities
        """
        entities: list[ExtractedEntity] = []

        for match in self._account_pattern.finditer(content):
            start, end = match.span()
            if self._is_overlapping(start, end, extracted_positions):
                continue

            # Get the matched group (either group 1 or group 2)
            original = match.group(1) or match.group(2)
            if not original:
                continue

            masked = self._mask_account(original)

            entities.append(
                ExtractedEntity(
                    entity_type=EntityType.ACCOUNT_NUMBER,
                    original_value=original,
                    masked_value=masked,
                    normalized_value=None,
                    message_index=message_index,
                    start_pos=start,
                    end_pos=end,
                )
            )
            extracted_positions.add((start, end))

        return entities

    def _mask_account(self, account: str) -> str:
        """Mask account number showing only last 4 digits.

        Args:
            account: Account number string

        Returns:
            Masked account with asterisks replacing all but last 4 digits

        Example:
            >>> extractor._mask_account("12345678")
            '****5678'
        """
        # Remove spaces and dashes for digit counting
        digits = re.sub(r"[\s\-]", "", account)
        if len(digits) > 4:
            return "*" * (len(digits) - 4) + digits[-4:]
        return digits  # Return as-is if 4 or fewer digits

    def _extract_currency(
        self,
        content: str,
        message_index: int,
        extracted_positions: set[tuple[int, int]],
    ) -> list[ExtractedEntity]:
        """Extract currency amounts from message content.

        Args:
            content: Message text
            message_index: Index of the message
            extracted_positions: Set of already extracted position ranges

        Returns:
            List of currency entities
        """
        entities: list[ExtractedEntity] = []

        for match in self._currency_pattern.finditer(content):
            start, end = match.span()
            if self._is_overlapping(start, end, extracted_positions):
                continue

            # Get the matched group (one of the alternates)
            original = match.group(0).strip()
            if not original:
                continue

            amount, currency_code = self._normalize_currency(original)
            normalized = f"{amount} {currency_code}"

            entities.append(
                ExtractedEntity(
                    entity_type=EntityType.CURRENCY,
                    original_value=original,
                    masked_value=None,
                    normalized_value=normalized,
                    message_index=message_index,
                    start_pos=start,
                    end_pos=end,
                )
            )
            extracted_positions.add((start, end))

        return entities

    def _normalize_currency(self, value: str) -> tuple[float, str]:
        """Normalize currency to amount and currency code.

        Args:
            value: Currency string (e.g., "$1,234.56", "100 EUR", "1.234,56 EUR")

        Returns:
            Tuple of (amount as float, currency code string)

        Example:
            >>> extractor._normalize_currency("$1,234.56")
            (1234.56, 'USD')
        """
        # Extract digits, decimal point, and comma
        amount_str = re.sub(r"[^\d.,]", "", value)

        # Handle European format (1.234,56) vs US format (1,234.56)
        # European: dots are thousand separators, comma is decimal
        # US: commas are thousand separators, dot is decimal
        if "," in amount_str and "." in amount_str:
            # Both present - determine format by position
            last_comma = amount_str.rfind(",")
            last_dot = amount_str.rfind(".")
            if last_comma > last_dot:
                # European format: 1.234,56 -> comma is decimal
                amount_str = amount_str.replace(".", "").replace(",", ".")
            else:
                # US format: 1,234.56 -> dot is decimal
                amount_str = amount_str.replace(",", "")
        elif "," in amount_str:
            # Only comma - check if it's decimal (e.g., "1,50") or thousand (e.g., "1,000")
            parts = amount_str.split(",")
            if len(parts) == 2 and len(parts[1]) <= 2:
                # Likely decimal: 1,50 or 100,99
                amount_str = amount_str.replace(",", ".")
            else:
                # Likely thousand separator: 1,000 or 1,234,567
                amount_str = amount_str.replace(",", "")
        # If only dot, it's already correct format

        try:
            amount = float(amount_str) if amount_str else 0.0
        except ValueError:
            amount = 0.0

        # Detect currency
        value_upper = value.upper()
        if "$" in value or "USD" in value_upper:
            currency = "USD"
        elif "EUR" in value_upper or "€" in value:
            currency = "EUR"
        elif "GBP" in value_upper or "£" in value:
            currency = "GBP"
        else:
            currency = "USD"  # Default

        return amount, currency

    def _extract_dates(
        self,
        content: str,
        message_index: int,
        reference_time: datetime,
        extracted_positions: set[tuple[int, int]],
    ) -> list[ExtractedEntity]:
        """Extract dates from message content.

        Args:
            content: Message text
            message_index: Index of the message
            reference_time: Reference timestamp for relative date parsing
            extracted_positions: Set of already extracted position ranges

        Returns:
            List of date entities
        """
        entities: list[ExtractedEntity] = []

        # Extract absolute dates
        for pattern in self._date_patterns:
            for match in pattern.finditer(content):
                start, end = match.span()
                if self._is_overlapping(start, end, extracted_positions):
                    continue

                original = match.group(1)
                normalized = self._normalize_date(original)

                entities.append(
                    ExtractedEntity(
                        entity_type=EntityType.DATE,
                        original_value=original,
                        masked_value=None,
                        normalized_value=normalized,
                        message_index=message_index,
                        start_pos=start,
                        end_pos=end,
                    )
                )
                extracted_positions.add((start, end))

        # Extract relative dates
        for match in self._relative_date_pattern.finditer(content):
            start, end = match.span()
            if self._is_overlapping(start, end, extracted_positions):
                continue

            original = match.group(1)
            normalized = self._parse_relative_date(original, reference_time)

            if normalized:
                entities.append(
                    ExtractedEntity(
                        entity_type=EntityType.DATE,
                        original_value=original,
                        masked_value=None,
                        normalized_value=normalized,
                        message_index=message_index,
                        start_pos=start,
                        end_pos=end,
                    )
                )
                extracted_positions.add((start, end))

        return entities

    def _normalize_date(self, date_str: str) -> Optional[str]:
        """Normalize date string to ISO 8601 format.

        Args:
            date_str: Date string in various formats

        Returns:
            ISO 8601 date string (YYYY-MM-DD) or original if parsing fails
        """
        # Already ISO format
        if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
            return date_str

        # Try US format MM/DD/YYYY or MM/DD/YY
        us_match = re.match(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", date_str)
        if us_match:
            month, day, year = us_match.groups()
            if len(year) == 2:
                year = "20" + year if int(year) < 50 else "19" + year
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

        # Try "Month DD, YYYY" or "Month DD YYYY" format
        month_names = {
            "jan": "01", "january": "01",
            "feb": "02", "february": "02",
            "mar": "03", "march": "03",
            "apr": "04", "april": "04",
            "may": "05",
            "jun": "06", "june": "06",
            "jul": "07", "july": "07",
            "aug": "08", "august": "08",
            "sep": "09", "september": "09",
            "oct": "10", "october": "10",
            "nov": "11", "november": "11",
            "dec": "12", "december": "12",
        }
        month_match = re.match(
            r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", date_str
        )
        if month_match:
            month_name, day, year = month_match.groups()
            month_num = month_names.get(month_name.lower())
            if month_num:
                return f"{year}-{month_num}-{day.zfill(2)}"

        # Return original if can't normalize
        return date_str

    def _parse_relative_date(
        self, text: str, reference: datetime
    ) -> Optional[str]:
        """Parse relative date to ISO 8601 format.

        Args:
            text: Relative date text (e.g., "yesterday", "last Tuesday")
            reference: Reference datetime for calculation

        Returns:
            ISO 8601 date string (YYYY-MM-DD) or None if not parseable

        Example:
            >>> extractor._parse_relative_date("yesterday", datetime(2024, 1, 15))
            '2024-01-14'
        """
        text_lower = text.lower()

        # Check simple relative dates
        for pattern, days in _RELATIVE_DATES.items():
            if pattern in text_lower:
                result = reference + timedelta(days=days)
                return result.strftime("%Y-%m-%d")

        # Handle "last/next <weekday>"
        for i, day in enumerate(_WEEKDAYS):
            if f"last {day}" in text_lower:
                # Calculate last occurrence of this weekday
                days_ago = (reference.weekday() - i) % 7
                if days_ago == 0:
                    days_ago = 7
                result = reference - timedelta(days=days_ago)
                return result.strftime("%Y-%m-%d")

            if f"next {day}" in text_lower:
                # Calculate next occurrence of this weekday
                days_ahead = (i - reference.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                result = reference + timedelta(days=days_ahead)
                return result.strftime("%Y-%m-%d")

        return None

    def _extract_emails(
        self,
        content: str,
        message_index: int,
        extracted_positions: set[tuple[int, int]],
    ) -> list[ExtractedEntity]:
        """Extract email addresses from message content.

        Args:
            content: Message text
            message_index: Index of the message
            extracted_positions: Set of already extracted position ranges

        Returns:
            List of email entities
        """
        entities: list[ExtractedEntity] = []

        for match in self._email_pattern.finditer(content):
            start, end = match.span()
            if self._is_overlapping(start, end, extracted_positions):
                continue

            original = match.group(1)

            # Mask email: show first char, mask middle, show domain
            masked = self._mask_email(original)

            entities.append(
                ExtractedEntity(
                    entity_type=EntityType.EMAIL,
                    original_value=original,
                    masked_value=masked,
                    normalized_value=original.lower(),
                    message_index=message_index,
                    start_pos=start,
                    end_pos=end,
                )
            )
            extracted_positions.add((start, end))

        return entities

    def _mask_email(self, email: str) -> str:
        """Mask email address for PII protection.

        Args:
            email: Email address string

        Returns:
            Masked email like 'u***r@example.com'
        """
        if "@" not in email:
            return email

        local, domain = email.rsplit("@", 1)
        if len(local) <= 2:
            masked_local = local[0] + "***"
        else:
            masked_local = local[0] + "***" + local[-1]

        return f"{masked_local}@{domain}"

    def _extract_phones(
        self,
        content: str,
        message_index: int,
        extracted_positions: set[tuple[int, int]],
    ) -> list[ExtractedEntity]:
        """Extract phone numbers from message content.

        Args:
            content: Message text
            message_index: Index of the message
            extracted_positions: Set of already extracted position ranges

        Returns:
            List of phone entities
        """
        entities: list[ExtractedEntity] = []

        for match in self._phone_pattern.finditer(content):
            start, end = match.span()
            if self._is_overlapping(start, end, extracted_positions):
                continue

            original = match.group(1)
            # Normalize phone: remove all non-digits
            normalized = re.sub(r"[^\d+]", "", original)
            # Mask phone: show last 4 digits
            masked = self._mask_phone(normalized)

            entities.append(
                ExtractedEntity(
                    entity_type=EntityType.PHONE,
                    original_value=original,
                    masked_value=masked,
                    normalized_value=normalized,
                    message_index=message_index,
                    start_pos=start,
                    end_pos=end,
                )
            )
            extracted_positions.add((start, end))

        return entities

    def _mask_phone(self, phone: str) -> str:
        """Mask phone number showing only last 4 digits.

        Args:
            phone: Normalized phone number (digits only)

        Returns:
            Masked phone with asterisks replacing all but last 4 digits
        """
        # Remove + prefix for masking calculation
        digits = phone.lstrip("+")
        if len(digits) > 4:
            return "***-***-" + digits[-4:]
        return digits
