# Story 3.3: Entity Extraction

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **support agent**,
I want to **see extracted entities (account numbers, amounts, dates) highlighted**,
So that **I can quickly understand the key details**.

## Acceptance Criteria

1. **Given** a conversation mentioning account number "12345678" **When** entities are extracted **Then** the number is identified and masked (****5678) **And** entity type is "account_number"

2. **Given** dollar amounts like "$1,234.56" or "1500 dollars" **When** entities are extracted **Then** amounts are identified with type "currency" **And** format is normalized

3. **Given** dates like "2025-12-25" or "last Tuesday" **When** entities are extracted **Then** dates are identified and parsed **And** relative dates are converted to absolute (where possible)

## Tasks / Subtasks

- [x] Task 1: Create EntityExtractor class (AC: #1, #2, #3)
  - [x] Subtask 1.1: Create `handoffkit/context/entity_extractor.py` with EntityExtractor class
  - [x] Subtask 1.2: Implement `__init__` with optional config
  - [x] Subtask 1.3: Implement `extract_entities(conversation: list[Message]) -> list[ExtractedEntity]`
  - [x] Subtask 1.4: Add structured logging with get_logger("context.entities")

- [x] Task 2: Create ExtractedEntity model (AC: #1, #2, #3)
  - [x] Subtask 2.1: Create ExtractedEntity in `handoffkit/context/models.py`
  - [x] Subtask 2.2: Fields: entity_type (enum), original_value, masked_value, normalized_value, message_index, start_pos, end_pos
  - [x] Subtask 2.3: Create EntityType enum: ACCOUNT_NUMBER, CURRENCY, DATE, EMAIL, PHONE, NAME
  - [x] Subtask 2.4: Implement to_dict() for serialization

- [x] Task 3: Implement account number extraction (AC: #1)
  - [x] Subtask 3.1: Create regex patterns for account numbers (8-17 digits)
  - [x] Subtask 3.2: Implement masking (show last 4 digits only: ****5678)
  - [x] Subtask 3.3: Handle various formats (spaces, dashes)
  - [x] Subtask 3.4: Avoid false positives (phone numbers, dates)

- [x] Task 4: Implement currency extraction (AC: #2)
  - [x] Subtask 4.1: Create regex patterns for currency ($1,234.56, 1500 dollars, USD 100)
  - [x] Subtask 4.2: Normalize to decimal format (float)
  - [x] Subtask 4.3: Handle international formats (1.234,56 EUR)
  - [x] Subtask 4.4: Extract currency symbol/code

- [x] Task 5: Implement date extraction (AC: #3)
  - [x] Subtask 5.1: Create regex patterns for absolute dates (2025-12-25, 12/25/2025, Dec 25 2025)
  - [x] Subtask 5.2: Parse relative dates (last Tuesday, yesterday, next week)
  - [x] Subtask 5.3: Convert to ISO 8601 format (YYYY-MM-DD)
  - [x] Subtask 5.4: Handle timezone awareness (use message timestamp as reference)

- [x] Task 6: Implement additional entity types (AC: #1, #2, #3)
  - [x] Subtask 6.1: Extract email addresses with validation
  - [x] Subtask 6.2: Extract phone numbers (US format, international)
  - [ ] Subtask 6.3: Basic name extraction (proper nouns after "my name is", "I am") [Deferred - not required for AC]

- [x] Task 7: Integrate with HandoffOrchestrator (AC: #1, #2, #3)
  - [x] Subtask 7.1: Add entity_extractor to HandoffOrchestrator.__init__
  - [x] Subtask 7.2: Update create_handoff() to extract entities
  - [x] Subtask 7.3: Include entities in HandoffResult.metadata["extracted_entities"]
  - [x] Subtask 7.4: Ensure backward compatibility

- [x] Task 8: Create comprehensive tests (AC: #1, #2, #3)
  - [x] Subtask 8.1: Create `tests/test_entity_extractor.py`
  - [x] Subtask 8.2: Test account number extraction and masking
  - [x] Subtask 8.3: Test currency extraction and normalization
  - [x] Subtask 8.4: Test date extraction (absolute and relative)
  - [x] Subtask 8.5: Test email extraction
  - [x] Subtask 8.6: Test phone number extraction
  - [x] Subtask 8.7: Test edge cases (no entities, overlapping patterns)
  - [x] Subtask 8.8: Test integration with HandoffOrchestrator

- [x] Task 9: Export new classes from package (AC: #1)
  - [x] Subtask 9.1: Update handoffkit/context/__init__.py exports
  - [x] Subtask 9.2: Update handoffkit/__init__.py with EntityExtractor, ExtractedEntity, EntityType exports

## Dev Notes

### Existing Code Context

From Story 3.2 (just completed):
- `MetadataCollector` class exists in `handoffkit/context/metadata.py`
- `ConversationMetadata` model exists in `handoffkit/context/models.py`
- `HandoffOrchestrator.create_handoff()` already calls `_metadata_collector.collect_metadata()`
- Late import pattern used to avoid circular dependencies
- All 520 tests currently passing

Core types from `handoffkit/core/types.py`:
- `Message` with fields: speaker (MessageSpeaker enum), content (str), timestamp (datetime), metadata (dict)
- `MessageSpeaker` enum: USER, AI, SYSTEM
- `HandoffResult` with metadata field (dict)

Context module structure:
```
handoffkit/context/
├── __init__.py              # Exports
├── packager.py              # ConversationPackager (Story 3.1 ✓)
├── metadata.py              # MetadataCollector (Story 3.2 ✓)
├── models.py                # Data models (ConversationPackage, ConversationMetadata)
├── entity_extractor.py      # EntityExtractor ← THIS STORY
```

### Architecture Compliance

**Section 3: Context Module** (architecture.md:549-556):
```
handoffkit/context/
├── entity_extractor.py     # Entity extraction ← THIS STORY
├── metadata.py             # Metadata collector (Story 3.2 ✓)
├── packager.py             # ConversationPackager (Story 3.1 ✓)
├── models.py               # Data models
```

**Entity Extraction Requirements** (epics.md:593-615):
- Account numbers: Extract and mask (show last 4 digits)
- Currency: Extract and normalize to decimal format
- Dates: Extract absolute and relative, convert to ISO 8601
- Additional: Emails, phone numbers, names

**Data Models** (architecture.md:722-738):
- Entities must be JSON-serializable
- Use Pydantic for validation
- Follow existing model patterns

### Implementation Strategy

**EntityExtractor Design**:
```python
import re
from datetime import datetime, timedelta
from typing import Optional
from handoffkit.context.models import ExtractedEntity, EntityType
from handoffkit.core.types import Message
from handoffkit.utils.logging import get_logger

class EntityExtractor:
    """Extract entities from conversation messages."""

    def __init__(self) -> None:
        self._logger = get_logger("context.entities")
        self._setup_patterns()

    def _setup_patterns(self) -> None:
        """Initialize regex patterns for entity extraction."""
        # Account numbers: 8-17 digits, may have spaces/dashes
        self._account_pattern = re.compile(
            r'\b(\d[\d\s\-]{6,15}\d)\b'
        )

        # Currency: $1,234.56 or 1500 dollars or USD 100
        self._currency_pattern = re.compile(
            r'(\$[\d,]+\.?\d*)|'
            r'([\d,]+\.?\d*\s*(?:dollars?|USD|EUR|GBP))|'
            r'((?:USD|EUR|GBP)\s*[\d,]+\.?\d*)',
            re.IGNORECASE
        )

        # Dates: Various formats
        self._date_patterns = [
            re.compile(r'\b(\d{4}-\d{2}-\d{2})\b'),  # ISO: 2025-12-25
            re.compile(r'\b(\d{1,2}/\d{1,2}/\d{2,4})\b'),  # US: 12/25/2025
            re.compile(r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b', re.IGNORECASE),
        ]

        # Email
        self._email_pattern = re.compile(
            r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
        )

        # Phone: US and international formats
        self._phone_pattern = re.compile(
            r'\b(\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})\b'
        )

    def extract_entities(
        self,
        conversation: list[Message],
    ) -> list[ExtractedEntity]:
        """
        Extract all entities from conversation messages.

        Args:
            conversation: List of Message objects

        Returns:
            List of ExtractedEntity objects
        """
        entities = []

        for idx, msg in enumerate(conversation):
            entities.extend(self._extract_from_message(msg.content, idx, msg.timestamp))

        return entities

    def _extract_from_message(
        self,
        content: str,
        message_index: int,
        reference_time: datetime,
    ) -> list[ExtractedEntity]:
        """Extract entities from a single message."""
        entities = []

        # Extract account numbers
        entities.extend(self._extract_accounts(content, message_index))

        # Extract currency
        entities.extend(self._extract_currency(content, message_index))

        # Extract dates
        entities.extend(self._extract_dates(content, message_index, reference_time))

        # Extract emails
        entities.extend(self._extract_emails(content, message_index))

        # Extract phones
        entities.extend(self._extract_phones(content, message_index))

        return entities
```

**ExtractedEntity Model**:
```python
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class EntityType(str, Enum):
    """Types of extractable entities."""
    ACCOUNT_NUMBER = "account_number"
    CURRENCY = "currency"
    DATE = "date"
    EMAIL = "email"
    PHONE = "phone"
    NAME = "name"

class ExtractedEntity(BaseModel):
    """Extracted entity from conversation."""

    entity_type: EntityType = Field(description="Type of entity")
    original_value: str = Field(description="Original text as found")
    masked_value: Optional[str] = Field(None, description="Masked value for PII")
    normalized_value: Optional[str] = Field(None, description="Normalized/parsed value")
    message_index: int = Field(description="Index of message containing entity")
    start_pos: int = Field(description="Start position in message")
    end_pos: int = Field(description="End position in message")

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump(mode="json")
```

**Account Number Masking**:
```python
def _mask_account(self, account: str) -> str:
    """Mask account number showing last 4 digits."""
    # Remove spaces and dashes for masking
    digits = re.sub(r'[\s\-]', '', account)
    if len(digits) >= 4:
        return '*' * (len(digits) - 4) + digits[-4:]
    return '*' * len(digits)
```

**Currency Normalization**:
```python
def _normalize_currency(self, value: str) -> tuple[float, str]:
    """Normalize currency to (amount, currency_code)."""
    # Extract digits
    amount_str = re.sub(r'[^\d.,]', '', value)
    # Handle comma as thousand separator
    amount_str = amount_str.replace(',', '')
    try:
        amount = float(amount_str)
    except ValueError:
        amount = 0.0

    # Detect currency
    if '$' in value or 'USD' in value.upper():
        currency = 'USD'
    elif 'EUR' in value.upper() or '€' in value:
        currency = 'EUR'
    elif 'GBP' in value.upper() or '£' in value:
        currency = 'GBP'
    else:
        currency = 'USD'  # Default

    return amount, currency
```

**Relative Date Parsing**:
```python
RELATIVE_DATES = {
    'today': 0,
    'yesterday': -1,
    'tomorrow': 1,
    'last week': -7,
    'next week': 7,
}

def _parse_relative_date(self, text: str, reference: datetime) -> Optional[str]:
    """Parse relative date to ISO 8601 format."""
    text_lower = text.lower()

    for pattern, days in RELATIVE_DATES.items():
        if pattern in text_lower:
            result = reference + timedelta(days=days)
            return result.strftime('%Y-%m-%d')

    # Handle "last Tuesday", "next Monday" etc.
    weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    for i, day in enumerate(weekdays):
        if f'last {day}' in text_lower:
            # Calculate last occurrence
            days_ago = (reference.weekday() - i) % 7
            if days_ago == 0:
                days_ago = 7
            result = reference - timedelta(days=days_ago)
            return result.strftime('%Y-%m-%d')
        if f'next {day}' in text_lower:
            # Calculate next occurrence
            days_ahead = (i - reference.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            result = reference + timedelta(days=days_ahead)
            return result.strftime('%Y-%m-%d')

    return None
```

### Integration with HandoffOrchestrator

Update `HandoffOrchestrator.__init__`:
```python
from handoffkit.context.entity_extractor import EntityExtractor

def __init__(self, ...):
    ...
    self._entity_extractor = EntityExtractor()
```

Update `create_handoff()`:
```python
def create_handoff(self, conversation, metadata=None):
    # Package conversation history (Story 3.1)
    conversation_package = self._context_packager.package_conversation(conversation)

    # Collect metadata (Story 3.2)
    conversation_metadata = self._metadata_collector.collect_metadata(
        conversation,
        metadata or {}
    )

    # Extract entities (Story 3.3)
    extracted_entities = self._entity_extractor.extract_entities(conversation)

    # Include all in result metadata
    if metadata is None:
        metadata = {}

    metadata["conversation_package"] = conversation_package.model_dump()
    metadata["conversation_metadata"] = conversation_metadata.to_dict()
    metadata["extracted_entities"] = [e.to_dict() for e in extracted_entities]

    # Create handoff
    return HandoffResult(...)
```

### Testing Strategy

**Unit Tests** (`tests/test_entity_extractor.py`):
1. Test account number extraction (various formats)
2. Test account number masking (last 4 digits visible)
3. Test currency extraction ($1,234.56, 1500 dollars, USD 100)
4. Test currency normalization (to float)
5. Test absolute date extraction (ISO, US format, Month DD YYYY)
6. Test relative date parsing (yesterday, last Tuesday)
7. Test email extraction
8. Test phone number extraction
9. Test edge cases:
   - No entities in conversation
   - Overlapping patterns (avoid double extraction)
   - Invalid formats (graceful handling)
   - Empty messages

**Integration Tests**:
1. Test entity extraction through HandoffOrchestrator
2. Test entities included in HandoffResult.metadata
3. Test backward compatibility (no entities to extract)

### Performance Requirements

- Entity extraction should complete in <50ms for typical conversation
- Use compiled regex patterns (initialized once in __init__)
- Single-pass extraction where possible
- Minimal memory allocations

### Previous Story Learnings (from 3.2)

✅ **Working Patterns**:
- Late import in HandoffOrchestrator to avoid circular deps
- Pydantic models with `model_dump(mode="json")` for serialization
- Structured logging with get_logger()
- Input validation in constructors
- Comprehensive test coverage (unit + integration)
- Limit lists to prevent bloat (e.g., last 5 items)

✅ **Code Quality**:
- All 520 tests passing
- Type hints on all functions
- Clear docstrings
- Edge case handling

### Git Intelligence (Recent Commits)

```
c24f227 feat: implement Story 3.2 - Metadata Collection
b3974f3 feat: implement Story 3.1 - Conversation History Packaging
d97b9e0 feat: implement Story 2.8 - Local LLM Sentiment Analysis (Tier 2)
```

**Established Pattern**:
- Commit format: `feat: implement Story X.Y - Title`
- All tests must pass before commit
- Include comprehensive test coverage
- Use Pydantic for data models
- Follow TDD (write tests first)

### Project Structure

New files:
- `handoffkit/context/entity_extractor.py` - EntityExtractor class
- `tests/test_entity_extractor.py` - Comprehensive tests

Modified files:
- `handoffkit/context/models.py` - Add ExtractedEntity model, EntityType enum
- `handoffkit/context/__init__.py` - Export new classes
- `handoffkit/__init__.py` - Export EntityExtractor, ExtractedEntity, EntityType
- `handoffkit/core/orchestrator.py` - Integrate entity extraction

### Key Technical Considerations

1. **Regex Patterns**:
   - Compile patterns once in __init__ for performance
   - Use non-capturing groups where appropriate
   - Test edge cases thoroughly

2. **Account Number Detection**:
   - 8-17 digits is typical range
   - Handle spaces, dashes
   - Avoid phone numbers (different format)
   - Avoid dates (year patterns)

3. **Currency Parsing**:
   - Handle $ symbol and written "dollars"
   - Handle comma as thousand separator
   - Normalize to float for comparison
   - Support multiple currencies (USD, EUR, GBP)

4. **Date Parsing**:
   - Absolute: ISO 8601, US format, Month DD YYYY
   - Relative: yesterday, last Tuesday, next week
   - Use message timestamp as reference for relative dates
   - Convert to ISO 8601 for consistency

5. **PII Protection**:
   - Account numbers masked (****5678)
   - Keep original for internal processing
   - Only expose masked_value in API responses

6. **Entity Overlap**:
   - Avoid extracting same text as multiple entities
   - Priority: account > phone (similar digit patterns)
   - Track positions to detect overlaps

### References

- [Source: _bmad-output/project-planning-artifacts/epics.md#Story 3.3: Entity Extraction]
- [Source: _bmad-output/architecture.md#3. Context Module]
- [Source: handoffkit/context/metadata.py] - Existing context module pattern
- [Source: handoffkit/context/models.py] - Existing model patterns
- [Source: handoffkit/core/orchestrator.py] - Integration point
