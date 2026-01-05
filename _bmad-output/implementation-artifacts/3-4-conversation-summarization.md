# Story 3.4: Conversation Summarization

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **support agent with limited time**,
I want to **see a brief AI-generated summary of the conversation**,
So that **I can understand the issue in seconds**.

## Acceptance Criteria

1. **Given** a 20-message conversation about a payment issue **When** summary is generated **Then** it captures: user's primary issue, AI's attempted solutions, current state **And** summary is max 200 words **And** generation completes in <500ms

2. **Given** MVP (rule-based summarization) **When** summary is generated **Then** template-based approach extracts key information **And** format is consistent: "Issue: X. Tried: Y. Status: Z."

## Tasks / Subtasks

- [x] Task 1: Create ConversationSummarizer class (AC: #1, #2)
  - [x] Subtask 1.1: Create `handoffkit/context/summarizer.py` with ConversationSummarizer class
  - [x] Subtask 1.2: Implement `__init__` accepting optional config (max_words from HandoffConfig)
  - [x] Subtask 1.3: Implement `summarize(conversation: list[Message]) -> ConversationSummary`
  - [x] Subtask 1.4: Add structured logging with get_logger("context.summarizer")

- [x] Task 2: Create ConversationSummary model (AC: #1, #2)
  - [x] Subtask 2.1: Create ConversationSummary in `handoffkit/context/models.py`
  - [x] Subtask 2.2: Fields: summary_text (str), issue (str), attempted_solutions (list[str]), current_status (str), word_count (int), generation_time_ms (float)
  - [x] Subtask 2.3: Implement to_dict() for serialization using model_dump(mode="json")

- [x] Task 3: Implement issue extraction (AC: #1, #2)
  - [x] Subtask 3.1: Identify first user message as potential issue statement
  - [x] Subtask 3.2: Look for problem indicators ("help with", "issue with", "problem", "can't", "won't")
  - [x] Subtask 3.3: Extract and condense issue to single sentence (max 50 words)
  - [x] Subtask 3.4: Handle multiple issues by prioritizing first mentioned

- [x] Task 4: Implement attempted solutions extraction (AC: #1)
  - [x] Subtask 4.1: Reuse logic from MetadataCollector._extract_solutions()
  - [x] Subtask 4.2: Format solutions as concise bullet points
  - [x] Subtask 4.3: Limit to most recent 3 solutions (more concise than metadata's 5)
  - [x] Subtask 4.4: Truncate each solution to max 30 words

- [x] Task 5: Implement current status detection (AC: #1, #2)
  - [x] Subtask 5.1: Analyze last 2-3 messages to determine conversation state
  - [x] Subtask 5.2: Detect "resolved" state (user confirms, thanks, satisfaction)
  - [x] Subtask 5.3: Detect "unresolved" state (continued questions, frustration)
  - [x] Subtask 5.4: Detect "awaiting_response" state (AI asked question, user hasn't responded)
  - [x] Subtask 5.5: Return status enum or string value

- [x] Task 6: Implement template-based summary generation (AC: #2)
  - [x] Subtask 6.1: Create summary template: "Issue: {issue}. Tried: {solutions}. Status: {status}."
  - [x] Subtask 6.2: Ensure total summary stays under max_words limit (default 200)
  - [x] Subtask 6.3: Truncate sections proportionally if needed
  - [x] Subtask 6.4: Track generation time in milliseconds

- [x] Task 7: Integrate with HandoffOrchestrator (AC: #1, #2)
  - [x] Subtask 7.1: Add _summarizer to HandoffOrchestrator.__init__ with late import
  - [x] Subtask 7.2: Update create_handoff() to generate summary
  - [x] Subtask 7.3: Include summary in HandoffResult.metadata["conversation_summary"]
  - [x] Subtask 7.4: Ensure backward compatibility (summary is optional)

- [x] Task 8: Create comprehensive tests (AC: #1, #2)
  - [x] Subtask 8.1: Create `tests/test_conversation_summarizer.py`
  - [x] Subtask 8.2: Test issue extraction from various conversation patterns
  - [x] Subtask 8.3: Test attempted solutions formatting
  - [x] Subtask 8.4: Test current status detection (resolved/unresolved/awaiting)
  - [x] Subtask 8.5: Test template generation and word limit
  - [x] Subtask 8.6: Test performance requirement (<500ms)
  - [x] Subtask 8.7: Test edge cases (empty conversation, single message, no solutions)
  - [x] Subtask 8.8: Test integration with HandoffOrchestrator

- [x] Task 9: Export new classes from package (AC: #1)
  - [x] Subtask 9.1: Update handoffkit/context/__init__.py exports
  - [x] Subtask 9.2: Update handoffkit/__init__.py with ConversationSummarizer, ConversationSummary exports

## Dev Notes

### Existing Code Context

From Story 3.3 (just completed):
- `EntityExtractor` class exists in `handoffkit/context/entity_extractor.py`
- `ExtractedEntity` model exists in `handoffkit/context/models.py`
- `HandoffOrchestrator.create_handoff()` calls `_entity_extractor.extract_entities()`
- Late import pattern used to avoid circular dependencies
- All 562 tests currently passing

From Story 3.2 (MetadataCollector):
- `MetadataCollector._extract_solutions()` contains solution extraction logic that can be reused
- Solution keywords: ["try", "you can", "here's how", "solution", "recommend"]
- Solutions are truncated to 200 chars and limited to 5 - for summary, limit to 3 and 30 words

Core types from `handoffkit/core/types.py`:
- `Message` with fields: speaker (MessageSpeaker enum), content (str), timestamp (datetime), metadata (dict)
- `MessageSpeaker` enum: USER, AI, SYSTEM
- `HandoffResult` with metadata field (dict)

Configuration from `handoffkit/core/config.py`:
- `HandoffConfig.summary_max_words`: default=200, range 50-500
- Already exists and loaded from environment/config files

Context module structure:
```
handoffkit/context/
├── __init__.py              # Exports
├── packager.py              # ConversationPackager (Story 3.1 ✓)
├── metadata.py              # MetadataCollector (Story 3.2 ✓)
├── entity_extractor.py      # EntityExtractor (Story 3.3 ✓)
├── models.py                # Data models
└── summarizer.py            # ConversationSummarizer ← THIS STORY
```

### Architecture Compliance

**Section 3: Context Module** (architecture.md:555):
```
│   ├── summarizer.py           # Conversation summarization
```

**Performance Requirements** (architecture.md & PRD):
- Summary generation: <500ms
- Max 200 words (configurable via summary_max_words)

### Implementation Strategy

**ConversationSummarizer Design:**
```python
from handoffkit.context.models import ConversationSummary
from handoffkit.core.types import Message, MessageSpeaker
from handoffkit.utils.logging import get_logger
import time

class ConversationSummarizer:
    """Generate concise summaries of conversations for handoff context."""

    def __init__(self, max_words: int = 200) -> None:
        self._max_words = max_words
        self._logger = get_logger("context.summarizer")

    def summarize(self, conversation: list[Message]) -> ConversationSummary:
        """Generate summary of conversation.

        Returns:
            ConversationSummary with issue, solutions, status, and formatted text
        """
        start_time = time.perf_counter()

        issue = self._extract_issue(conversation)
        solutions = self._format_solutions(conversation)
        status = self._detect_status(conversation)

        summary_text = self._generate_template_summary(issue, solutions, status)

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return ConversationSummary(
            summary_text=summary_text,
            issue=issue,
            attempted_solutions=solutions,
            current_status=status,
            word_count=len(summary_text.split()),
            generation_time_ms=elapsed_ms
        )
```

**ConversationSummary Model:**
```python
class ConversationSummary(BaseModel):
    """Summary of conversation for handoff context."""

    summary_text: str = Field(description="Full formatted summary text")
    issue: str = Field(description="Primary issue identified")
    attempted_solutions: list[str] = Field(
        default_factory=list,
        description="List of solutions attempted"
    )
    current_status: str = Field(description="Current state: resolved/unresolved/awaiting_response")
    word_count: int = Field(description="Total word count of summary")
    generation_time_ms: float = Field(description="Time to generate in milliseconds")

    def to_dict(self) -> dict:
        return self.model_dump(mode="json")
```

**Issue Extraction Logic:**
```python
def _extract_issue(self, conversation: list[Message]) -> str:
    """Extract primary issue from conversation."""
    problem_indicators = ["help with", "issue with", "problem", "can't", "won't", "unable to", "need to"]

    for msg in conversation:
        if msg.speaker == MessageSpeaker.USER:
            content_lower = msg.content.lower()
            if any(indicator in content_lower for indicator in problem_indicators):
                # Truncate to ~50 words
                words = msg.content.split()
                return " ".join(words[:50]) + ("..." if len(words) > 50 else "")

    # Fallback: use first user message
    for msg in conversation:
        if msg.speaker == MessageSpeaker.USER:
            words = msg.content.split()
            return " ".join(words[:50]) + ("..." if len(words) > 50 else "")

    return "No issue identified"
```

**Status Detection Logic:**
```python
def _detect_status(self, conversation: list[Message]) -> str:
    """Detect current conversation status."""
    if not conversation:
        return "unknown"

    # Analyze last 2-3 messages
    recent = conversation[-3:] if len(conversation) >= 3 else conversation

    resolved_indicators = ["thank", "thanks", "perfect", "that worked", "solved", "resolved"]
    unresolved_indicators = ["still", "doesn't work", "not working", "help", "?"]

    last_user_msg = None
    last_ai_msg = None

    for msg in reversed(recent):
        if msg.speaker == MessageSpeaker.USER and last_user_msg is None:
            last_user_msg = msg
        elif msg.speaker == MessageSpeaker.AI and last_ai_msg is None:
            last_ai_msg = msg
        if last_user_msg and last_ai_msg:
            break

    if last_user_msg:
        content_lower = last_user_msg.content.lower()
        if any(ind in content_lower for ind in resolved_indicators):
            return "resolved"
        if any(ind in content_lower for ind in unresolved_indicators):
            return "unresolved"

    # If last message is AI asking a question, status is awaiting response
    if last_ai_msg and "?" in last_ai_msg.content:
        return "awaiting_response"

    return "unresolved"  # Default to unresolved for handoff
```

**Template Generation:**
```python
def _generate_template_summary(self, issue: str, solutions: list[str], status: str) -> str:
    """Generate template-based summary."""
    parts = []

    parts.append(f"Issue: {issue}")

    if solutions:
        solutions_text = "; ".join(solutions[:3])
        parts.append(f"Tried: {solutions_text}")
    else:
        parts.append("Tried: No solutions attempted")

    status_map = {
        "resolved": "Resolved",
        "unresolved": "Unresolved - needs human assistance",
        "awaiting_response": "Awaiting customer response",
        "unknown": "Status unknown"
    }
    parts.append(f"Status: {status_map.get(status, status)}")

    summary = " ".join(parts)

    # Truncate to max words if needed
    words = summary.split()
    if len(words) > self._max_words:
        summary = " ".join(words[:self._max_words]) + "..."

    return summary
```

### Integration with HandoffOrchestrator

Update `HandoffOrchestrator.__init__`:
```python
from handoffkit.context.summarizer import ConversationSummarizer

self._summarizer = ConversationSummarizer(
    max_words=self._config.summary_max_words
)
```

Update `create_handoff()`:
```python
# Generate summary (Story 3.4)
conversation_summary = self._summarizer.summarize(conversation)

# Include in metadata
metadata["conversation_summary"] = conversation_summary.to_dict()
```

### Testing Strategy

**Unit Tests** (`tests/test_conversation_summarizer.py`):
1. Test issue extraction from various patterns
2. Test solutions formatting (max 3, truncated)
3. Test status detection (resolved, unresolved, awaiting_response)
4. Test template generation
5. Test word count limit enforcement
6. Test performance (<500ms)
7. Test edge cases:
   - Empty conversation → sensible defaults
   - Single message → uses that as issue
   - No AI solutions → "No solutions attempted"
   - All SYSTEM messages → handles gracefully

**Integration Tests**:
1. Test summary generation through HandoffOrchestrator
2. Test backward compatibility (summary in metadata)
3. Test max_words config respected

### Performance Requirements

- Summary generation MUST complete in <500ms
- Use simple string matching (no LLM for MVP)
- Minimal memory allocations
- Use time.perf_counter() for timing

### Previous Story Learnings (from 3.3)

**Working Patterns**:
- Late import in HandoffOrchestrator to avoid circular deps
- Pydantic models with `model_dump(mode="json")` for serialization
- Structured logging with get_logger()
- Performance tests with time.perf_counter()
- Comprehensive test coverage for edge cases

**Code Quality**:
- All 562 tests passing
- Type hints on all functions
- Clear docstrings with examples
- Edge case handling (empty, single message)

### Git Intelligence (Recent Commits)

```
d7313a6 fix(3-2): code review - add negative duration handling and tests
a781c4f fix(3-1): code review - remove dead ContextPackager stub
8ac5583 feat: implement Story 3.3 - Entity Extraction
c24f227 feat: implement Story 3.2 - Metadata Collection
b3974f3 feat: implement Story 3.1 - Conversation History Packaging
```

**Established Pattern**:
- Commit format: `feat: implement Story X.Y - Title`
- All tests must pass before commit
- Code review fixes use `fix(X-Y):` prefix
- Use Pydantic for data models
- Synchronous implementation (no async needed for rule-based)

### Project Structure

New files:
- `handoffkit/context/summarizer.py` - ConversationSummarizer class
- `tests/test_conversation_summarizer.py` - Comprehensive tests

Modified files:
- `handoffkit/context/models.py` - Add ConversationSummary model
- `handoffkit/context/__init__.py` - Export new classes
- `handoffkit/__init__.py` - Export ConversationSummarizer, ConversationSummary
- `handoffkit/core/orchestrator.py` - Integrate summarizer

### Key Technical Considerations

1. **Reuse from MetadataCollector**:
   - Solution extraction keywords already defined
   - Can reference but keep summarizer logic self-contained for clarity

2. **Word Counting**:
   - Use simple `split()` for word counting
   - More accurate than character limits for readability

3. **Template Format**:
   - Consistent format: "Issue: X. Tried: Y. Status: Z."
   - Easy for human agents to scan quickly

4. **Status Detection Priority**:
   - Check resolved first (positive outcome)
   - Then unresolved (needs handoff)
   - Then awaiting_response (context for agent)
   - Default to unresolved (safe for handoff scenario)

5. **Performance**:
   - Single pass through conversation
   - Simple string matching
   - No external API calls

### References

- [Source: _bmad-output/project-planning-artifacts/epics.md#Story 3.4: Conversation Summarization]
- [Source: _bmad-output/architecture.md#3. Context Module - summarizer.py]
- [Source: handoffkit/core/config.py:250-255 - summary_max_words config]
- [Source: handoffkit/context/metadata.py - solution extraction pattern]
- [Source: handoffkit/context/models.py - existing model patterns]

## Dev Agent Record

### Agent Model Used

gemini-claude-opus-4-5-thinking

### Debug Log References

N/A - Clean TDD implementation with no significant debugging needed

### Completion Notes List

**Implementation Summary:**
- Created `ConversationSummarizer` class in `handoffkit/context/summarizer.py` for generating conversation summaries
- Created `ConversationSummary` Pydantic model in `handoffkit/context/models.py` with fields: summary_text, issue, attempted_solutions, current_status, word_count, generation_time_ms
- Implemented issue extraction using problem indicators ("help with", "issue with", "problem", "can't", "won't", "unable to", "need to")
- Implemented solution extraction from AI messages using keywords ("try", "you can", "here's how", "solution", "recommend")
- Limited solutions to last 3 (more concise than metadata's 5) and truncated to 30 words each
- Implemented status detection: resolved (thanks, that worked, perfect), unresolved (still, doesn't work, help), awaiting_response (AI ends with ?)
- Implemented template-based summary: "Issue: {issue}. Tried: {solutions}. Status: {status}." (AC#2 format with periods)
- Added structured logging at start and completion of summarization
- Integrated with `HandoffOrchestrator.create_handoff()` using late import pattern
- Summary included in `HandoffResult.metadata["conversation_summary"]`
- Exported classes from `handoffkit.context` and `handoffkit` main package
- Created 30 comprehensive unit tests in test_conversation_summarizer.py (16 core + 2 model + 12 edge cases)
- Created 4 integration tests in test_orchestrator_integration.py (2 packaging + 2 summarizer tests)
- All tests pass with no regressions

**Technical Decisions:**
- Used late import in `HandoffOrchestrator.__init__` to avoid circular dependency (same pattern as Story 3.1-3.3)
- Issue truncation to 50 words for conciseness
- Solution truncation to 30 words (stricter than metadata's 200 chars)
- Status detection prioritizes checking if last message is AI with question mark BEFORE checking user message indicators
- Pydantic `model_dump(mode="json")` for JSON-safe serialization
- Empty conversations return sensible defaults (issue="No issue identified", status="unknown")
- Performance well under 500ms requirement (typically <5ms)

**Performance Characteristics:**
- Summarization completes well under 500ms target (tested with 100 messages)
- Single-pass conversation analysis using simple string matching
- No external API calls or LLM invocations (rule-based MVP)
- Minimal memory allocations

### File List

- `handoffkit/context/summarizer.py` - ConversationSummarizer class (new file, 324 lines)
- `handoffkit/context/models.py` - Added ConversationSummary model
- `handoffkit/context/__init__.py` - Updated exports
- `handoffkit/__init__.py` - Updated main package exports
- `handoffkit/core/orchestrator.py` - Integrated ConversationSummarizer with late import
- `tests/test_conversation_summarizer.py` - 30 comprehensive unit tests (new file)
- `tests/test_orchestrator_integration.py` - 4 integration tests (2 packaging + 2 summarizer)
- `_bmad-output/implementation-artifacts/3-4-conversation-summarization.md` - Story file (this file)

### Code Review Fixes Applied

The following issues were found and fixed during code review:

| Severity | Issue | Fix Applied |
|----------|-------|-------------|
| HIGH | AC#2: Template format missing periods | Changed to "Issue: X. Tried: Y. Status: Z." format |
| HIGH | Performance test name didn't match AC#1 | Renamed to test_performance_under_500ms_ac1 |
| HIGH | No test for default 200-word limit | Added test_default_max_words_is_200 |
| HIGH | Story file test counts incorrect | Updated to accurate counts (30 unit + 4 integration) |
| MEDIUM | Template format test not validating periods | Added assertions for ". Tried:" and ". Status:" |
| MEDIUM | Story claimed wrong integration test count | Fixed to 4 tests total |
