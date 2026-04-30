from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


DIRECT_ATS_HOSTS = {
    "greenhouse.io",
    "job-boards.greenhouse.io",
    "boards.greenhouse.io",
    "jobs.lever.co",
    "lever.co",
    "myworkdayjobs.com",
    "wd1.myworkdaysite.com",
    "icims.com",
    "careers.smartrecruiters.com",
    "jobvite.com",
    "ashbyhq.com",
}

PUBLIC_BOARD_HOSTS = {
    "indeed.com",
    "www.indeed.com",
    "linkedin.com",
    "www.linkedin.com",
    "builtin.com",
    "www.builtin.com",
    "ziprecruiter.com",
    "www.ziprecruiter.com",
    "glassdoor.com",
    "www.glassdoor.com",
    "themuse.com",
    "www.themuse.com",
}

POSITIVE_CUES = [
    "still resolves",
    "resolves",
    "still live",
    "remains live",
    "visible",
    "appears",
    "listed",
    "current openings page",
    "title/location remain aligned",
    "comp still",
    "compensation remains",
    "travel",
    "remote",
]

NEGATIVE_CUES = [
    "no longer",
    "disappeared",
    "failed to resolve",
    "stopped resolving",
    "not listed",
    "unavailable",
    "expired",
    "closed",
    "stale",
    "removed",
]


class FreshnessError(Exception):
    pass


@dataclass
class RoleRow:
    company: str
    title: str
    state: str
    rank: str
    score: str
    last_confirmed_live: str
    last_reviewed: str
    canonical_url: str
    evidence_note: str
    notes: str
    work_model: str = ""
    geography: str = ""


@dataclass
class FreshnessResult:
    role: RoleRow
    source_type: str
    source_score: float
    age_days: int
    age_score: float
    availability_score: float
    evidence_score: float
    confidence: int
    band: str
    suggestion: str
    rationale: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score freshness confidence for Emily live roles.")
    parser.add_argument("--ledger", required=True, help="Path to Role State Ledger.md")
    parser.add_argument("--shortlist", required=True, help="Path to Live Role Shortlist.md")
    parser.add_argument("--as-of", help="Scoring date in YYYY-MM-DD (defaults to today)")
    parser.add_argument("--output", help="Optional output markdown path")
    parser.add_argument("--include-nonlive", action="store_true", help="Include non-live ledger rows in the output")
    return parser.parse_args()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FreshnessError(f"Required file not found: {path}") from exc


def parse_markdown_table(markdown: str) -> list[dict[str, str]]:
    lines = [line.rstrip() for line in markdown.splitlines() if line.strip()]
    table_lines = [line for line in lines if line.strip().startswith("|")]
    if len(table_lines) < 2:
        return []
    header = [cell.strip() for cell in table_lines[0].strip().strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in table_lines[2:]:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < len(header):
            cells += [""] * (len(header) - len(cells))
        rows.append({header[i]: cells[i] for i in range(len(header))})
    return rows


def extract_table_after_heading(markdown: str, heading: str) -> list[dict[str, str]]:
    marker = f"## {heading}"
    idx = markdown.find(marker)
    if idx < 0:
        raise FreshnessError(f"Could not find heading: {heading}")
    tail = markdown[idx + len(marker):]
    return parse_markdown_table(tail)


def strip_angle_brackets(value: str) -> str:
    value = value.strip()
    if value.startswith("<") and value.endswith(">"):
        return value[1:-1]
    return value


def parse_role_rows(ledger_path: Path, shortlist_path: Path, include_nonlive: bool) -> list[RoleRow]:
    ledger_rows = extract_table_after_heading(read_text(ledger_path), "Ledger")
    shortlist_rows = extract_table_after_heading(read_text(shortlist_path), "Current live set")

    shortlist_map = {
        (row.get("Company", "").strip(), row.get("Title", "").strip()): row
        for row in shortlist_rows
    }

    rows: list[RoleRow] = []
    for row in ledger_rows:
        company = row.get("Company", "").strip()
        title = row.get("Title", "").strip()
        state = row.get("Current state", "").strip()
        shortlist_row = shortlist_map.get((company, title))
        if not include_nonlive and not shortlist_row and state not in {"new", "active", "aging"}:
            continue
        if not include_nonlive and not shortlist_row:
            continue
        rank = (shortlist_row or {}).get("Rank", row.get("Current rank", "")).strip()
        work_model = (shortlist_row or {}).get("Work model", "").strip()
        geography = (shortlist_row or {}).get("Geography", "").strip()
        rows.append(
            RoleRow(
                company=company,
                title=title,
                state=state,
                rank=rank,
                score=row.get("Score", "").strip(),
                last_confirmed_live=row.get("Last confirmed live", "").strip(),
                last_reviewed=row.get("Last reviewed", "").strip(),
                canonical_url=strip_angle_brackets(row.get("Canonical URL", "")),
                evidence_note=row.get("Evidence note", "").strip(),
                notes=row.get("Notes", "").strip(),
                work_model=work_model,
                geography=geography,
            )
        )
    rows.sort(key=lambda item: int(item.rank) if item.rank.isdigit() else math.inf)
    return rows


def parse_date(value: str, field_name: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise FreshnessError(f"Invalid {field_name} date: {value}") from exc


def infer_source_type(url: str) -> tuple[str, float, str]:
    host = urlparse(url).netloc.lower()
    if not host:
        return ("unknown", 0.55, "No canonical URL recorded.")
    if host in PUBLIC_BOARD_HOSTS or any(host.endswith(f".{name}") for name in PUBLIC_BOARD_HOSTS):
        return ("validated public board", 0.62, f"Canonical URL points to a public board host ({host}).")
    if host in DIRECT_ATS_HOSTS or any(host.endswith(f".{name}") for name in DIRECT_ATS_HOSTS):
        return ("direct ATS", 0.86, f"Canonical URL points to a direct ATS host ({host}).")
    return ("direct company posting", 0.98, f"Canonical URL points to a company-controlled host ({host}).")


def score_confirmation_age(days_since_live: int) -> tuple[float, str]:
    if days_since_live <= 0:
        return (1.0, "Confirmed live today.")
    if days_since_live == 1:
        return (0.92, "Confirmed live yesterday.")
    if days_since_live == 2:
        return (0.8, "Last live confirmation is 2 days old.")
    if days_since_live == 3:
        return (0.68, "Last live confirmation is 3 days old.")
    if days_since_live == 4:
        return (0.52, "Last live confirmation is 4 days old.")
    if days_since_live == 5:
        return (0.36, "Last live confirmation is 5 days old.")
    return (0.18, f"Last live confirmation is {days_since_live} days old.")


def cue_count(text: str, cues: list[str]) -> int:
    haystack = text.lower()
    return sum(1 for cue in cues if cue in haystack)


def score_availability(role: RoleRow) -> tuple[float, str]:
    base_by_state = {
        "new": 0.78,
        "active": 0.9,
        "aging": 0.52,
        "stale": 0.2,
        "closed": 0.0,
        "disqualified": 0.0,
        "applied": 0.0,
        "ignored": 0.0,
        "archived": 0.0,
    }
    base = base_by_state.get(role.state, 0.45)
    text = f"{role.notes} {role.evidence_note}".strip().lower()
    positives = cue_count(text, POSITIVE_CUES)
    negatives = cue_count(text, NEGATIVE_CUES)
    score = base + min(0.16, positives * 0.04) - min(0.48, negatives * 0.12)
    score = max(0.0, min(1.0, score))
    reason_bits = [f"State baseline: {role.state or 'unknown'}."]
    if positives:
        reason_bits.append(f"Positive availability cues: {positives}.")
    if negatives:
        reason_bits.append(f"Negative availability cues: {negatives}.")
    return (score, " ".join(reason_bits))


def score_evidence_quality(role: RoleRow, as_of: date) -> tuple[float, str]:
    reviewed_days = (as_of - parse_date(role.last_reviewed, "last_reviewed")).days
    text = f"{role.notes} {role.evidence_note}".lower()
    score = 0.25
    reasons: list[str] = []

    if role.evidence_note:
        score += 0.1
        reasons.append("Evidence note link is present.")
    if "direct" in text or "careers page" in text or "greenhouse" in text or "ats" in text:
        score += 0.16
        reasons.append("Evidence references the source surface directly.")
    if "title" in text or "location" in text or "remote" in text or "united states" in text:
        score += 0.14
        reasons.append("Evidence notes role-shape or geography details.")
    if "comp" in text or "salary" in text or "$" in text or "base" in text:
        score += 0.14
        reasons.append("Evidence notes compensation details.")
    if "travel" in text:
        score += 0.08
        reasons.append("Evidence notes travel constraints.")
    if reviewed_days <= 0:
        score += 0.13
        reasons.append("Last reviewed today.")
    elif reviewed_days == 1:
        score += 0.08
        reasons.append("Last reviewed yesterday.")
    elif reviewed_days >= 4:
        score -= 0.1
        reasons.append(f"Last reviewed {reviewed_days} days ago.")

    score = max(0.0, min(1.0, score))
    if not reasons:
        reasons.append("Evidence detail is sparse.")
    return (score, " ".join(reasons))


def band_for(confidence: int) -> str:
    if confidence >= 85:
        return "strong"
    if confidence >= 70:
        return "stable-watch"
    if confidence >= 50:
        return "borderline"
    return "fragile"


def suggest_action(role: RoleRow, confidence: int, days_since_live: int, availability_score: float) -> tuple[str, list[str]]:
    rationale: list[str] = []
    if role.state in {"closed", "disqualified", "applied", "ignored", "archived"}:
        rationale.append(f"Role is already in terminal state `{role.state}`.")
        return (f"Keep `{role.state}`.", rationale)

    if role.state == "stale":
        rationale.append("Role is already marked stale.")
        if confidence >= 75 and days_since_live <= 1 and availability_score >= 0.8:
            rationale.append("Fresh direct evidence is strong enough to reconsider the stale flag.")
            return ("Suggest reconsidering stale → active after direct-source reconfirmation.", rationale)
        return ("Keep stale unless a fresh direct reconfirmation appears.", rationale)

    if role.state == "aging":
        if confidence < 40 or days_since_live >= 5:
            rationale.append("Low confidence plus aging state points toward removal from the live set.")
            return ("Suggest aging → stale and removal from live shortlist unless reconfirmed now.", rationale)
        if confidence >= 82 and days_since_live <= 1 and availability_score >= 0.82:
            rationale.append("Fresh evidence is strong enough to restore active status.")
            return ("Suggest aging → active.", rationale)
        rationale.append("Evidence is mixed but not weak enough for stale.")
        return ("Keep aging; prioritize next-pass reconfirmation.", rationale)

    # new / active
    if confidence < 45 or (days_since_live >= 5 and availability_score < 0.55):
        rationale.append("Freshness confidence is too weak for a live role.")
        return ("Suggest active/new → stale unless a direct reconfirmation lands immediately.", rationale)
    if confidence < 70 or days_since_live >= 3:
        rationale.append("Live evidence is getting old or thin for an active role.")
        return ("Suggest active/new → aging pending reconfirmation.", rationale)
    rationale.append("Evidence is current enough to keep the role live.")
    return ("Keep active.", rationale)


def score_role(role: RoleRow, as_of: date) -> FreshnessResult:
    source_type, source_score, source_reason = infer_source_type(role.canonical_url)
    last_live = parse_date(role.last_confirmed_live, "last_confirmed_live")
    days_since_live = (as_of - last_live).days
    if days_since_live < 0:
        raise FreshnessError(
            f"Role {role.company} — {role.title} has last_confirmed_live in the future: {role.last_confirmed_live}"
        )
    age_score, age_reason = score_confirmation_age(days_since_live)
    availability_score, availability_reason = score_availability(role)
    evidence_score, evidence_reason = score_evidence_quality(role, as_of)

    confidence = round(
        100 * (
            0.30 * source_score
            + 0.30 * age_score
            + 0.20 * availability_score
            + 0.20 * evidence_score
        )
    )
    band = band_for(confidence)
    suggestion, suggestion_rationale = suggest_action(role, confidence, days_since_live, availability_score)
    rationale = [source_reason, age_reason, availability_reason, evidence_reason, *suggestion_rationale]
    return FreshnessResult(
        role=role,
        source_type=source_type,
        source_score=source_score,
        age_days=days_since_live,
        age_score=age_score,
        availability_score=availability_score,
        evidence_score=evidence_score,
        confidence=confidence,
        band=band,
        suggestion=suggestion,
        rationale=rationale,
    )


def build_markdown(results: list[FreshnessResult], as_of: date, ledger_path: Path, shortlist_path: Path) -> str:
    live_count = sum(1 for result in results if result.role.state in {"new", "active", "aging"})
    risky_count = sum(1 for result in results if result.band in {"borderline", "fragile"})
    suggestion_count = sum(1 for result in results if result.suggestion != "Keep active.")

    lines = [
        "---",
        'type: "project-note"',
        'status: "active"',
        f'created: "{as_of.isoformat()}"',
        'project: "Emily Job Search"',
        "---",
        f"# Role Freshness Advisory — {as_of.isoformat()}",
        "",
        "## Purpose",
        "Mechanical freshness-confidence pass for the current Emily live-role set. This is an advisory layer, not the final source-of-truth decision.",
        "",
        "## Summary",
        f"- Live roles scored: {live_count}",
        f"- Borderline or fragile roles: {risky_count}",
        f"- Roles with a non-keep suggestion: {suggestion_count}",
        "",
        "## Scoring model",
        "- Source priority: 30%",
        "- Last confirmed live age: 30%",
        "- Posting availability signal: 20%",
        "- Evidence quality: 20%",
        "",
        "## Current results",
        "| Rank | Company | State | Freshness | Band | Source type | Days since live | Suggestion |",
        "| --- | --- | --- | ---: | --- | --- | ---: | --- |",
    ]
    for result in results:
        lines.append(
            f"| {result.role.rank or '—'} | {result.role.company} | {result.role.state} | {result.confidence} | {result.band} | {result.source_type} | {result.age_days} | {result.suggestion} |"
        )

    lines.extend(["", "## Role notes"])
    for result in results:
        lines.extend([
            f"### {result.role.rank or '—'}) {result.role.company} — {result.role.title}",
            f"- **Freshness confidence:** {result.confidence}/100 ({result.band})",
            f"- **Suggested action:** {result.suggestion}",
            f"- **Source type:** {result.source_type} ({round(result.source_score * 100)}/100)",
            f"- **Confirmation age:** {result.age_days} day(s) since last confirmed live ({round(result.age_score * 100)}/100)",
            f"- **Posting availability signal:** {round(result.availability_score * 100)}/100",
            f"- **Evidence quality:** {round(result.evidence_score * 100)}/100",
            f"- **Notes:** {result.role.notes}",
        ])
        lines.extend(f"- {item}" for item in result.rationale)
        lines.append("")

    lines.extend([
        "## Guardrail",
        "- Use the direct company/ATS check as the final authority when the advisory and the live page disagree.",
        "- `aging` is the preferred downgrade when the evidence only weakens once; `stale` should usually wait for repeated failure or materially weaker confidence.",
        "",
        "## Related",
        f"- [{ledger_path.name}]({ledger_path.name.replace(' ', '%20')})",
        f"- [{shortlist_path.name}]({shortlist_path.name.replace(' ', '%20')})",
        "- [Daily Refresh Runbook](Daily%20Refresh%20Runbook.md)",
        "- [Recurring Search and Digest Plan](Recurring%20Search%20and%20Digest%20Plan.md)",
        "",
        "#emily-job-search #freshness #watchlist #generated",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    ledger_path = Path(args.ledger).resolve()
    shortlist_path = Path(args.shortlist).resolve()
    as_of = parse_date(args.as_of, "as_of") if args.as_of else date.today()

    try:
        roles = parse_role_rows(ledger_path, shortlist_path, args.include_nonlive)
        if not roles:
            raise FreshnessError("No roles were found to score.")
        results = [score_role(role, as_of) for role in roles]
        output_path = Path(args.output).resolve() if args.output else ledger_path.parent / f"Role Freshness Advisory - {as_of.isoformat()}.md"
        output_path.write_text(build_markdown(results, as_of, ledger_path, shortlist_path), encoding="utf-8")
        print(f"Wrote freshness advisory: {output_path}")
        return 0
    except FreshnessError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())


# NOTE: mechanical scoring only; direct-source evidence still wins.
