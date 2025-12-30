# HandoffKit

AI-to-human handoff orchestration for conversational AI.

## Installation

```bash
# Lightweight (rule-based only)
pip install handoffkit

# With local LLM support
pip install handoffkit[ml]

# Full (with dashboard + local LLM)
pip install handoffkit[ml,dashboard]

# For development
pip install handoffkit[dev]
```

## Quick Start

```python
from handoffkit import HandoffOrchestrator, Message, MessageSpeaker

# Create a conversation
messages = [
    Message(speaker=MessageSpeaker.USER, content="I need help with my order"),
    Message(speaker="ai", content="I'd be happy to help! What's the issue?"),
    Message(speaker="user", content="I want to talk to a human"),
]

# Create orchestrator with default settings
orchestrator = HandoffOrchestrator(helpdesk="zendesk")

# Check if handoff is needed
should_handoff, trigger_result = orchestrator.should_handoff(
    messages,
    current_message="I want to talk to a human"
)

if should_handoff:
    # Create handoff with preserved context
    result = orchestrator.create_handoff(
        messages,
        metadata={"user_id": "123", "channel": "web"}
    )
```

## Core Types

### Message

Messages use the `MessageSpeaker` enum for type-safe speaker identification:

```python
from handoffkit import Message, MessageSpeaker

# Using enum (recommended)
msg = Message(speaker=MessageSpeaker.USER, content="Hello!")

# Using string (also supported)
msg = Message(speaker="user", content="Hello!")
msg = Message(speaker="ai", content="Hi there!")
msg = Message(speaker="assistant", content="How can I help?")  # Alias for 'ai'
```

### Configuration

All configuration is immutable and validated with Pydantic:

```python
from handoffkit import HandoffConfig, TriggerConfig

# Create with defaults
config = HandoffConfig()
print(config.triggers.failure_threshold)  # 3
print(config.triggers.sentiment_threshold)  # 0.3

# Create with custom settings
config = HandoffConfig(
    triggers=TriggerConfig(
        failure_threshold=2,       # 1-5 consecutive failures
        sentiment_threshold=0.4,   # 0.0-1.0 (lower = more negative)
        critical_keywords=["fraud", "emergency"],
    ),
    max_context_messages=50,
)

# Configs are immutable - use model_copy to create modified versions
new_config = config.model_copy(
    update={"triggers": TriggerConfig(failure_threshold=5)}
)
```

### Configuration from Environment Variables

Load configuration from environment variables and YAML files:

```python
from handoffkit import HandoffOrchestrator, load_config

# Load from environment variables and config files
config = load_config()
orchestrator = HandoffOrchestrator(helpdesk="zendesk", config=config)

# Or use factory methods:
orchestrator = HandoffOrchestrator.from_env()  # From env vars + files
orchestrator = HandoffOrchestrator.from_file("config.yaml")  # From specific file
```

**Supported Environment Variables:**

| Variable | Description | Type | Example |
|----------|-------------|------|---------|
| `HANDOFFKIT_FAILURE_THRESHOLD` | Consecutive failures before handoff | int | `3` |
| `HANDOFFKIT_SENTIMENT_THRESHOLD` | Sentiment score threshold | float | `0.3` |
| `HANDOFFKIT_CRITICAL_KEYWORDS` | Comma-separated keywords | list | `fraud,emergency` |
| `HANDOFFKIT_HELPDESK` | Helpdesk provider | str | `zendesk` |
| `HANDOFFKIT_API_KEY` | Integration API key | str | `key123` |
| `HANDOFFKIT_API_URL` | Integration API URL | str | `https://api.example.com` |
| `HANDOFFKIT_MAX_CONTEXT_MESSAGES` | Max messages in context | int | `100` |
| `HANDOFFKIT_ROUTING_STRATEGY` | Routing strategy | str | `round_robin` |
| `HANDOFFKIT_CONFIG_FILE` | Path to config file | str | `/path/to/config.yaml` |

**YAML Configuration File:**

Create `handoffkit.yaml` in your working directory:

```yaml
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

max_context_messages: 100
```

**Configuration Precedence** (highest to lowest):
1. Explicit config passed to `HandoffOrchestrator`
2. Environment variables (`HANDOFFKIT_*`)
3. Config file (`handoffkit.yaml` or `handoffkit.yml`)
4. Default values

## Features

- **Framework-Agnostic**: Works with any conversational AI system (LangChain, LlamaIndex, custom)
- **3-Tier Detection**: Rule-based + Local LLM + Optional Cloud LLM
- **Type Safety**: Full Pydantic validation with IDE autocompletion
- **Immutable Config**: All configuration is frozen after creation
- **Flexible Configuration**: Environment variables, YAML files, or programmatic
- **Context Preservation**: Maintains conversation history during handoff
- **Multiple Integrations**: Zendesk, Intercom, and more
- **Optional Dashboard**: Real-time monitoring and analytics

## License

MIT
