---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
inputDocuments:
  - /home/hieutt50/projects/handoffkit/_bmad-output/prd.md
  - /home/hieutt50/projects/handoffkit/_bmad-output/architecture.md
  - /home/hieutt50/projects/handoffkit/brief.md
workflowType: 'ux-design'
lastStep: 14
project_name: 'handoffkit'
user_name: 'Hieu TRAN'
date: '2025-12-25'
status: 'complete'
---

# UX Design Specification handoffkit

**Author:** Hieu TRAN
**Date:** 2025-12-25

---

## Executive Summary

### Project Vision

HandoffKit is an open-source Python SDK and web dashboard that enables seamless AI-to-human handoffs in conversational AI systems. It provides framework-agnostic integration with intelligent detection (3-tier: rule-based + local LLM + optional cloud LLM) and context preservation, allowing frustrated or stuck users to seamlessly connect with human agents while maintaining full conversation history.

### Target Users

**Primary Personas:**

1. **Python Developer (Solo/Small Team)** - Building chatbots with LangChain/LlamaIndex, needs simple integration with 3 lines of code
2. **Solo Full-Stack Developer** - Limited time, needs zero-config solution that "just works"
3. **Product Manager/CTO** - Needs visibility into handoff patterns and metrics via dashboard for operational insights

**User Technical Profile:**
- Intermediate to advanced Python developers
- Comfortable with pip install, APIs, and documentation
- Desktop/laptop primary environment (not mobile-first)
- Values simplicity, developer experience, and "just works" solutions

### Key Design Challenges

1. **Dual-mode complexity**: Dashboard must serve both "quick glance" monitoring (live feed) and deep configuration needs without overwhelming users
2. **Real-time data presentation**: WebSocket updates need clear visual feedback without causing distraction or interface overwhelm
3. **Technical audience balance**: Show necessary technical details (confidence scores, trigger types, API keys) while maintaining visual clarity and usability

### Design Opportunities

1. **Developer-first aesthetics**: Clean, terminal-inspired design that resonates with Python developers and matches their existing tools
2. **Progressive disclosure**: Simple by default, powerful when needed - hide complexity until user explicitly needs advanced features
3. **Data visualization excellence**: Transform handoff patterns into actionable insights (trigger frequency, sentiment trends, peak times, pattern detection)

## Core User Experience

### Defining Experience

HandoffKit serves two distinct but interconnected core experiences:

**Developer Experience (SDK Integration):**
The critical user action is calling `orchestrator.should_handoff()` to determine if a conversation needs human intervention. This must be accurate (high confidence detection), fast (<150ms average), and require zero configuration to get started. Developers should integrate handoffs in 3 lines of code and have it "just work" with sensible defaults.

**Operations Experience (Dashboard Monitoring):**
The critical user action is monitoring live handoffs in real-time to understand system behavior and patterns. Product managers and CTOs should open the dashboard and immediately grasp what's happening, why handoffs are occurring, and identify actionable patterns - all within 3 seconds without reading documentation.

### Platform Strategy

**Primary Platform:** Web dashboard accessed via desktop/laptop browsers
- **Interaction Model:** Mouse/keyboard navigation with developer-tool aesthetics
- **Real-Time Architecture:** WebSocket-powered live updates (no page refresh)
- **Deployment Model:** Self-hosted alongside SDK, no external dependencies
- **Offline Support:** Not required - operational monitoring tool for active systems
- **Responsive Strategy:** Desktop-first (1280px+), tablet-readable, mobile not prioritized

### Effortless Interactions

Users should experience zero friction in these critical areas:

1. **Live Feed Auto-Updates** - New handoffs appear instantly without user action or page refresh
2. **One-Click Filtering** - Quickly filter by trigger type, time range, channel, or status without complex UI
3. **Instant Context Access** - Click any handoff to see full conversation history in expandable detail view
4. **Simple Configuration** - Adjust thresholds, keywords, and settings with immediate visual feedback
5. **API Key Management** - Generate, copy, regenerate keys with single-click actions

### Critical Success Moments

**"It Just Works" Moment (Developers):**
Developer integrates SDK with 3 lines of code, triggers first handoff, opens Zendesk/Intercom and sees the full conversation context perfectly preserved. No configuration needed. Immediate validation of value.

**"Instant Understanding" Moment (Product Managers):**
Opens dashboard for first time, immediately sees live handoff stream with clear visual indicators showing trigger reasons (frustrated user icon, keyword badge, etc.). Understands system behavior within 3 seconds without training.

**"I'm In Control" Moment (Operations):**
Adjusts sentiment threshold slider, sees live preview of how many handoffs would change, confirms change, and immediately sees impact in the live feed. Feels empowered to optimize without fear.

**"Actionable Insight" Moment (Strategic):**
Views trigger breakdown pie chart, discovers 80% of handoffs are sentiment-based, realizes AI needs prompt improvements. Dashboard transforms raw data into business action.

### Experience Principles

1. **Instant Clarity** - Users understand what's happening within 3 seconds of looking at any screen
2. **Zero Cognitive Load** - Default behavior requires no configuration, no decisions, no manual
3. **Progressive Power** - Simple by default with advanced features hidden behind clear progressive disclosure
4. **Developer-Native Aesthetics** - Visual design mirrors tools developers love (terminal, VSCode, GitHub)
5. **Real-Time Transparency** - Live updates show system behavior immediately, building trust through visibility

## Desired Emotional Response

### Primary Emotional Goals

**For Developers (SDK Integration):**
- **Confidence** - "This will work in production without surprises"
- **Relief** - "Finally, a handoff solution that just works out of the box"
- **Trust** - "The detection is accurate and won't create false positives"
- **Professional Pride** - "This is the right way to handle handoffs"

**For Product Managers/CTOs (Dashboard Users):**
- **Clarity** - "I understand what's happening immediately without training"
- **Control** - "I can optimize this system based on real data"
- **Strategic Insight** - "This data tells me exactly what to improve in my AI"
- **Operational Confidence** - "I trust this system to handle our users"

### Emotional Journey Mapping

**Discovery Phase:**
- Feeling: Cautious optimism mixed with skepticism
- Thought: "Could this finally solve our handoff problem without platform lock-in?"

**Integration Phase:**
- Feeling: Growing confidence and pleasant surprise
- Thought: "Wow, 3 lines of code and it actually works with sensible defaults"

**First Handoff Moment:**
- Feeling: Relief and validation
- Thought: "The context transferred perfectly to Zendesk - exactly what we needed!"

**Regular Usage:**
- Feeling: Trust and control
- Thought: "I understand the system behavior and can tune it precisely"

**Pattern Discovery:**
- Feeling: Strategic empowerment
- Thought: "These insights show me exactly what to improve in our AI prompts"

### Micro-Emotions

**Critical Emotional States:**

1. **Confidence > Confusion**
   - Users must always understand what's happening
   - Clear visual indicators, explicit trigger reasons
   - No mysterious black-box behavior

2. **Trust > Skepticism**
   - Accurate detection builds credibility
   - Transparent confidence scores show system reasoning
   - Consistent behavior across sessions

3. **Accomplishment > Frustration**
   - Quick wins from first integration
   - Visible success in live feed
   - Immediate feedback on configuration changes

4. **Control > Anxiety**
   - Users feel empowered to adjust thresholds
   - Preview impact before committing changes
   - Easy rollback if needed

5. **Belonging > Isolation**
   - Developer-native aesthetics create familiarity
   - Feels like "their" tool, not foreign software
   - Speaks their language (technical, precise)

### Design Implications

**To Create Confidence:**
- Show confidence scores for all detections
- Display clear trigger reasons (not just "handoff triggered")
- Provide detailed logs and transparency into decision-making

**To Build Trust:**
- Accurate detection from day one (3-tier LLM approach)
- Consistent visual language and behavior
- Real-time updates show system is working reliably

**To Enable Control:**
- Live preview of configuration changes before applying
- Sliders and visual controls (not just text inputs)
- One-click rollback to previous settings

**To Generate Insight:**
- Transform raw data into actionable visualizations
- Highlight patterns automatically (spike detection, trend analysis)
- Show "what this means" not just "what happened"

### Emotional Design Principles

1. **Transparency Builds Trust** - Show the system's reasoning at every decision point
2. **Immediate Feedback Creates Confidence** - Users see impact within seconds of any action
3. **Progressive Disclosure Reduces Anxiety** - Simple by default, detail on demand
4. **Developer Aesthetics Create Belonging** - Design language that resonates with technical users
5. **Data Becomes Insight** - Visualizations that answer "what should I do?" not just "what happened?"

## UX Pattern Analysis & Inspiration

### Inspiring Products Analysis

**GitHub (Developer Platform)**

*Why developers love it:*
- **Clean, data-dense interface** without feeling overwhelming
- **Progressive disclosure** - simple by default, detailed when needed
- **Instant visual indicators** - status badges, color coding for states
- **Live activity feed** shows real-time changes
- **Command palette** for power users (Cmd+K)

*Key UX Principles:*
- Information hierarchy through typography and spacing
- Consistent iconography and color semantics
- Context-aware actions (buttons appear when relevant)

**Datadog / Grafana (Monitoring Dashboards)**

*Why ops teams love them:*
- **Real-time updates** without refresh
- **Customizable dashboards** - users control what they see
- **Time-range filtering** - quick access to "last hour" or "last 24h"
- **Drill-down capability** - overview to detail seamlessly
- **Alert highlighting** - critical issues stand out immediately

*Key UX Principles:*
- Dark mode optimized for long monitoring sessions
- Charts that tell stories, not just display data
- Quick filters always accessible
- Anomaly detection with visual indicators

**VS Code (Developer Tool)**

*Why it's the standard:*
- **Command palette** for keyboard-driven users
- **Sidebar navigation** - collapsible, context-aware
- **Status bar** shows critical info without taking space
- **Settings UI** - both GUI and JSON for power users
- **Extension ecosystem** - progressive enhancement

*Key UX Principles:*
- Native feel on all platforms
- Fast, responsive, never blocks
- Keyboard shortcuts for everything
- Progressive complexity (simple → advanced)

### Transferable UX Patterns

**For HandoffKit Dashboard:**

**Navigation Patterns:**
1. **Sidebar Navigation (GitHub-style)**
   - Live Feed (home)
   - Analytics
   - Configuration
   - API Keys
   - Collapsible for more screen space

2. **Command Palette (VS Code-style)**
   - Quick access to any action
   - Filter handoffs by trigger type
   - Jump to configuration sections
   - Keyboard-driven efficiency

**Data Visualization Patterns:**
1. **Live Feed with Auto-Scroll (GitHub activity feed)**
   - Latest handoffs at top
   - Auto-update without refresh
   - Smooth animations for new entries
   - "Pause feed" option when investigating

2. **Time-Series Charts (Datadog-style)**
   - Handoffs over time
   - Trigger breakdown with hover details
   - Quick time-range selection (1h, 24h, 7d, 30d)
   - Anomaly highlighting

3. **Status Indicators (GitHub-style)**
   - Color-coded trigger types (sentiment = red, keyword = orange, request = blue)
   - Confidence score badges
   - Status pills (pending, assigned, resolved)

**Interaction Patterns:**
1. **Expandable Details (GitHub PR/Issue view)**
   - Click handoff to expand inline
   - Show full conversation history
   - Metadata in structured format
   - Quick actions (copy ID, view in Zendesk)

2. **Live Configuration Preview (Figma-style)**
   - Adjust threshold slider
   - Preview affected handoffs count
   - Apply/Cancel actions
   - Undo support

**Visual Design Patterns:**
1. **Developer-Native Aesthetics**
   - Monospace fonts for technical data
   - Muted color palette (not bright/saturated)
   - Dark mode optimized
   - Terminal-inspired color scheme

2. **Progressive Disclosure**
   - Simple overview by default
   - "Show more" for technical details
   - Collapsible sections
   - Keyboard shortcuts for power users

### Anti-Patterns to Avoid

**Common Dashboard Mistakes:**

1. **Information Overload**
   - *Problem:* Showing all data at once
   - *Why avoid:* Users can't find what matters
   - *HandoffKit strategy:* Progressive disclosure, smart defaults

2. **Refresh-Required Updates**
   - *Problem:* Manual page refresh to see new data
   - *Why avoid:* Breaks monitoring flow, missed events
   - *HandoffKit strategy:* WebSocket real-time updates

3. **Configuration Anxiety**
   - *Problem:* No preview, fear of breaking things
   - *Why avoid:* Users avoid optimizing settings
   - *HandoffKit strategy:* Live preview before apply, easy rollback

4. **Generic Error Messages**
   - *Problem:* "Something went wrong" without context
   - *Why avoid:* Users can't self-serve, creates support tickets
   - *HandoffKit strategy:* Specific, actionable error messages

5. **Mobile-First for Desktop Tools**
   - *Problem:* Oversimplified for desktop monitoring
   - *Why avoid:* Wastes screen space, reduces information density
   - *HandoffKit strategy:* Desktop-first, data-dense, information-rich

6. **Arbitrary Color Choices**
   - *Problem:* Colors without semantic meaning
   - *Why avoid:* Users can't quickly parse status
   - *HandoffKit strategy:* Consistent color semantics (red = negative sentiment, green = resolved, etc.)

### Design Inspiration Strategy

**What to Adopt Directly:**

1. **GitHub's Information Architecture**
   - Clean, scannable lists
   - Status indicators and badges
   - Collapsible sidebar navigation
   - *Reason:* Proven pattern developers already understand

2. **Datadog's Real-Time Updates**
   - WebSocket-powered live feed
   - Time-range quick filters
   - Pause/resume capability
   - *Reason:* Essential for monitoring dashboards

3. **VS Code's Progressive Complexity**
   - Simple by default
   - Command palette for power users
   - Settings with both GUI and advanced modes
   - *Reason:* Serves both new and power users

**What to Adapt for HandoffKit:**

1. **GitHub's Pull Request Details → Handoff Details**
   - Adapt expandable inline view
   - Modify for conversation history display
   - Add handoff-specific metadata (trigger type, confidence, sentiment)

2. **Grafana's Dashboard Customization → Configuration UI**
   - Adapt drag-and-drop for thresholds
   - Simplify for our specific use case
   - Keep slider approach, skip complex dashboard building

3. **Datadog's Alerting → Handoff Notifications**
   - Adapt alert highlighting
   - Simplify to focus on critical handoffs only
   - Skip complex alert routing (not needed for MVP)

**What to Avoid:**

1. **Complex Dashboard Builders** (Grafana's full power)
   - *Reason:* Overkill for HandoffKit's focused use case
   - *Alternative:* Fixed, well-designed layout

2. **Multi-Tenant Admin Interfaces** (SaaS platforms)
   - *Reason:* HandoffKit is self-hosted, single-tenant
   - *Alternative:* Single configuration interface

3. **Mobile-Responsive Complexity**
   - *Reason:* Desktop-first tool, mobile not priority
   - *Alternative:* Mobile-readable, not mobile-optimized

**Design Philosophy:**

Take GitHub's clean aesthetics + Datadog's real-time monitoring + VS Code's progressive complexity = HandoffKit's developer-native monitoring dashboard.

## Design System Choice

### Selected Foundation

**Themeable System: Tailwind CSS + shadcn-svelte**

*Rationale:*
- **Utility-first approach** aligns with developer-native mindset
- **shadcn-svelte components** provide accessible, customizable building blocks
- **SvelteKit integration** matches architecture decision
- **Fast development** with flexibility to customize
- **No design lock-in** - components are copied into codebase, not imported
- **Developer-friendly** - modify components as needed without fighting framework

### Design System Components

**Foundation:**
- **Tailwind CSS 3.4+** - Utility-first CSS framework
- **shadcn-svelte 0.8+** - High-quality accessible components
- **Lucide Icons** - Consistent iconography
- **Recharts** - Data visualization library

**Component Strategy:**
- Copy components from shadcn-svelte into `/src/lib/components/ui`
- Customize as needed for HandoffKit-specific requirements
- Maintain consistency through Tailwind design tokens
- Build custom components on top of base primitives

### Design Token System

**Color Palette (Terminal-Inspired Dark Theme):**

```css
/* Background */
--background: 222.2 84% 4.9%        /* #0A0E14 - Deep blue-black */
--surface: 217.2 32.6% 17.5%        /* #1F2937 - Surface cards */
--surface-hover: 215 20.2% 24.1%    /* #374151 - Hover state */

/* Text */
--foreground: 210 40% 98%           /* #F9FAFB - Primary text */
--muted-foreground: 215.4 16.3% 56.9% /* #9CA3AF - Secondary text */

/* Semantic Colors */
--primary: 217.2 91.2% 59.8%        /* #3B82F6 - Primary blue */
--success: 142.1 70.6% 45.3%        /* #10B981 - Success green */
--warning: 38 92% 50%               /* #F59E0B - Warning orange */
--danger: 0 72.2% 50.6%             /* #EF4444 - Danger red */

/* Trigger Type Colors */
--trigger-request: 217.2 91.2% 59.8%    /* Blue - Direct request */
--trigger-sentiment: 0 72.2% 50.6%      /* Red - Negative sentiment */
--trigger-keyword: 38 92% 50%           /* Orange - Keyword match */
--trigger-failure: 280 61% 50%          /* Purple - Failure tracking */
```

**Typography:**

```css
/* Font Families */
--font-sans: 'Inter', system-ui, sans-serif      /* UI text */
--font-mono: 'JetBrains Mono', monospace        /* Code, IDs, technical */

/* Font Sizes */
--text-xs: 0.75rem    /* 12px - Badges, labels */
--text-sm: 0.875rem   /* 14px - Secondary text */
--text-base: 1rem     /* 16px - Body text */
--text-lg: 1.125rem   /* 18px - Subheadings */
--text-xl: 1.25rem    /* 20px - Section titles */
--text-2xl: 1.5rem    /* 24px - Page titles */
```

**Spacing System (8px base):**
- 1 unit = 0.25rem (4px)
- 2 units = 0.5rem (8px)
- 4 units = 1rem (16px)
- 6 units = 1.5rem (24px)
- 8 units = 2rem (32px)

### Component Library

**Core Components:**

1. **Button** - Primary, secondary, ghost, danger variants
2. **Card** - Container for handoff items, configuration sections
3. **Badge** - Trigger types, status indicators, confidence scores
4. **Input** - Text inputs for configuration
5. **Select** - Dropdowns for filters
6. **Slider** - Threshold adjustments
7. **Switch** - Toggle settings on/off
8. **Table** - Structured data display
9. **Dialog** - Modals for confirmation, details
10. **Command** - Command palette (Cmd+K)
11. **Tabs** - Navigation between sections
12. **Toast** - Notifications for actions

**Custom Components:**

1. **HandoffCard** - Displays individual handoff with expandable details
2. **LiveFeed** - Real-time stream of handoffs with auto-scroll
3. **TriggerChart** - Pie chart breakdown of trigger types
4. **TimeRangeSelector** - Quick filters (1h, 24h, 7d, 30d)
5. **ConfidenceScore** - Visual representation of detection confidence
6. **ConversationViewer** - Displays chat history with speaker indicators
7. **ThresholdSlider** - Configuration slider with live preview

## Visual Foundation

### Visual Hierarchy

**Information Density:**
- **High density** for live feed (show more per screen)
- **Medium density** for analytics (balance detail and overview)
- **Low density** for configuration (clarity over speed)

**Typography Scale:**
- **H1 (24px):** Page titles - "Live Handoff Feed"
- **H2 (20px):** Section headers - "Trigger Breakdown"
- **H3 (18px):** Subsection headers - "Configuration"
- **Body (16px):** Primary content
- **Small (14px):** Secondary information, metadata
- **Tiny (12px):** Labels, badges, timestamps

**Color Semantics:**
- **Blue (#3B82F6):** Primary actions, direct request triggers
- **Red (#EF4444):** Negative sentiment, critical alerts
- **Orange (#F59E0B):** Warnings, keyword triggers
- **Green (#10B981):** Success states, resolved handoffs
- **Purple (#9333EA):** Failure tracking triggers
- **Gray shades:** Neutral states, disabled elements

### Layout System

**Grid Structure:**
- **Sidebar:** 256px fixed width, collapsible to 64px (icon-only)
- **Main content:** Flexible, min-width 640px
- **Right panel:** 384px (for expanded handoff details)
- **Max content width:** 1920px

**Responsive Breakpoints:**
- **sm:** 640px (Tablet portrait)
- **md:** 768px (Tablet landscape)
- **lg:** 1024px (Laptop)
- **xl:** 1280px (Desktop - optimal)
- **2xl:** 1536px (Large desktop)

### Iconography

**Icon Library:** Lucide Icons

**Key Icons:**
- **Menu:** Navigation toggle
- **Activity:** Live feed
- **BarChart:** Analytics
- **Settings:** Configuration
- **Key:** API keys
- **MessageCircle:** Conversation
- **AlertTriangle:** Warnings
- **CheckCircle:** Success
- **Clock:** Timestamp
- **Filter:** Filtering
- **Search:** Search
- **Copy:** Copy to clipboard

**Icon Sizing:**
- **xs:** 12px - Inline with text
- **sm:** 16px - List items, buttons
- **md:** 20px - Section headers
- **lg:** 24px - Navigation
- **xl:** 32px - Empty states

## Color Themes

### Dark Theme (Primary)

**Background Layers:**
```
Level 0 (Base):     #0A0E14  - App background
Level 1 (Surface):  #1F2937  - Cards, panels
Level 2 (Elevated): #374151  - Hover states, dropdowns
Level 3 (Overlay):  #4B5563  - Modals, tooltips
```

**Text Hierarchy:**
```
Primary:   #F9FAFB  - Main content (98% opacity)
Secondary: #E5E7EB  - Supporting text (87% opacity)
Tertiary:  #9CA3AF  - Labels, placeholders (60% opacity)
Disabled:  #6B7280  - Disabled state (38% opacity)
```

**Interactive Elements:**
```
Primary Button:    #3B82F6  - Call to action
Primary Hover:     #2563EB  - Hover state
Secondary Button:  #374151  - Secondary actions
Danger Button:     #EF4444  - Destructive actions
```

### Light Theme (Optional)

Inverse of dark theme for users preferring light mode:
```
Background: #FFFFFF
Surface: #F9FAFB
Text: #111827
```

*Note: Dark theme is primary, light theme optional for V2*

## Design Directions

### Direction 1: Terminal-Inspired (Recommended)

**Visual Language:**
- Monospace fonts for technical data
- Dark background (#0A0E14) with high contrast text
- Syntax highlighting-inspired color coding
- Minimalist borders and subtle shadows
- Green accent for success (#10B981) - terminal aesthetic

**Characteristics:**
- Feels like a developer tool, not a generic admin panel
- High information density without clutter
- Familiar to target audience (Python developers)
- Reduces eye strain for extended monitoring sessions

**Example Components:**
- Handoff cards look like terminal output blocks
- Timestamps in monospace with ms precision
- Confidence scores displayed as percentage with colored bar
- Conversation history with speaker prefixes (USER:, AI:)

### Direction 2: Data Dashboard (Alternative)

**Visual Language:**
- Card-based layout with elevation
- Emphasis on data visualization and charts
- Colorful but professional palette
- Gradient accents for visual interest

**Characteristics:**
- More approachable for non-technical stakeholders
- Emphasizes metrics and insights over raw data
- Polished, modern SaaS aesthetic

*Note: Terminal-Inspired is recommended as it better aligns with developer-native aesthetic principle*

## User Journeys

### Journey 1: First-Time Dashboard Setup

**User Goal:** Install HandoffKit, see first handoff in dashboard

**Steps:**
1. **Install SDK** - `pip install handoffkit[ml,dashboard]`
2. **Start Dashboard** - `handoffkit dashboard start`
3. **Open Browser** - Navigate to `http://localhost:8000`
4. **Generate API Key** - Click "Generate API Key" button
5. **Copy Key** - One-click copy to clipboard
6. **Integrate SDK** - Paste key into Python code
7. **Trigger Handoff** - Test chatbot interaction
8. **See Live Update** - Handoff appears in feed immediately

**Success Criteria:**
- User completes setup in under 5 minutes
- No confusion about next steps
- First handoff appears with clear explanation

### Journey 2: Investigating High Handoff Rate

**User Goal:** Understand why handoffs increased suddenly

**Steps:**
1. **Notice Spike** - Time-series chart shows sudden increase
2. **Filter by Time** - Click "Last 1 hour" to focus on spike
3. **View Breakdown** - Trigger pie chart shows 80% sentiment-based
4. **Expand Handoff** - Click first item to see details
5. **Read Conversation** - Review what user said
6. **Identify Pattern** - Multiple users saying similar frustrated phrases
7. **Adjust AI** - Realize AI prompt needs improvement
8. **Take Action** - Update AI prompts in main chatbot code

**Success Criteria:**
- User identifies root cause within 2 minutes
- Clear path from observation → insight → action
- Feels empowered to optimize system

### Journey 3: Configuring Sentiment Threshold

**User Goal:** Reduce false positive handoffs from sentiment detector

**Steps:**
1. **Navigate to Config** - Click "Configuration" in sidebar
2. **Find Sentiment** - Scroll to "Sentiment Detection" section
3. **Current Value** - See current threshold: 0.3 (30%)
4. **Preview Impact** - Move slider, see "~45 handoffs would change"
5. **Adjust Value** - Set to 0.2 (20% - more strict)
6. **Preview Again** - Now shows "~12 handoffs would change"
7. **Apply Change** - Click "Apply" button
8. **See Confirmation** - Toast notification "Threshold updated"
9. **Verify in Feed** - Fewer sentiment handoffs appear

**Success Criteria:**
- User understands current vs. new behavior
- Live preview builds confidence before applying
- Immediate feedback confirms change worked

## Component Strategy

### Component Hierarchy

**Atomic Components:**
- Button, Input, Label, Badge, Icon, Avatar
- Reusable across entire application
- Styled with Tailwind utilities
- No business logic

**Molecular Components:**
- Card, Dialog, Dropdown, Form, Table Row
- Combine atomic components
- Light business logic (e.g., form validation)
- Reusable patterns

**Organism Components:**
- HandoffCard, TriggerChart, LiveFeed, ConfigPanel
- HandoffKit-specific components
- Domain logic included
- May be page-specific

**Templates:**
- DashboardLayout, SettingsLayout, AuthLayout
- Page-level structure
- Navigation and routing
- Consistent across pages

### Key Component Specifications

**HandoffCard:**
```
Purpose: Display individual handoff with expandable details
States: Collapsed, Expanded, Loading
Props: handoff (object), onExpand (function)

Layout:
- Header: Trigger icon + type badge + timestamp
- Body: User message preview (first 100 chars)
- Footer: Confidence score + status pill + actions
- Expanded: Full conversation history + metadata
```

**LiveFeed:**
```
Purpose: Real-time stream of handoffs with auto-scroll
States: Active, Paused, Empty, Loading
Features:
- Auto-scroll to top on new handoff
- Pause button to stop auto-scroll
- Virtual scrolling for performance (>100 items)
- Skeleton loading states
```

**TriggerChart:**
```
Purpose: Pie chart breakdown of trigger types
States: Data, Empty, Loading
Features:
- Color-coded by trigger type
- Hover shows count + percentage
- Click slice to filter live feed
- Legend with toggle to show/hide types
```

## UX Patterns

### Progressive Disclosure

**Simple → Advanced:**

**Configuration Panel:**
- **Level 1 (Default):** Common settings with sliders and toggles
- **Level 2 (Advanced):** Click "Advanced" to reveal threshold decimals, regex patterns
- **Level 3 (Expert):** Click "JSON Editor" for raw configuration

**Handoff Details:**
- **Level 1:** Summary card with key info (trigger, time, status)
- **Level 2:** Click to expand - full conversation, metadata
- **Level 3:** Click "Raw JSON" to see complete API response

### Real-Time Updates

**WebSocket Integration:**
```
- New handoff → Slide in from top with animation
- Status change → Update badge with transition
- Configuration change → Reflect in UI immediately
- Connection lost → Show warning banner
- Reconnected → Show success message, resume updates
```

**Update Patterns:**
- **Append** - New items added to top of feed
- **In-place update** - Existing items update without re-rendering entire list
- **Optimistic UI** - Show changes immediately, rollback if server rejects

### Empty States

**No Handoffs Yet:**
```
Icon: MessageCircle (large, muted)
Title: "No handoffs yet"
Description: "Handoffs will appear here when triggered"
Action: "View Integration Guide" button
```

**No Results (Filtered):**
```
Icon: Filter (large, muted)
Title: "No handoffs match your filters"
Description: "Try adjusting your filter criteria"
Action: "Clear Filters" button
```

### Error Handling

**Error Message Format:**
```
[Icon] [Error Title]
[Clear description of what went wrong]
[Specific action to resolve]

Example:
⚠️  Failed to Update Threshold
The sentiment threshold could not be updated due to a connection error.
[Retry] [View Docs]
```

**Error States:**
- **Validation errors:** Inline, next to field
- **Network errors:** Toast notification with retry
- **Critical errors:** Full-page error with support link

## Responsive & Accessibility

### Responsive Strategy

**Desktop-First Approach:**

**Desktop (1280px+) - Optimal:**
- Sidebar (256px) + Main content (flexible) + Right panel (384px)
- Live feed shows 15-20 items
- Charts side-by-side
- All features accessible

**Laptop (1024px):**
- Sidebar collapses to icons (64px) on toggle
- Right panel overlays main content
- Live feed shows 12-15 items
- Charts stack vertically if needed

**Tablet (768px):**
- Sidebar becomes drawer (slides in from left)
- Single column layout
- Live feed shows 8-10 items
- Charts full-width

**Mobile (< 768px):**
- Bottom navigation bar
- Single column, simplified views
- Focus on viewing handoffs, not configuration
- *Note: Mobile is read-only for MVP, full features desktop-only*

### Accessibility Requirements

**WCAG 2.1 Level AA Compliance:**

**Color Contrast:**
- Text: Minimum 4.5:1 ratio
- Interactive elements: Minimum 3:1 ratio
- Status indicators: Never rely on color alone (use icons + text)

**Keyboard Navigation:**
- All interactive elements focusable
- Tab order logical (top to bottom, left to right)
- Focus visible (2px blue outline)
- Shortcuts: Cmd/Ctrl+K (command palette), Esc (close modals)

**Screen Readers:**
- Semantic HTML (nav, main, aside, article)
- ARIA labels for icon-only buttons
- Live regions for real-time updates
- Skip navigation links

**Interactive Targets:**
- Minimum 44x44px touch targets
- 8px spacing between targets
- Hover states for all clickable elements

**Animations:**
- Respect `prefers-reduced-motion`
- Disable auto-scroll if motion reduced
- Instant transitions instead of animations

**Forms:**
- Labels for all inputs
- Error messages associated with fields
- Required fields clearly marked
- Helpful validation messages

---

## Implementation Notes

### Performance Targets

- **Initial Load:** < 500ms
- **Time to Interactive:** < 1s
- **WebSocket Connection:** < 200ms
- **Handoff Render:** < 50ms per item
- **Chart Render:** < 100ms
- **Filter Application:** < 100ms

### Browser Support

**Primary (Full Features):**
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

**Secondary (Degraded):**
- Chrome/Edge 80-89
- Firefox 78-87
- Safari 13

**Not Supported:**
- Internet Explorer (EOL)

### Build Optimization

- Code splitting by route
- Lazy load charts library
- Virtual scrolling for long lists
- Image optimization (if any images added later)
- Tree-shaking unused components

---

## Document Status

**Completion:** ✅ All UX design specifications defined
**Ready For:** Epic and Story Creation
**Next Steps:** Use this document as input for `/bmad:bmm:workflows:create-epics-and-stories`
