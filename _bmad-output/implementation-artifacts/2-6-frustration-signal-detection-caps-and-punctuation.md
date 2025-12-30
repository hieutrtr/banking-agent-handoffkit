# Story 2.6: Frustration Signal Detection (Caps and Punctuation)

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **chatbot developer**,
I want to **detect frustration from text formatting like CAPS LOCK and excessive punctuation**,
So that **I catch non-verbal frustration signals**.

## Acceptance Criteria

1. **Given** a message with ALL CAPS words like "I NEED HELP NOW" **When** sentiment is analyzed **Then** the score is reduced by 0.1 per caps word **And** this combines with other negative signals

2. **Given** excessive punctuation like "Why isn't this working???" or "Help!!!" **When** sentiment is analyzed **Then** the score is reduced by 0.05 per excessive punctuation instance (3+ consecutive ! or ?)

3. **Given** a message with both ALL CAPS and excessive punctuation **When** sentiment is analyzed **Then** signals combine for a stronger frustration indicator **And** frustration_level reflects the combined intensity

4. **Given** normal text with proper capitalization **When** sentiment is analyzed **Then** no caps penalty is applied

5. **Given** the analyzer is invoked **When** <10ms passes **Then** the evaluation completes (performance requirement - Tier 1 rule-based)

## Tasks / Subtasks

- [x] Task 1: Enhance caps word detection (AC: #1, #4)
  - [x] Subtask 1.1: Add method _count_caps_words() to count words that are entirely uppercase
  - [x] Subtask 1.2: Minimum word length of 2 characters to count as caps word (avoid counting "I", "A")
  - [x] Subtask 1.3: Extract caps_word_count in extract_features() method
  - [x] Subtask 1.4: Add caps_word_count field to SentimentFeatures model if needed

- [x] Task 2: Enhance punctuation pattern detection (AC: #2)
  - [x] Subtask 2.1: Add pattern to detect 3+ consecutive exclamation marks (!!!)
  - [x] Subtask 2.2: Add pattern to detect 3+ consecutive question marks (???)
  - [x] Subtask 2.3: Add pattern to detect mixed excessive punctuation (!?!? or ?!?!)
  - [x] Subtask 2.4: Extract excessive_punctuation_count in extract_features()

- [x] Task 3: Update scoring algorithm (AC: #1, #2, #3)
  - [x] Subtask 3.1: Apply -0.1 per caps word (replacing simple caps_ratio > 0.5 check)
  - [x] Subtask 3.2: Apply -0.05 per excessive punctuation instance
  - [x] Subtask 3.3: Cap maximum penalty from caps words at -0.3 (3 words max impact)
  - [x] Subtask 3.4: Cap maximum penalty from punctuation at -0.2 (4 instances max impact)
  - [x] Subtask 3.5: Maintain backward compatibility with existing threshold-based escalation

- [x] Task 4: Update frustration_level calculation (AC: #3)
  - [x] Subtask 4.1: Include caps_word_count in frustration_level formula
  - [x] Subtask 4.2: Include excessive_punctuation_count in frustration_level formula
  - [x] Subtask 4.3: Normalize frustration_level to 0.0-1.0 range

- [x] Task 5: Create comprehensive tests (AC: #1, #2, #3, #4, #5)
  - [x] Subtask 5.1: Create `tests/test_frustration_signals.py`
  - [x] Subtask 5.2: Test single caps word reduces score by 0.1
  - [x] Subtask 5.3: Test multiple caps words have cumulative effect
  - [x] Subtask 5.4: Test excessive !!! reduces score by 0.05 per instance
  - [x] Subtask 5.5: Test excessive ??? reduces score by 0.05 per instance
  - [x] Subtask 5.6: Test combined caps + punctuation has stronger effect
  - [x] Subtask 5.7: Test normal capitalization has no penalty
  - [x] Subtask 5.8: Test performance (<10ms for evaluation)
  - [x] Subtask 5.9: Run all tests to verify no regressions (419+ tests passing)

- [x] Task 6: Update logging for new signals (AC: #1, #2)
  - [x] Subtask 6.1: Log caps_word_count at DEBUG level
  - [x] Subtask 6.2: Log excessive_punctuation_count at DEBUG level
  - [x] Subtask 6.3: Log combined frustration signal strength

## Dev Notes

- **Existing Code**: Story 2.5 implemented basic caps and punctuation handling in `RuleBasedAnalyzer`:
  - Current: `caps_ratio > 0.5` triggers flat -0.1 penalty
  - Current: `exclamation_count > 2` triggers -0.05 per extra mark
  - Need to enhance to per-word caps penalty and pattern-based punctuation detection

- **Architecture Reference**: See architecture.md section 2.6 and FR-2.2 "Caps Lock and Punctuation Detection"

- **Performance Target**: <10ms for Tier 1 rule-based evaluation (must maintain)

- **Existing Models**: SentimentFeatures in `handoffkit/sentiment/models.py` may need new fields

### Scoring Algorithm Enhancement

```python
# Current implementation (Story 2.5):
if features.caps_ratio > 0.5:
    score -= 0.1  # Flat penalty

if features.exclamation_count > 2:
    score -= 0.05 * (features.exclamation_count - 2)

# New implementation (Story 2.6):
# Count ALL CAPS words (2+ chars, all uppercase)
caps_word_count = sum(1 for word in words if len(word) >= 2 and word.isupper())
score -= min(caps_word_count * 0.1, 0.3)  # Max -0.3 penalty

# Count excessive punctuation patterns (3+ consecutive ! or ?)
excessive_punct_count = len(re.findall(r'[!?]{3,}', content))
score -= min(excessive_punct_count * 0.05, 0.2)  # Max -0.2 penalty
```

### Caps Word Detection Rules

- Word must be 2+ characters (avoid penalizing "I", "A")
- Word must be entirely uppercase
- Examples that count: "HELP", "NOW", "URGENT"
- Examples that don't count: "I", "A", "Help", "HELP."

### Excessive Punctuation Patterns

- 3+ consecutive exclamation marks: `!!!`, `!!!!`, etc.
- 3+ consecutive question marks: `???`, `????`, etc.
- Mixed patterns: `!?!`, `?!?!`, etc. (3+ chars of ! and ?)

### Project Structure Notes

- `handoffkit/sentiment/rule_based.py` - Main implementation file to modify
- `handoffkit/sentiment/models.py` - May need to add fields to SentimentFeatures
- `tests/test_frustration_signals.py` - New test file

### Previous Story Learnings (from Story 2.5)

- All 419 tests currently passing
- RuleBasedAnalyzer already has extract_features() and analyze() methods
- Pre-compiled regex patterns work well for performance
- Maintain backward compatibility with existing tests
- Use get_logger("sentiment.rule_based") for consistent logging

### Git Intelligence (Recent Commits)

```
4bb0e62 feat: implement Story 2.5 - Rule-Based Sentiment Scoring (Tier 1)
f6fa67c feat: implement Story 2.4 - Custom Rule Engine
347d5e7 feat: implement Story 2.3 - Critical Keyword Monitoring Trigger
```

Pattern established: feat prefix, story ID in message, brief description of implementation.

### References

- [Source: _bmad-output/project-planning-artifacts/epics.md#Story 2.6: Frustration Signal Detection]
- [Source: _bmad-output/architecture.md#FR-2.2 Caps Lock and Punctuation Detection]
- [Source: handoffkit/sentiment/rule_based.py] - Current implementation with basic caps/punctuation handling
- [Source: handoffkit/sentiment/models.py] - SentimentFeatures model
- [Source: tests/test_sentiment_rule_based.py] - Existing tests for reference

## Dev Agent Record

### Agent Model Used

gemini-claude-opus-4-5-thinking

### Debug Log References

N/A - Clean implementation with no significant debugging needed

### Completion Notes List

- Enhanced RuleBasedAnalyzer with per-word caps detection via `_count_caps_words()` method
- Added `caps_word_count` and `excessive_punctuation_count` fields to SentimentFeatures model
- Pre-compiled regex pattern `[!?]{3,}` for excessive punctuation detection (!!!, ???, !?!)
- Scoring algorithm updated:
  - Caps penalty: -0.1 per ALL CAPS word (2+ chars), capped at -0.3 (3 words max)
  - Punctuation penalty: -0.05 per excessive pattern instance, capped at -0.2 (4 instances max)
- frustration_level calculation updated to include both caps_word_count and excessive_punctuation_count
- Single letter caps (I, A) correctly excluded from penalty
- Enhanced DEBUG logging with new signal counts
- All 435 tests pass (419 existing + 16 new)
- Performance verified: <10ms for evaluation (actual: <1ms typically)

### File List

- `handoffkit/sentiment/rule_based.py` - Enhanced implementation with new detection methods
- `handoffkit/sentiment/models.py` - Added caps_word_count and excessive_punctuation_count fields
- `tests/test_frustration_signals.py` - 16 comprehensive tests for Story 2.6
