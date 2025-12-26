---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories', 'step-04-final-validation']
status: complete
date: '2025-12-26'
project_name: 'handoffkit'
user_name: 'Hieu TRAN'
inputDocuments:
  - /Users/hieutt50/projects/banking-agent-handoffkit/_bmad-output/prd.md
  - /Users/hieutt50/projects/banking-agent-handoffkit/_bmad-output/architecture.md
  - /Users/hieutt50/projects/banking-agent-handoffkit/_bmad-output/project-planning-artifacts/ux-design-specification.md
---

# HandoffKit - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for HandoffKit, decomposing the requirements from the PRD, UX Design, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

**FR-1: Trigger Detection System (Must Have - MVP)**
- FR-1.1: Direct Request Detection - System SHALL detect explicit requests for human agent using NLP pattern matching with 0.8 confidence threshold, response time <100ms
- FR-1.2: Failure Pattern Tracking - System SHALL track consecutive failed AI responses with configurable threshold (default 2-3 attempts)
- FR-1.3: Critical Keyword Monitoring - System SHALL trigger immediate handoff on critical keywords (fraud, emergency, locked out, dispute, unauthorized, stolen) with <50ms trigger time
- FR-1.4: Custom Rule Engine - System SHALL support custom trigger rules via API with IF-THEN-priority syntax and boolean logic

**FR-2: Hybrid Sentiment Analysis (Must Have - MVP)**
- FR-2.1: Keyword Scoring - System SHALL score messages based on negative keywords (strong: -0.3, moderate: -0.15, base: 0.5)
- FR-2.2: Caps Lock and Punctuation Detection - System SHALL detect frustration signals in text formatting
- FR-2.3: Conversation Degradation Tracking - System SHALL track sentiment trend over rolling window of last 5 messages
- FR-2.4: Domain-Specific Amplification - System SHALL amplify urgency for domain-specific keywords with 1.5x multiplier
- FR-2.5: Configurable Thresholds - System SHALL support configurable sentiment trigger threshold (default: 0.3)

**FR-3: Context Preservation Module (Must Have - MVP)**
- FR-3.1: Conversation History Packaging - System SHALL preserve complete conversation history (max 100 messages or 50KB) in JSON format
- FR-3.2: Metadata Collection - System SHALL collect user ID, session ID, channel, user segment, attempted solutions, failed queries, conversation duration
- FR-3.3: Entity Extraction - System SHALL extract and highlight key entities (account numbers masked, dollar amounts, dates, emails, phones, names)
- FR-3.4: Semantic Summarization - System SHALL generate AI summary of conversation (max 200 words)
- FR-3.5: Format Adapters - System SHALL export context to Zendesk, Intercom, Generic JSON, and Markdown formats

**FR-4: Smart Routing (Must Have MVP Basic)**
- FR-4.1: Agent Availability Checking - System SHALL check agent availability via helpdesk API with 30-second cache TTL
- FR-4.2: Round-Robin Distribution - System SHALL distribute handoffs evenly across available agents
- FR-4.3: Fallback Ticket Creation - System SHALL create ticket if no agents available with priority based on trigger type
- FR-4.4: Configurable Routing Rules - System SHALL support basic routing configuration via dashboard UI or config file

**FR-5: REST API (Must Have - MVP)**
- FR-5.1: Check Endpoint - POST /api/v1/check with conversation, current_message, metadata; returns should_handoff, trigger_reason, confidence, suggested_priority
- FR-5.2: Handoff Endpoint - POST /api/v1/handoff with conversation, metadata, helpdesk, priority; returns handoff_id, status, agent, ticket_url
- FR-5.3: Status Endpoint - GET /api/v1/handoff/{id} returns handoff status and timeline
- FR-5.4: OpenAPI Documentation - System SHALL provide auto-generated OpenAPI 3.0 spec with Swagger UI at /api/docs
- FR-5.5: Authentication - API key authentication via Authorization: Bearer header with 100 requests/minute rate limiting

**FR-6: Live Handoff Feed - Dashboard (Must Have - MVP)**
- FR-6.1: WebSocket Real-Time Updates - Dashboard SHALL receive handoff events via WebSocket with <1 second latency
- FR-6.2: Filterable Feed - Dashboard SHALL support filtering by trigger type, channel, time range, status
- FR-6.3: Conversation Detail View - Clicking handoff SHALL open detail modal with full conversation, entities, summary, trigger info
- FR-6.4: Cross-Browser Compatibility - Dashboard SHALL work on Chrome 100+, Firefox 100+, Safari 15+, Edge 100+

**FR-7: Trigger Breakdown Chart - Dashboard (Must Have - MVP)**
- FR-7.1: Pie Chart Visualization - Dashboard SHALL display pie chart of trigger types with color coding and percentages
- FR-7.2: Time Range Filters - Chart SHALL support Today, Last 7 days, Last 30 days, Custom date range
- FR-7.3: Drill-Down to Examples - Clicking pie slice SHALL filter handoff feed to that trigger type
- FR-7.4: CSV Export - Export button SHALL download CSV of trigger data

**FR-8: Configuration UI - Dashboard (Must Have - MVP)**
- FR-8.1: Failure Threshold Configuration - UI SHALL provide slider for failure threshold (1-5 attempts, default 3)
- FR-8.2: Sentiment Threshold Configuration - UI SHALL provide slider for sentiment threshold (0.0-1.0, default 0.3)
- FR-8.3: Critical Keywords Management - UI SHALL provide keyword list editor with add/remove as chips
- FR-8.4: Helpdesk Integration Configuration - UI SHALL provide forms for Zendesk and Intercom credentials with test connection
- FR-8.5: Test Mode Toggle - UI SHALL provide test mode switch for logging without actual handoff creation

### NonFunctional Requirements

**NFR-1: Performance**
- NFR-1.1: Trigger detection <100ms (95th percentile), sentiment analysis <50ms (95th percentile), total handoff decision <200ms
- NFR-1.2: WebSocket updates <1 second, handle 100+ concurrent connections, chart rendering <500ms, 60fps scrolling
- NFR-1.3: /check endpoint <200ms, /handoff endpoint <500ms, /status endpoint <100ms (95th percentile at 50 req/s)
- NFR-1.4: Handle 1,000 handoffs per day, database queries <50ms, horizontal scaling supported

**NFR-2: Reliability & Availability**
- NFR-2.1: 99.5% uptime target, graceful degradation (SDK works if dashboard down)
- NFR-2.2: Proper HTTP error codes, SDK handles helpdesk API failures, WebSocket auto-reconnect with exponential backoff
- NFR-2.3: SQLite with automatic backups, conversation history survives restarts, no data loss on graceful shutdown

**NFR-3: Security**
- NFR-3.1: API key authentication for all endpoints, dashboard login (username/password), 24-hour session timeout, revocable API keys
- NFR-3.2: Conversation data encrypted at rest, helpdesk credentials encrypted, API keys hashed (bcrypt), PII masked in logs
- NFR-3.3: Rate limiting 100 req/min per key, brute force protection (5 attempts, 15 min lockout)
- NFR-3.4: Dependencies from trusted sources, automated security scanning (Dependabot), no critical vulnerabilities

**NFR-4: Usability & Developer Experience**
- NFR-4.1: Single pip install command, zero config for basic usage, Python 3.9+ support
- NFR-4.2: Comprehensive README, API documentation with examples, tutorial series for LangChain/LlamaIndex/custom
- NFR-4.3: Clear actionable error messages with resolution guidance
- NFR-4.4: Structured JSON logging, optional verbose mode, health check endpoint

**NFR-5: Maintainability & Quality**
- NFR-5.1: >80% test coverage, linting passes (black, flake8, mypy), no critical code smells
- NFR-5.2: GitHub Actions CI/CD with unit tests, integration tests, linting, security scanning
- NFR-5.3: Semantic versioning, automated release notes, PyPI and Docker Hub releases

**NFR-6: Compatibility & Portability**
- NFR-6.1: SDK works on Linux, macOS, Windows; Dashboard on Linux, macOS; Docker images for amd64, arm64
- NFR-6.2: Verified integrations with LangChain 0.1.0+, LlamaIndex 0.9.0+, REST API for custom frameworks
- NFR-6.3: Documented migration path SQLite to PostgreSQL, Alembic migrations, zero downtime migration

### Additional Requirements

**From Architecture:**
- Implement 3-tier LLM detection strategy: Tier 1 (rule-based <10ms), Tier 2 (local LLM DistilBERT/FinBERT 50-100ms), Tier 3 (optional cloud LLM 200-500ms)
- Package structure: handoffkit/core, triggers, sentiment, context, routing, integrations, utils, api
- Modular SDK design with HandoffOrchestrator as primary interface
- FastAPI 0.109+ for REST API with async support
- SvelteKit 2.0+ dashboard with Tailwind CSS and shadcn-svelte components
- SQLAlchemy 2.0+ ORM with SQLite default, PostgreSQL production support
- Database schema: handoffs, handoff_events, api_keys, dashboard_users tables
- Docker Compose for development, Dockerfile for production deployment
- Installation options: pip install handoffkit (lightweight ~5MB), handoffkit[ml] (with local LLM), handoffkit[ml,dashboard] (full)
- WebSocket connection manager for real-time dashboard updates
- Adapter pattern for helpdesk integrations (Zendesk, Intercom)
- API key management with bcrypt hashing
- JWT tokens for dashboard authentication (24-hour expiry)
- Rate limiting with token bucket algorithm

**From UX Design:**
- Terminal-inspired dark theme with color palette (#0A0E14 background, #F9FAFB text, #3B82F6 primary)
- Trigger type color coding: Blue (direct request), Red (sentiment), Orange (keyword), Purple (failure)
- Lucide Icons for consistent iconography
- Progressive disclosure: simple by default, advanced on demand
- Command palette (Cmd+K) for power users
- Sidebar navigation (256px, collapsible to 64px)
- HandoffCard component with collapsed/expanded states
- LiveFeed with auto-scroll and pause capability
- TriggerChart with click-to-filter interaction
- ThresholdSlider with live preview before apply
- Empty states with helpful guidance
- WCAG 2.1 Level AA accessibility compliance
- Desktop-first responsive design (1280px+ optimal)
- Performance targets: <500ms initial load, <1s time to interactive, <50ms per handoff render

### FR Coverage Map

| FR | Epic | Description |
|----|------|-------------|
| FR-1 | Epic 2 | Trigger Detection System (direct request, failure tracking, keywords, custom rules) |
| FR-2 | Epic 2 | Hybrid Sentiment Analysis (keyword scoring, caps detection, degradation tracking, domain amplification) |
| FR-3 | Epic 3 | Context Preservation Module (history, metadata, entities, summarization, adapters) |
| FR-4 | Epic 3 | Smart Routing (availability checking, round-robin, fallback tickets, routing rules) |
| FR-5 | Epic 4 | REST API (check/handoff/status endpoints, OpenAPI docs, authentication, rate limiting) |
| FR-6 | Epic 5 | Live Handoff Feed (WebSocket updates, filtering, detail view, cross-browser) |
| FR-7 | Epic 6 | Trigger Breakdown Chart (pie chart, time filters, drill-down, CSV export) |
| FR-8 | Epic 6 | Configuration UI (thresholds, keywords, helpdesk config, test mode) |

## Epic List

### Epic 1: Project Foundation & Core SDK Architecture

Developers can install HandoffKit via pip and have a working SDK skeleton with core types, interfaces, and configuration management.

**User Outcome:** `pip install handoffkit` works, core classes importable
**FRs covered:** Foundation layer enabling all subsequent FRs
**Implementation Notes:** Package structure, Pydantic models, HandoffOrchestrator interface, logging utilities

---

### Epic 2: Intelligent Handoff Detection

Developers can detect when conversations need human intervention using a 3-tier detection approach (rule-based + local LLM + optional cloud LLM).

**User Outcome:** `orchestrator.should_handoff()` accurately detects handoff needs in <200ms
**FRs covered:** FR-1, FR-2
**Implementation Notes:** Direct request detection, failure tracking, keyword monitoring, custom rules, sentiment scoring, local LLM integration

---

### Epic 3: Context Preservation & Helpdesk Integration

Conversations transfer seamlessly to helpdesk systems (Zendesk, Intercom) with complete context including history, metadata, entities, and AI-generated summaries.

**User Outcome:** `orchestrator.create_handoff()` sends full context to Zendesk/Intercom
**FRs covered:** FR-3, FR-4
**Implementation Notes:** Conversation packaging, entity extraction, summarization, format adapters, agent availability, round-robin distribution

---

### Epic 4: REST API & External Integration

Any language or framework can integrate HandoffKit via a well-documented REST API with authentication and rate limiting.

**User Outcome:** Non-Python systems can POST to `/api/v1/check` and `/api/v1/handoff`
**FRs covered:** FR-5
**Implementation Notes:** FastAPI endpoints, OpenAPI documentation, API key auth, rate limiting, WebSocket foundation

---

### Epic 5: Real-Time Dashboard Monitoring

Operations teams can monitor handoffs as they happen in real-time via a web dashboard with WebSocket updates.

**User Outcome:** Open dashboard, see live handoff feed updating instantly
**FRs covered:** FR-6
**Implementation Notes:** SvelteKit dashboard, WebSocket real-time updates, filtering, conversation detail view, cross-browser support

---

### Epic 6: Dashboard Analytics & Configuration

Product managers can analyze handoff patterns via charts and configure trigger thresholds, keywords, and helpdesk settings.

**User Outcome:** View trigger breakdown chart, adjust sentiment threshold, see fewer false positives
**FRs covered:** FR-7, FR-8
**Implementation Notes:** Pie chart visualization, time range filters, CSV export, threshold sliders, keyword management, test mode

---
---

## Epic 1: Project Foundation & Core SDK Architecture

Developers can install HandoffKit via pip and have a working SDK skeleton with core types, interfaces, and configuration management.

### Story 1.1: Project Skeleton and Package Structure

As a **Python developer**,
I want to **install handoffkit via pip and import the core module**,
So that **I can begin integrating handoff logic into my chatbot**.

**Acceptance Criteria:**

**Given** a Python 3.9+ environment
**When** I run `pip install handoffkit`
**Then** the package installs successfully without errors
**And** I can run `from handoffkit import HandoffOrchestrator`
**And** the package structure follows the architecture specification (core/, triggers/, sentiment/, context/, routing/, integrations/, utils/, api/)

**Given** the package is installed
**When** I check the package metadata
**Then** the version follows semantic versioning (e.g., 0.1.0)
**And** the package size is under 5MB (without ML dependencies)

---

### Story 1.2: Core Type Definitions and Pydantic Models

As a **developer integrating HandoffKit**,
I want to **use well-typed data models for messages and configuration**,
So that **I get IDE autocompletion and type safety**.

**Acceptance Criteria:**

**Given** the handoffkit package is imported
**When** I create a Message object
**Then** I can specify speaker (user/ai), message content, and timestamp
**And** Pydantic validates the input types automatically
**And** invalid inputs raise clear ValidationError with helpful messages

**Given** I need to configure HandoffKit
**When** I create a HandoffConfig object
**Then** I can set failure_threshold (1-5), sentiment_threshold (0.0-1.0), and critical_keywords (list)
**And** default values are sensible (failure=3, sentiment=0.3, keywords=[])
**And** the config is immutable after creation

---

### Story 1.3: HandoffOrchestrator Base Interface

As a **developer building a chatbot**,
I want to **instantiate a HandoffOrchestrator with minimal configuration**,
So that **I can start using handoff detection immediately**.

**Acceptance Criteria:**

**Given** the handoffkit package is imported
**When** I create `HandoffOrchestrator(helpdesk="zendesk")`
**Then** the orchestrator initializes with default triggers and config
**And** the orchestrator has `should_handoff()` and `create_handoff()` methods
**And** the orchestrator accepts an optional `config` parameter for customization

**Given** an orchestrator is created without triggers
**When** I call `should_handoff(conversation, message)`
**Then** it returns `(False, None)` by default
**And** no exceptions are raised

---

### Story 1.4: Configuration Management System

As a **developer deploying HandoffKit**,
I want to **configure settings via environment variables or config file**,
So that **I can change behavior without modifying code**.

**Acceptance Criteria:**

**Given** environment variables are set (HANDOFFKIT_FAILURE_THRESHOLD, HANDOFFKIT_SENTIMENT_THRESHOLD)
**When** HandoffOrchestrator is created without explicit config
**Then** it reads configuration from environment variables
**And** environment variables override default values

**Given** a config.yaml file exists in the working directory
**When** HandoffOrchestrator is created
**Then** it loads configuration from the file
**And** environment variables take precedence over file configuration

---

### Story 1.5: Structured Logging Utilities

As a **developer debugging HandoffKit integration**,
I want to **structured JSON logs with configurable verbosity**,
So that **I can troubleshoot issues and monitor behavior**.

**Acceptance Criteria:**

**Given** HandoffKit is running
**When** a handoff decision is made
**Then** a log entry is created with timestamp, level, message, and context
**And** the log format is valid JSON for machine parsing
**And** log level respects the LOG_LEVEL environment variable

**Given** verbose mode is enabled (LOG_LEVEL=DEBUG)
**When** trigger evaluation occurs
**Then** detailed logs show each trigger's evaluation result
**And** confidence scores are included in the log output

---
---

## Epic 2: Intelligent Handoff Detection

Developers can detect when conversations need human intervention using a 3-tier detection approach (rule-based + local LLM + optional cloud LLM).

### Story 2.1: Direct Request Detection Trigger

As a **chatbot developer**,
I want to **detect when users explicitly request a human agent**,
So that **my chatbot immediately escalates these requests**.

**Acceptance Criteria:**

**Given** a conversation with the message "I want to talk to a human"
**When** `should_handoff()` is called
**Then** it returns `(True, TriggerResult)` with trigger_type="direct_request"
**And** confidence is >= 0.8
**And** evaluation completes in <100ms

**Given** variations like "get me a real person", "speak to an agent", "human please"
**When** `should_handoff()` is called
**Then** these are also detected as direct requests
**And** the detection uses NLP pattern matching, not just exact string match

**Given** a message like "Can you help me with my account?"
**When** `should_handoff()` is called
**Then** it returns `(False, None)` - no false positive

---

### Story 2.2: Failure Pattern Tracking Trigger

As a **chatbot developer**,
I want to **detect when the AI has failed to help multiple times**,
So that **frustrated users get human assistance**.

**Acceptance Criteria:**

**Given** a conversation where the user repeats the same question 3 times
**When** `should_handoff()` is called
**Then** it returns `(True, TriggerResult)` with trigger_type="failure_tracking"
**And** the threshold is configurable (default: 3)

**Given** the AI responds with "I don't understand" 2 times
**When** `should_handoff()` is called with failure_threshold=2
**Then** it triggers on the 2nd failure
**And** the failure counter resets after a successful exchange

**Given** a single failed response followed by successful help
**When** `should_handoff()` is called
**Then** it returns `(False, None)` - counter was reset

---

### Story 2.3: Critical Keyword Monitoring Trigger

As a **chatbot developer handling sensitive topics**,
I want to **immediately escalate conversations mentioning fraud, emergencies, or security issues**,
So that **urgent matters get human attention instantly**.

**Acceptance Criteria:**

**Given** a message containing "fraud" or "unauthorized transaction"
**When** `should_handoff()` is called
**Then** it triggers immediately with trigger_type="keyword"
**And** priority is set to "immediate"
**And** trigger time is <50ms

**Given** default critical keywords: ["fraud", "emergency", "locked out", "dispute", "unauthorized", "stolen"]
**When** any of these appear in a message (case-insensitive)
**Then** handoff is triggered

**Given** custom keywords configured: ["regulation E", "FDIC complaint"]
**When** these phrases appear in a message
**Then** handoff is triggered for custom keywords too

---

### Story 2.4: Custom Rule Engine

As a **developer with domain-specific needs**,
I want to **define custom handoff rules with conditions and priorities**,
So that **handoff logic matches my business requirements**.

**Acceptance Criteria:**

**Given** a custom rule: IF sentiment < 0.3 AND keyword contains "account" THEN trigger with priority "high"
**When** a message matches this rule
**Then** handoff is triggered with the specified priority
**And** the rule reason is included in TriggerResult

**Given** multiple rules that could match
**When** `should_handoff()` is called
**Then** the highest priority matching rule is used
**And** all matching rules are logged for debugging

**Given** rules configured via the API
**When** new rules are added
**Then** they take effect for new conversations without restart

---

### Story 2.5: Rule-Based Sentiment Scoring (Tier 1)

As a **developer using the lightweight SDK installation**,
I want to **detect user frustration using rule-based sentiment analysis**,
So that **I can identify negative sentiment without ML dependencies**.

**Acceptance Criteria:**

**Given** a message with strong negative keywords ("terrible", "awful", "frustrated")
**When** sentiment is analyzed
**Then** the score is < 0.3 (on 0.0-1.0 scale where 0 is negative)
**And** analysis completes in <10ms

**Given** a neutral message without emotion indicators
**When** sentiment is analyzed
**Then** the score is approximately 0.5 (neutral baseline)

**Given** configurable negative keywords with weights (strong: -0.3, moderate: -0.15)
**When** sentiment is calculated
**Then** the algorithm uses the configured weights

---

### Story 2.6: Frustration Signal Detection (Caps and Punctuation)

As a **chatbot developer**,
I want to **detect frustration from text formatting like CAPS LOCK and excessive punctuation**,
So that **I catch non-verbal frustration signals**.

**Acceptance Criteria:**

**Given** a message in ALL CAPS like "I NEED HELP NOW"
**When** sentiment is analyzed
**Then** the score is reduced by 0.1 per caps word
**And** this combines with other negative signals

**Given** excessive punctuation like "Why isn't this working???" or "Help!!!"
**When** sentiment is analyzed
**Then** the score is reduced by 0.05 per instance
**And** combined with other signals (caps + punctuation = stronger signal)

---

### Story 2.7: Conversation Degradation Tracking

As a **developer monitoring conversation quality**,
I want to **detect when sentiment trends downward over multiple messages**,
So that **I can escalate before users become extremely frustrated**.

**Acceptance Criteria:**

**Given** a conversation where sentiment drops from 0.7 → 0.6 → 0.5 → 0.4 → 0.3
**When** `should_handoff()` is called
**Then** it triggers due to degradation (drop > 0.3 over 5 messages)
**And** trigger_type is "sentiment_degradation"

**Given** a rolling window of the last 5 messages
**When** sentiment is tracked
**Then** the trend is calculated from window start to end
**And** older messages outside the window are not considered

---

### Story 2.8: Local LLM Sentiment Analysis (Tier 2)

As a **developer using handoffkit[ml] installation**,
I want to **use DistilBERT for accurate semantic sentiment analysis**,
So that **I get better accuracy than rule-based without API costs**.

**Acceptance Criteria:**

**Given** handoffkit[ml] is installed
**When** sentiment is analyzed
**Then** DistilBERT model is used for semantic understanding
**And** analysis completes in <100ms (CPU)
**And** accuracy is ~92% on standard sentiment benchmarks

**Given** the financial_domain config is True
**When** sentiment is analyzed
**Then** FinBERT model is used instead
**And** banking-specific terms are weighted appropriately

**Given** models are not yet downloaded
**When** first analysis is requested
**Then** models are downloaded on-demand (~500MB)
**And** progress is logged

---

### Story 2.9: Optional Cloud LLM Integration (Tier 3)

As a **developer needing highest accuracy**,
I want to **optionally use cloud LLM for complex sentiment analysis**,
So that **ambiguous cases get the most accurate detection**.

**Acceptance Criteria:**

**Given** cloud_llm_enabled=True and cloud_llm_api_key is set
**When** local LLM confidence is below threshold (default 0.3)
**Then** cloud LLM (GPT-4o-mini or Claude) is called for analysis
**And** response time is <500ms

**Given** cloud LLM is configured with OpenAI
**When** complex conversation is analyzed
**Then** the full conversation context is sent
**And** structured JSON response with reasoning is returned

**Given** cloud LLM API call fails
**When** fallback occurs
**Then** local LLM result is used
**And** error is logged but not raised

---
---

## Epic 3: Context Preservation & Helpdesk Integration

Conversations transfer seamlessly to helpdesk systems (Zendesk, Intercom) with complete context including history, metadata, entities, and AI-generated summaries.

### Story 3.1: Conversation History Packaging

As a **support agent receiving a handoff**,
I want to **see the complete conversation history**,
So that **I don't ask the customer to repeat themselves**.

**Acceptance Criteria:**

**Given** a conversation with 10 messages
**When** `create_handoff()` is called
**Then** all messages are included in the handoff package
**And** each message includes timestamp, speaker, content, and AI confidence

**Given** a conversation exceeding 100 messages
**When** context is packaged
**Then** the most recent 100 messages are included
**And** total size is capped at 50KB
**And** format is valid JSON

---

### Story 3.2: Metadata Collection

As a **support team analyzing handoffs**,
I want to **see user and session metadata**,
So that **I have context about the customer and channel**.

**Acceptance Criteria:**

**Given** a handoff is created with metadata
**When** context is packaged
**Then** user_id, session_id, channel are included
**And** attempted_solutions (AI suggestions) are listed
**And** failed_queries (unanswered questions) are captured
**And** conversation_duration is calculated

**Given** minimal metadata provided (only user_id)
**When** context is packaged
**Then** session_id is auto-generated
**And** missing fields default to "unknown" or null

---

### Story 3.3: Entity Extraction

As a **support agent**,
I want to **see extracted entities (account numbers, amounts, dates) highlighted**,
So that **I can quickly understand the key details**.

**Acceptance Criteria:**

**Given** a conversation mentioning account number "12345678"
**When** entities are extracted
**Then** the number is identified and masked (****5678)
**And** entity type is "account_number"

**Given** dollar amounts like "$1,234.56" or "1500 dollars"
**When** entities are extracted
**Then** amounts are identified with type "currency"
**And** format is normalized

**Given** dates like "2025-12-25" or "last Tuesday"
**When** entities are extracted
**Then** dates are identified and parsed
**And** relative dates are converted to absolute (where possible)

---

### Story 3.4: Conversation Summarization

As a **support agent with limited time**,
I want to **see a brief AI-generated summary of the conversation**,
So that **I can understand the issue in seconds**.

**Acceptance Criteria:**

**Given** a 20-message conversation about a payment issue
**When** summary is generated
**Then** it captures: user's primary issue, AI's attempted solutions, current state
**And** summary is max 200 words
**And** generation completes in <500ms

**Given** MVP (rule-based summarization)
**When** summary is generated
**Then** template-based approach extracts key information
**And** format is consistent: "Issue: X. Tried: Y. Status: Z."

---

### Story 3.5: Zendesk Integration Adapter

As a **developer using Zendesk**,
I want to **automatically create tickets with conversation context**,
So that **handoffs appear in my existing support workflow**.

**Acceptance Criteria:**

**Given** Zendesk credentials configured (subdomain, email, API token)
**When** `create_handoff(helpdesk="zendesk")` is called
**Then** a Zendesk ticket is created via API
**And** conversation history is added as the ticket description
**And** priority is mapped (immediate→urgent, high→high, normal→normal)
**And** ticket URL is returned in HandoffResult

**Given** Zendesk API returns an error
**When** ticket creation fails
**Then** error is captured in HandoffResult.error
**And** status is "failed"
**And** handoff is queued for retry

---

### Story 3.6: Intercom Integration Adapter

As a **developer using Intercom**,
I want to **create conversations with conversation context**,
So that **handoffs work with my Intercom setup**.

**Acceptance Criteria:**

**Given** Intercom credentials configured (app_id, access_token)
**When** `create_handoff(helpdesk="intercom")` is called
**Then** an Intercom conversation is created
**And** conversation history is formatted as markdown
**And** priority is set according to mapping

**Given** test connection is requested
**When** credentials are validated
**Then** a test API call confirms connectivity
**And** result (success/failure) is returned

---

### Story 3.7: Generic JSON and Markdown Adapters

As a **developer with a custom helpdesk**,
I want to **get handoff context in generic JSON or Markdown format**,
So that **I can integrate with any system**.

**Acceptance Criteria:**

**Given** helpdesk="json" is configured
**When** `create_handoff()` is called
**Then** a standardized JSON structure is returned
**And** structure includes: conversation, metadata, summary, entities
**And** no external API is called

**Given** helpdesk="markdown" is configured
**When** context is exported
**Then** human-readable markdown is generated
**And** format is suitable for pasting into tickets/emails

---

### Story 3.8: Agent Availability Checking

As a **developer implementing real-time routing**,
I want to **check which agents are currently available**,
So that **handoffs can be assigned immediately when possible**.

**Acceptance Criteria:**

**Given** Zendesk integration is configured
**When** availability is checked
**Then** list of online agents is returned
**And** results are cached for 30 seconds (TTL)
**And** query completes in <200ms

**Given** no agents are available
**When** availability check returns empty
**Then** fallback to ticket creation is triggered
**And** user is notified of estimated response time

---

### Story 3.9: Round-Robin Agent Distribution

As a **support team manager**,
I want to **handoffs distributed evenly across available agents**,
So that **no single agent gets overloaded**.

**Acceptance Criteria:**

**Given** 3 agents are available: A, B, C
**When** 6 handoffs are created
**Then** each agent receives 2 handoffs (A→B→C→A→B→C)
**And** distribution resets daily at midnight

**Given** an agent goes offline mid-rotation
**When** next handoff is created
**Then** that agent is skipped
**And** rotation continues with remaining agents

---

### Story 3.10: Fallback Ticket Creation

As a **developer handling after-hours handoffs**,
I want to **create tickets when no agents are available**,
So that **users aren't left hanging**.

**Acceptance Criteria:**

**Given** no agents are available
**When** `create_handoff()` is called
**Then** a ticket is created instead of live assignment
**And** priority is set based on trigger type
**And** user receives message: "No agents available. Ticket created. You'll hear from us within X hours."

**Given** ticket creation also fails
**When** fallback is exhausted
**Then** handoff is logged locally
**And** status is "pending_retry"
**And** retry mechanism queues the handoff

---

### Story 3.11: Configurable Routing Rules

As a **support team lead**,
I want to **route specific handoffs to specific teams**,
So that **billing issues go to billing, tech issues go to tech support**.

**Acceptance Criteria:**

**Given** routing rule: keyword "billing" → team "billing-support"
**When** handoff contains "billing issue"
**Then** ticket is assigned to billing-support team/queue

**Given** business hours rule: 9am-5pm → live chat, after hours → ticket
**When** handoff occurs at 7pm
**Then** ticket is created instead of live assignment

**Given** rules are configured via dashboard or config file
**When** rules are updated
**Then** changes apply to new handoffs without restart

---
---

## Epic 4: REST API & External Integration

Any language or framework can integrate HandoffKit via a well-documented REST API with authentication and rate limiting.

### Story 4.1: FastAPI Application Setup

As a **developer running HandoffKit as a service**,
I want to **start a REST API server with a single command**,
So that **I can integrate from any language or platform**.

**Acceptance Criteria:**

**Given** handoffkit[dashboard] is installed
**When** I run `handoffkit api start`
**Then** FastAPI server starts on port 8000
**And** health check at /health returns {"status": "healthy"}
**And** server handles graceful shutdown on SIGTERM

**Given** the server is running
**When** I visit /api/docs
**Then** Swagger UI is displayed with all endpoints documented

---

### Story 4.2: Check Endpoint (POST /api/v1/check)

As a **developer in any language**,
I want to **check if a conversation needs handoff via HTTP**,
So that **I can use HandoffKit without Python**.

**Acceptance Criteria:**

**Given** a valid API key and conversation payload
**When** POST /api/v1/check is called
**Then** response includes: should_handoff (bool), trigger_reason, confidence, suggested_priority
**And** response time is <200ms (95th percentile)

**Given** conversation where user says "I need a human"
**When** /check is called
**Then** should_handoff is true
**And** trigger_reason is "direct_request"

**Given** invalid or missing API key
**When** /check is called
**Then** 401 Unauthorized is returned
**And** error message explains the issue

---

### Story 4.3: Handoff Endpoint (POST /api/v1/handoff)

As a **developer integrating via REST**,
I want to **create a handoff via HTTP**,
So that **I can trigger handoffs from any platform**.

**Acceptance Criteria:**

**Given** a valid request with conversation, metadata, helpdesk, priority
**When** POST /api/v1/handoff is called
**Then** handoff is created in the configured helpdesk
**And** response includes: handoff_id, status, agent (if assigned), ticket_url
**And** response time is <500ms (95th percentile)

**Given** required field "user_id" is missing from metadata
**When** /handoff is called
**Then** 422 Validation Error is returned
**And** error message specifies missing field

---

### Story 4.4: Status Endpoint (GET /api/v1/handoff/{id})

As a **developer tracking handoff progress**,
I want to **query the status of a handoff**,
So that **I can update the user on progress**.

**Acceptance Criteria:**

**Given** a valid handoff_id
**When** GET /api/v1/handoff/{id} is called
**Then** response includes: handoff_id, status, agent, created_at, updated_at, events
**And** response time is <100ms

**Given** an invalid or non-existent handoff_id
**When** /handoff/{id} is called
**Then** 404 Not Found is returned

---

### Story 4.5: OpenAPI Documentation

As a **developer integrating HandoffKit**,
I want to **access auto-generated API documentation**,
So that **I can understand all endpoints without reading source code**.

**Acceptance Criteria:**

**Given** the API server is running
**When** I access /api/docs
**Then** Swagger UI displays all endpoints with request/response schemas
**And** I can try endpoints directly from the UI

**Given** I need machine-readable documentation
**When** I access /api/openapi.json
**Then** valid OpenAPI 3.0 spec is returned
**And** spec can be imported into Postman, Insomnia, or code generators

---

### Story 4.6: API Key Authentication

As a **administrator managing API access**,
I want to **secure API endpoints with API keys**,
So that **only authorized applications can access HandoffKit**.

**Acceptance Criteria:**

**Given** an API key is generated via dashboard
**When** requests include Authorization: Bearer {key}
**Then** requests are authenticated and processed
**And** API key is hashed with bcrypt in database

**Given** an invalid API key
**When** any protected endpoint is called
**Then** 401 Unauthorized is returned
**And** rate limiting applies (max 5 failed attempts per IP per 15 min)

**Given** an API key is revoked
**When** subsequent requests use that key
**Then** 401 is returned
**And** last_used_at is not updated

---

### Story 4.7: Rate Limiting

As a **service operator**,
I want to **rate limit API requests**,
So that **no single client can overwhelm the system**.

**Acceptance Criteria:**

**Given** rate limit of 100 requests/minute per API key
**When** 101st request is made within a minute
**Then** 429 Too Many Requests is returned
**And** Retry-After header indicates when to retry

**Given** burst allowance of 10 requests
**When** 10 requests arrive simultaneously
**Then** all 10 are processed
**And** subsequent requests count against the limit

---
---

## Epic 5: Real-Time Dashboard Monitoring

Operations teams can monitor handoffs as they happen in real-time via a web dashboard with WebSocket updates.

### Story 5.1: SvelteKit Dashboard Scaffold

As a **developer deploying HandoffKit**,
I want to **start the dashboard with a single command**,
So that **I can monitor handoffs visually**.

**Acceptance Criteria:**

**Given** handoffkit[dashboard] is installed
**When** I run `handoffkit dashboard start`
**Then** SvelteKit dashboard starts on port 5173
**And** browser opens to http://localhost:5173
**And** login page is displayed

**Given** the dashboard is built for production
**When** I run `handoffkit dashboard build`
**Then** optimized static files are generated
**And** bundle size is <2MB

---

### Story 5.2: WebSocket Connection Manager

As a **dashboard user**,
I want to **see handoffs appear in real-time without refreshing**,
So that **I can monitor activity as it happens**.

**Acceptance Criteria:**

**Given** dashboard is open and connected
**When** a new handoff is created via API
**Then** it appears in the feed within 1 second
**And** no page refresh is required

**Given** WebSocket connection is lost
**When** network is restored
**Then** connection auto-reconnects with exponential backoff
**And** missed events are fetched via REST fallback

**Given** dashboard is open
**When** heartbeat is sent every 30 seconds
**Then** connection remains active
**And** server detects stale connections

---

### Story 5.3: Live Handoff Feed Component

As a **support team lead**,
I want to **see a scrolling feed of recent handoffs**,
So that **I can monitor activity at a glance**.

**Acceptance Criteria:**

**Given** handoffs are occurring
**When** I view the dashboard
**Then** a list of handoffs is displayed, newest at top
**And** list auto-scrolls when new handoffs arrive
**And** "Pause" button stops auto-scroll for investigation

**Given** 100+ handoffs in the feed
**When** scrolling through the list
**Then** virtual scrolling ensures smooth 60fps performance
**And** memory usage stays constant (not loading all DOM nodes)

---

### Story 5.4: Handoff Card Component

As a **dashboard user**,
I want to **see key information for each handoff at a glance**,
So that **I can quickly assess priority and status**.

**Acceptance Criteria:**

**Given** a handoff in the feed
**When** I view the card
**Then** I see: trigger type icon, trigger badge (color-coded), timestamp, user message preview (100 chars), confidence score, status pill

**Given** trigger type colors
**When** displaying badges
**Then** blue=direct_request, red=sentiment, orange=keyword, purple=failure
**And** colors are consistent across the dashboard

---

### Story 5.5: Conversation Detail View

As a **support manager investigating a handoff**,
I want to **expand a handoff to see the full conversation**,
So that **I can understand what happened**.

**Acceptance Criteria:**

**Given** a handoff card in the feed
**When** I click on it
**Then** the card expands inline to show full conversation
**And** each message shows speaker icon (user/AI), timestamp, content
**And** extracted entities are highlighted

**Given** the detail view is open
**When** I press ESC or click outside
**Then** the view collapses back to card

**Given** metadata is available
**When** viewing detail
**Then** user_id, session_id, channel, conversation_duration are displayed
**And** AI summary is shown at the top

---

### Story 5.6: Filtering Controls

As a **dashboard user analyzing patterns**,
I want to **filter handoffs by trigger type, time, and status**,
So that **I can focus on specific categories**.

**Acceptance Criteria:**

**Given** the filter bar is visible
**When** I select "Sentiment" trigger type
**Then** only sentiment-triggered handoffs are shown
**And** filter is applied instantly (client-side)

**Given** time range options
**When** I select "Last 24 hours"
**Then** only handoffs from that period are shown
**And** custom date range picker is also available

**Given** multiple filters are active
**When** combined (trigger=sentiment AND status=pending)
**Then** only matching handoffs are shown
**And** "Clear Filters" button resets all filters

---

### Story 5.7: Cross-Browser Compatibility

As a **dashboard user on various browsers**,
I want to **use the dashboard on Chrome, Firefox, Safari, and Edge**,
So that **I'm not forced to use a specific browser**.

**Acceptance Criteria:**

**Given** the dashboard
**When** opened in Chrome 100+, Firefox 100+, Safari 15+, Edge 100+
**Then** all features work correctly
**And** no console errors on any supported browser

**Given** responsive breakpoints
**When** viewed on desktop (1280px+)
**Then** optimal layout with sidebar, main content, detail panel
**And** on tablet (768px+), sidebar becomes drawer
**And** on mobile, layout is single column (read-only)

---
---

## Epic 6: Dashboard Analytics & Configuration

Product managers can analyze handoff patterns via charts and configure trigger thresholds, keywords, and helpdesk settings.

### Story 6.1: Trigger Breakdown Pie Chart

As a **product manager analyzing handoffs**,
I want to **see a pie chart showing trigger type distribution**,
So that **I can identify the most common reasons for handoffs**.

**Acceptance Criteria:**

**Given** handoffs have occurred
**When** I view the analytics section
**Then** a pie chart shows: sentiment (red), keyword (orange), failure (purple), direct_request (blue)
**And** each slice shows percentage and count
**And** legend shows "Sentiment (45) - 40%"

**Given** I hover over a slice
**When** tooltip appears
**Then** it shows count and percentage for that trigger type

---

### Story 6.2: Time Range Filters for Charts

As a **analyst reviewing trends**,
I want to **view chart data for different time periods**,
So that **I can compare patterns over time**.

**Acceptance Criteria:**

**Given** the chart is displayed
**When** I select "Today" / "Last 7 days" / "Last 30 days"
**Then** chart updates immediately with data for that period
**And** data is cached for performance

**Given** I need a specific range
**When** I use the custom date picker
**Then** I can select start and end dates
**And** chart updates with that range

---

### Story 6.3: Drill-Down from Chart to Feed

As a **analyst investigating a trend**,
I want to **click a pie slice to see those specific handoffs**,
So that **I can explore examples of that trigger type**.

**Acceptance Criteria:**

**Given** the pie chart is displayed
**When** I click the "Sentiment" slice
**Then** the handoff feed is filtered to only sentiment-triggered handoffs
**And** a breadcrumb shows "Filtered: Sentiment"

**Given** drill-down view is active
**When** I click "Back to Chart" or clear filters
**Then** I return to the full analytics view

---

### Story 6.4: CSV Export

As a **analyst needing data for reports**,
I want to **export trigger data to CSV**,
So that **I can analyze in Excel or share with stakeholders**.

**Acceptance Criteria:**

**Given** the chart is displayed
**When** I click "Export CSV"
**Then** a file downloads: handoff-triggers-{date-range}.csv
**And** columns include: Date, Trigger Type, Count, Percentage

**Given** the exported CSV
**When** opened in Excel or Google Sheets
**Then** data displays correctly with proper formatting

---

### Story 6.5: Failure Threshold Configuration

As a **administrator tuning handoff behavior**,
I want to **adjust the failure threshold via UI slider**,
So that **I can control when repeated failures trigger handoff**.

**Acceptance Criteria:**

**Given** the configuration panel is open
**When** I view the failure threshold slider
**Then** current value is displayed (default: 3)
**And** range is 1-5 attempts

**Given** I move the slider to 2
**When** preview is shown
**Then** I see "Handoff after 2 failed attempts"
**And** "~X handoffs would be affected" based on historical data

**Given** I click "Apply"
**When** change is saved
**Then** toast notification confirms "Threshold updated"
**And** new threshold applies to subsequent conversations

---

### Story 6.6: Sentiment Threshold Configuration

As a **administrator reducing false positives**,
I want to **adjust the sentiment threshold via UI**,
So that **I can balance sensitivity vs noise**.

**Acceptance Criteria:**

**Given** the configuration panel is open
**When** I view the sentiment slider
**Then** current value is displayed (default: 0.3)
**And** range is 0.0 to 1.0 with 0.05 increments
**And** visual indicator shows: green (happy) → red (angry)

**Given** I move slider from 0.3 to 0.2 (more strict)
**When** preview is shown
**Then** I see "~Y fewer handoffs would trigger"
**And** preview updates in real-time as I drag

---

### Story 6.7: Critical Keywords Management

As a **administrator managing trigger keywords**,
I want to **add, remove, and view critical keywords via UI**,
So that **I can customize domain-specific escalation**.

**Acceptance Criteria:**

**Given** the keywords section is open
**When** I view current keywords
**Then** they appear as removable chips/tags
**And** default keywords are pre-populated

**Given** I click "Add Keyword"
**When** I enter "regulation E"
**Then** keyword is added to the list
**And** validation prevents duplicates
**And** maximum 50 keywords enforced

**Given** I click X on a keyword chip
**When** keyword is removed
**Then** it no longer triggers handoffs
**And** change applies without restart

---

### Story 6.8: Helpdesk Integration Configuration

As a **administrator connecting to Zendesk/Intercom**,
I want to **configure helpdesk credentials via UI**,
So that **I don't need to edit config files**.

**Acceptance Criteria:**

**Given** the integrations section is open
**When** I select Zendesk
**Then** form shows: subdomain, email, API token (masked input)

**Given** credentials are entered
**When** I click "Test Connection"
**Then** a test API call validates credentials
**And** result shows "Connected" (green) or "Failed: reason" (red)

**Given** valid credentials
**When** I click "Save"
**Then** credentials are stored encrypted
**And** integration is activated

---

### Story 6.9: Test Mode Toggle

As a **developer testing handoff logic**,
I want to **enable test mode that logs but doesn't send handoffs**,
So that **I can validate behavior without affecting real users**.

**Acceptance Criteria:**

**Given** the configuration panel
**When** I toggle "Test Mode" ON
**Then** visual indicator shows "TEST MODE ACTIVE" prominently
**And** handoffs are logged but not sent to helpdesk

**Given** test mode is active
**When** a handoff is triggered
**Then** it appears in the feed with "TEST" badge
**And** no ticket is created in Zendesk/Intercom

**Given** I toggle test mode OFF
**When** handoffs are triggered
**Then** normal behavior resumes
**And** handoffs are sent to configured helpdesk

