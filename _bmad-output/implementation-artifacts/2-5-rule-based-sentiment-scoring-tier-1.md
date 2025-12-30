# Story 2.5: Rule-Based Sentiment Scoring (Tier 1)

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer using the lightweight SDK installation**,
I want to **detect user frustration using rule-based sentiment analysis**,
So that **I can identify negative sentiment without ML dependencies**.

## Acceptance Criteria

1. **Given** a message with strong negative keywords ("terrible", "awful", "frustrated") **When** sentiment is analyzed **Then** the score is < 0.3 (on 0.0-1.0 scale where 0 is negative) **And** analysis completes in <10ms

2. **Given** a neutral message without emotion indicators **When** sentiment is analyzed **Then** the score is approximately 0.5 (neutral baseline)

3. **Given** configurable negative keywords with weights (strong: -0.3, moderate: -0.15) **When** sentiment is calculated **Then** the algorithm uses the configured weights

4. **Given** sentiment threshold is configured (default: 0.3) **When** score falls below threshold **Then** should_escalate is set to True in SentimentResult

5. **Given** the analyzer is invoked **When** <10ms passes **Then** the evaluation completes (performance requirement - Tier 1 rule-based)

## Tasks / Subtasks

- [x] Task 1: Implement keyword scoring algorithm (AC: #1, #2, #3)
  - [x] Subtask 1.1: Define STRONG_NEGATIVE_KEYWORDS with -0.3 weight (terrible, awful, horrible, worst, hate, useless, stupid, ridiculous, unacceptable)
  - [x] Subtask 1.2: Define MODERATE_NEGATIVE_KEYWORDS with -0.15 weight (frustrated, annoyed, upset, disappointed, waste, angry)
  - [x] Subtask 1.3: Define POSITIVE_KEYWORDS with +0.2 weight (thank, great, awesome, excellent, helpful, amazing, perfect, wonderful, love, appreciate)
  - [x] Subtask 1.4: Implement score calculation starting from 0.5 baseline
  - [x] Subtask 1.5: Use pre-compiled regex with word boundaries for matching

- [x] Task 2: Implement extract_features() method (AC: #1, #3)
  - [x] Subtask 2.1: Count negative_keyword_count, positive_keyword_count, frustration_keyword_count
  - [x] Subtask 2.2: Extract exclamation_count and question_count
  - [x] Subtask 2.3: Calculate caps_ratio (uppercase letters / total letters)
  - [x] Subtask 2.4: Detect repeated_chars pattern (3+ consecutive same chars like "nooo" or "???")
  - [x] Subtask 2.5: Set message_length and conversation_length fields

- [x] Task 3: Implement RuleBasedAnalyzer.analyze() method (AC: #1, #2, #4, #5)
  - [x] Subtask 3.1: Import time module and get_logger from handoffkit.utils.logging
  - [x] Subtask 3.2: Call extract_features() to get SentimentFeatures
  - [x] Subtask 3.3: Calculate base score from keyword weights
  - [x] Subtask 3.4: Apply modifiers for caps_ratio and repeated punctuation
  - [x] Subtask 3.5: Clamp final score to 0.0-1.0 range
  - [x] Subtask 3.6: Set should_escalate based on threshold comparison
  - [x] Subtask 3.7: Return SentimentResult with score, frustration_level, tier_used="rule_based", processing_time_ms
  - [x] Subtask 3.8: Add DEBUG logging for feature extraction and scoring

- [x] Task 4: Add configurable thresholds (AC: #3, #4)
  - [x] Subtask 4.1: Accept threshold parameter in __init__ (default 0.3)
  - [x] Subtask 4.2: Accept custom keyword weights dict in __init__
  - [x] Subtask 4.3: Support domain-specific amplification (1.5x multiplier for domain keywords)

- [x] Task 5: Create comprehensive tests (AC: #1, #2, #3, #4, #5)
  - [x] Subtask 5.1: Create `tests/test_sentiment_rule_based.py`
  - [x] Subtask 5.2: Test strong negative keywords produce score < 0.3
  - [x] Subtask 5.3: Test neutral messages produce score ~0.5
  - [x] Subtask 5.4: Test positive keywords increase score
  - [x] Subtask 5.5: Test keyword weight configuration
  - [x] Subtask 5.6: Test threshold-based escalation
  - [x] Subtask 5.7: Test performance (<10ms for evaluation)
  - [x] Subtask 5.8: Test feature extraction (caps, punctuation, etc.)
  - [x] Subtask 5.9: Run all tests to verify no regressions (380+ tests passing)

- [x] Task 6: Add logging integration (AC: #5)
  - [x] Subtask 6.1: Initialize logger with get_logger("sentiment.rule_based")
  - [x] Subtask 6.2: Log evaluation start at DEBUG level
  - [x] Subtask 6.3: Log extracted features at DEBUG level
  - [x] Subtask 6.4: Log final score and escalation decision at DEBUG level
  - [x] Subtask 6.5: Log timing measurement (processing_time_ms in result)

- [x] Task 7: Verify package exports (AC: #1)
  - [x] Subtask 7.1: Ensure RuleBasedAnalyzer is exported from handoffkit.sentiment
  - [x] Subtask 7.2: Ensure SentimentFeatures is exported from handoffkit.sentiment

## Dev Notes

- **Existing Code**: `RuleBasedAnalyzer` skeleton exists at `handoffkit/sentiment/rule_based.py` with `__init__`, `extract_features`, and `analyze` method stubs (raise NotImplementedError)
- **Existing Models**: `SentimentFeatures` at `handoffkit/sentiment/models.py`, `SentimentResult` at `handoffkit/core/types.py`
- **Architecture Reference**: See architecture.md section 2.6 "LLM Integration Architecture" for Tier 1 rule-based approach
- **Performance Target**: <10ms for Tier 1 rule-based evaluation
- **Score Scale**: 0.0 (very negative) to 1.0 (very positive), 0.5 is neutral baseline
- **Threshold**: Default 0.3 - scores below this trigger escalation

### Keyword Weight Reference (from PRD FR-2.1)

Strong Negative (-0.3): terrible, awful, horrible, worst, hate, useless, stupid, ridiculous, unacceptable
Moderate Negative (-0.15): frustrated, annoyed, upset, disappointed, waste, angry
Positive (+0.2): thank, great, awesome, excellent, helpful, amazing, perfect, wonderful, love, appreciate
Frustration (-0.1): again, already, still, not working, doesn't work, broken, wrong, failed, error, problem

### Scoring Algorithm

```python
# Start with neutral baseline
score = 0.5

# Apply keyword weights
score += (positive_count * 0.2)
score -= (strong_negative_count * 0.3)
score -= (moderate_negative_count * 0.15)
score -= (frustration_count * 0.1)

# Apply modifiers
if caps_ratio > 0.5:
    score -= 0.1  # ALL CAPS penalty
if exclamation_count > 2:
    score -= 0.05 * (exclamation_count - 2)  # Excessive punctuation

# Clamp to valid range
score = max(0.0, min(1.0, score))
```

### Project Structure Notes

- `handoffkit/sentiment/rule_based.py` - Main implementation file (skeleton exists)
- `handoffkit/sentiment/models.py` - SentimentFeatures, SentimentTier models
- `handoffkit/core/types.py` - SentimentResult model
- `tests/test_sentiment_rule_based.py` - New test file

### Existing Keywords in Skeleton

The skeleton already has keyword lists defined:
- NEGATIVE_KEYWORDS: angry, frustrated, annoyed, upset, terrible, awful, horrible, worst, hate, useless, stupid, ridiculous, unacceptable, disappointed, waste
- POSITIVE_KEYWORDS: thank, great, awesome, excellent, helpful, amazing, perfect, wonderful, love, appreciate
- FRUSTRATION_KEYWORDS: again, already, still, not working, doesn't work, broken, wrong, failed, error, problem

Pre-compiled patterns exist in `__init__` via `_compile_pattern()` helper.

### Previous Story Learnings (from Story 2.1, 2.2, 2.3, 2.4)

- All 380 tests currently passing
- Use get_logger("sentiment.rule_based") for module-specific logging
- Follow async pattern (async def analyze)
- Use Pydantic models for type safety (SentimentResult, SentimentFeatures)
- Add timing measurement in result (processing_time_ms)
- Pre-compile regex patterns in __init__ for performance
- Return early on clear matches
- Handle edge cases gracefully (empty messages, None values)

### Git Intelligence (Recent Commits)

```
f6fa67c feat: implement Story 2.4 - Custom Rule Engine
347d5e7 feat: implement Story 2.3 - Critical Keyword Monitoring Trigger
a4696a1 feat: implement Story 2.2 - Failure Pattern Tracking Trigger
560d012 feat: implement Story 2.1 - Direct Request Detection Trigger
```

Pattern established: feat prefix, story ID in message, brief description of implementation.

### References

- [Source: _bmad-output/project-planning-artifacts/epics.md#Story 2.5: Rule-Based Sentiment Scoring (Tier 1)]
- [Source: _bmad-output/architecture.md#2.6 LLM Integration Architecture] - Tier 1 rule-based approach
- [Source: handoffkit/sentiment/rule_based.py] - Existing skeleton with keyword lists and pattern compilation
- [Source: handoffkit/sentiment/models.py] - SentimentFeatures, SentimentTier models
- [Source: handoffkit/core/types.py] - SentimentResult model (score, frustration_level, should_escalate, tier_used, processing_time_ms)

## Dev Agent Record

### Agent Model Used

gemini-claude-opus-4-5-thinking

### Debug Log References

N/A - Clean implementation with no significant debugging needed

### Completion Notes List

- Implemented RuleBasedAnalyzer.extract_features() method with full feature extraction
- Implemented RuleBasedAnalyzer.analyze() method with keyword scoring algorithm
- Keyword categories: STRONG_NEGATIVE (-0.3), MODERATE_NEGATIVE (-0.15), POSITIVE (+0.2), FRUSTRATION (-0.1)
- Score calculation starts from 0.5 baseline, applies keyword weights, then modifiers
- Caps ratio > 0.5 applies -0.1 penalty (ALL CAPS detection)
- Excessive punctuation (>2 exclamation marks) applies -0.05 per extra mark
- Configurable threshold parameter (default 0.3) for should_escalate decision
- Configurable keyword weights dict in __init__
- Domain-specific keyword amplification with 1.5x multiplier
- Pre-compiled regex patterns with word boundaries for performance
- Repeated character detection (3+ consecutive same char)
- Integrated structured logging (DEBUG level for all operations)
- Timing measurement in result (processing_time_ms)
- All 419 tests pass (380 existing + 39 new)
- Performance verified: <10ms for evaluation (actual: <1ms typically)

### File List

- `handoffkit/sentiment/rule_based.py` - Complete implementation (269 lines)
- `tests/test_sentiment_rule_based.py` - 39 comprehensive tests
