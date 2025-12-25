---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
inputDocuments:
  - /home/hieutt50/projects/handoffkit/_bmad-output/prd.md
workflowType: 'architecture'
project_name: 'handoffkit'
user_name: 'Hieu TRAN'
date: '2025-12-25'
lastStep: 10
---

# Architecture Decision Document - HandoffKit

**Project:** HandoffKit
**Author:** Hieu TRAN
**Date:** 2025-12-25
**Version:** 1.0
**Status:** Ready for Implementation

---

## Executive Summary

This architecture document defines the system design for HandoffKit, an open-source Python SDK and web dashboard for AI-to-human handoffs in conversational AI systems. The architecture follows a **dual-package design pattern** with a core SDK library and optional dashboard, emphasizing framework-agnosticism, developer experience, and production readiness.

### Key Architectural Principles

1. **Framework-Agnostic Core** - SDK works with any conversational AI system
2. **Modular Design** - Independent components (triggers, sentiment, context, routing)
3. **Optional Dashboard** - SDK works standalone, dashboard adds visibility
4. **Developer-First** - Simple API, zero-config defaults, excellent DX
5. **Production-Ready** - Performance, security, reliability built-in

---

## 1. System Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────┐
│   User's Chatbot Application        │
│   (LangChain/LlamaIndex/Custom)     │
└──────────────┬──────────────────────┘
               │ import handoffkit
┌──────────────▼──────────────────────┐
│       HandoffKit Core SDK            │
│  ┌────────┐ ┌─────────┐ ┌────────┐ │
│  │Triggers│ │Sentiment│ │Context │ │
│  └────────┘ └─────────┘ └────────┘ │
│  ┌────────┐ ┌──────────────────┐   │
│  │Routing │ │Integrations      │   │
│  └────────┘ │(Zendesk/Intercom)│   │
│  └──────────┴──────────────────┘   │
│  ┌──────────────────────────────┐  │
│  │   FastAPI REST API (Optional)│  │
│  └──────────────────────────────┘  │
└──────────────┬──────────────────────┘
               │ Optional: Dashboard
┌──────────────▼──────────────────────┐
│    HandoffKit Dashboard (Optional)   │
│  ┌──────────┐      ┌──────────────┐ │
│  │FastAPI   │◄────►│SvelteKit UI  │ │
│  │Backend   │      │Live Feed     │ │
│  │WebSocket │      │Charts/Config │ │
│  └──────────┘      └──────────────┘ │
└──────────────┬──────────────────────┘
               │ Handoff Event
┌──────────────▼──────────────────────┐
│  Helpdesk Systems                    │
│  (Zendesk/Intercom/Salesforce)      │
└──────────────────────────────────────┘
```

### 1.2 Architectural Style

**Modular Monolith with Optional Services**

- **Core SDK:** Modular library architecture
- **REST API:** Optional service layer
- **Dashboard:** Optional web application
- **Integrations:** Plugin-based adapters

**Why This Style:**
- SDK can be used standalone (no infrastructure required)
- Optional components add capabilities without forcing adoption
- Clear separation of concerns
- Easy to test and maintain

---

## 2. Technology Stack Decisions

### 2.1 Core SDK

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| **Language** | Python | 3.9+ | Target audience is Python AI/ML developers, rich ecosystem |
| **Async Support** | asyncio | Built-in | Non-blocking operations, better performance |
| **Data Validation** | Pydantic | 2.5+ | Type safety, automatic validation, JSON serialization |
| **HTTP Client** | httpx | 0.26+ | Async support, modern API, well-maintained |
| **Testing** | pytest | 7.4+ | Industry standard, great async support |

**Constraints:**
- Pure Python (no compiled extensions) for maximum portability
- Minimal dependencies for lightweight installation
- No ML libraries in core (keeps pip install fast)

### 2.2 REST API (Optional)

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| **Web Framework** | FastAPI | 0.109+ | Async native, auto OpenAPI docs, high performance |
| **ASGI Server** | Uvicorn | 0.27+ | Production-ready, great async performance |
| **WebSocket** | FastAPI WebSocket | Built-in | Real-time dashboard updates |
| **Database ORM** | SQLAlchemy | 2.0+ | Async support, production-proven |
| **Migrations** | Alembic | 1.13+ | Standard SQLAlchemy migration tool |

**Why FastAPI:**
- Automatic OpenAPI documentation (critical for developer tool)
- Native async/await (non-blocking operations)
- High performance (comparable to Node.js)
- Built-in Pydantic validation
- WebSocket support built-in

### 2.3 Dashboard (Optional)

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| **Frontend Framework** | SvelteKit | 2.0+ | Fast development, smaller bundles, great DX |
| **UI Library** | Svelte | 4.2+ | Reactive, no virtual DOM overhead |
| **CSS Framework** | Tailwind CSS | 3.4+ | Utility-first, great for rapid development |
| **Component Library** | shadcn-svelte | 0.8+ | High-quality accessible components |
| **Charts** | Recharts | 2.10+ | React-based but works with Svelte, good charts |
| **WebSocket Client** | socket.io-client | 4.6+ | Reliable real-time connection |

**Why SvelteKit:**
- Faster development than React (less boilerplate)
- Smaller bundle sizes (better performance)
- Built-in SSR and routing
- Excellent for dashboards (reactive updates)
- Great developer experience

### 2.4 Database

| Environment | Database | Rationale |
|------------|----------|-----------|
| **Development/MVP** | SQLite | Zero configuration, file-based, perfect for getting started |
| **Production** | PostgreSQL | Production-grade, scales well, full SQL features |

**Migration Strategy:**
- SQLAlchemy ORM abstracts database differences
- Alembic migrations work with both
- Documented migration path from SQLite to PostgreSQL
- Schema designed for PostgreSQL features (JSONB, indexes)

### 2.5 Deployment

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Containerization** | Docker | Standard deployment, multi-platform support |
| **Orchestration** | Docker Compose | Simple multi-container setup for MVP |
| **CI/CD** | GitHub Actions | Free for open source, great ecosystem |
| **Package Registry** | PyPI | Python standard, global CDN |
| **Container Registry** | Docker Hub | Free for public images, well-known |

---

## 3. Core SDK Architecture

### 3.1 Package Structure

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
│   ├── analyzer.py             # Hybrid sentiment analyzer
│   ├── keyword_scorer.py       # Keyword-based scoring
│   ├── formatter_detector.py   # Caps/punctuation detection
│   └── domain_amplifier.py     # Domain-specific amplification
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

### 3.2 Core Classes and Interfaces

#### HandoffOrchestrator (Primary Interface)

```python
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
        helpdesk: str,
        triggers: List[BaseTrigger],
        config: Optional[HandoffConfig] = None
    ):
        self.triggers = TriggerFactory.create_triggers(triggers)
        self.sentiment_analyzer = SentimentAnalyzer(config)
        self.context_preserver = ContextPreserver(config)
        self.router = SmartRouter(config)
        self.integration = IntegrationFactory.create(helpdesk, config)

    def should_handoff(
        self,
        conversation: List[Message],
        current_message: str,
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, Optional[TriggerResult]]:
        """
        Evaluate if handoff is needed.

        Returns:
            (should_handoff: bool, trigger_result: Optional[TriggerResult])
        """

    def create_handoff(
        self,
        conversation: List[Message],
        metadata: Dict,
        priority: Optional[str] = None
    ) -> HandoffResult:
        """
        Create handoff with preserved context.

        Returns:
            HandoffResult with status, agent, ticket URL
        """
```

#### BaseTrigger (Abstract Interface)

```python
from abc import ABC, abstractmethod

class BaseTrigger(ABC):
    """Base class for all trigger types."""

    @abstractmethod
    def evaluate(
        self,
        conversation: List[Message],
        current_message: str,
        context: Dict
    ) -> TriggerResult:
        """
        Evaluate if this trigger should fire.

        Returns:
            TriggerResult(triggered: bool, confidence: float, reason: str)
        """
        pass

    @abstractmethod
    def get_priority(self) -> TriggerPriority:
        """Return trigger priority (immediate, high, normal)."""
        pass
```

#### ContextAdapter (Integration Interface)

```python
from abc import ABC, abstractmethod

class ContextAdapter(ABC):
    """Base adapter for helpdesk integrations."""

    @abstractmethod
    def format_context(
        self,
        conversation: List[Message],
        metadata: Dict,
        summary: str
    ) -> Dict:
        """Format context for specific helpdesk API."""
        pass

    @abstractmethod
    def create_ticket(
        self,
        context: Dict,
        priority: str
    ) -> TicketResult:
        """Create ticket/conversation in helpdesk system."""
        pass

    @abstractmethod
    def assign_to_agent(
        self,
        ticket_id: str,
        agent_id: str
    ) -> bool:
        """Assign ticket to specific agent."""
        pass
```

### 3.3 Data Models (Pydantic)

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class MessageSpeaker(str, Enum):
    USER = "user"
    AI = "ai"

class Message(BaseModel):
    """Single conversation message."""
    speaker: MessageSpeaker
    message: str
    timestamp: datetime
    confidence: Optional[float] = None
    metadata: Optional[Dict] = None

class TriggerPriority(str, Enum):
    IMMEDIATE = "immediate"
    HIGH = "high"
    NORMAL = "normal"

class TriggerResult(BaseModel):
    """Result of trigger evaluation."""
    triggered: bool
    trigger_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    priority: TriggerPriority

class HandoffConfig(BaseModel):
    """Configuration for handoff orchestrator."""
    failure_threshold: int = Field(default=3, ge=1, le=5)
    sentiment_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    critical_keywords: List[str] = []
    enable_test_mode: bool = False
    helpdesk_config: Optional[Dict] = None

class HandoffResult(BaseModel):
    """Result of handoff creation."""
    handoff_id: str
    status: str  # "assigned", "pending", "failed"
    agent: Optional[Dict] = None
    ticket_url: Optional[str] = None
    created_at: datetime
    error: Optional[str] = None
```

### 3.4 Public API Surface

```python
# handoffkit/__init__.py
from handoffkit.core.orchestrator import HandoffOrchestrator
from handoffkit.core.config import HandoffConfig
from handoffkit.core.types import Message, MessageSpeaker, HandoffResult
from handoffkit.triggers import Triggers

__all__ = [
    "HandoffOrchestrator",
    "HandoffConfig",
    "Message",
    "MessageSpeaker",
    "HandoffResult",
    "Triggers",
]

class Triggers:
    """Factory class for creating triggers with simple API."""

    @staticmethod
    def direct_request():
        """Detect explicit requests for human agent."""
        from handoffkit.triggers.direct_request import DirectRequestTrigger
        return DirectRequestTrigger()

    @staticmethod
    def failed_attempts(threshold: int = 3):
        """Track consecutive failed AI responses."""
        from handoffkit.triggers.failure_tracking import FailureTrackingTrigger
        return FailureTrackingTrigger(threshold=threshold)

    @staticmethod
    def negative_sentiment(threshold: float = 0.3):
        """Detect user frustration via sentiment."""
        from handoffkit.triggers.sentiment import SentimentTrigger
        return SentimentTrigger(threshold=threshold)

    @staticmethod
    def keywords(keywords: List[str]):
        """Monitor critical keywords."""
        from handoffkit.triggers.keyword import KeywordTrigger
        return KeywordTrigger(keywords=keywords)
```

---

## 4. REST API Architecture

### 4.1 API Design

**Base URL:** `http://localhost:8000/api/v1`

**Authentication:** API Key via `Authorization: Bearer {key}` header

**Endpoints:**

| Method | Endpoint | Purpose | Request | Response |
|--------|----------|---------|---------|----------|
| POST | `/check` | Check if handoff needed | CheckRequest | CheckResponse |
| POST | `/handoff` | Create handoff | HandoffRequest | HandoffResponse |
| GET | `/handoff/{id}` | Get handoff status | - | HandoffStatusResponse |
| GET | `/health` | Health check | - | HealthResponse |
| GET | `/docs` | Swagger UI | - | HTML |
| GET | `/openapi.json` | OpenAPI spec | - | JSON |

### 4.2 Request/Response Schemas

```python
# Pydantic models for API
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class CheckRequest(BaseModel):
    """POST /api/v1/check"""
    conversation: List[Message]
    current_message: str
    metadata: Optional[Dict] = None

class CheckResponse(BaseModel):
    """Response for /check endpoint."""
    should_handoff: bool
    trigger_reason: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    suggested_priority: Optional[str] = None

class HandoffRequest(BaseModel):
    """POST /api/v1/handoff"""
    conversation: List[Message]
    metadata: Dict = Field(..., description="Required: user_id, channel")
    helpdesk: str = Field(..., description="zendesk|intercom")
    priority: Optional[str] = "normal"

class HandoffResponse(BaseModel):
    """Response for /handoff endpoint."""
    handoff_id: str
    status: str
    agent: Optional[Dict] = None
    ticket_url: Optional[str] = None
    created_at: datetime

class HandoffStatusResponse(BaseModel):
    """Response for /handoff/{id} endpoint."""
    handoff_id: str
    status: str
    agent: Optional[Dict] = None
    created_at: datetime
    updated_at: datetime
    events: List[Dict] = []
```

### 4.3 FastAPI Application Structure

```python
# handoffkit/api/app.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI(
    title="HandoffKit API",
    description="AI-to-human handoff orchestration API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware for dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # SvelteKit dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API key authentication
security = HTTPBearer()

async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Verify API key from Authorization header."""
    # Check against database of valid API keys
    # Return user_id if valid, raise HTTPException if invalid
    pass

# Include routers
from handoffkit.api.routes import check, handoff, status
app.include_router(check.router, prefix="/api/v1", tags=["check"])
app.include_router(handoff.router, prefix="/api/v1", tags=["handoff"])
app.include_router(status.router, prefix="/api/v1", tags=["status"])

# WebSocket endpoint for dashboard
from handoffkit.api.websocket import websocket_endpoint
app.add_websocket_route("/ws", websocket_endpoint)

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}
```

### 4.4 Rate Limiting Strategy

**Implementation:** Token bucket algorithm with Redis (optional) or in-memory

**Limits:**
- 100 requests per minute per API key
- Burst allowance: 10 requests
- 429 Too Many Requests response when exceeded

```python
from functools import wraps
from time import time

class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, max_requests: int = 100, window: int = 60):
        self.max_requests = max_requests
        self.window = window
        self.requests = {}  # {api_key: [(timestamp, count)]}

    def check_limit(self, api_key: str) -> bool:
        now = time()
        if api_key not in self.requests:
            self.requests[api_key] = []

        # Clean old requests outside window
        self.requests[api_key] = [
            (ts, count) for ts, count in self.requests[api_key]
            if now - ts < self.window
        ]

        # Count requests in window
        total = sum(count for _, count in self.requests[api_key])

        if total >= self.max_requests:
            return False

        self.requests[api_key].append((now, 1))
        return True
```

---

## 5. Database Architecture

### 5.1 Schema Design

**Tables:**

#### handoffs

```sql
CREATE TABLE handoffs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    conversation JSONB NOT NULL,  -- Full conversation history
    metadata JSONB NOT NULL,       -- Channel, session, etc.
    trigger_type VARCHAR(50) NOT NULL,
    trigger_reason TEXT,
    confidence FLOAT,
    priority VARCHAR(20) DEFAULT 'normal',
    status VARCHAR(20) DEFAULT 'pending',  -- pending, assigned, resolved, failed
    agent_id VARCHAR(255),
    agent_name VARCHAR(255),
    ticket_id VARCHAR(255),
    ticket_url TEXT,
    helpdesk VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_trigger_type (trigger_type)
);
```

#### handoff_events

```sql
CREATE TABLE handoff_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    handoff_id UUID NOT NULL REFERENCES handoffs(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,  -- created, assigned, updated, resolved
    event_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_handoff_id (handoff_id),
    INDEX idx_created_at (created_at)
);
```

#### api_keys

```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash VARCHAR(255) UNIQUE NOT NULL,  -- bcrypt hash
    name VARCHAR(255) NOT NULL,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_key_hash (key_hash)
);
```

#### dashboard_users

```sql
CREATE TABLE dashboard_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- bcrypt hash
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

### 5.2 SQLAlchemy Models

```python
from sqlalchemy import Column, String, Text, Float, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class Handoff(Base):
    __tablename__ = "handoffs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    conversation = Column(JSON, nullable=False)
    metadata = Column(JSON, nullable=False)
    trigger_type = Column(String(50), nullable=False, index=True)
    trigger_reason = Column(Text)
    confidence = Column(Float)
    priority = Column(String(20), default="normal")
    status = Column(String(20), default="pending", index=True)
    agent_id = Column(String(255))
    agent_name = Column(String(255))
    ticket_id = Column(String(255))
    ticket_url = Column(Text)
    helpdesk = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime)

class HandoffEvent(Base):
    __tablename__ = "handoff_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    handoff_id = Column(UUID(as_uuid=True), ForeignKey("handoffs.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    event_data = Column(JSON)
    created_at = Column(DateTime, default=func.now(), index=True)
```

### 5.3 Migration Strategy

**SQLite → PostgreSQL:**

1. Export data from SQLite using `sqlite3` CLI or Python
2. Transform JSON fields if needed
3. Import into PostgreSQL using `psql` COPY or Python script
4. Update connection string in config
5. Run Alembic migrations to ensure schema matches

**Alembic Setup:**

```python
# alembic/env.py
from handoffkit.api.database import Base
from handoffkit.api.models import *  # Import all models

target_metadata = Base.metadata
```

```bash
# Generate migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head
```

---

## 6. Dashboard Architecture

### 6.1 SvelteKit Application Structure

```
dashboard/
├── src/
│   ├── lib/
│   │   ├── components/
│   │   │   ├── LiveFeed.svelte       # Real-time handoff feed
│   │   │   ├── TriggerChart.svelte   # Pie chart visualization
│   │   │   ├── ConfigPanel.svelte    # Settings management
│   │   │   ├── HandoffDetail.svelte  # Detail modal
│   │   │   └── FilterBar.svelte      # Filter controls
│   │   ├── stores/
│   │   │   ├── handoffs.ts           # Handoff data store
│   │   │   ├── websocket.ts          # WebSocket connection
│   │   │   └── config.ts             # Configuration store
│   │   └── api/
│   │       ├── client.ts             # API client
│   │       └── websocket.ts          # WebSocket manager
│   ├── routes/
│   │   ├── +page.svelte              # Dashboard home
│   │   ├── +layout.svelte            # App layout
│   │   ├── login/
│   │   │   └── +page.svelte          # Login page
│   │   └── settings/
│   │       └── +page.svelte          # Settings page
│   └── app.html                      # HTML template
├── static/
│   └── favicon.png
├── svelte.config.js
├── vite.config.ts
├── package.json
└── tsconfig.json
```

### 6.2 WebSocket Architecture

**Connection Management:**

```typescript
// src/lib/api/websocket.ts
import { io, Socket } from 'socket.io-client';
import { writable } from 'svelte/store';

class WebSocketManager {
    private socket: Socket | null = null;
    public connected = writable(false);
    public handoffs = writable<Handoff[]>([]);

    connect(apiKey: string) {
        this.socket = io('ws://localhost:8000', {
            auth: { token: apiKey },
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            reconnectionAttempts: Infinity
        });

        this.socket.on('connect', () => {
            console.log('WebSocket connected');
            this.connected.set(true);
        });

        this.socket.on('disconnect', () => {
            console.log('WebSocket disconnected');
            this.connected.set(false);
        });

        this.socket.on('handoff', (handoff: Handoff) => {
            this.handoffs.update(h => [handoff, ...h]);
        });

        this.socket.on('handoff_update', (update: HandoffUpdate) => {
            this.handoffs.update(handoffs =>
                handoffs.map(h =>
                    h.id === update.handoff_id
                        ? { ...h, ...update }
                        : h
                )
            );
        });
    }

    disconnect() {
        this.socket?.disconnect();
        this.socket = null;
        this.connected.set(false);
    }
}

export const wsManager = new WebSocketManager();
```

**Backend WebSocket Handler:**

```python
# handoffkit/api/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Set
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                # Connection closed, will be removed on disconnect
                pass

manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send heartbeat every 30 seconds
        while True:
            data = await websocket.receive_text()
            # Handle client messages (ping/pong, etc.)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Broadcast handoff events
async def broadcast_handoff_event(handoff: Handoff):
    await manager.broadcast({
        "type": "handoff",
        "data": handoff.dict()
    })
```

### 6.3 State Management

**Svelte Stores for Global State:**

```typescript
// src/lib/stores/handoffs.ts
import { writable, derived } from 'svelte/store';

export interface Handoff {
    id: string;
    trigger_type: string;
    status: string;
    created_at: string;
    // ... other fields
}

// Raw handoffs data
export const handoffs = writable<Handoff[]>([]);

// Filters
export const filters = writable({
    triggerType: 'all',
    channel: 'all',
    timeRange: 'today',
    status: 'all'
});

// Filtered handoffs (derived store)
export const filteredHandoffs = derived(
    [handoffs, filters],
    ([$handoffs, $filters]) => {
        return $handoffs.filter(h => {
            if ($filters.triggerType !== 'all' && h.trigger_type !== $filters.triggerType) {
                return false;
            }
            if ($filters.status !== 'all' && h.status !== $filters.status) {
                return false;
            }
            // ... other filter logic
            return true;
        });
    }
);

// Trigger breakdown (derived store)
export const triggerBreakdown = derived(
    filteredHandoffs,
    ($filteredHandoffs) => {
        const counts = {};
        $filteredHandoffs.forEach(h => {
            counts[h.trigger_type] = (counts[h.trigger_type] || 0) + 1;
        });

        const total = $filteredHandoffs.length;
        return Object.entries(counts).map(([type, count]) => ({
            type,
            count,
            percentage: (count / total * 100).toFixed(1)
        }));
    }
);
```

---

## 7. Integration Architecture

### 7.1 Helpdesk Integration Pattern

**Adapter Pattern for Extensibility:**

```python
from abc import ABC, abstractmethod
from typing import Dict, Optional

class HelpdeskAdapter(ABC):
    """Base adapter for helpdesk integrations."""

    @abstractmethod
    async def check_agent_availability(self) -> List[Dict]:
        """Get list of available agents."""
        pass

    @abstractmethod
    async def create_ticket(
        self,
        conversation: List[Message],
        metadata: Dict,
        summary: str,
        priority: str
    ) -> Dict:
        """Create ticket with conversation context."""
        pass

    @abstractmethod
    async def assign_to_agent(
        self,
        ticket_id: str,
        agent_id: str
    ) -> bool:
        """Assign ticket to agent."""
        pass

    @abstractmethod
    async def add_comment(
        self,
        ticket_id: str,
        comment: str
    ) -> bool:
        """Add comment to ticket."""
        pass
```

### 7.2 Zendesk Integration

**API Wrapper:**

```python
import httpx
from typing import List, Dict

class ZendeskAdapter(HelpdeskAdapter):
    """Zendesk API integration."""

    def __init__(self, subdomain: str, email: str, api_token: str):
        self.base_url = f"https://{subdomain}.zendesk.com/api/v2"
        self.auth = (f"{email}/token", api_token)
        self.client = httpx.AsyncClient(auth=self.auth)

    async def check_agent_availability(self) -> List[Dict]:
        """Get online agents."""
        response = await self.client.get(
            f"{self.base_url}/users/search",
            params={"role": "agent", "query": "status:online"}
        )
        response.raise_for_status()
        return response.json()["users"]

    async def create_ticket(
        self,
        conversation: List[Message],
        metadata: Dict,
        summary: str,
        priority: str
    ) -> Dict:
        """Create Zendesk ticket."""
        # Format conversation as HTML for ticket description
        description = self._format_conversation_html(conversation)

        ticket_data = {
            "ticket": {
                "subject": f"Handoff: {summary[:100]}",
                "description": description,
                "priority": self._map_priority(priority),
                "tags": ["handoffkit", "ai-handoff"],
                "custom_fields": [
                    {"id": "metadata", "value": json.dumps(metadata)}
                ]
            }
        }

        response = await self.client.post(
            f"{self.base_url}/tickets",
            json=ticket_data
        )
        response.raise_for_status()
        return response.json()["ticket"]

    async def assign_to_agent(self, ticket_id: str, agent_id: str) -> bool:
        """Assign ticket to agent."""
        response = await self.client.put(
            f"{self.base_url}/tickets/{ticket_id}",
            json={"ticket": {"assignee_id": agent_id}}
        )
        return response.status_code == 200

    def _format_conversation_html(self, conversation: List[Message]) -> str:
        """Format conversation as HTML for Zendesk."""
        html = ["<h3>Conversation History</h3>"]
        for msg in conversation:
            speaker = "👤 User" if msg.speaker == "user" else "🤖 AI"
            html.append(f"<p><strong>{speaker}</strong> ({msg.timestamp}):<br/>{msg.message}</p>")
        return "\n".join(html)

    def _map_priority(self, priority: str) -> str:
        """Map our priority to Zendesk priority."""
        mapping = {
            "immediate": "urgent",
            "high": "high",
            "normal": "normal"
        }
        return mapping.get(priority, "normal")
```

### 7.3 Intercom Integration

```python
class IntercomAdapter(HelpdeskAdapter):
    """Intercom API integration."""

    def __init__(self, app_id: str, access_token: str):
        self.base_url = "https://api.intercom.io"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient(headers=self.headers)

    async def create_ticket(
        self,
        conversation: List[Message],
        metadata: Dict,
        summary: str,
        priority: str
    ) -> Dict:
        """Create Intercom conversation."""
        # Format conversation for Intercom
        body = self._format_conversation_markdown(conversation)

        conversation_data = {
            "from": {
                "type": "user",
                "id": metadata["user_id"]
            },
            "body": body,
            "priority": self._map_priority(priority)
        }

        response = await self.client.post(
            f"{self.base_url}/conversations",
            json=conversation_data
        )
        response.raise_for_status()
        return response.json()

    def _format_conversation_markdown(self, conversation: List[Message]) -> str:
        """Format conversation as markdown for Intercom."""
        lines = ["## Conversation History\n"]
        for msg in conversation:
            speaker = "**User**" if msg.speaker == "user" else "*AI*"
            lines.append(f"{speaker} ({msg.timestamp}): {msg.message}\n")
        return "\n".join(lines)
```

---

## 8. Security Architecture

### 8.1 Authentication & Authorization

**API Key Authentication:**

```python
import secrets
import hashlib
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class APIKeyManager:
    """Manage API keys."""

    @staticmethod
    def generate_key() -> str:
        """Generate secure API key."""
        return f"hk_{secrets.token_urlsafe(32)}"

    @staticmethod
    def hash_key(key: str) -> str:
        """Hash API key for storage."""
        return pwd_context.hash(key)

    @staticmethod
    def verify_key(key: str, hashed: str) -> bool:
        """Verify API key against hash."""
        return pwd_context.verify(key, hashed)

# Usage in API endpoint
async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    key = credentials.credentials
    # Look up key hash in database
    api_key = await db.query(APIKey).filter_by(key_hash=hash_key(key)).first()
    if not api_key or not api_key.is_active:
        raise HTTPException(status_code=401, detail="Invalid API key")
    # Update last_used_at
    api_key.last_used_at = datetime.utcnow()
    await db.commit()
    return api_key
```

**Dashboard Authentication:**

```python
from jose import JWTError, jwt
from datetime import datetime, timedelta

SECRET_KEY = os.getenv("SECRET_KEY")  # Load from environment
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

def create_access_token(data: dict) -> str:
    """Create JWT token for dashboard session."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    """Verify JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### 8.2 Data Protection

**Encryption at Rest:**

```python
from cryptography.fernet import Fernet

class DataEncryptor:
    """Encrypt sensitive data at rest."""

    def __init__(self, key: bytes):
        self.fernet = Fernet(key)

    def encrypt(self, data: str) -> str:
        """Encrypt string data."""
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, encrypted: str) -> str:
        """Decrypt string data."""
        return self.fernet.decrypt(encrypted.encode()).decode()

# Store helpdesk credentials encrypted
encryptor = DataEncryptor(os.getenv("ENCRYPTION_KEY").encode())

def store_helpdesk_config(config: Dict) -> Dict:
    """Encrypt sensitive fields before storage."""
    config_copy = config.copy()
    config_copy["api_token"] = encryptor.encrypt(config["api_token"])
    return config_copy
```

**PII Masking:**

```python
import re

def mask_account_number(text: str) -> str:
    """Mask account numbers in text."""
    # Match account numbers (8-12 digits)
    return re.sub(r'\b\d{8,12}\b', lambda m: '*' * (len(m.group()) - 4) + m.group()[-4:], text)

def mask_email(text: str) -> str:
    """Mask email addresses."""
    return re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        lambda m: m.group()[0] + '***@' + m.group().split('@')[1],
        text
    )

def mask_phone(text: str) -> str:
    """Mask phone numbers."""
    return re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', 'XXX-XXX-####', text)
```

### 8.3 Input Validation

**Pydantic Validation:**

```python
from pydantic import BaseModel, Field, validator

class HandoffRequest(BaseModel):
    conversation: List[Message] = Field(..., max_items=100)
    metadata: Dict = Field(...)
    helpdesk: str = Field(..., regex="^(zendesk|intercom)$")
    priority: str = Field("normal", regex="^(immediate|high|normal)$")

    @validator('conversation')
    def validate_conversation(cls, v):
        if not v:
            raise ValueError("Conversation cannot be empty")
        if len(v) > 100:
            raise ValueError("Conversation too long (max 100 messages)")
        return v

    @validator('metadata')
    def validate_metadata(cls, v):
        if 'user_id' not in v:
            raise ValueError("metadata.user_id is required")
        if 'channel' not in v:
            raise ValueError("metadata.channel is required")
        return v
```

**SQL Injection Prevention:**

- Use SQLAlchemy ORM (parameterized queries)
- Never construct SQL with string concatenation
- Validate all inputs with Pydantic

**XSS Prevention:**

- Dashboard uses Svelte (auto-escapes by default)
- API returns JSON (not HTML)
- Set proper Content-Security-Policy headers

---

## 9. Performance & Scalability

### 9.1 Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Trigger Evaluation** | <100ms | 95th percentile, 10 concurrent |
| **Sentiment Analysis** | <50ms | 95th percentile |
| **API /check** | <200ms | 95th percentile, 50 req/s |
| **API /handoff** | <500ms | 95th percentile, 50 req/s |
| **WebSocket Latency** | <1 second | Event to dashboard display |
| **Dashboard Render** | <500ms | Initial page load |

### 9.2 Optimization Strategies

**Caching:**

```python
from functools import lru_cache
from datetime import datetime, timedelta

class CachedRouter:
    """Router with agent availability caching."""

    def __init__(self, adapter: HelpdeskAdapter, ttl_seconds: int = 30):
        self.adapter = adapter
        self.ttl_seconds = ttl_seconds
        self._cache = None
        self._cache_time = None

    async def get_available_agents(self) -> List[Dict]:
        """Get available agents with 30-second cache."""
        now = datetime.utcnow()

        if self._cache is None or \
           (now - self._cache_time).total_seconds() > self.ttl_seconds:
            self._cache = await self.adapter.check_agent_availability()
            self._cache_time = now

        return self._cache
```

**Database Indexing:**

```sql
-- High-priority indexes for common queries
CREATE INDEX idx_handoffs_created_at ON handoffs(created_at DESC);
CREATE INDEX idx_handoffs_status ON handoffs(status);
CREATE INDEX idx_handoffs_trigger_type ON handoffs(trigger_type);
CREATE INDEX idx_handoffs_user_id ON handoffs(user_id);

-- Composite index for filtered queries
CREATE INDEX idx_handoffs_status_created ON handoffs(status, created_at DESC);
```

**Async Operations:**

```python
import asyncio

async def create_handoff_with_context(
    conversation: List[Message],
    metadata: Dict
) -> HandoffResult:
    """Create handoff with parallel operations."""

    # Run sentiment analysis and entity extraction in parallel
    sentiment_task = asyncio.create_task(
        sentiment_analyzer.analyze(conversation)
    )
    entities_task = asyncio.create_task(
        entity_extractor.extract(conversation)
    )
    summary_task = asyncio.create_task(
        summarizer.summarize(conversation)
    )

    # Wait for all to complete
    sentiment, entities, summary = await asyncio.gather(
        sentiment_task,
        entities_task,
        summary_task
    )

    # Create context package
    context = {
        "conversation": conversation,
        "metadata": metadata,
        "sentiment": sentiment,
        "entities": entities,
        "summary": summary
    }

    # Send to helpdesk
    result = await helpdesk_adapter.create_ticket(context)
    return result
```

### 9.3 Scalability Architecture

**Horizontal Scaling:**

```
                    ┌──────────────┐
                    │ Load Balancer│
                    └───────┬──────┘
            ┌───────────────┼───────────────┐
            │               │               │
    ┌───────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
    │ API Instance │ │ API Instance│ │ API Instance│
    │   (Stateless)│ │  (Stateless)│ │  (Stateless)│
    └───────┬──────┘ └─────┬──────┘ └─────┬──────┘
            └───────────────┼───────────────┘
                    ┌───────▼──────┐
                    │  PostgreSQL  │
                    │  (Primary)   │
                    └──────────────┘
```

**Stateless API Design:**

- No session state in API instances
- All state in database or cache
- Any instance can handle any request
- Easy to add/remove instances

**Connection Pooling:**

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Create engine with connection pool
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,           # Max 20 connections per instance
    max_overflow=10,        # Allow 10 extra connections under load
    pool_pre_ping=True,     # Verify connections before use
    pool_recycle=3600       # Recycle connections after 1 hour
)

# Session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)
```

---

## 10. Deployment Architecture

### 10.1 Docker Compose Setup (Development/MVP)

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://handoffkit:password@db:5432/handoffkit
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
    volumes:
      - ./handoffkit:/app/handoffkit
    command: uvicorn handoffkit.api.app:app --host 0.0.0.0 --port 8000 --reload

  dashboard:
    build:
      context: ./dashboard
      dockerfile: Dockerfile
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://localhost:8000
    volumes:
      - ./dashboard/src:/app/src
    command: npm run dev -- --host

  db:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=handoffkit
      - POSTGRES_USER=handoffkit
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### 10.2 Production Deployment

**Container Images:**

```dockerfile
# Dockerfile.api
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY handoffkit/ ./handoffkit/

# Run as non-root user
RUN useradd -m -u 1000 handoffkit && chown -R handoffkit:handoffkit /app
USER handoffkit

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"

EXPOSE 8000

CMD ["uvicorn", "handoffkit.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

```dockerfile
# dashboard/Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:20-alpine

WORKDIR /app

COPY --from=builder /app/build ./build
COPY --from=builder /app/package.json ./

RUN npm ci --production

EXPOSE 3000

CMD ["node", "build"]
```

### 10.3 Environment Configuration

**.env File Structure:**

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname

# Security
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here

# Helpdesk Integrations
ZENDESK_SUBDOMAIN=your-subdomain
ZENDESK_EMAIL=your-email
ZENDESK_API_TOKEN=your-token

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Dashboard
DASHBOARD_URL=http://localhost:5173
```

---

## 11. Testing Strategy

### 11.1 Testing Pyramid

```
           ┌─────────────┐
          /  E2E Tests   /   10% - Full system integration
         /   (10%)      /
        /───────────────/
       /  Integration  /     30% - Component interactions
      /   Tests (30%) /
     /───────────────/
    /  Unit Tests   /       60% - Individual functions
   /    (60%)      /
  /───────────────/
```

### 11.2 Unit Testing

```python
# tests/test_triggers.py
import pytest
from handoffkit.triggers.direct_request import DirectRequestTrigger
from handoffkit.core.types import Message, MessageSpeaker
from datetime import datetime

@pytest.fixture
def direct_request_trigger():
    return DirectRequestTrigger()

def test_detect_direct_request(direct_request_trigger):
    """Test detection of explicit agent request."""
    message = "I want to talk to a human"
    result = direct_request_trigger.evaluate([], message, {})

    assert result.triggered is True
    assert result.confidence >= 0.8
    assert "direct request" in result.reason.lower()

def test_no_false_positive(direct_request_trigger):
    """Test that normal messages don't trigger."""
    message = "Can you help me with my account?"
    result = direct_request_trigger.evaluate([], message, {})

    assert result.triggered is False

@pytest.mark.asyncio
async def test_sentiment_analysis():
    """Test sentiment scoring."""
    from handoffkit.sentiment.analyzer import SentimentAnalyzer

    analyzer = SentimentAnalyzer()

    # Positive message
    score = await analyzer.analyze_message("This is great, thank you!")
    assert score > 0.5

    # Negative message
    score = await analyzer.analyze_message("This is terrible and frustrating")
    assert score < 0.3

    # All caps (frustration)
    score = await analyzer.analyze_message("I NEED HELP NOW!!!")
    assert score < 0.4
```

### 11.3 Integration Testing

```python
# tests/integration/test_handoff_flow.py
import pytest
from handoffkit import HandoffOrchestrator, Triggers
from handoffkit.core.types import Message, MessageSpeaker
from datetime import datetime

@pytest.fixture
def orchestrator():
    """Create orchestrator with mock helpdesk."""
    return HandoffOrchestrator(
        helpdesk="mock",
        triggers=[
            Triggers.direct_request(),
            Triggers.failed_attempts(threshold=2),
            Triggers.negative_sentiment(threshold=0.3)
        ]
    )

@pytest.mark.asyncio
async def test_full_handoff_flow(orchestrator):
    """Test complete handoff creation flow."""
    conversation = [
        Message(
            speaker=MessageSpeaker.USER,
            message="Help me with my account",
            timestamp=datetime.utcnow()
        ),
        Message(
            speaker=MessageSpeaker.AI,
            message="I can help you with that",
            timestamp=datetime.utcnow()
        ),
        Message(
            speaker=MessageSpeaker.USER,
            message="This isn't working, get me a person",
            timestamp=datetime.utcnow()
        )
    ]

    # Check if handoff needed
    should_handoff, trigger_result = await orchestrator.should_handoff(
        conversation,
        "This isn't working, get me a person",
        {"user_id": "test123"}
    )

    assert should_handoff is True
    assert trigger_result.trigger_type == "direct_request"

    # Create handoff
    result = await orchestrator.create_handoff(
        conversation,
        metadata={"user_id": "test123", "channel": "web"}
    )

    assert result.handoff_id is not None
    assert result.status in ["assigned", "pending"]
```

### 11.4 API Testing

```python
# tests/api/test_endpoints.py
import pytest
from httpx import AsyncClient
from handoffkit.api.app import app

@pytest.mark.asyncio
async def test_check_endpoint():
    """Test /api/v1/check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/check",
            json={
                "conversation": [
                    {
                        "speaker": "user",
                        "message": "I need a human",
                        "timestamp": "2025-12-25T10:00:00Z"
                    }
                ],
                "current_message": "I need a human",
                "metadata": {"user_id": "123"}
            },
            headers={"Authorization": "Bearer test_api_key"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "should_handoff" in data
        assert data["should_handoff"] is True
        assert data["trigger_reason"] is not None
```

### 11.5 E2E Testing

```python
# tests/e2e/test_dashboard.py
import pytest
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_dashboard_live_feed():
    """Test dashboard displays handoffs in real-time."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Navigate to dashboard
        await page.goto("http://localhost:5173")

        # Login
        await page.fill('input[name="username"]', "admin")
        await page.fill('input[name="password"]', "password")
        await page.click('button[type="submit"]')

        # Wait for dashboard to load
        await page.wait_for_selector('.handoff-feed')

        # Trigger handoff via API
        # ... create handoff ...

        # Verify handoff appears in feed within 1 second
        await page.wait_for_selector('.handoff-item', timeout=1000)

        await browser.close()
```

---

## 12. Monitoring & Observability

### 12.1 Logging Strategy

**Structured Logging:**

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for machine parsing."""

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add custom fields
        if hasattr(record, 'handoff_id'):
            log_data["handoff_id"] = record.handoff_id
        if hasattr(record, 'user_id'):
            log_data["user_id"] = record.user_id

        return json.dumps(log_data)

# Configure logging
logging.basicConfig(level=logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger("handoffkit")
logger.addHandler(handler)
```

**Key Metrics to Log:**

```python
# Handoff events
logger.info("Handoff created", extra={
    "handoff_id": handoff.id,
    "user_id": handoff.user_id,
    "trigger_type": handoff.trigger_type,
    "confidence": handoff.confidence
})

# Performance metrics
logger.info("Trigger evaluation completed", extra={
    "duration_ms": duration,
    "trigger_count": len(triggers)
})

# Errors
logger.error("Helpdesk API error", extra={
    "helpdesk": "zendesk",
    "status_code": response.status_code,
    "error": str(error)
})
```

### 12.2 Health Checks

```python
from fastapi import Response

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    checks = {
        "database": await check_database(),
        "redis": await check_redis() if USE_REDIS else "skipped",
        "zendesk": await check_zendesk() if ZENDESK_ENABLED else "skipped"
    }

    all_healthy = all(v == "healthy" for v in checks.values() if v != "skipped")
    status_code = 200 if all_healthy else 503

    return Response(
        content=json.dumps({"status": "healthy" if all_healthy else "unhealthy", "checks": checks}),
        status_code=status_code,
        media_type="application/json"
    )

async def check_database() -> str:
    """Check database connectivity."""
    try:
        await db.execute("SELECT 1")
        return "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return "unhealthy"
```

### 12.3 Metrics Collection

```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics
handoff_total = Counter('handoffkit_handoffs_total', 'Total handoffs created', ['trigger_type', 'helpdesk'])
handoff_duration = Histogram('handoffkit_handoff_duration_seconds', 'Handoff creation duration')
trigger_evaluation_duration = Histogram('handoffkit_trigger_evaluation_duration_seconds', 'Trigger evaluation duration')
active_handoffs = Gauge('handoffkit_active_handoffs', 'Number of active handoffs')

# Usage
with handoff_duration.time():
    result = await create_handoff(...)
handoff_total.labels(trigger_type=result.trigger_type, helpdesk="zendesk").inc()
```

---

## 13. Open Questions & Future Decisions

### 13.1 For Implementation Phase

**Q1: Sentiment Keyword Weights**
- Decision needed: Exact scoring weights for negative keywords
- Approach: Start with conservative values, tune based on testing
- Testing: A/B test different thresholds in production

**Q2: Entity Extraction Regex Patterns**
- Decision needed: Comprehensive regex patterns for all entity types
- Approach: Start with common patterns, expand based on real data
- Consider: spaCy for ML-based extraction in V2

**Q3: WebSocket Reconnection Strategy**
- Decision needed: Exponential backoff parameters
- Approach: Start with 1s delay, max 5s, infinite attempts
- Monitoring: Track reconnection frequency and success rate

**Q4: Database Migration Timing**
- Decision needed: When to recommend SQLite → PostgreSQL migration
- Criteria: >1000 handoffs/day or >10GB database size
- Documentation: Step-by-step migration guide needed

### 13.2 V2 Architecture Considerations

**ML-Powered Sentiment Analysis:**
- Model: DistilBERT or FinBERT for banking domain
- Hosting: Model served via separate service or embedded
- Performance: Ensure <100ms inference time

**Advanced Smart Routing:**
- Skill matching algorithm design
- Priority queue implementation
- Load balancing strategy across agents

**Multi-tenant Architecture:**
- Tenant isolation strategy (database per tenant vs shared schema)
- API key scoping and permissions
- Resource quotas and rate limiting per tenant

---

## 14. Architecture Decision Records

### ADR-001: Framework-Agnostic Core Design

**Status:** Accepted

**Context:**
HandoffKit must work with any conversational AI system (LangChain, LlamaIndex, custom frameworks). Competing solutions are locked to specific platforms.

**Decision:**
Design core SDK as pure Python library with no framework dependencies. Provide optional integration helpers for popular frameworks.

**Consequences:**
- ✅ Maximum flexibility and adoption
- ✅ Simple pip installation
- ⚠️ Framework-specific conveniences must be separate modules
- ⚠️ Documentation must show examples for each framework

---

### ADR-002: Rule-Based Sentiment for MVP

**Status:** Accepted

**Context:**
Sentiment analysis can use ML models (DistilBERT, FinBERT) or rule-based approaches. ML provides better accuracy but adds complexity and dependencies.

**Decision:**
Use hybrid rule-based sentiment analysis for MVP. Defer ML to V2.

**Rationale:**
- Faster installation (no torch dependency)
- Simpler to tune and debug
- Good enough accuracy for MVP validation
- Can add ML later without breaking changes

**Consequences:**
- ✅ Lightweight installation
- ✅ Fast inference (<50ms)
- ⚠️ Lower accuracy than ML models
- ⚠️ Requires manual keyword tuning

---

### ADR-003: SQLite for MVP, PostgreSQL for Production

**Status:** Accepted

**Context:**
Database choice affects developer experience (ease of setup) vs production capabilities (scalability, features).

**Decision:**
Default to SQLite for MVP/development, provide clear migration path to PostgreSQL for production.

**Rationale:**
- SQLite: Zero configuration, file-based, perfect for getting started
- PostgreSQL: Production-grade, JSONB support, horizontal scaling
- SQLAlchemy: Abstracts differences, makes migration straightforward

**Consequences:**
- ✅ Excellent developer experience (zero setup)
- ✅ Clear production upgrade path
- ⚠️ Must document migration process
- ⚠️ Must design schema for PostgreSQL features

---

### ADR-004: Optional Dashboard via Separate Package

**Status:** Accepted

**Context:**
Dashboard adds value but increases installation complexity (Node.js, npm dependencies).

**Decision:**
Make dashboard completely optional. SDK works standalone. Dashboard is separate installation: `pip install handoffkit[dashboard]`.

**Rationale:**
- SDK-only users don't need dashboard overhead
- Dashboard users opt-in explicitly
- Maintains lightweight core promise

**Consequences:**
- ✅ Flexible deployment options
- ✅ Minimal SDK installation
- ⚠️ Must maintain two deployment paths
- ⚠️ Dashboard must gracefully handle SDK-only deployments

---

### ADR-005: FastAPI for REST API

**Status:** Accepted

**Context:**
API framework choice affects performance, documentation, and developer experience.

**Decision:**
Use FastAPI for REST API layer.

**Rationale:**
- Automatic OpenAPI documentation (critical for developer tool)
- Native async/await (non-blocking operations)
- High performance (comparable to Node.js)
- Excellent developer experience
- Built-in WebSocket support

**Consequences:**
- ✅ Auto-generated API docs
- ✅ Type safety via Pydantic
- ✅ Great async performance
- ⚠️ Python 3.9+ requirement

---

## 15. Appendix

### 15.1 Technology Version Matrix

| Technology | Minimum Version | Recommended Version | Notes |
|-----------|-----------------|---------------------|-------|
| Python | 3.9 | 3.11 | Type hints, async improvements |
| FastAPI | 0.109.0 | Latest 0.x | Stable API |
| Pydantic | 2.5.0 | Latest 2.x | V2 performance improvements |
| SQLAlchemy | 2.0.25 | Latest 2.x | Async support |
| PostgreSQL | 13 | 15 | JSONB performance improvements |
| Node.js | 18 LTS | 20 LTS | Dashboard build |
| SvelteKit | 2.0.0 | Latest 2.x | Stable API |

### 15.2 File Size Estimates

| Component | Estimated Size | Notes |
|-----------|---------------|-------|
| SDK Core | ~500 KB | Pure Python, minimal deps |
| SDK with deps | ~5 MB | Including FastAPI, httpx, etc. |
| Dashboard build | ~2 MB | Minified SvelteKit bundle |
| Database (1K handoffs) | ~10 MB | SQLite file size |
| Database (100K handoffs) | ~1 GB | PostgreSQL recommended |

### 15.3 Glossary

**Handoff:** The process of transferring a conversation from AI to human agent

**Trigger:** Condition that indicates a handoff is needed

**Orchestrator:** Main class coordinating handoff logic

**Adapter:** Integration interface for helpdesk systems

**Context:** Conversation history and metadata preserved during handoff

**Sentiment:** Numerical score (0-1) indicating user satisfaction/frustration

---

## Document Control

**Version:** 1.0 (Complete)
**Status:** Ready for Implementation
**Last Updated:** 2025-12-25
**Next Phase:** UX Design (Recommended) or Epics & Stories

**Approved By:** Auto-generated (YOLO Mode)

---

*This architecture document was generated using the BMad Method Architecture workflow, transforming the PRD into implementation-ready architectural decisions.*
