# Story 1.1: Project Skeleton and Package Structure

Status: done

## Story

As a **Python developer**,
I want to **install handoffkit via pip and import the core module**,
So that **I can begin integrating handoff logic into my chatbot**.

## Acceptance Criteria

1. **Given** a Python 3.9+ environment
   **When** I run `pip install handoffkit` (or `pip install -e .` for local dev)
   **Then** the package installs successfully without errors
   **And** I can run `from handoffkit import HandoffOrchestrator`
   **And** the package structure follows the architecture specification

2. **Given** the package is installed
   **When** I check the package metadata
   **Then** the version follows semantic versioning (e.g., 0.1.0)
   **And** the package size is under 5MB (without ML dependencies)

## Tasks / Subtasks

- [ ] Task 1: Initialize Project Structure (AC: #1)
  - [ ] 1.1: Create root project directory structure
  - [ ] 1.2: Create `pyproject.toml` with project metadata and dependencies
  - [ ] 1.3: Create `README.md` with basic usage instructions
  - [ ] 1.4: Create `.gitignore` for Python projects

- [ ] Task 2: Create Core Package Structure (AC: #1)
  - [ ] 2.1: Create `handoffkit/` package directory
  - [ ] 2.2: Create `handoffkit/__init__.py` with public exports
  - [ ] 2.3: Create `handoffkit/core/` subpackage
  - [ ] 2.4: Create `handoffkit/triggers/` subpackage
  - [ ] 2.5: Create `handoffkit/sentiment/` subpackage
  - [ ] 2.6: Create `handoffkit/context/` subpackage
  - [ ] 2.7: Create `handoffkit/routing/` subpackage
  - [ ] 2.8: Create `handoffkit/integrations/` subpackage
  - [ ] 2.9: Create `handoffkit/utils/` subpackage
  - [ ] 2.10: Create `handoffkit/api/` subpackage

- [ ] Task 3: Create Stub Classes and Imports (AC: #1)
  - [ ] 3.1: Create `handoffkit/core/orchestrator.py` with `HandoffOrchestrator` stub class
  - [ ] 3.2: Create `handoffkit/core/config.py` with `HandoffConfig` placeholder
  - [ ] 3.3: Create `handoffkit/core/types.py` with basic type stubs
  - [ ] 3.4: Ensure `from handoffkit import HandoffOrchestrator` works

- [ ] Task 4: Configure Package Metadata (AC: #2)
  - [ ] 4.1: Set version to 0.1.0 in `pyproject.toml`
  - [ ] 4.2: Configure optional dependencies: `[ml]`, `[dashboard]`, `[dev]`
  - [ ] 4.3: Add package classifiers and metadata

- [ ] Task 5: Create Test Infrastructure (AC: #1, #2)
  - [ ] 5.1: Create `tests/` directory structure
  - [ ] 5.2: Create `tests/conftest.py` with pytest fixtures
  - [ ] 5.3: Create `tests/test_package.py` with import tests
  - [ ] 5.4: Verify tests pass with `pytest`

- [ ] Task 6: Validation (AC: #1, #2)
  - [ ] 6.1: Run `pip install -e .` and verify installation
  - [ ] 6.2: Verify `from handoffkit import HandoffOrchestrator` works
  - [ ] 6.3: Verify package structure matches architecture spec
  - [ ] 6.4: Verify package size is under 5MB

## Dev Notes

### Architecture Requirements

The package structure MUST match the architecture specification exactly:

```
handoffkit/
├── __init__.py                 # Public API exports
├── core/
│   ├── __init__.py
│   ├── orchestrator.py         # Main HandoffOrchestrator class
│   ├── config.py               # Configuration management
│   └── types.py                # Core type definitions
├── triggers/
│   ├── __init__.py
│   ├── base.py                 # BaseTrigger abstract class
│   ├── direct_request.py       # Direct request detection
│   ├── failure_tracking.py     # Failed attempt tracking
│   ├── keyword.py              # Critical keyword monitoring
│   ├── custom_rules.py         # Custom rule engine
│   └── factory.py              # Trigger factory
├── sentiment/
│   ├── __init__.py
│   ├── analyzer.py             # Main sentiment analyzer
│   ├── rule_based.py           # Tier 1: Rule-based sentiment
│   ├── local_llm.py            # Tier 2: Local LLM sentiment
│   ├── cloud_llm.py            # Tier 3: Cloud LLM sentiment
│   └── models.py               # Model management
├── context/
│   ├── __init__.py
│   ├── preserver.py            # Context preservation
│   ├── history.py              # Conversation history
│   ├── metadata.py             # Metadata collector
│   ├── entity_extractor.py     # Entity extraction
│   ├── summarizer.py           # Conversation summarization
│   └── adapters/
│       ├── __init__.py
│       ├── base.py             # Base adapter interface
│       ├── zendesk.py          # Zendesk adapter
│       ├── intercom.py         # Intercom adapter
│       └── json.py             # Generic JSON adapter
├── routing/
│   ├── __init__.py
│   ├── router.py               # Smart routing logic
│   ├── availability.py         # Agent availability checker
│   ├── distributor.py          # Round-robin distribution
│   └── fallback.py             # Ticket creation fallback
├── integrations/
│   ├── __init__.py
│   ├── base.py                 # Base integration interface
│   ├── zendesk/
│   │   ├── __init__.py
│   │   ├── client.py           # Zendesk API client
│   │   └── mapper.py           # Data mapping
│   └── intercom/
│       ├── __init__.py
│       ├── client.py           # Intercom API client
│       └── mapper.py           # Data mapping
├── utils/
│   ├── __init__.py
│   ├── logging.py              # Structured logging
│   └── validation.py           # Input validation
└── api/                        # Optional REST API
    ├── __init__.py
    ├── app.py                  # FastAPI application
    ├── routes/
    │   ├── check.py            # POST /api/v1/check
    │   ├── handoff.py          # POST /api/v1/handoff
    │   └── status.py           # GET /api/v1/handoff/{id}
    ├── models.py               # Request/response models
    ├── auth.py                 # API key authentication
    └── websocket.py            # WebSocket handler
```

[Source: _bmad-output/architecture.md#3.1-Package-Structure]

### Technology Stack Requirements

| Component | Technology | Version | Notes |
|-----------|-----------|---------|-------|
| Language | Python | 3.9+ | Target audience is Python AI/ML developers |
| Data Validation | Pydantic | 2.5+ | Type safety, automatic validation |
| HTTP Client | httpx | 0.26+ | Async support (for later stories) |
| Testing | pytest | 7.4+ | Industry standard |

[Source: _bmad-output/architecture.md#2.1-Core-SDK]

### pyproject.toml Structure

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "handoffkit"
version = "0.1.0"
description = "AI-to-human handoff orchestration for conversational AI"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.9"
authors = [
    {name = "HandoffKit Team", email = "team@handoffkit.io"}
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Libraries :: Python Modules",
]
dependencies = [
    "pydantic>=2.5.0",
    "httpx>=0.26.0",
]

[project.optional-dependencies]
ml = [
    "transformers>=4.36.0",
    "torch>=2.1.0",
]
dashboard = [
    "fastapi>=0.109.0",
    "uvicorn>=0.27.0",
    "sqlalchemy>=2.0.25",
    "alembic>=1.13.0",
    "python-jose>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "mypy>=1.5.0",
]

[project.urls]
Homepage = "https://github.com/handoffkit/handoffkit"
Documentation = "https://handoffkit.io/docs"
Repository = "https://github.com/handoffkit/handoffkit"

[tool.setuptools.packages.find]
where = ["."]
include = ["handoffkit*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.black]
line-length = 88
target-version = ["py39", "py310", "py311", "py312"]

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
```

[Source: _bmad-output/architecture.md#2.1-Core-SDK]

### Public API Surface

The `handoffkit/__init__.py` MUST export:

```python
from handoffkit.core.orchestrator import HandoffOrchestrator
from handoffkit.core.config import HandoffConfig
from handoffkit.core.types import Message, MessageSpeaker, HandoffResult

__all__ = [
    "HandoffOrchestrator",
    "HandoffConfig",
    "Message",
    "MessageSpeaker",
    "HandoffResult",
]

__version__ = "0.1.0"
```

[Source: _bmad-output/architecture.md#3.4-Public-API-Surface]

### HandoffOrchestrator Stub

For this story, create a minimal stub that can be imported:

```python
# handoffkit/core/orchestrator.py
from typing import List, Optional, Tuple, Dict, Any

class HandoffOrchestrator:
    """
    Main interface for handoff logic.

    Usage:
        orchestrator = HandoffOrchestrator(
            helpdesk="zendesk",
            triggers=[...],
            config={...}
        )

        if orchestrator.should_handoff(conversation, message):
            handoff = orchestrator.create_handoff(...)
    """

    def __init__(
        self,
        helpdesk: str = "json",
        triggers: Optional[List[Any]] = None,
        config: Optional[Any] = None
    ):
        self.helpdesk = helpdesk
        self.triggers = triggers or []
        self.config = config

    def should_handoff(
        self,
        conversation: List[Any],
        current_message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[Any]]:
        """
        Evaluate if handoff is needed.

        Returns:
            (should_handoff: bool, trigger_result: Optional[TriggerResult])
        """
        # Stub implementation - returns False by default
        return (False, None)

    def create_handoff(
        self,
        conversation: List[Any],
        metadata: Dict[str, Any],
        priority: Optional[str] = None
    ) -> Any:
        """
        Create handoff with preserved context.

        Returns:
            HandoffResult with status, agent, ticket URL
        """
        # Stub implementation
        raise NotImplementedError("Handoff creation not yet implemented")
```

[Source: _bmad-output/architecture.md#3.2-Core-Classes-and-Interfaces]

### Project Structure Notes

- All subpackages should have `__init__.py` files (can be empty for stubs)
- Files that are stubs should have minimal class/function definitions
- Use type hints throughout for IDE support
- Follow PEP 8 style guidelines

### Testing Requirements

Create a basic test to verify the package structure:

```python
# tests/test_package.py
import pytest

def test_import_handoffkit():
    """Test that handoffkit package can be imported."""
    import handoffkit
    assert hasattr(handoffkit, '__version__')
    assert handoffkit.__version__ == "0.1.0"

def test_import_orchestrator():
    """Test that HandoffOrchestrator can be imported."""
    from handoffkit import HandoffOrchestrator
    assert HandoffOrchestrator is not None

def test_orchestrator_instantiation():
    """Test that HandoffOrchestrator can be instantiated."""
    from handoffkit import HandoffOrchestrator
    orchestrator = HandoffOrchestrator(helpdesk="zendesk")
    assert orchestrator.helpdesk == "zendesk"

def test_orchestrator_should_handoff_default():
    """Test that should_handoff returns (False, None) by default."""
    from handoffkit import HandoffOrchestrator
    orchestrator = HandoffOrchestrator()
    result = orchestrator.should_handoff([], "Hello")
    assert result == (False, None)

def test_package_exports():
    """Test that all expected exports are available."""
    from handoffkit import (
        HandoffOrchestrator,
        HandoffConfig,
        Message,
        MessageSpeaker,
        HandoffResult,
    )
    # All imports should succeed
```

### References

- Architecture specification: [Source: _bmad-output/architecture.md]
- Package structure: [Source: _bmad-output/architecture.md#3.1-Package-Structure]
- Technology stack: [Source: _bmad-output/architecture.md#2.1-Core-SDK]
- Public API: [Source: _bmad-output/architecture.md#3.4-Public-API-Surface]
- Core classes: [Source: _bmad-output/architecture.md#3.2-Core-Classes-and-Interfaces]
- NFR-4.1: Single pip install, zero config: [Source: _bmad-output/project-planning-artifacts/epics.md#NFR-4]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

