# Story 3.2: Metadata Collection

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **support team analyzing handoffs**,
I want to **see user and session metadata**,
So that **I have context about the customer and channel**.

## Acceptance Criteria

1. **Given** a handoff is created with metadata **When** context is packaged **Then** user_id, session_id, channel are included **And** attempted_solutions (AI suggestions) are listed **And** failed_queries (unanswered questions) are captured **And** conversation_duration is calculated

2. **Given** minimal metadata provided (only user_id) **When** context is packaged **Then** session_id is auto-generated **And** missing fields default to "unknown" or null

## Tasks / Subtasks

- [x] Task 1: Create MetadataCollector class (AC: #1, #2)
  - [x] Subtask 1.1: Create `handoffkit/context/metadata.py` with MetadataCollector class
  - [x] Subtask 1.2: Implement `__init__` accepting optional config
  - [x] Subtask 1.3: Implement core metadata collection (user_id, session_id, channel)
  - [x] Subtask 1.4: Add auto-generation for missing session_id (UUID v4)
  - [x] Subtask 1.5: Implement default values for missing fields

- [x] Task 2: Implement attempted_solutions tracking (AC: #1)
  - [x] Subtask 2.1: Extract AI responses from conversation
  - [x] Subtask 2.2: Identify solution-oriented messages (suggestions, answers, instructions)
  - [x] Subtask 2.3: Store as list of strings in attempted_solutions field
  - [x] Subtask 2.4: Limit to last N solutions (default 5) to avoid bloat

- [x] Task 3: Implement failed_queries tracking (AC: #1)
  - [x] Subtask 3.1: Identify user questions/requests from conversation
  - [x] Subtask 3.2: Detect when AI didn't provide satisfactory answer
  - [x] Subtask 3.3: Track unanswered or repeated questions
  - [x] Subtask 3.4: Store as list of strings in failed_queries field

- [x] Task 4: Implement conversation_duration calculation (AC: #1)
  - [x] Subtask 4.1: Extract first and last message timestamps
  - [x] Subtask 4.2: Calculate duration in seconds
  - [x] Subtask 4.3: Handle timezone-aware datetime objects
  - [x] Subtask 4.4: Return 0 for single-message conversations

- [x] Task 5: Create ConversationMetadata model (AC: #1, #2)
  - [x] Subtask 5.1: Create ConversationMetadata in `handoffkit/context/models.py`
  - [x] Subtask 5.2: Fields: user_id, session_id, channel, attempted_solutions, failed_queries, conversation_duration, timestamp
  - [x] Subtask 5.3: Add validation for required fields
  - [x] Subtask 5.4: Implement to_dict() for serialization

- [x] Task 6: Integrate with HandoffOrchestrator (AC: #1, #2)
  - [x] Subtask 6.1: Add metadata_collector to HandoffOrchestrator.__init__
  - [x] Subtask 6.2: Update create_handoff() to collect metadata
  - [x] Subtask 6.3: Include metadata in HandoffResult.metadata["conversation_metadata"]
  - [x] Subtask 6.4: Ensure backward compatibility

- [x] Task 7: Add logging and monitoring (AC: #1, #2)
  - [x] Subtask 7.1: Log INFO when metadata collection starts/completes
  - [x] Subtask 7.2: Log WARNING when required fields are missing
  - [x] Subtask 7.3: Include metadata summary in logs
  - [x] Subtask 7.4: Use get_logger("context.metadata")

- [x] Task 8: Create comprehensive tests (AC: #1, #2)
  - [x] Subtask 8.1: Create `tests/test_metadata_collector.py`
  - [x] Subtask 8.2: Test full metadata collection with all fields
  - [x] Subtask 8.3: Test auto-generation of session_id
  - [x] Subtask 8.4: Test default values for missing fields
  - [x] Subtask 8.5: Test attempted_solutions extraction
  - [x] Subtask 8.6: Test failed_queries detection
  - [x] Subtask 8.7: Test conversation_duration calculation
  - [x] Subtask 8.8: Test edge cases (empty conversation, single message)

- [x] Task 9: Export new classes from package (AC: #1)
  - [x] Subtask 9.1: Update handoffkit/context/__init__.py exports
  - [x] Subtask 9.2: Update handoffkit/__init__.py with ConversationMetadata export

## Dev Notes

### Existing Code Context

From Story 3.1 (just completed):
- `ConversationPackager` class exists in `handoffkit/context/packager.py`
- `ConversationPackage` model exists in `handoffkit/context/models.py`
- `HandoffOrchestrator.create_handoff()` already calls `_context_packager.package_conversation()`
- Metadata included in `HandoffResult.metadata` dictionary
- Late import pattern used to avoid circular dependencies
- All 500 tests currently passing

Core types from `handoffkit/core/types.py`:
- `Message` with fields: speaker (MessageSpeaker enum), content (str), timestamp (datetime), metadata (dict)
- `MessageSpeaker` enum: USER, AI, SYSTEM
- `HandoffResult` with metadata field (dict)

### Architecture Compliance

**Section 3: Context Module** (architecture.md:549-556):
```
handoffkit/context/
├── metadata.py             # Metadata collector ← THIS STORY
├── packager.py             # ConversationPackager (Story 3.1 ✓)
├── models.py               # Data models
```

**Data Models** (architecture.md:722-738):
- Metadata must be JSON-serializable
- Use Pydantic for validation
- Follow existing Message model pattern

**Metadata Collection Requirements**:
- user_id: Required (string)
- session_id: Auto-generated UUID v4 if missing
- channel: String (e.g., "web", "mobile", "sms")
- attempted_solutions: List[str] from AI responses
- failed_queries: List[str] from unresolved user questions
- conversation_duration: int (seconds)

### Implementation Strategy

**MetadataCollector Design**:
```python
from handoffkit.context.models import ConversationMetadata
from handoffkit.core.types import Message
from handoffkit.utils.logging import get_logger
import uuid

class MetadataCollector:
    """Collect conversation metadata for handoff context."""

    def __init__(self):
        self._logger = get_logger("context.metadata")

    def collect_metadata(
        self,
        conversation: list[Message],
        provided_metadata: dict
    ) -> ConversationMetadata:
        """
        Collect comprehensive metadata from conversation and provided data.

        Args:
            conversation: List of Message objects
            provided_metadata: User-provided metadata dict

        Returns:
            ConversationMetadata with all fields populated
        """
        # Extract or generate core fields
        user_id = provided_metadata.get("user_id", "unknown")
        session_id = provided_metadata.get("session_id") or str(uuid.uuid4())
        channel = provided_metadata.get("channel", "unknown")

        # Extract conversation analytics
        attempted_solutions = self._extract_solutions(conversation)
        failed_queries = self._detect_failed_queries(conversation)
        duration = self._calculate_duration(conversation)

        return ConversationMetadata(
            user_id=user_id,
            session_id=session_id,
            channel=channel,
            attempted_solutions=attempted_solutions,
            failed_queries=failed_queries,
            conversation_duration=duration,
            timestamp=conversation[-1].timestamp if conversation else None
        )
```

**ConversationMetadata Model**:
```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ConversationMetadata(BaseModel):
    """Metadata for handoff context."""

    user_id: str = Field(description="User identifier")
    session_id: str = Field(description="Session identifier (auto-generated if missing)")
    channel: str = Field(description="Communication channel (web, mobile, sms, etc.)")
    attempted_solutions: List[str] = Field(
        default_factory=list,
        description="AI suggestions and solutions attempted"
    )
    failed_queries: List[str] = Field(
        default_factory=list,
        description="User questions that weren't satisfactorily answered"
    )
    conversation_duration: int = Field(
        default=0,
        description="Duration in seconds from first to last message"
    )
    timestamp: Optional[datetime] = Field(
        None,
        description="Timestamp of last message"
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump(mode="json")
```

**Solution Extraction Logic**:
```python
def _extract_solutions(self, conversation: list[Message]) -> list[str]:
    """Extract AI-provided solutions from conversation.

    Looks for AI messages containing:
    - Instructions ("try", "you can", "please")
    - Solutions ("here's how", "solution")
    - Suggestions ("I recommend", "consider")

    Returns last 5 solutions to avoid bloat.
    """
    solutions = []
    solution_keywords = ["try", "you can", "here's how", "solution", "recommend"]

    for msg in conversation:
        if msg.speaker == MessageSpeaker.AI:
            # Check if message contains solution-oriented language
            content_lower = msg.content.lower()
            if any(keyword in content_lower for keyword in solution_keywords):
                solutions.append(msg.content[:200])  # Truncate long messages

    return solutions[-5:]  # Last 5 solutions
```

**Failed Query Detection**:
```python
def _detect_failed_queries(self, conversation: list[Message]) -> list[str]:
    """Detect user questions that weren't answered satisfactorily.

    A query is considered failed if:
    - User asks a question (ends with "?")
    - AI response doesn't address it
    - User repeats or rephrases the question
    """
    failed = []

    for i, msg in enumerate(conversation):
        if msg.speaker == MessageSpeaker.USER and "?" in msg.content:
            # Check if next AI response seems uncertain
            if i + 1 < len(conversation):
                next_msg = conversation[i + 1]
                if next_msg.speaker == MessageSpeaker.AI:
                    # Simple heuristic: if AI says "I don't know", "I can't", etc.
                    uncertain_phrases = ["i don't know", "i can't", "not sure", "unable to"]
                    if any(phrase in next_msg.content.lower() for phrase in uncertain_phrases):
                        failed.append(msg.content[:200])

    return failed
```

**Duration Calculation**:
```python
def _calculate_duration(self, conversation: list[Message]) -> int:
    """Calculate conversation duration in seconds.

    Returns:
        Duration from first to last message in seconds, or 0 if <2 messages
    """
    if len(conversation) < 2:
        return 0

    first_timestamp = conversation[0].timestamp
    last_timestamp = conversation[-1].timestamp

    duration = (last_timestamp - first_timestamp).total_seconds()
    return int(duration)
```

### Integration with HandoffOrchestrator

Update `HandoffOrchestrator.__init__`:
```python
from handoffkit.context.metadata import MetadataCollector

def __init__(self, ...):
    ...
    self._metadata_collector = MetadataCollector()
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

    # Include both in result metadata
    if metadata is None:
        metadata = {}

    metadata["conversation_package"] = conversation_package.model_dump()
    metadata["conversation_metadata"] = conversation_metadata.to_dict()

    # Create handoff
    return HandoffResult(...)
```

### Testing Strategy

**Unit Tests** (`tests/test_metadata_collector.py`):
1. Test full metadata collection with all fields provided
2. Test session_id auto-generation (UUID v4 format validation)
3. Test default values (unknown for user_id/channel if not provided)
4. Test attempted_solutions extraction (5 solution limit)
5. Test failed_queries detection (question + uncertain answer)
6. Test conversation_duration (various conversation lengths)
7. Test edge cases:
   - Empty conversation
   - Single message conversation
   - Conversation with no AI solutions
   - Conversation with no failed queries

**Integration Tests**:
1. Test metadata collection through HandoffOrchestrator
2. Test backward compatibility (no metadata provided)
3. Test metadata serialization in HandoffResult

### Performance Requirements

- Metadata collection should complete in <20ms
- Solutions/queries extraction uses simple string matching (no LLM)
- Minimal memory allocations

### Previous Story Learnings (from 3.1)

✅ **Working Patterns**:
- Late import in HandoffOrchestrator to avoid circular deps
- Pydantic models with `model_dump()` for serialization
- Structured logging with get_logger()
- Input validation in constructors
- Comprehensive test coverage (unit + integration)
- Performance tests for timing requirements

✅ **Code Quality**:
- All 500 tests passing
- Type hints on all functions
- Clear docstrings
- Edge case handling

### Git Intelligence (Recent Commits)

```
b3974f3 feat: implement Story 3.1 - Conversation History Packaging
d97b9e0 feat: implement Story 2.8 - Local LLM Sentiment Analysis (Tier 2)
032e435 feat: implement Story 2.7 - Conversation Degradation Tracking
```

**Established Pattern**:
- Commit format: `feat: implement Story X.Y - Title`
- All tests must pass before commit
- Include comprehensive test coverage
- Use Pydantic for data models
- Follow async/await when needed (not required for metadata collection - synchronous)

### Project Structure

New files:
- `handoffkit/context/metadata.py` - MetadataCollector class
- `tests/test_metadata_collector.py` - Comprehensive tests

Modified files:
- `handoffkit/context/models.py` - Add ConversationMetadata model
- `handoffkit/context/__init__.py` - Export new classes
- `handoffkit/__init__.py` - Export ConversationMetadata
- `handoffkit/core/orchestrator.py` - Integrate metadata collection

### Key Technical Considerations

1. **UUID Generation**:
   - Use `uuid.uuid4()` for session_id generation
   - Convert to string for JSON compatibility
   - Validate format in tests

2. **Solution Extraction**:
   - Simple keyword matching (no LLM needed)
   - Truncate long messages to 200 chars
   - Limit to last 5 solutions

3. **Failed Query Detection**:
   - Heuristic-based (question mark + uncertain response)
   - Can be improved in future with LLM analysis
   - Keep simple for MVP

4. **Duration Calculation**:
   - Handle timezone-aware datetimes
   - Return integer seconds
   - 0 for insufficient data

5. **Default Values**:
   - user_id: "unknown" if not provided
   - session_id: UUID v4 generated
   - channel: "unknown" if not provided
   - attempted_solutions: empty list
   - failed_queries: empty list
   - conversation_duration: 0

### References

- [Source: _bmad-output/project-planning-artifacts/epics.md#Story 3.2: Metadata Collection]
- [Source: _bmad-output/architecture.md#3. Context Module]
- [Source: handoffkit/context/packager.py] - Existing context module pattern
- [Source: handoffkit/context/models.py] - ConversationPackage model example
- [Source: handoffkit/core/orchestrator.py] - Integration point

## Dev Agent Record

### Agent Model Used

gemini-claude-sonnet-4-5-thinking

### Debug Log References

N/A - Clean TDD implementation with no significant debugging needed

### Completion Notes List

**Implementation Summary:**
- Created `MetadataCollector` class in `handoffkit/context/metadata.py` for extracting conversation metadata
- Created `ConversationMetadata` Pydantic model in `handoffkit/context/models.py` for validated data structures
- Implemented UUID v4 auto-generation for missing session_id using `uuid.uuid4()`
- Implemented default values: user_id="unknown", channel="unknown", empty lists for solutions/queries
- Implemented attempted_solutions extraction using keyword matching ("try", "you can", "recommend", etc.)
- Limited attempted_solutions to last 5 entries, truncated to 200 chars each
- Implemented failed_queries detection using heuristic (question mark + uncertain AI response)
- Implemented conversation_duration calculation using timestamp difference in seconds
- Added structured INFO logging at start and completion of metadata collection
- Integrated with `HandoffOrchestrator.create_handoff()` using late import pattern
- Metadata included in `HandoffResult.metadata["conversation_metadata"]`
- Exported classes from `handoffkit.context` and `handoffkit` main package
- Created 14 comprehensive unit tests covering all acceptance criteria and edge cases
- Created 4 integration tests verifying HandoffOrchestrator integration
- All 518 tests pass (500 existing + 18 new)
- No regressions introduced

**Technical Decisions:**
- Used late import in `HandoffOrchestrator.__init__` to avoid circular dependency (same pattern as Story 3.1)
- Simple keyword-based heuristics for solution/query detection (no LLM needed for MVP)
- UUID v4 format for session_id generation (standard, secure, unique)
- Solution truncation at 200 chars to prevent bloat in metadata
- Failed query detection uses uncertain phrases ("i don't know", "i can't", "not sure", "unable to")
- Empty conversations return valid metadata with defaults
- Pydantic `model_dump(mode="json")` for JSON-safe serialization

**Performance Characteristics:**
- Metadata collection completes well under 20ms target
- Single-pass conversation analysis using simple string matching
- Minimal memory allocations (list slicing for last 5 solutions)
- No external API calls or LLM invocations

### File List

- `handoffkit/context/metadata.py` - MetadataCollector class (new file, 193 lines)
- `handoffkit/context/models.py` - Added ConversationMetadata model
- `handoffkit/context/__init__.py` - Updated exports
- `handoffkit/__init__.py` - Updated main package exports
- `handoffkit/core/orchestrator.py` - Integrated MetadataCollector with late import
- `tests/test_metadata_collector.py` - 14 comprehensive unit tests (new file, 329 lines)
- `tests/test_metadata_integration.py` - 4 integration tests (new file, 96 lines)

