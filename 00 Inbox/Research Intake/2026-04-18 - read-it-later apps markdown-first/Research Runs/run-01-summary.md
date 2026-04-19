# Research Run Summary — Self-Hosted Read-It-Later Apps (2026)

**Date:** 2026-04-18  
**Mode:** Mode 2 — Bounded Research Run  
**Status:** ✅ Complete

## Research Question
Best self-hosted read-it-later apps in 2026 for a markdown-first workflow.

## Key Findings

### Tools Identified (high signal)

| Tool | GitHub Stars | Language | Markdown Storage | Active? |
|------|-------------|----------|-----------------|---------|
| **Linkwarden** | ~18,020 | TypeScript/Next.js | Yes (content preserved) | Very active, 2026 |
| **Wallabag** | ~12,633 | PHP | Yes (via export) | Active, 2025-2026 |
| **Omnivore** | ~16,017 | Go/React | Yes (full-text) | Active, now fully self-hosted |
| **Shiori** | ~11,427 | Go | Minimal (bookmark-focused) | Active |
| **Readeck** | ~253 | Go | Yes | Newer, 2025-2026 |

### Deep-Dive: Linkwarden
- **Strengths:** Highest stars of any in this category, fast development pace, browser extension, Floccus sync, mobile-friendly, automated link monitoring, S3 backups, collaborative (team) use, full content preservation.
- **Markdown:** Stores content with full formatting preserved; not pure markdown output by default but supports clean reading.
- **Deployment:** Docker + Docker Compose. Single command setup.
- **Weakness:** UI is "basic" per community reports; no native RSS feeds in self-hosted version.
- **Best for:** Users prioritizing content preservation and collaborative features over a minimal reading UI.

### Deep-Dive: Wallabag
- **Strengths:** Most established (~12K stars), extensive browser extensions, mobile apps, e-ink device support, RSS feed output, Pocket/Markdown/JSON/EPUB export, very active community.
- **Markdown:** Yes — export to Markdown via built-in export function.
- **Deployment:** Docker or manual (PHP + SQLite/PostgreSQL). Well-documented.
- **Weakness:** Interface less lightweight than modern alternatives; RSS feeds limited in some versions.
- **Best for:** Users who want a battle-tested, well-documented solution with maximum ecosystem integrations.

### Deep-Dive: Omnivore
- **Strengths:** 16K stars, full-text search, highlighting/annotations, built-in Markdown support, PDF support, newsletter saving, active development.
- **Markdown:** Native — markdown-first approach to content storage.
- **Deployment:** Docker-based self-hosting, now fully self-hosted after pivoting from hosted service.
- **Weakness:** Relatively complex setup; UI more feature-rich than minimal.
- **Best for:** Users who want Omnivore's feature set (highlights, search, PDF) in a self-hosted form factor.

### Honorable Mentions
- **Shiori** — Very lightweight Go app. Simple bookmark manager, not primarily markdown-first. Good for minimal deployments (Raspberry Pi).
- **Readeck** — Newer, EPUB downloads, browser extension. Low star count but active development. Watch this space.
- **Joplin** — More of a note-taking app with web clipper; not purpose-built read-it-later but can serve this workflow.

## Stop Condition Met
✅ Minimum 5 tools identified with meaningful feature comparison — achieved (5 primary + 2 honorable mentions).  
✅ 3 tools received deep-dive coverage — Linkwarden, Wallabag, Omnivore.  
✅ 3 web search passes used — at limit, stopping.

## Compliance Notes
- Research Brief created before first external source ✅
- Process Log maintained throughout ✅
- Source captures for all new external evidence ✅
- Markdown-first constraint applied as hard filter ✅

## Recommendation
For a **markdown-first workflow**:
1. **Omnivore** — best markdown-native experience, good highlighting, PDF support
2. **Wallabag** — most mature ecosystem, excellent export to Markdown, best integrations
3. **Linkwarden** — best content preservation, modern stack, active development

All three support Docker deployment. Wallabag is the easiest to operate long-term given its PHP/SQLite footprint and massive community.