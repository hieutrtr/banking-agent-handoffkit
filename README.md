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
from handoffkit import HandoffOrchestrator

# Create orchestrator with default settings
orchestrator = HandoffOrchestrator(helpdesk="zendesk")

# Check if handoff is needed
conversation = [...]  # Your conversation history
should_handoff, trigger_result = orchestrator.should_handoff(
    conversation,
    current_message="I want to talk to a human"
)

if should_handoff:
    # Create handoff with preserved context
    result = orchestrator.create_handoff(
        conversation,
        metadata={"user_id": "123", "channel": "web"}
    )
```

## Features

- **Framework-Agnostic**: Works with any conversational AI system (LangChain, LlamaIndex, custom)
- **3-Tier Detection**: Rule-based + Local LLM + Optional Cloud LLM
- **Context Preservation**: Maintains conversation history during handoff
- **Multiple Integrations**: Zendesk, Intercom, and more
- **Optional Dashboard**: Real-time monitoring and analytics

## License

MIT
