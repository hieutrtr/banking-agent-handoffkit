# Story 2.9: Optional Cloud LLM Integration (Tier 3)

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer needing highest accuracy**,
I want to **optionally use cloud LLM for complex sentiment analysis**,
So that **ambiguous cases get the most accurate detection**.

## Acceptance Criteria

1. **Given** cloud_llm_enabled=True and cloud_llm_api_key is set **When** local LLM confidence is below threshold (default 0.3) **Then** cloud LLM (GPT-4o-mini or Claude) is called for analysis **And** response time is <500ms

2. **Given** cloud LLM is configured with OpenAI **When** complex conversation is analyzed **Then** the full conversation context is sent **And** structured JSON response with reasoning is returned

3. **Given** cloud LLM API call fails **When** fallback occurs **Then** local LLM result is used **And** error is logged but not raised

## Tasks / Subtasks

- [x] Task 1: Implement CloudLLMAnalyzer (AC: #1, #2, #3)
  - [x] Subtask 1.1: Complete `handoffkit/sentiment/cloud_llm.py` - replace NotImplementedError stubs
  - [x] Subtask 1.2: Implement `initialize()` method for OpenAI and Anthropic clients
  - [x] Subtask 1.3: Implement `analyze()` method with proper prompt engineering
  - [x] Subtask 1.4: Add structured JSON response parsing with validation
  - [x] Subtask 1.5: Implement timeout handling (<500ms target)

- [x] Task 2: Add OpenAI integration (AC: #1, #2)
  - [x] Subtask 2.1: Use `openai` async client with `AsyncOpenAI`
  - [x] Subtask 2.2: Implement sentiment analysis prompt with JSON response format
  - [x] Subtask 2.3: Default model: `gpt-4o-mini` (cost-effective, <$0.15/1M tokens)
  - [x] Subtask 2.4: Handle response parsing to SentimentResult

- [x] Task 3: Add Anthropic integration (AC: #1, #2)
  - [x] Subtask 3.1: Use `anthropic` async client with `AsyncAnthropic`
  - [x] Subtask 3.2: Default model: `claude-3-haiku-20240307` (fastest, cheapest)
  - [x] Subtask 3.3: Adapt prompt for Claude's response style
  - [x] Subtask 3.4: Handle response parsing to SentimentResult

- [x] Task 4: Update SentimentConfig for Cloud LLM (AC: #1)
  - [x] Subtask 4.1: Add `enable_cloud_llm: bool = False` field
  - [x] Subtask 4.2: Add `cloud_llm_provider: Optional[str] = None` (openai/anthropic)
  - [x] Subtask 4.3: Add `cloud_llm_api_key: Optional[str] = None`
  - [x] Subtask 4.4: Add `cloud_llm_model: str = "gpt-4o-mini"`
  - [x] Subtask 4.5: Add `cloud_llm_threshold: float = 0.3` (escalate when local < this)

- [x] Task 5: Integrate with SentimentAnalyzer (AC: #1, #3)
  - [x] Subtask 5.1: Initialize `_cloud_llm` when `enable_cloud_llm=True` and API key provided
  - [x] Subtask 5.2: Implement Tier 2 → Tier 3 escalation when local LLM confidence < cloud_llm_threshold
  - [x] Subtask 5.3: Implement graceful fallback to Tier 2 result on API errors
  - [x] Subtask 5.4: Log escalation decisions and results at DEBUG level

- [x] Task 6: Add error handling and fallback (AC: #3)
  - [x] Subtask 6.1: Handle API timeout errors gracefully (use httpx timeout)
  - [x] Subtask 6.2: Handle rate limit errors (429) with warning log
  - [x] Subtask 6.3: Handle authentication errors (401/403) with clear error message
  - [x] Subtask 6.4: Handle network errors with fallback to lower tier
  - [x] Subtask 6.5: Never raise exceptions - always return valid SentimentResult

- [x] Task 7: Add optional dependencies (AC: #1)
  - [x] Subtask 7.1: Add `openai>=1.0.0` to `cloud` extras in pyproject.toml
  - [x] Subtask 7.2: Add `anthropic>=0.25.0` to `cloud` extras in pyproject.toml
  - [x] Subtask 7.3: Create conditional import pattern (like TRANSFORMERS_AVAILABLE)
  - [x] Subtask 7.4: Add `OPENAI_AVAILABLE` and `ANTHROPIC_AVAILABLE` flags

- [x] Task 8: Create comprehensive tests (AC: #1, #2, #3)
  - [x] Subtask 8.1: Create `tests/test_cloud_llm_analyzer.py`
  - [x] Subtask 8.2: Test OpenAI provider initialization and analysis (mock API)
  - [x] Subtask 8.3: Test Anthropic provider initialization and analysis (mock API)
  - [x] Subtask 8.4: Test graceful fallback on API errors
  - [x] Subtask 8.5: Test timeout handling (<500ms requirement)
  - [x] Subtask 8.6: Test tier escalation in SentimentAnalyzer
  - [x] Subtask 8.7: Test conditional imports (when openai/anthropic not installed)
  - [x] Subtask 8.8: Run all tests to verify no regressions (625 tests passing, +32 new)

- [x] Task 9: Update exports (AC: #1)
  - [x] Subtask 9.1: Export CloudLLMAnalyzer from handoffkit.sentiment
  - [x] Subtask 9.2: Ensure conditional import doesn't break when deps not installed

## Dev Notes

### Existing Code Context

From Story 2.8 (just completed):
- `LocalLLMAnalyzer` class in `handoffkit/sentiment/local_llm.py` - Tier 2 implementation
- `SentimentAnalyzer` in `handoffkit/sentiment/analyzer.py` - orchestrates all tiers
- `TRANSFORMERS_AVAILABLE` flag pattern for conditional imports
- Tier 1 → Tier 2 escalation: when score within 0.1 of threshold
- All 593 tests currently passing

**Existing CloudLLMAnalyzer stub** (to be replaced):
```python
# handoffkit/sentiment/cloud_llm.py - Current stub
class CloudLLMAnalyzer:
    def __init__(self, provider="openai", api_key=None, model=None, endpoint=None):
        # Basic initialization exists

    async def initialize(self) -> None:
        raise NotImplementedError("CloudLLMAnalyzer initialization pending")

    async def analyze(self, message, history=None) -> SentimentResult:
        raise NotImplementedError("CloudLLMAnalyzer analysis pending")

    def is_available(self) -> bool:
        return self._api_key is not None
```

### Architecture Reference

**Section 2.6 "LLM Integration Architecture"** (architecture.md):
- Tier 3: Cloud LLM (200-500ms, highest accuracy)
- Providers: OpenAI (gpt-4o-mini, gpt-4o), Anthropic (claude-3-haiku, claude-3-sonnet)
- Only called for ambiguous cases (<10% of requests)
- Cost optimization: gpt-4o-mini at $0.15/1M tokens

**Performance Target**: <500ms for Tier 3 evaluation (95th percentile)

### Algorithm Design

```python
from typing import Optional
import time
import json

# Conditional imports
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

class CloudLLMAnalyzer:
    """Cloud API-based sentiment analysis for complex cases (Tier 3)."""

    SENTIMENT_PROMPT = """Analyze the sentiment of this customer service message.
Consider frustration level, urgency, and whether the user needs human assistance.

Message: {message}

Respond with JSON only:
{{
  "sentiment_score": 0.0-1.0 (0=very negative, 1=very positive),
  "frustration_level": 0.0-1.0 (0=calm, 1=very frustrated),
  "should_escalate": true/false,
  "reasoning": "brief explanation"
}}"""

    def __init__(
        self,
        provider: str = "openai",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        threshold: float = 0.3,
    ) -> None:
        self._provider = provider
        self._api_key = api_key
        self._model = model or self._default_model(provider)
        self._threshold = threshold
        self._client = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the async API client."""
        if self._provider == "openai" and OPENAI_AVAILABLE:
            self._client = AsyncOpenAI(api_key=self._api_key)
        elif self._provider == "anthropic" and ANTHROPIC_AVAILABLE:
            self._client = AsyncAnthropic(api_key=self._api_key)
        self._initialized = True

    async def analyze(
        self,
        message: Message,
        history: Optional[list[Message]] = None,
    ) -> SentimentResult:
        """Analyze sentiment using cloud LLM API."""
        if not self._initialized:
            await self.initialize()

        start_time = time.perf_counter()

        try:
            if self._provider == "openai":
                result = await self._analyze_openai(message.content)
            elif self._provider == "anthropic":
                result = await self._analyze_anthropic(message.content)
            else:
                raise ValueError(f"Unknown provider: {self._provider}")

            processing_time_ms = (time.perf_counter() - start_time) * 1000

            return SentimentResult(
                score=result["sentiment_score"],
                frustration_level=result["frustration_level"],
                should_escalate=result["should_escalate"],
                tier_used="cloud_llm",
                processing_time_ms=processing_time_ms,
            )

        except Exception as e:
            # Graceful fallback - log error but don't raise
            logger.warning(f"Cloud LLM error: {e}. Returning neutral result.")
            return SentimentResult(
                score=0.5,  # Neutral
                frustration_level=0.5,
                should_escalate=False,
                tier_used="cloud_llm",
                processing_time_ms=(time.perf_counter() - start_time) * 1000,
            )
```

### Tier Escalation Logic (Update SentimentAnalyzer)

```python
# In SentimentAnalyzer.analyze() - add after Tier 2
async def analyze(self, message: Message, history: Optional[list[Message]] = None) -> SentimentResult:
    # Tier 1: Always run rule-based first
    tier1_result = await self._rule_based.analyze(message, history)

    # Tier 2 escalation (existing code)
    if self._config.enable_local_llm and self._local_llm is not None:
        if abs(tier1_result.score - self._config.sentiment_threshold) < 0.1:
            tier2_result = await self._local_llm.analyze(message, history)

            # NEW: Tier 3 escalation
            if self._config.enable_cloud_llm and self._cloud_llm is not None:
                if tier2_result.score < self._config.cloud_llm_threshold:
                    logger.debug(
                        f"Escalating to Tier 3: Tier 2 score {tier2_result.score:.3f} "
                        f"below threshold {self._config.cloud_llm_threshold}"
                    )
                    tier3_result = await self._cloud_llm.analyze(message, history)
                    return tier3_result

            return tier2_result

    return tier1_result
```

### Configuration Updates (SentimentConfig)

```python
class SentimentConfig(BaseModel):
    # ... existing fields ...

    # Cloud LLM Settings (Tier 3)
    enable_cloud_llm: bool = Field(
        default=False,
        description="Enable Tier 3 (cloud LLM) sentiment analysis",
    )
    cloud_llm_provider: Optional[str] = Field(
        default=None,
        pattern="^(openai|anthropic)$",
        description="Cloud LLM provider: 'openai' or 'anthropic'",
    )
    cloud_llm_api_key: Optional[str] = Field(
        default=None,
        description="API key for cloud LLM provider",
    )
    cloud_llm_model: str = Field(
        default="gpt-4o-mini",
        description="Model to use for cloud LLM analysis",
    )
    cloud_llm_threshold: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Escalate to cloud LLM when local score below this threshold",
    )
```

### Previous Story Learnings (from Story 2.8)

- All 593 tests currently passing (increased from 478 in Story 2.8)
- LocalLLMAnalyzer returns SentimentResult with tier_used="local_llm"
- SentimentAnalyzer already has `_cloud_llm` attribute (set to None)
- `analyze_with_tier()` method exists for explicit tier selection
- Use async/await for all analyze() methods
- Processing time tracking required for performance validation
- Use get_logger("sentiment.cloud_llm") for consistent logging
- Conditional imports pattern: `TRANSFORMERS_AVAILABLE` flag

### Git Intelligence (Recent Commits)

```
1e87e65 feat(3-4): implement conversation summarization with code review fixes
d7313a6 fix(3-2): code review - add negative duration handling and tests
d97b9e0 feat: implement Story 2.8 - Local LLM Sentiment Analysis (Tier 2)
032e435 feat: implement Story 2.7 - Conversation Degradation Tracking
f66e80b feat: implement Story 2.6 - Frustration Signal Detection (Caps and Punctuation)
```

Pattern: `feat(X-Y): description` or `feat: implement Story X.Y - Title`

### Key Technical Considerations

1. **API Client Libraries**:
   - OpenAI: `openai>=1.0.0` with `AsyncOpenAI` class
   - Anthropic: `anthropic>=0.25.0` with `AsyncAnthropic` class
   - Both support async/await patterns

2. **Prompt Engineering**:
   - Request JSON response format for structured parsing
   - OpenAI: Use `response_format={"type": "json_object"}`
   - Anthropic: Include explicit JSON format instructions in prompt
   - Include reasoning field for debugging

3. **Error Handling Strategy**:
   - Never raise exceptions from analyze() - always return valid SentimentResult
   - Log errors at WARNING level
   - Return neutral score (0.5) on any failure
   - Handle specific errors: timeout, rate limit (429), auth (401/403)

4. **Timeout Configuration**:
   - Target: <500ms response time
   - Set timeout at 2000ms to allow for network variance
   - Use httpx timeout in both OpenAI and Anthropic clients

5. **Cost Optimization**:
   - Only escalate when local LLM confidence < threshold (default 0.3)
   - Use cheapest models by default (gpt-4o-mini, claude-3-haiku)
   - Expected: <10% of requests use cloud LLM
   - gpt-4o-mini: $0.15/1M input, $0.60/1M output tokens

6. **Testing Strategy**:
   - Mock API responses for unit tests (don't make real API calls)
   - Test error handling paths thoroughly
   - Test conditional imports (when packages not installed)
   - Use `pytest.mark.asyncio` for async tests

### Project Structure Notes

Files to modify/create:
- `handoffkit/sentiment/cloud_llm.py` - Replace stubs with implementation
- `handoffkit/core/config.py` - Add cloud LLM config fields to SentimentConfig
- `handoffkit/sentiment/analyzer.py` - Add Tier 2 → Tier 3 escalation
- `tests/test_cloud_llm_analyzer.py` - New comprehensive test file
- `pyproject.toml` - Add `cloud` extras with openai and anthropic

### References

- [Source: _bmad-output/project-planning-artifacts/epics.md#Story 2.9: Optional Cloud LLM Integration]
- [Source: _bmad-output/architecture.md#Tier 3: Cloud LLM (Optional, User Opt-In)]
- [Source: _bmad-output/architecture.md#2.6 LLM Integration Architecture]
- [Source: handoffkit/sentiment/analyzer.py] - SentimentAnalyzer tier orchestration
- [Source: handoffkit/sentiment/local_llm.py] - Tier 2 implementation reference
- [Source: handoffkit/sentiment/cloud_llm.py] - Existing stub to implement
- [Source: handoffkit/core/config.py#SentimentConfig] - Config fields to add

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5

### Debug Log References

No debug issues encountered during implementation.

### Completion Notes List

1. Implemented CloudLLMAnalyzer with full OpenAI and Anthropic integration
2. Added conditional imports: `OPENAI_AVAILABLE` and `ANTHROPIC_AVAILABLE` flags
3. Implemented graceful error handling - never raises exceptions, returns neutral result (0.5) on any error
4. Added 5 new config fields to SentimentConfig for cloud LLM configuration
5. Integrated Tier 2 → Tier 3 escalation in SentimentAnalyzer.analyze()
6. Added `cloud` extras in pyproject.toml with openai>=1.0.0 and anthropic>=0.25.0
7. Created 39 comprehensive tests covering:
   - OpenAI and Anthropic initialization and analysis
   - Error handling and graceful fallback (429/401/403/network errors)
   - Timeout handling (with Anthropic timeout fix)
   - Conditional imports
   - SentimentConfig cloud fields
   - SentimentAnalyzer integration
   - Full Tier 2 → Tier 3 escalation flow
   - Fallback to Tier 2 on cloud LLM error (AC #3)
8. All 632 tests passing (up from 593, +39 new tests)
9. Exported OPENAI_AVAILABLE and ANTHROPIC_AVAILABLE from handoffkit.sentiment
10. Code review fixes applied:
    - Added timeout to Anthropic client initialization
    - Fixed fallback to return tier2_result on cloud error (not neutral)
    - Removed unused _endpoint parameter
    - Completed docstring examples

### File List

- handoffkit/sentiment/cloud_llm.py - CloudLLMAnalyzer implementation (replaced stub)
- handoffkit/core/config.py - Added cloud LLM fields to SentimentConfig
- handoffkit/sentiment/analyzer.py - Added Tier 2 → Tier 3 escalation with fallback
- handoffkit/sentiment/__init__.py - Updated exports with availability flags
- pyproject.toml - Added `cloud` extras with openai and anthropic
- uv.lock - Updated with cloud dependencies
- tests/test_cloud_llm_analyzer.py - Comprehensive tests (escalation, error handling)
