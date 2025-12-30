# Story 2.8: Local LLM Sentiment Analysis (Tier 2)

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer using handoffkit[ml] installation**,
I want to **use DistilBERT for accurate semantic sentiment analysis**,
So that **I get better accuracy than rule-based without API costs**.

## Acceptance Criteria

1. **Given** handoffkit[ml] is installed **When** sentiment is analyzed **Then** DistilBERT model is used for semantic understanding **And** analysis completes in <100ms (CPU) **And** accuracy is ~92% on standard sentiment benchmarks

2. **Given** the financial_domain config is True **When** sentiment is analyzed **Then** FinBERT model is used instead **And** banking-specific terms are weighted appropriately

3. **Given** models are not yet downloaded **When** first analysis is requested **Then** models are downloaded on-demand (~500MB) **And** progress is logged

## Tasks / Subtasks

- [ ] Task 1: Create LocalLLMAnalyzer class (AC: #1, #2, #3)
  - [ ] Subtask 1.1: Create `handoffkit/sentiment/local_llm.py` with LocalLLMAnalyzer class
  - [ ] Subtask 1.2: Implement `__init__` with model initialization (DistilBERT and FinBERT)
  - [ ] Subtask 1.3: Handle on-demand model download with progress logging
  - [ ] Subtask 1.4: Support CPU/GPU device selection via config

- [ ] Task 2: Implement DistilBERT sentiment analysis (AC: #1)
  - [ ] Subtask 2.1: Load `distilbert-base-uncased-finetuned-sst-2-english` model via transformers pipeline
  - [ ] Subtask 2.2: Implement `analyze()` method returning SentimentResult
  - [ ] Subtask 2.3: Map DistilBERT output (POSITIVE/NEGATIVE + score) to normalized 0.0-1.0 range
  - [ ] Subtask 2.4: Maintain <100ms performance on CPU

- [ ] Task 3: Implement FinBERT for financial domain (AC: #2)
  - [ ] Subtask 3.1: Load `ProsusAI/finbert` model when financial_domain=True
  - [ ] Subtask 3.2: Handle banking-specific terminology appropriately
  - [ ] Subtask 3.3: Map FinBERT output to normalized sentiment scores
  - [ ] Subtask 3.4: Support switching between models based on config

- [ ] Task 4: Integrate with SentimentAnalyzer (AC: #1)
  - [ ] Subtask 4.1: Update `handoffkit/sentiment/analyzer.py` to support Tier 2
  - [ ] Subtask 4.2: Implement tier escalation: Tier 1 → Tier 2 when ambiguous
  - [ ] Subtask 4.3: Set tier_used="local_llm" in SentimentResult when Tier 2 used
  - [ ] Subtask 4.4: Maintain graceful degradation if transformers not installed

- [ ] Task 5: Model management and caching (AC: #3)
  - [ ] Subtask 5.1: Implement singleton pattern for model instances (load once, reuse)
  - [ ] Subtask 5.2: Add model download progress logging using tqdm or logging
  - [ ] Subtask 5.3: Cache models in ~/.cache/huggingface (transformers default)
  - [ ] Subtask 5.4: Handle download errors gracefully with helpful error messages

- [ ] Task 6: Update package dependencies (AC: #1, #2, #3)
  - [ ] Subtask 6.1: Add `transformers>=4.36.0` to `ml` extras in pyproject.toml
  - [ ] Subtask 6.2: Add `torch>=2.1.0` to `ml` extras (CPU-optimized)
  - [ ] Subtask 6.3: Add `tqdm` for download progress (if not already included)
  - [ ] Subtask 6.4: Update installation docs to mention model download on first run

- [ ] Task 7: Create comprehensive tests (AC: #1, #2, #3)
  - [ ] Subtask 7.1: Create `tests/test_local_llm_analyzer.py`
  - [ ] Subtask 7.2: Test DistilBERT model loads and analyzes sentiment correctly
  - [ ] Subtask 7.3: Test FinBERT model when financial_domain=True
  - [ ] Subtask 7.4: Test performance (<100ms for analysis)
  - [ ] Subtask 7.5: Test graceful handling when models not downloaded (mock download)
  - [ ] Subtask 7.6: Test tier escalation in SentimentAnalyzer
  - [ ] Subtask 7.7: Run all tests to verify no regressions (463+ tests passing)

- [ ] Task 8: Export new classes from package (AC: #1)
  - [ ] Subtask 8.1: Export LocalLLMAnalyzer from handoffkit.sentiment
  - [ ] Subtask 8.2: Update __init__.py with conditional import (try/except for transformers)

## Dev Notes

- **Existing Code**:
  - `RuleBasedAnalyzer` (Tier 1) already implemented in Story 2.5
  - `SentimentAnalyzer` exists but currently only uses Tier 1
  - `DegradationTracker` from Story 2.7 works with any tier
  - All 463 tests currently passing

- **Architecture Reference**:
  - Section 2.6 "LLM Integration Architecture" - 3-tier strategy
  - Tier 2: Local LLM (50-100ms, ~92% accuracy)
  - Models: DistilBERT (general, 268MB) and FinBERT (financial, 438MB)
  - Performance target: <100ms on CPU (95th percentile)

- **Performance Target**: <100ms for Tier 2 evaluation (must maintain)

### Algorithm Design

```python
from transformers import pipeline
import torch

class LocalLLMAnalyzer:
    def __init__(
        self,
        device: str = "cpu",
        financial_domain: bool = False,
    ) -> None:
        \"\"\"Initialize Local LLM analyzer with model selection.

        Args:
            device: \"cpu\" or \"cuda\" for GPU acceleration
            financial_domain: If True, use FinBERT instead of DistilBERT
        \"\"\"
        self._device = 0 if device == "cuda" and torch.cuda.is_available() else -1
        self._financial_domain = financial_domain

        # Load appropriate model based on domain
        if financial_domain:
            self._model_name = "ProsusAI/finbert"
        else:
            self._model_name = "distilbert-base-uncased-finetuned-sst-2-english"

        # Initialize pipeline (downloads model on first run)
        self._sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model=self._model_name,
            device=self._device
        )

    async def analyze(
        self,
        message: Message,
        history: Optional[list[Message]] = None,
    ) -> SentimentResult:
        \"\"\"Analyze sentiment using local LLM.

        Args:
            message: Current message to analyze
            history: Optional conversation history (unused in Tier 2)

        Returns:
            SentimentResult with score from local LLM
        \"\"\"
        start_time = time.perf_counter()

        # Run model inference
        result = self._sentiment_pipeline(message.content)[0]

        # Map DistilBERT/FinBERT output to 0.0-1.0 range
        # Output: {"label": "POSITIVE"/"NEGATIVE", "score": 0.0-1.0}
        if result["label"] == "POSITIVE":
            score = result["score"]  # Already 0.5-1.0
        else:  # NEGATIVE
            score = 1.0 - result["score"]  # Invert to 0.0-0.5

        processing_time_ms = (time.perf_counter() - start_time) * 1000

        return SentimentResult(
            score=score,
            frustration_level=1.0 - score,
            should_escalate=score < threshold,
            tier_used="local_llm",
            processing_time_ms=processing_time_ms,
        )
```

### Tier Escalation Logic

```python
# In SentimentAnalyzer.analyze()
async def analyze(self, message: Message, history: Optional[list[Message]] = None) -> SentimentResult:
    # Tier 1: Always run rule-based first
    tier1_result = await self._rule_based.analyze(message, history)

    # Check if we should escalate to Tier 2
    if self._config.enable_local_llm:
        # Escalate if Tier 1 is ambiguous (score near threshold)
        if abs(tier1_result.score - self._config.sentiment_threshold) < 0.1:
            # Use Tier 2 for more accurate analysis
            tier2_result = await self._local_llm.analyze(message, history)
            return tier2_result

    return tier1_result
```

### Installation Configuration

pyproject.toml:
```toml
[project.optional-dependencies]
ml = [
    "transformers>=4.36.0",
    "torch>=2.1.0",
    "tqdm>=4.66.0",
]
```

Installation:
```bash
# Lightweight (Tier 1 only, ~5MB)
pip install handoffkit

# With Local LLM (Tier 1 + Tier 2, ~8MB + 500MB models on first run)
pip install handoffkit[ml]
```

### Project Structure Notes

- `handoffkit/sentiment/local_llm.py` - New LocalLLMAnalyzer class
- `handoffkit/sentiment/analyzer.py` - Update tier escalation logic
- `handoffkit/sentiment/__init__.py` - Conditional export (try/except transformers)
- `tests/test_local_llm_analyzer.py` - New test file
- `pyproject.toml` - Add ml extras dependencies

### Previous Story Learnings (from Story 2.7)

- All 463 tests currently passing
- RuleBasedAnalyzer.analyze() returns SentimentResult with tier_used field
- DegradationTracker integrates with any analyzer tier
- Use async/await for all analyze() methods
- Processing time tracking required for performance validation
- Use get_logger("sentiment.local_llm") for consistent logging
- Tests should use pytest.approx for floating-point comparisons

### Git Intelligence (Recent Commits)

```
032e435 feat: implement Story 2.7 - Conversation Degradation Tracking
f66e80b feat: implement Story 2.6 - Frustration Signal Detection (Caps and Punctuation)
4bb0e62 feat: implement Story 2.5 - Rule-Based Sentiment Scoring (Tier 1)
f6fa67c feat: implement Story 2.4 - Custom Rule Engine
347d5e7 feat: implement Story 2.3 - Critical Keyword Monitoring Trigger
```

Pattern established: feat prefix, story ID in message, brief description of implementation.

### Key Technical Considerations

1. **Model Download Handling**:
   - First run will download ~268MB (DistilBERT) or ~438MB (FinBERT)
   - Use transformers default cache (~/.cache/huggingface)
   - Log download progress with INFO level
   - Provide clear error if download fails (network issue)

2. **Performance Optimization**:
   - Load models once on initialization (singleton pattern)
   - Keep models in memory between requests
   - Use batch processing if multiple messages (future enhancement)
   - CPU optimization: torch.set_num_threads() for better performance

3. **Graceful Degradation**:
   - If transformers not installed → fall back to Tier 1 only
   - If model download fails → fall back to Tier 1
   - Log warnings when falling back, not errors

4. **Financial Domain Support**:
   - FinBERT specifically trained on financial text
   - Better at understanding banking terminology ("fraud", "dispute", "locked account")
   - Switch models via config.financial_domain boolean

5. **Memory Considerations**:
   - DistilBERT: ~500MB RAM when loaded
   - FinBERT: ~700MB RAM when loaded
   - Don't load both simultaneously (config selects one)
   - Consider model quantization for memory-constrained environments (future)

### References

- [Source: _bmad-output/project-planning-artifacts/epics.md#Story 2.8: Local LLM Sentiment Analysis]
- [Source: _bmad-output/architecture.md#2.6 LLM Integration Architecture]
- [Source: _bmad-output/architecture.md#Tier 2: Local LLM]
- [Source: handoffkit/sentiment/analyzer.py] - SentimentAnalyzer tier orchestration
- [Source: handoffkit/sentiment/rule_based.py] - Tier 1 implementation reference
- [Source: handoffkit/core/types.py] - SentimentResult model

## Dev Agent Record

### Agent Model Used

gemini-claude-sonnet-4-5-thinking

### Debug Log References

N/A - Clean implementation with no significant debugging needed

### Completion Notes List

- Created `LocalLLMAnalyzer` class in `handoffkit/sentiment/local_llm.py` with full DistilBERT and FinBERT support
- Implemented conditional imports with `TRANSFORMERS_AVAILABLE` flag for graceful degradation
- Added model selection logic: DistilBERT (general) or FinBERT (financial domain)
- Implemented device selection: CPU (-1) or GPU (0) with automatic CUDA detection
- Model pipeline loaded once during `__init__` (singleton pattern) and reused for all analyze() calls
- Implemented sentiment score mapping: POSITIVE → keep score, NEGATIVE → invert score (1.0 - score)
- Added frustration_level calculation as inverse of sentiment score
- Implemented threshold-based escalation logic in `analyze()` method
- Added comprehensive logging at INFO (initialization) and DEBUG (analysis) levels
- Processing time tracking using `time.perf_counter()` for performance validation
- Integrated with `SentimentAnalyzer` for tier escalation (Tier 1 → Tier 2 when ambiguous)
- Updated `SentimentConfig` with new fields: `sentiment_threshold`, `enable_local_llm`, `financial_domain`
- Added tier escalation logic in `SentimentAnalyzer.analyze()`: escalates when score within 0.1 of threshold
- Implemented `analyze_with_tier()` method for explicit tier selection
- Created 15 comprehensive unit tests in `tests/test_local_llm_analyzer.py` covering all acceptance criteria
- All 478 tests pass (463 existing + 15 new)
- LocalLLMAnalyzer already exported from `handoffkit.sentiment.__init__.py`
- ML dependencies already in pyproject.toml: `transformers>=4.36.0`, `torch>=2.1.0`
- transformers library includes tqdm for download progress automatically

### File List

- `handoffkit/sentiment/local_llm.py` - Complete LocalLLMAnalyzer implementation (161 lines)
- `handoffkit/sentiment/analyzer.py` - Updated with Tier 2 integration and escalation logic
- `handoffkit/core/config.py` - Added sentiment_threshold, enable_local_llm, financial_domain fields to SentimentConfig
- `tests/test_local_llm_analyzer.py` - 15 comprehensive unit tests (300 lines)
- `handoffkit/sentiment/__init__.py` - Already exports LocalLLMAnalyzer (no changes needed)
- `pyproject.toml` - ML dependencies already present (no changes needed)
