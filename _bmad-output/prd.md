---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
inputDocuments:
  - /home/hieutt50/projects/handoffkit/brief.md
documentCounts:
  briefs: 1
  research: 0
  brainstorming: 0
  projectDocs: 0
workflowType: 'prd'
lastStep: 11
project_name: 'handoffkit'
user_name: 'Hieu TRAN'
date: '2025-12-25'
---

# Product Requirements Document - HandoffKit

**Author:** Hieu TRAN
**Date:** 2025-12-25
**Version:** 1.0
**Status:** Ready for Architecture Phase

---

## Executive Summary

HandoffKit is an open-source Python SDK and web dashboard for perfect AI-to-human handoffs in conversational AI systems. It provides production-ready handoff logic with smart trigger detection, full context preservation, and integrated monitoring that works with any conversational AI framework.

### Vision Alignment

HandoffKit solves the critical problem where 61% of customers are dissatisfied with chatbot handoffs by providing a lightweight, framework-agnostic SDK that developers can integrate in minutes rather than weeks. The product fills a significant market gap - there is currently no standalone, open-source handoff SDK with an integrated dashboard.

### What Makes This Special

1. **Framework-Agnostic Design** - Unlike competitors locked to specific platforms (Rasa, Microsoft Bot), HandoffKit works with ANY conversational AI system (LangChain, LlamaIndex, custom RAG, legacy chatbots)

2. **SDK + Dashboard Dual Offering** - Provides the flexibility of a library with the visibility of a platform, without forcing adoption of an entire ecosystem

3. **2025 Best Practices Built-In** - Research-backed triggers pre-configured (2-3 failure threshold, sentiment analysis, critical keywords) so developers don't need to research and build themselves

4. **Developer Experience First** - Simple API (`pip install handoffkit`), excellent documentation, 5-minute integration time vs 5+ weeks to build from scratch

5. **Open Source & Self-Hosted** - Free forever, no vendor lock-in, full data control, no recurring $89-139/seat costs like enterprise SaaS

## Project Classification

**Technical Type:** Developer Tool (SDK + Dashboard)
**Domain:** General (AI/Developer Tooling)
**Complexity:** Medium
**Project Context:** Greenfield - New open source project

**Classification Rationale:**
- **Developer Tool signals detected:** SDK, library, pip package, Python, framework-agnostic, API design
- **Domain:** General software development focused on AI/ML developers
- **Complexity:** Medium - Requires solid software engineering but not high-risk regulatory domain

---

## Success Criteria

### Launch Success (Month 1)

**GitHub Metrics:**
- 100+ GitHub stars within first month
- HackerNews front page appearance
- 500+ PyPI downloads

**Quality Indicators:**
- All MVP features functional and tested (>80% coverage)
- Zero critical bugs blocking integration
- Complete documentation with quickstart guide
- 3 working example integrations (LangChain, LlamaIndex, custom)

### Early Traction (Month 3)

**Adoption Metrics:**
- 300 GitHub stars
- 1,000+ PyPI downloads per month
- 2+ production deployments mentioned in issues/discussions
- 50 weekly active users

**Community Health:**
- <48 hour response time on bugs
- Active Discord with 50+ members
- 1-2 external contributors

### Product-Market Fit (Month 6)

**Growth Indicators:**
- 500 GitHub stars
- Featured in Python Weekly or similar newsletter
- 5+ production deployments
- High star-to-fork ratio (real users, not just browsers)

**Quality Metrics:**
- Trigger detection <100ms latency
- Dashboard updates <1 second real-time
- Test coverage maintained >80%
- <5 open critical bugs at any time

### Long-term Success (Year 1)

**Ecosystem Validation:**
- 1,500+ GitHub stars
- 5,000+ PyPI downloads per month
- 200 weekly active users
- 5+ contributors beyond maintainer
- Blog posts and tutorials from community
- Integration requests for additional frameworks

**Leading Indicators:**
- "In production" mentions in GitHub issues
- External contributor PRs accepted
- Tutorial/blog mentions from community
- Feature requests indicating expansion opportunities

---

## User Personas

### Primary Persona 1: Python Developer at Digital-First Neobank

**Background:**
- Name: Alex Chen
- Role: Senior Backend Developer
- Experience: 5+ years Python, 2 years AI/ML
- Tech Stack: LangChain, FastAPI, PostgreSQL, Docker

**Context:**
- Building customer service chatbot for routine banking queries
- Needs human fallback for fraud detection, disputes, complex issues
- Team of 3-5 developers, tight deadlines
- Budget conscious, prefer open source

**Pain Points:**
- Poor chatbot handoffs causing customer complaints
- 5+ weeks estimated to build handoff system from scratch
- Enterprise SaaS too expensive ($89-139/seat × support team)
- Existing frameworks (Rasa) require adopting entire ecosystem

**Goals:**
- Integrate production-ready handoff logic quickly
- Maintain flexibility to use existing LangChain setup
- Get visibility into handoff quality for optimization
- Keep costs low while delivering professional solution

**How HandoffKit Helps:**
- 5-minute integration via `pip install handoffkit`
- Works with existing LangChain architecture
- Dashboard provides metrics for optimization
- Open source, free forever

**Success Scenario:**
Alex integrates HandoffKit in an afternoon, configures triggers for fraud/dispute keywords, connects to Zendesk, and has production-ready handoff logic. Dashboard shows trigger patterns, allowing continuous optimization. Dev time reduced 40%.

---

### Primary Persona 2: Solo Developer / Open Source Contributor

**Background:**
- Name: Jordan Martinez
- Role: Independent Developer / Weekend Warrior
- Experience: 3 years Python, building AI side projects
- Tech Stack: LlamaIndex, Streamlit, SQLite

**Context:**
- Building AI chatbot side project
- Limited time (weekends only)
- Values clean code and best practices
- Interested in contributing to open source

**Pain Points:**
- Limited time to research and implement handoff logic
- Wants to learn best practices but needs quick results
- Existing solutions too complex or enterprise-focused
- No reusable components available

**Goals:**
- Quick integration without deep research
- Learn handoff best practices
- Build portfolio-worthy project
- Potentially contribute back to community

**How HandoffKit Helps:**
- Well-documented, simple API
- Best practices built-in (no research needed)
- Modular design for learning
- Contribution opportunities

**Success Scenario:**
Jordan adds HandoffKit to their project in one weekend, learns about sentiment analysis and trigger patterns from documentation, successfully deploys chatbot with professional handoff logic. Later contributes a new integration example.

---

### Primary Persona 3: Product Manager / CTO at Scale-up

**Background:**
- Name: Sarah Johnson
- Role: Head of Product / CTO
- Experience: 10+ years tech leadership
- Context: 20-50 person company, AI product focus

**Context:**
- Making build vs buy decisions
- Managing development team and budget
- Concerned about vendor lock-in
- Needs metrics to prove ROI

**Pain Points:**
- Enterprise tools too expensive for current scale
- Vendor lock-in risk with SaaS platforms
- Need visibility into handoff quality
- Must justify tool decisions with data

**Goals:**
- Cost-effective solution that scales
- Avoid vendor lock-in
- Get metrics for optimization and ROI proof
- Maintain team velocity

**How HandoffKit Helps:**
- Open source eliminates licensing costs
- Self-hosted maintains data control
- Dashboard provides ROI metrics
- Scales without per-seat costs

**Success Scenario:**
Sarah evaluates HandoffKit, sees it saves 5 weeks of dev time vs building custom. Dashboard provides metrics showing 30% reduction in repeat contacts. No recurring costs. Presents ROI analysis showing $50K+ saved in year 1.

---

## User Stories & Scenarios

### Core User Journey 1: First-Time Integration

**As a** Python developer building a chatbot
**I want to** integrate professional handoff logic quickly
**So that** my users don't get frustrated when they need human help

**Acceptance Criteria:**
- Can install with single pip command
- Can configure basic triggers in <10 lines of code
- Can test handoff locally without external dependencies
- Clear error messages if misconfigured
- Documentation includes quickstart with working example

**User Scenario:**
```python
# Install
pip install handoffkit

# Basic integration
from handoffkit import HandoffOrchestrator, Triggers

orchestrator = HandoffOrchestrator(
    helpdesk="zendesk",
    triggers=[
        Triggers.direct_request(),
        Triggers.failed_attempts(threshold=3),
        Triggers.negative_sentiment(threshold=0.7),
        Triggers.keywords(["fraud", "emergency"])
    ]
)

# In chatbot loop
if orchestrator.should_handoff(conversation_history, user_message):
    handoff = orchestrator.create_handoff(
        conversation=conversation_history,
        metadata={"user_id": "123", "channel": "web"}
    )
    return handoff.transfer_to_agent()
```

**Success Metric:** Developer completes integration in <1 hour

---

### Core User Journey 2: Monitoring Handoff Quality

**As a** product manager overseeing chatbot quality
**I want to** see real-time handoff patterns and triggers
**So that** I can optimize triggers and improve satisfaction

**Acceptance Criteria:**
- Dashboard shows live handoff feed (<1 second latency)
- Can filter by trigger type, channel, time range
- Pie chart shows trigger breakdown (sentiment/keyword/failure/direct)
- Can drill down to see conversation context
- Can export data to CSV for analysis

**User Scenario:**
Sarah opens HandoffKit dashboard, sees 40% of handoffs triggered by negative sentiment vs 30% by direct request. Drills into sentiment handoffs, notices pattern around password reset flows. Updates chatbot to handle password resets better, watches sentiment handoffs drop to 25%.

**Success Metric:** Product manager identifies and acts on optimization opportunity within first week

---

### Core User Journey 3: Custom Trigger Configuration

**As a** developer with domain-specific needs
**I want to** configure custom handoff triggers
**So that** my chatbot handles my business context appropriately

**Acceptance Criteria:**
- Can add custom keyword lists via API
- Can adjust failure threshold (1-5 attempts)
- Can adjust sentiment threshold (0-1 scale)
- Can combine multiple trigger types with AND/OR logic
- Changes take effect without redeployment

**User Scenario:**
Alex's banking chatbot needs special handling for regulatory terms. Adds custom keywords: `["regulation E", "dispute transaction", "file complaint", "FDIC"]`. Sets failure threshold to 2 for faster escalation. Sentiment threshold set to 0.6 for proactive handoff. Updates via config UI without code deployment.

**Success Metric:** Custom configuration completed in <30 minutes, working as expected

---

### Core User Journey 4: Framework Integration

**As a** developer using LangChain/LlamaIndex
**I want to** integrate HandoffKit with my existing framework
**So that** handoff logic fits naturally into my architecture

**Acceptance Criteria:**
- LangChain callback integration documented
- LlamaIndex event handler integration documented
- REST API available for non-Python systems
- Examples provided for both frameworks
- No breaking changes to existing chatbot code

**User Scenario:**
Jordan uses LlamaIndex for RAG chatbot. Follows HandoffKit LlamaIndex example, adds event handler to query engine. Handoff logic automatically evaluates after each response. Conversation context flows seamlessly to Zendesk. Zero changes to existing query logic.

**Success Metric:** Framework integration completed following examples in <2 hours

---

## Functional Requirements

### FR-1: Trigger Detection System

**Priority:** Must Have (MVP)
**Complexity:** Medium

**Description:**
Intelligent system to detect when AI should hand off to human agent based on multiple trigger types.

**Detailed Requirements:**

**FR-1.1: Direct Request Detection**
- System SHALL detect explicit requests for human agent using NLP pattern matching
- Supported patterns: "talk to human", "speak to agent", "real person", "customer service", "help me" (when frustrated)
- Detection confidence threshold: 0.8
- Must handle variations: "I want to talk to someone", "get me a real person", etc.
- Response time: <100ms per message evaluation

**FR-1.2: Failure Pattern Tracking**
- System SHALL track consecutive failed AI responses within a conversation
- Configurable failure threshold (default: 2-3 attempts)
- Failure indicators:
  - AI responds with "I don't understand"
  - User repeats same question 2+ times
  - User expresses frustration after AI response
  - AI confidence score below threshold
- Must reset failure counter after successful resolution

**FR-1.3: Critical Keyword Monitoring**
- System SHALL trigger immediate handoff on critical keywords
- Default critical keywords: "fraud", "emergency", "locked out", "dispute", "unauthorized", "stolen"
- Configurable custom keyword lists per domain
- Case-insensitive matching
- Support for phrases (not just single words)
- Instant escalation (<50ms trigger time)

**FR-1.4: Custom Rule Engine**
- System SHALL support custom trigger rules via API
- Rule syntax: IF condition THEN trigger with priority
- Conditions support: keyword match, sentiment score, conversation length, time of day, user segment
- Boolean logic: AND, OR, NOT operators
- Priority levels: immediate, high, normal
- Rules configurable via dashboard UI

**Acceptance Criteria:**
- All trigger types functional and tested
- Configurable thresholds working as specified
- Custom rules can be added and evaluated correctly
- Trigger evaluation completes in <100ms
- Triggers logged with reason and confidence score

---

### FR-2: Hybrid Sentiment Analysis

**Priority:** Must Have (MVP)
**Complexity:** Medium

**Description:**
Rule-based sentiment analysis for MVP to detect user frustration proactively without ML dependencies.

**Detailed Requirements:**

**FR-2.1: Keyword Scoring**
- System SHALL score messages based on negative keywords
- Negative keyword lists:
  - Strong negative: "terrible", "awful", "worst", "useless", "hate", "angry", "frustrated"
  - Moderate negative: "bad", "poor", "disappointing", "confused", "annoyed"
- Scoring algorithm:
  - Strong negative: -0.3 per occurrence
  - Moderate negative: -0.15 per occurrence
  - Base score: 0.5 (neutral)
  - Score range: 0.0 (very negative) to 1.0 (very positive)

**FR-2.2: Caps Lock and Punctuation Detection**
- System SHALL detect frustration signals in text formatting
- Caps lock: ALL CAPS WORDS increase negative score by 0.1 per word
- Excessive punctuation: "!!!" or "???" increase negative score by 0.05
- Combined indicators amplify (caps + punctuation = stronger signal)

**FR-2.3: Conversation Degradation Tracking**
- System SHALL track sentiment trend over conversation
- Maintain rolling window of last 5 messages
- Trigger if sentiment drops >0.3 points across window
- Example: Start 0.7 → 0.6 → 0.5 → 0.4 → 0.3 = trigger at 0.4 threshold

**FR-2.4: Domain-Specific Amplification**
- System SHALL amplify urgency for domain-specific keywords
- Banking keywords score higher: "locked", "fraud", "unauthorized", "account", "money"
- Amplification multiplier: 1.5x for domain keywords
- Configurable per domain via config file

**FR-2.5: Configurable Thresholds**
- System SHALL support configurable sentiment trigger threshold
- Default threshold: 0.3 (on 0-1 scale)
- Configurable via dashboard and API
- Changes apply to new conversations immediately

**Acceptance Criteria:**
- Sentiment scoring returns values 0.0 to 1.0
- Degradation detection triggers appropriately
- Domain keywords amplify as specified
- Threshold configuration works via UI and API
- Sentiment evaluation completes in <50ms

**Future Enhancement (V2):**
- ML-powered sentiment using DistilBERT or FinBERT
- Training on domain-specific data
- Confidence scores with model predictions

---

### FR-3: Context Preservation Module

**Priority:** Must Have (MVP)
**Complexity:** Medium

**Description:**
Comprehensive context packaging system to eliminate information loss during handoff.

**Detailed Requirements:**

**FR-3.1: Conversation History Packaging**
- System SHALL preserve complete conversation history
- Each message includes:
  - Timestamp (ISO 8601 format)
  - Speaker (user/ai)
  - Message content (full text)
  - AI confidence score (if applicable)
  - Trigger events (if any)
- Maximum history: 100 messages or 50KB (whichever comes first)
- Format: JSON structure

**FR-3.2: Metadata Collection**
- System SHALL collect and preserve metadata:
  - User ID (required)
  - Session ID (generated if not provided)
  - Channel (web/mobile/api)
  - User segment (if provided)
  - Attempted solutions (AI suggestions made)
  - Failed queries (user questions AI couldn't answer)
  - Conversation duration
  - Device/browser info (if available)

**FR-3.3: Entity Extraction**
- System SHALL extract and highlight key entities:
  - Account numbers (masked for security: ****1234)
  - Dollar amounts ($1,234.56)
  - Dates (2025-12-25, "last Tuesday")
  - Email addresses
  - Phone numbers
  - Names (user name, mentioned persons)
- Entities highlighted in conversation summary
- Regex-based extraction (no ML required for MVP)

**FR-3.4: Semantic Summarization**
- System SHALL generate AI summary of conversation
- Summary includes:
  - User's primary issue (1-2 sentences)
  - AI's attempted solutions (bullet list)
  - Current conversation state
  - Recommended next actions
- Maximum 200 words
- Uses simple template-based approach (ML optional for V2)

**FR-3.5: Format Adapters**
- System SHALL export context to helpdesk formats:
  - **Zendesk:** Ticket creation with conversation in comments
  - **Intercom:** Message format with metadata
  - **Generic JSON:** Standardized structure for custom integrations
  - **Markdown:** Human-readable format
- Adapter selection based on integration configuration

**Acceptance Criteria:**
- Complete conversation history preserved (no data loss)
- All metadata fields captured correctly
- Entities extracted and highlighted accurately
- Summary generated in <500ms
- Adapters produce valid helpdesk API payloads
- Context package <100KB for typical conversation

---

### FR-4: Smart Routing

**Priority:** Must Have (MVP - Basic), Nice to Have (Advanced)
**Complexity:** Low-Medium (Basic), High (Advanced)

**Description:**
Route handoffs to available agents with fallback mechanisms.

**Detailed Requirements (MVP - Basic):**

**FR-4.1: Agent Availability Checking**
- System SHALL check agent availability via helpdesk API
- Query available agents before routing
- Cache availability status (30 second TTL)
- Fallback to ticket creation if no agents available

**FR-4.2: Round-Robin Distribution**
- System SHALL distribute handoffs evenly across available agents
- Track last assigned agent per channel
- Next handoff goes to next available agent in rotation
- Reset rotation daily at midnight

**FR-4.3: Fallback Ticket Creation**
- System SHALL create ticket if no agents available
- Ticket priority based on trigger type:
  - Critical keywords: Urgent
  - Negative sentiment: High
  - Direct request: Normal
  - Failed attempts: Normal
- User notified: "No agents available. Ticket created. You'll hear from us within [X hours]"

**FR-4.4: Configurable Routing Rules**
- System SHALL support basic routing configuration:
  - Route to specific team/queue by keyword
  - Business hours vs after-hours routing
  - VIP user priority routing
- Configured via dashboard UI or config file

**Acceptance Criteria (MVP):**
- Agent availability check functional
- Round-robin distribution working
- Fallback ticket creation successful
- Routing rules configurable and applied correctly
- Routing decision made in <200ms

**Future Enhancement (V2 - Advanced):**
- **Skill-Based Routing:** Match user issue to agent expertise
- **Priority Queues:** VIP users, urgent issues skip queue
- **Load Balancing:** Consider agent workload, not just availability
- **Predictive Routing:** ML-based assignment for best resolution

---

### FR-5: REST API

**Priority:** Must Have (MVP)
**Complexity:** Low

**Description:**
Language/framework-agnostic HTTP API for handoff operations.

**Detailed Requirements:**

**FR-5.1: Check Endpoint**
```
POST /api/v1/check
Content-Type: application/json

Request Body:
{
  "conversation": [
    {"speaker": "user", "message": "I need help", "timestamp": "2025-12-25T10:00:00Z"},
    {"speaker": "ai", "message": "I can help you", "timestamp": "2025-12-25T10:00:05Z"}
  ],
  "current_message": "This is terrible, get me a person",
  "metadata": {
    "user_id": "123",
    "channel": "web"
  }
}

Response:
{
  "should_handoff": true,
  "trigger_reason": "negative_sentiment",
  "confidence": 0.85,
  "suggested_priority": "high"
}
```

**FR-5.2: Handoff Endpoint**
```
POST /api/v1/handoff
Content-Type: application/json

Request Body:
{
  "conversation": [...],
  "metadata": {...},
  "helpdesk": "zendesk",
  "priority": "high"
}

Response:
{
  "handoff_id": "hnd_abc123",
  "status": "assigned",
  "agent": {
    "id": "agent_456",
    "name": "Sarah"
  },
  "ticket_url": "https://support.example.com/tickets/789"
}
```

**FR-5.3: Status Endpoint**
```
GET /api/v1/handoff/{handoff_id}

Response:
{
  "handoff_id": "hnd_abc123",
  "status": "assigned",
  "agent": {...},
  "created_at": "2025-12-25T10:05:00Z",
  "updated_at": "2025-12-25T10:05:30Z"
}
```

**FR-5.4: OpenAPI Documentation**
- System SHALL provide auto-generated OpenAPI 3.0 spec
- Interactive Swagger UI at `/api/docs`
- ReDoc documentation at `/api/redoc`
- Downloadable spec at `/api/openapi.json`

**FR-5.5: Authentication**
- API key authentication required
- Header: `Authorization: Bearer {api_key}`
- API keys generated via dashboard
- Rate limiting: 100 requests/minute per key

**Acceptance Criteria:**
- All endpoints functional and tested
- OpenAPI documentation accurate and complete
- Authentication working correctly
- Rate limiting enforced
- Response times <200ms for check, <500ms for handoff

---

### FR-6: Live Handoff Feed (Dashboard)

**Priority:** Must Have (MVP)
**Complexity:** Medium

**Description:**
Real-time dashboard view of handoff events as they occur.

**Detailed Requirements:**

**FR-6.1: WebSocket Real-Time Updates**
- Dashboard SHALL receive handoff events via WebSocket
- Update latency: <1 second from event occurrence
- Auto-reconnection on connection loss
- Heartbeat every 30 seconds to maintain connection

**FR-6.2: Filterable Feed**
- Dashboard SHALL support filtering handoffs by:
  - Trigger type (sentiment/keyword/failure/direct)
  - Channel (web/mobile/api)
  - Time range (last hour/today/week/month)
  - Status (pending/assigned/resolved)
- Filters applied client-side for instant update
- Multiple filters combinable (AND logic)

**FR-6.3: Conversation Detail View**
- Clicking handoff SHALL open detail modal
- Detail view shows:
  - Full conversation history
  - Extracted entities highlighted
  - AI-generated summary
  - Trigger reason and confidence
  - Agent assignment info
  - Ticket/handoff timeline
- Modal closable with ESC key or click outside

**FR-6.4: Cross-Browser Compatibility**
- Dashboard SHALL work on:
  - Chrome 100+ (target)
  - Firefox 100+
  - Safari 15+
  - Edge 100+
- Responsive design: desktop (1920x1080), laptop (1366x768), tablet (768x1024)

**Acceptance Criteria:**
- WebSocket updates appear <1 second after event
- Filters work instantly client-side
- Detail modal loads and displays correctly
- Cross-browser testing passed
- No console errors on any supported browser

---

### FR-7: Trigger Breakdown Chart (Dashboard)

**Priority:** Must Have (MVP)
**Complexity:** Low

**Description:**
Visual analytics showing handoff trigger distribution.

**Detailed Requirements:**

**FR-7.1: Pie Chart Visualization**
- Dashboard SHALL display pie chart of trigger types:
  - Sentiment (color: red)
  - Keywords (color: orange)
  - Failed attempts (color: yellow)
  - Direct request (color: blue)
- Percentages shown on each slice
- Legend with counts: "Sentiment (45) - 40%"

**FR-7.2: Time Range Filters**
- Chart SHALL support time range selection:
  - Today (default)
  - Last 7 days
  - Last 30 days
  - Custom date range picker
- Chart updates immediately on selection
- Data cached for performance

**FR-7.3: Drill-Down to Examples**
- Clicking pie slice SHALL show handoffs for that trigger type
- Opens filtered handoff feed view
- Back button returns to chart view

**FR-7.4: CSV Export**
- Export button SHALL download CSV of trigger data
- Filename: `handoff-triggers-{date-range}.csv`
- Columns: Date, Trigger Type, Count, Percentage
- Opens in Excel/Google Sheets correctly

**Acceptance Criteria:**
- Pie chart renders correctly with accurate percentages
- Time range filters update chart data
- Drill-down opens filtered handoff feed
- CSV export downloads and opens correctly
- Chart responsive on different screen sizes

---

### FR-8: Configuration UI (Dashboard)

**Priority:** Must Have (MVP)
**Complexity:** Medium

**Description:**
Web interface for non-developer settings management.

**Detailed Requirements:**

**FR-8.1: Failure Threshold Configuration**
- UI SHALL provide slider for failure threshold
- Range: 1-5 attempts
- Default: 3 attempts
- Real-time preview: "Handoff after {N} failed attempts"
- Save button applies changes

**FR-8.2: Sentiment Threshold Configuration**
- UI SHALL provide slider for sentiment threshold
- Range: 0.0 (trigger on any negativity) to 1.0 (only extreme negativity)
- Default: 0.3
- Real-time preview: "Handoff when sentiment score below {N}"
- Visual indicator: green (happy) → red (angry)

**FR-8.3: Critical Keywords Management**
- UI SHALL provide keyword list editor
- Add keyword button opens input modal
- Keywords displayed as removable chips
- Default keywords pre-populated
- Validation: no duplicates, max 50 keywords

**FR-8.4: Helpdesk Integration Configuration**
- UI SHALL provide forms for helpdesk credentials:
  - Zendesk: subdomain, API key, email
  - Intercom: app ID, access token
  - Test connection button verifies credentials
- Credentials stored encrypted
- Option to disable integration

**FR-8.5: Test Mode Toggle**
- UI SHALL provide test mode switch
- Test mode: handoffs logged but not sent to helpdesk
- Useful for development and testing
- Visual indicator when test mode active

**Acceptance Criteria:**
- All configuration changes save successfully
- Changes apply to new handoffs immediately
- Helpdesk test connection validates correctly
- Test mode prevents actual handoff creation
- Form validation prevents invalid values

---

## Non-Functional Requirements

### NFR-1: Performance

**NFR-1.1: Trigger Detection Latency**
- Trigger evaluation SHALL complete in <100ms for 95th percentile
- Sentiment analysis SHALL complete in <50ms for 95th percentile
- Total handoff decision time SHALL be <200ms for 95th percentile
- Measured under load: 10 concurrent handoff checks

**NFR-1.2: Dashboard Real-Time Updates**
- WebSocket updates SHALL appear in <1 second from event
- Dashboard SHALL handle 100+ concurrent connections
- Chart rendering SHALL complete in <500ms
- Feed scrolling SHALL maintain 60fps

**NFR-1.3: API Response Times**
- `/check` endpoint: <200ms for 95th percentile
- `/handoff` endpoint: <500ms for 95th percentile
- `/status` endpoint: <100ms for 95th percentile
- Measured under load: 50 requests/second

**NFR-1.4: Scalability Targets**
- System SHALL handle 1,000 handoffs per day (MVP target)
- Database queries optimized for <50ms response time
- Horizontal scaling supported (stateless API design)

---

### NFR-2: Reliability & Availability

**NFR-2.1: Uptime Target**
- System SHALL maintain 99.5% uptime (MVP self-hosted)
- Graceful degradation: if dashboard down, SDK still functional
- No single point of failure in SDK (works offline if needed)

**NFR-2.2: Error Handling**
- All API errors SHALL return proper HTTP status codes and messages
- SDK SHALL handle helpdesk API failures gracefully (fallback to local logging)
- WebSocket reconnection automatic with exponential backoff
- Failed handoffs SHALL be queued and retried (max 3 attempts)

**NFR-2.3: Data Persistence**
- Handoff data SHALL be persisted in SQLite (MVP) with automatic backups
- Conversation history SHALL survive system restarts
- No data loss on graceful shutdown

---

### NFR-3: Security

**NFR-3.1: Authentication & Authorization**
- API SHALL require API key authentication for all endpoints
- Dashboard SHALL require login (username/password)
- Session timeout: 24 hours
- API keys SHALL be revocable

**NFR-3.2: Data Protection**
- Conversation data SHALL be stored encrypted at rest
- Helpdesk credentials SHALL be stored encrypted
- API keys SHALL be hashed (bcrypt)
- PII (account numbers, emails) SHALL be masked in logs

**NFR-3.3: Rate Limiting**
- API SHALL enforce rate limits: 100 requests/minute per key
- Brute force protection: max 5 failed login attempts, 15 minute lockout

**NFR-3.4: Dependency Security**
- All dependencies SHALL be from trusted sources (PyPI, npm)
- Automated security scanning in CI/CD (GitHub Dependabot)
- No known critical vulnerabilities in dependencies

---

### NFR-4: Usability & Developer Experience

**NFR-4.1: Installation Simplicity**
- SDK SHALL install with single command: `pip install handoffkit`
- Dashboard SHALL start with: `handoffkit dashboard start`
- Zero configuration required for basic usage
- Works on Python 3.9+

**NFR-4.2: Documentation Quality**
- Comprehensive README with badges, quickstart, screenshots
- API documentation (Sphinx) with examples for every endpoint
- Tutorial series: LangChain integration, LlamaIndex integration, custom chatbot
- Example projects in `/examples` directory, all working and tested

**NFR-4.3: Error Messages**
- Error messages SHALL be clear and actionable
- Examples:
  - ❌ "Authentication failed"
  - ✅ "Authentication failed: Invalid API key. Get your API key from https://dashboard/settings/api-keys"

**NFR-4.4: Observability**
- Structured logging with levels (DEBUG, INFO, WARNING, ERROR)
- Log format: JSON for machine parsing
- Optional verbose mode for debugging
- Health check endpoint: `/health`

---

### NFR-5: Maintainability & Quality

**NFR-5.1: Code Quality**
- Test coverage SHALL be >80% for SDK and API
- Linting SHALL pass: black (formatting), flake8 (style), mypy (type checking)
- No critical code smells (SonarQube or equivalent)

**NFR-5.2: CI/CD Pipeline**
- GitHub Actions SHALL run on every commit:
  - Unit tests
  - Integration tests
  - Linting
  - Security scanning
- All checks must pass before merge

**NFR-5.3: Release Process**
- Semantic versioning (MAJOR.MINOR.PATCH)
- Automated release notes generation
- PyPI releases automated via GitHub releases
- Docker images published to Docker Hub

---

### NFR-6: Compatibility & Portability

**NFR-6.1: Platform Support**
- SDK SHALL work on: Linux, macOS, Windows
- Dashboard SHALL work on: Linux, macOS (Windows via WSL)
- Docker images for all platforms: amd64, arm64

**NFR-6.2: Framework Compatibility**
- Verified integrations with:
  - LangChain 0.1.0+
  - LlamaIndex 0.9.0+
  - Custom frameworks via REST API
- Backward compatibility maintained within major versions

**NFR-6.3: Database Migration**
- Migration path from SQLite to PostgreSQL documented
- Alembic migrations for schema changes
- Zero downtime migration possible

---

## Technical Constraints & Dependencies

### Technical Constraints

**TC-1: Technology Stack (Fixed)**
- **Language:** Python 3.9+ (SDK and backend)
- **Backend Framework:** FastAPI (async support, OpenAPI generation)
- **Frontend Framework:** SvelteKit (dashboard)
- **Database:** SQLite for MVP, PostgreSQL for production
- **Real-time:** WebSocket via FastAPI

**Rationale:**
- Python: Target audience is Python AI/ML developers
- FastAPI: Modern async framework, auto-generated API docs
- SvelteKit: Fast development, smaller bundles than React
- SQLite: Zero config for MVP, easy PostgreSQL migration later

**TC-2: MVP Scope - Rule-Based Sentiment**
- Sentiment analysis SHALL use rule-based approach (no ML models)
- Avoids heavy dependencies (transformers, torch)
- Keeps installation simple and fast
- ML sentiment deferred to V2

**TC-3: Packaging Constraints**
- SDK SHALL be published to PyPI (Python Package Index)
- Installation size SHALL be <10MB (excluding optional dashboard)
- Dashboard SHALL be optional extra: `pip install handoffkit[dashboard]`

**TC-4: Open Source License**
- Project SHALL use MIT License
- Maximum adoption, permissive for commercial use
- No copyleft restrictions

---

### External Dependencies

**ED-1: Helpdesk API Dependencies**

**Zendesk Integration:**
- Zendesk API v2
- Required credentials: subdomain, email, API token
- Rate limits: 400 requests/minute (well above needs)
- Ticket creation, agent assignment, comments

**Intercom Integration:**
- Intercom API v2.8+
- Required credentials: app ID, access token
- Rate limits: 500 requests/10 seconds
- Message creation, conversation assignment

**ED-2: Python Dependencies (Backend)**
```python
fastapi==0.109.0          # Web framework
uvicorn==0.27.0           # ASGI server
websockets==12.0          # WebSocket support
httpx==0.26.0             # HTTP client
pydantic==2.5.0           # Data validation
sqlalchemy==2.0.25        # Database ORM
alembic==1.13.0           # Database migrations
python-multipart==0.0.6   # Form data parsing
python-jose[cryptography]==3.3.0  # JWT tokens
passlib[bcrypt]==1.7.4    # Password hashing
```

**ED-3: JavaScript Dependencies (Frontend)**
```javascript
"@sveltejs/kit": "^2.0.0"       // Framework
"svelte": "^4.2.0"               // UI library
"tailwindcss": "^3.4.0"          // CSS framework
"shadcn-svelte": "^0.8.0"        // UI components
"recharts": "^2.10.0"            // Charts
"socket.io-client": "^4.6.0"     // WebSocket client
```

**ED-4: Development Dependencies**
```python
pytest==7.4.0             # Testing framework
pytest-asyncio==0.21.0    # Async test support
pytest-cov==4.1.0         # Coverage reporting
black==23.7.0             # Code formatting
flake8==6.1.0             # Linting
mypy==1.5.0               # Type checking
```

**ED-5: Infrastructure Dependencies**
- **Docker:** For containerized deployment
- **GitHub Actions:** CI/CD pipeline
- **PyPI:** Package distribution
- **Docker Hub:** Container image distribution

---

### Integration Dependencies

**ID-1: LangChain Integration**
- LangChain 0.1.0+ for callback hooks
- Documentation: callback integration pattern
- Example: `examples/langchain-integration/`

**ID-2: LlamaIndex Integration**
- LlamaIndex 0.9.0+ for event handlers
- Documentation: event handler pattern
- Example: `examples/llamaindex-integration/`

**ID-3: Custom Framework Integration**
- REST API for framework-agnostic access
- Documentation: REST API integration guide
- Example: `examples/custom-integration/`

---

## Open Questions & Decisions Needed

### Architecture Phase (Next Phase)

The following questions will be addressed in the Architecture phase:

**AQ-1: Database Schema Design**
- Handoff event table structure
- Conversation history storage strategy
- Indexing strategy for fast queries
- Migration from SQLite to PostgreSQL

**AQ-2: WebSocket Architecture**
- WebSocket connection management
- Broadcasting strategy for multiple dashboard connections
- Message queue for event distribution
- Reconnection handling

**AQ-3: Sentiment Analysis Algorithm**
- Exact scoring formula for rule-based sentiment
- Keyword weight tuning based on testing
- Conversation degradation detection algorithm
- Domain-specific amplification factors

**AQ-4: API Design Details**
- Exact request/response schemas for all endpoints
- Error response format standardization
- Pagination strategy for large datasets
- API versioning strategy

**AQ-5: Security Implementation**
- API key generation and storage mechanism
- Session management implementation
- Encryption algorithm for sensitive data
- Rate limiting implementation details

---

### Implementation Phase

**IQ-1: Testing Strategy**
- Unit test coverage targets per module
- Integration test scenarios
- Mock helpdesk API setup for testing
- Performance testing methodology

**IQ-2: CI/CD Pipeline**
- GitHub Actions workflow structure
- Automated release process
- Docker image build and push strategy
- PyPI publish automation

**IQ-3: Documentation**
- Documentation generation tool (Sphinx vs MkDocs)
- Example project structure
- Tutorial content outline
- Video tutorial needs

---

## Out of Scope (V2 and Beyond)

The following features are explicitly OUT OF SCOPE for MVP (Phase 1) and deferred to V2:

**V2 Features:**
- ML-powered sentiment analysis (DistilBERT/FinBERT)
- Advanced smart routing (skill-based, priority queues, load balancing)
- Additional integrations (Salesforce, Slack, Microsoft Teams, webhooks)
- Conversation replay with step-by-step timeline
- Agent performance analytics (response time, resolution rates, CSAT)
- Channel comparison analytics
- Alerting system (Slack/email notifications for anomalies)

**V3+ Features:**
- Multi-language support (Spanish, French, German)
- A/B testing framework for trigger strategies
- Voice channel support (audio sentiment, tone analysis)
- Predictive handoff (ML early warning)
- Self-service analytics API
- Enterprise SSO integration
- Multi-tenant SaaS offering

---

## Approval & Sign-off

**PRD Status:** ✅ Complete - Ready for Architecture Phase

**Generated from:** brief.md (comprehensive technical specification)

**Next Steps:**
1. **Architecture Phase:** Create detailed system architecture document
2. **UX Phase (Recommended):** Design dashboard UI/UX patterns
3. **Epics & Stories Phase:** Break down into implementation tasks
4. **Implementation Readiness Check:** Validate all planning complete

**Review Checklist:**
- ✅ Executive summary captures vision and differentiators
- ✅ Success criteria defined with measurable metrics
- ✅ User personas detailed with pain points and goals
- ✅ User stories cover core journeys with acceptance criteria
- ✅ Functional requirements specify MVP features completely
- ✅ Non-functional requirements cover performance, security, quality
- ✅ Technical constraints and dependencies documented
- ✅ Open questions identified for architecture phase
- ✅ Out of scope features explicitly listed

**Document Control:**
- **Last Updated:** 2025-12-25
- **Version:** 1.0 (Complete)
- **Workflow Mode:** YOLO (Auto-generated)

---

*This PRD was generated using the BMad Method PRD workflow, transforming the comprehensive brief.md technical specification into a structured requirements document ready for architecture design.*
