# Story 1.4: Configuration Management System

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer deploying HandoffKit**,
I want to **configure settings via environment variables or config file**,
so that **I can change behavior without modifying code**.

## Acceptance Criteria

1. **Given** environment variables are set (HANDOFFKIT_FAILURE_THRESHOLD, HANDOFFKIT_SENTIMENT_THRESHOLD) **When** HandoffOrchestrator is created without explicit config **Then** it reads configuration from environment variables **And** environment variables override default values

2. **Given** a config.yaml file exists in the working directory **When** HandoffOrchestrator is created **Then** it loads configuration from the file **And** environment variables take precedence over file configuration

## Tasks / Subtasks

- [x] Task 1: Create configuration loader module (AC: #1, #2)
  - [x] Subtask 1.1: Create `handoffkit/core/config_loader.py` with ConfigLoader class
  - [x] Subtask 1.2: Implement `load_from_env()` method to read HANDOFFKIT_* environment variables
  - [x] Subtask 1.3: Implement `load_from_file()` method to read YAML config files
  - [x] Subtask 1.4: Implement `load()` method that combines both sources with correct precedence

- [x] Task 2: Define environment variable mappings (AC: #1)
  - [x] Subtask 2.1: Map HANDOFFKIT_FAILURE_THRESHOLD → TriggerConfig.failure_threshold (int)
  - [x] Subtask 2.2: Map HANDOFFKIT_SENTIMENT_THRESHOLD → TriggerConfig.sentiment_threshold (float)
  - [x] Subtask 2.3: Map HANDOFFKIT_HELPDESK → IntegrationConfig.provider (str)
  - [x] Subtask 2.4: Map HANDOFFKIT_API_KEY → IntegrationConfig.api_key (str)
  - [x] Subtask 2.5: Map HANDOFFKIT_API_URL → IntegrationConfig.api_url (str)
  - [x] Subtask 2.6: Map HANDOFFKIT_CRITICAL_KEYWORDS → TriggerConfig.critical_keywords (comma-separated list)
  - [x] Subtask 2.7: Map HANDOFFKIT_MAX_CONTEXT_MESSAGES → HandoffConfig.max_context_messages (int)
  - [x] Subtask 2.8: Map HANDOFFKIT_ROUTING_STRATEGY → RoutingConfig.strategy (str)
  - [x] Subtask 2.9: Add type coercion with helpful error messages for invalid values

- [x] Task 3: Implement YAML file configuration loading (AC: #2)
  - [x] Subtask 3.1: Support loading from `handoffkit.yaml` or `handoffkit.yml` in current directory
  - [x] Subtask 3.2: Support loading from custom path via HANDOFFKIT_CONFIG_FILE env var
  - [x] Subtask 3.3: Parse YAML structure matching HandoffConfig nested structure
  - [x] Subtask 3.4: Validate loaded values against Pydantic model constraints
  - [x] Subtask 3.5: Handle missing file gracefully (use defaults)

- [x] Task 4: Implement configuration precedence (AC: #1, #2)
  - [x] Subtask 4.1: Precedence order: explicit config > env vars > config file > defaults
  - [x] Subtask 4.2: Create `merge_configs()` function to combine multiple sources
  - [x] Subtask 4.3: Deep merge nested config (triggers, sentiment, routing, integration)
  - [x] Subtask 4.4: Document precedence in docstrings

- [x] Task 5: Integrate with HandoffOrchestrator (AC: #1, #2)
  - [x] Subtask 5.1: Update HandoffOrchestrator.__init__ to use ConfigLoader when no config provided
  - [x] Subtask 5.2: Add `from_env()` class method as convenience factory
  - [x] Subtask 5.3: Add `from_file(path)` class method for explicit file loading
  - [x] Subtask 5.4: Preserve current behavior when explicit config is passed

- [x] Task 6: Create comprehensive tests (AC: #1, #2)
  - [x] Subtask 6.1: Create `tests/test_config_loader.py` with test class
  - [x] Subtask 6.2: Test environment variable loading for each HANDOFFKIT_* var
  - [x] Subtask 6.3: Test YAML file loading with valid config
  - [x] Subtask 6.4: Test precedence: env vars override file values
  - [x] Subtask 6.5: Test precedence: explicit config overrides env vars
  - [x] Subtask 6.6: Test handling of missing config file (uses defaults)
  - [x] Subtask 6.7: Test invalid environment variable values produce helpful errors
  - [x] Subtask 6.8: Test comma-separated list parsing for critical_keywords
  - [x] Subtask 6.9: Run all tests to verify no regressions (172 tests passing)

- [x] Task 7: Update package exports (AC: #1, #2)
  - [x] Subtask 7.1: Export ConfigLoader from handoffkit package if useful as public API
  - [x] Subtask 7.2: Add `load_config()` convenience function to package

## Dev Notes

- **PyYAML Dependency**: The project already has `pyyaml` available (check pyproject.toml). If not, add as optional dependency in `[project.optional-dependencies]`.
- **Environment Variable Prefix**: All env vars use `HANDOFFKIT_` prefix for namespace isolation.
- **Type Coercion**: Environment variables are strings - need to coerce to int, float, bool, list as needed.
- **Immutable Configs**: Remember all config models have `frozen=True` - use Pydantic's model construction, not mutation.
- **No Breaking Changes**: Existing code passing explicit `config` must continue to work unchanged.
- **Error Messages**: Follow Story 1.2 pattern of helpful, actionable error messages for invalid values.

### Environment Variable Mapping

| Environment Variable | Config Path | Type | Example |
|---------------------|-------------|------|---------|
| HANDOFFKIT_FAILURE_THRESHOLD | triggers.failure_threshold | int | `3` |
| HANDOFFKIT_SENTIMENT_THRESHOLD | triggers.sentiment_threshold | float | `0.3` |
| HANDOFFKIT_HELPDESK | integration.provider | str | `zendesk` |
| HANDOFFKIT_API_KEY | integration.api_key | str | `key123` |
| HANDOFFKIT_API_URL | integration.api_url | str | `https://api.example.com` |
| HANDOFFKIT_CRITICAL_KEYWORDS | triggers.critical_keywords | list | `fraud,emergency,stolen` |
| HANDOFFKIT_MAX_CONTEXT_MESSAGES | max_context_messages | int | `50` |
| HANDOFFKIT_ROUTING_STRATEGY | routing.strategy | str | `round_robin` |
| HANDOFFKIT_CONFIG_FILE | (special) | str | `/path/to/config.yaml` |

### YAML Config File Structure

```yaml
# handoffkit.yaml
triggers:
  failure_threshold: 3
  sentiment_threshold: 0.3
  critical_keywords:
    - fraud
    - emergency

sentiment:
  tier: rule_based

routing:
  strategy: round_robin

integration:
  provider: zendesk
  api_key: ${ZENDESK_API_KEY}  # Optional: support env var substitution in YAML

max_context_messages: 100
```

### Previous Story Learnings (from Story 1.3)

- HandoffOrchestrator now has `helpdesk` as first positional arg, `config` as keyword-only
- All config models are frozen (immutable) with `ConfigDict(frozen=True)`
- Use `model_copy(update={...})` for creating modified configs
- Tests follow patterns in test_types.py and test_config.py
- pytest with pydantic ValidationError assertions for error testing

### Project Structure Notes

- `handoffkit/core/config_loader.py` - New module for configuration loading
- `handoffkit/core/config.py` - Existing config models (no changes needed)
- `handoffkit/core/orchestrator.py` - Update to use ConfigLoader
- `tests/test_config_loader.py` - New test file
- Follow existing test patterns from tests/test_config.py

### References

- [Source: _bmad-output/project-planning-artifacts/epics.md#Story 1.4: Configuration Management System]
- [Source: handoffkit/core/config.py] - Current config models with frozen=True
- [Source: handoffkit/core/orchestrator.py] - Current constructor using default HandoffConfig
- [Source: _bmad-output/architecture.md#10.3 Environment Configuration] - Env var patterns
- [Source: _bmad-output/implementation-artifacts/1-3-handofforchestrator-base-interface.md] - Previous story learnings

## Dev Agent Record

### Agent Model Used

Claude (Opus 4.5)

### Debug Log References

N/A - No debugging issues encountered

### Completion Notes List

- Created `handoffkit/core/config_loader.py` with ConfigLoader class supporting environment variables and YAML files
- Implemented type coercion for env vars (str, int, float, bool, list) with helpful error messages
- Added deep merge functionality for nested config dictionaries
- Integrated ConfigLoader with HandoffOrchestrator via `from_env()` and `from_file()` class methods
- Added `load_config()` convenience function as top-level package export
- Created 49 tests for config_loader + 10 tests for orchestrator integration = 59 new tests
- Total test count: 172 tests passing
- PyYAML was already in pyproject.toml dependencies

### File List

- `handoffkit/core/config_loader.py` (created) - ConfigLoader class with env var and YAML loading
- `handoffkit/core/orchestrator.py` (modified) - Added from_env() and from_file() class methods
- `handoffkit/__init__.py` (modified) - Added ConfigLoader and load_config exports
- `tests/test_config_loader.py` (created) - 49 comprehensive tests for config loading
- `tests/test_orchestrator.py` (modified) - Added 10 tests for from_env/from_file methods

