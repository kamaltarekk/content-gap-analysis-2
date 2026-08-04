# Architecture

## MVP architecture

```text
React/Vite Web
    ↓ REST
FastAPI Modular Monolith
    ├── Project & Setup
    ├── Sources & Collection
    ├── Evidence & Content
    ├── Analysis
    ├── Review
    └── Exports
        ↓
SQLite/PostgreSQL
        ↓
Playwright Collector + Anthropic/Mock Analyzer
```

## Why Claude Code is not the production runtime

Claude Code is the development agent for the repository. The user-facing tool needs deterministic runtime services. Browser collection is implemented with Playwright; structured analysis is implemented through an Anthropic adapter or mock provider.

## Modules

### Project

Owns scope, buying decision, segment, bottleneck, collection config, and state.

### Entity

Brand or competitor.

### Source

Exact URL or uploaded file. Stores status, entity, source type, collection limits, and timestamps.

### Content item

A normalized page, post, ad, review, or document chunk.

### Evidence

A traceable quote/observation linked to content and source.

### Assessment

A candidate classification, including Sales Element, confidence, and review state.

### Gap

A structured diagnostic candidate linked to evidence and root cause.

### Job

A collection or analysis execution with progress and logs.

## Collection adapters

MVP:

- same-origin website collector,
- single-page collector,
- uploaded CSV/JSON/HTML text importer.

Later:

- social browser sessions,
- Meta Ad Library adapter,
- video transcript adapter,
- review platform adapters.

## AI contract

AI returns strict JSON candidates. Deterministic code:

- validates enums,
- validates evidence IDs,
- prevents auto-approval,
- applies score rules,
- applies comparability gates,
- calculates summaries.

## Security

- Secrets only in environment variables.
- SSRF protection and domain allowlist.
- Private IP ranges blocked.
- Crawl cap and request delay.
- No login automation in MVP.
- HTML sanitization before rendering.
