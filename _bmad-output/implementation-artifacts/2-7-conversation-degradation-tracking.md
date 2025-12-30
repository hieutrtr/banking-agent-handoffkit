# Story 2.7: Conversation Degradation Tracking

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer monitoring conversation quality**,
I want to **detect when sentiment trends downward over multiple messages**,
So that **I can escalate before users become extremely frustrated**.

## Acceptance Criteria

1. **Given** a conversation where sentiment drops from 0.7 → 0.6 → 0.5 → 0.4 → 0.3 **When** `should_handoff()` is called **Then** it triggers due to degradation (drop > 0.3 over 5 messages) **And** trigger_type is "sentiment_degradation"

2. **Given** a rolling window of the last 5 messages **When** sentiment is tracked **Then** the trend is calculated from window start to end **And** older messages outside the window are not considered

3. **Given** a conversation with stable sentiment (0.5 → 0.5 → 0.5 → 0.5 → 0.5) **When** degradation is checked **Then** no degradation trigger fires

4. **Given** a conversation with improving sentiment (0.3 → 0.4 → 0.5 → 0.6 → 0.7) **When** degradation is checked **Then** no degradation trigger fires

5. **Given** less than 5 messages in history **When** degradation is checked **Then** the available messages are used for trend calculation **And** no error is raised

6. **Given** the analyzer is invoked **When** <10ms passes **Then** the evaluation completes (performance requirement - Tier 1 rule-based)

## Tasks / Subtasks

- [x] Task 1: Create DegradationTracker class (AC: #1, #2, #5)
  - [x] Subtask 1.1: Create `handoffkit/sentiment/degradation.py` with DegradationTracker class
  - [x] Subtask 1.2: Implement `__init__` with configurable window_size (default 5) and threshold (default 0.3)
  - [x] Subtask 1.3: Implement `calculate_trend(scores: list[float]) -> float` method to calculate sentiment change
  - [x] Subtask 1.4: Handle edge cases: empty list, single score, fewer than window_size scores

- [x] Task 2: Implement sentiment history tracking (AC: #2, #5)
  - [x] Subtask 2.1: Add method `track_score(score: float)` to accumulate sentiment scores
  - [x] Subtask 2.2: Maintain internal rolling window (deque with maxlen=window_size)
  - [x] Subtask 2.3: Add method `get_recent_scores() -> list[float]` to retrieve window
  - [x] Subtask 2.4: Add method `clear()` to reset tracking for new conversations

- [x] Task 3: Implement degradation detection (AC: #1, #3, #4)
  - [x] Subtask 3.1: Add method `check_degradation() -> DegradationResult`
  - [x] Subtask 3.2: Calculate trend as: (first_score - last_score) in window
  - [x] Subtask 3.3: Return `is_degrading=True` if trend > threshold (default 0.3)
  - [x] Subtask 3.4: Include trend_value and window_scores in result

- [x] Task 4: Create DegradationResult model (AC: #1)
  - [x] Subtask 4.1: Add DegradationResult to `handoffkit/sentiment/models.py`
  - [x] Subtask 4.2: Fields: is_degrading (bool), trend_value (float), window_size (int), scores (list[float])
  - [x] Subtask 4.3: Add trigger_type constant "sentiment_degradation"

- [x] Task 5: Integrate with RuleBasedAnalyzer (AC: #1, #6)
  - [x] Subtask 5.1: Add optional `degradation_tracker` parameter to RuleBasedAnalyzer.__init__
  - [x] Subtask 5.2: Update analyze() to track scores and check degradation when history provided
  - [x] Subtask 5.3: Update SentimentResult to include degradation_detected flag
  - [x] Subtask 5.4: Maintain <10ms performance target

- [x] Task 6: Update SentimentFeatures model (AC: #2)
  - [x] Subtask 6.1: Populate recent_negative_trend field with calculated trend
  - [x] Subtask 6.2: Populate conversation_length field when history provided
  - [x] Subtask 6.3: Populate message_position field based on history length

- [x] Task 7: Create comprehensive tests (AC: #1, #2, #3, #4, #5, #6)
  - [x] Subtask 7.1: Create `tests/test_degradation_tracking.py`
  - [x] Subtask 7.2: Test degradation detected when drop > 0.3 over 5 messages
  - [x] Subtask 7.3: Test no degradation on stable sentiment
  - [x] Subtask 7.4: Test no degradation on improving sentiment
  - [x] Subtask 7.5: Test rolling window correctly limits to last 5 messages
  - [x] Subtask 7.6: Test edge case: fewer than 5 messages
  - [x] Subtask 7.7: Test edge case: empty history
  - [x] Subtask 7.8: Test performance (<10ms for evaluation)
  - [x] Subtask 7.9: Run all tests to verify no regressions (463 tests passing)

- [x] Task 8: Add logging for degradation tracking (AC: #1)
  - [x] Subtask 8.1: Log trend calculation at DEBUG level
  - [x] Subtask 8.2: Log degradation trigger events at INFO level
  - [x] Subtask 8.3: Include window scores and trend value in logs

- [x] Task 9: Export new classes from package (AC: #1)
  - [x] Subtask 9.1: Export DegradationTracker from handoffkit.sentiment
  - [x] Subtask 9.2: Export DegradationResult from handoffkit.sentiment

## Dev Notes

- **Existing Code**: RuleBasedAnalyzer in `handoffkit/sentiment/rule_based.py` already accepts `history` parameter but doesn't use it for degradation tracking
- **Existing Models**: SentimentFeatures has `recent_negative_trend` field (currently unused), set to 0.0
- **Architecture Reference**: FR-2.3 "Conversation Degradation Tracking" - track sentiment trend over rolling window of last 5 messages
- **Performance Target**: <10ms for Tier 1 rule-based evaluation (must maintain)

### Algorithm Design

```python
from collections import deque

class DegradationTracker:
    def __init__(self, window_size: int = 5, threshold: float = 0.3):
        self._window_size = window_size
        self._threshold = threshold
        self._scores: deque[float] = deque(maxlen=window_size)

    def track_score(self, score: float) -> None:
        """Add a sentiment score to the rolling window."""
        self._scores.append(score)

    def calculate_trend(self) -> float:
        """Calculate sentiment trend (positive = improving, negative = degrading).

        Returns:
            Trend value: first_score - last_score (positive means degrading)
        """
        if len(self._scores) < 2:
            return 0.0
        return self._scores[0] - self._scores[-1]

    def check_degradation(self) -> DegradationResult:
        """Check if conversation is degrading."""
        trend = self.calculate_trend()
        is_degrading = trend > self._threshold
        return DegradationResult(
            is_degrading=is_degrading,
            trend_value=trend,
            window_size=len(self._scores),
            scores=list(self._scores),
        )
```

### Degradation Detection Logic

- **Window**: Rolling window of last 5 user messages (configurable)
- **Trend Calculation**: `first_score - last_score` in window
  - Positive trend value = sentiment getting worse (degrading)
  - Negative trend value = sentiment improving
- **Threshold**: Default 0.3 (configurable)
  - If trend > 0.3, trigger degradation handoff
  - Example: 0.7 → 0.3 = trend of 0.4 > 0.3 threshold → triggers

### Integration Points

1. **RuleBasedAnalyzer.analyze()** - when history is provided:
   - Analyze each historical user message for sentiment
   - Track scores in DegradationTracker
   - Check for degradation after current message
   - Include degradation result in SentimentResult

2. **SentimentFeatures** - populate contextual fields:
   - `recent_negative_trend`: calculated trend value
   - `conversation_length`: len(history) + 1
   - `message_position`: len(history)

### Project Structure Notes

- `handoffkit/sentiment/degradation.py` - New file for DegradationTracker
- `handoffkit/sentiment/models.py` - Add DegradationResult model
- `handoffkit/sentiment/rule_based.py` - Integrate degradation tracking
- `handoffkit/sentiment/__init__.py` - Export new classes
- `tests/test_degradation_tracking.py` - New test file

### Previous Story Learnings (from Story 2.6)

- All 435 tests currently passing
- RuleBasedAnalyzer.analyze() already accepts history parameter (currently unused)
- SentimentFeatures has recent_negative_trend field (currently set to 0.0)
- Pre-compiled patterns and minimal allocations ensure <10ms performance
- Use collections.deque for efficient rolling window
- Use get_logger("sentiment.degradation") for consistent logging

### Git Intelligence (Recent Commits)

```
f66e80b feat: implement Story 2.6 - Frustration Signal Detection (Caps and Punctuation)
4bb0e62 feat: implement Story 2.5 - Rule-Based Sentiment Scoring (Tier 1)
f6fa67c feat: implement Story 2.4 - Custom Rule Engine
347d5e7 feat: implement Story 2.3 - Critical Keyword Monitoring Trigger
a4696a1 feat: implement Story 2.2 - Failure Pattern Tracking Trigger
```

Pattern established: feat prefix, story ID in message, brief description of implementation.

### References

- [Source: _bmad-output/project-planning-artifacts/epics.md#Story 2.7: Conversation Degradation Tracking]
- [Source: _bmad-output/project-planning-artifacts/epics.md#FR-2.3 Conversation Degradation Tracking]
- [Source: handoffkit/sentiment/rule_based.py] - RuleBasedAnalyzer with history parameter
- [Source: handoffkit/sentiment/models.py] - SentimentFeatures with recent_negative_trend field
- [Source: handoffkit/core/types.py] - SentimentResult model

## Dev Agent Record

### Agent Model Used

gemini-claude-sonnet-4-5-thinking

### Debug Log References

N/A - Clean implementation with no significant debugging needed

### Completion Notes List

- Created `DegradationTracker` class in `handoffkit/sentiment/degradation.py` using `collections.deque` for efficient rolling window
- Implemented configurable `window_size` (default 5) and `threshold` (default 0.3) parameters
- Trend calculation: `first_score - last_score` (positive = degrading, negative = improving)
- Added `DegradationResult` model to `handoffkit/sentiment/models.py` with fields: is_degrading, trend_value, window_size, scores
- Integrated with `RuleBasedAnalyzer` via optional `degradation_tracker` parameter
- Analyzer now tracks sentiment scores from historical user messages when history provided
- Added `degradation_detected` field to `SentimentResult` model
- Degradation detection triggers escalation even if score alone wouldn't trigger
- Populated contextual fields: `recent_negative_trend`, `conversation_length`, `message_position`
- Added `SENTIMENT_DEGRADATION` to `TriggerType` enum
- Comprehensive logging at DEBUG (trend calculation) and INFO (degradation events) levels
- Created 20 unit tests in `tests/test_degradation_tracking.py` covering all acceptance criteria
- Created 8 integration tests in `tests/test_degradation_integration.py` for RuleBasedAnalyzer integration
- All 463 tests pass (435 existing + 20 degradation + 8 integration)
- Performance verified: <10ms for evaluation (typically <1ms)
- Handles edge cases: empty history, single score, fewer than window_size messages
- Used pytest.approx for floating-point comparisons in tests
- Refactored `analyze()` to extract `_calculate_score()` helper method for code reuse

### File List

- `handoffkit/sentiment/degradation.py` - New DegradationTracker class (129 lines)
- `handoffkit/sentiment/models.py` - Added DegradationResult model
- `handoffkit/sentiment/rule_based.py` - Integrated degradation tracking with RuleBasedAnalyzer
- `handoffkit/sentiment/__init__.py` - Exported DegradationTracker and DegradationResult
- `handoffkit/core/types.py` - Added degradation_detected field to SentimentResult, added SENTIMENT_DEGRADATION to TriggerType
- `tests/test_degradation_tracking.py` - 20 comprehensive unit tests
- `tests/test_degradation_integration.py` - 8 integration tests for RuleBasedAnalyzer

