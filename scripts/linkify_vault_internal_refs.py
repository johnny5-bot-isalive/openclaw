from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import quote

VAULT_ROOT = Path('/mnt/c/Users/Jaret/Obsidian/The Nexus')
SUPPORTED_EXTS = {'.md', '.html'}
SKIP_EXACT = {
    'memory/YYYY-MM-DD.md',
    'Projects/PROJECT_NAME/Project Backlog.md',
    'Projects/PROJECT_NAME/Project Kanban.md',
    'Projects/PROJECT_NAME/Project Brief.md',
}

LINK_RE = re.compile(r'\[\[[^\]]+\]\]|\[[^\]]+\]\([^\)]+\)')
CODE_RE = re.compile(r'`([^`\n]+)`')
BROKEN_CODE_LINK_RE = re.compile(r'`(?P<prefix>[^`\[]*?(?:/| ))\[(?P<text>[^\]]+\.(?:md|html))\]\((?P<url>[^)]+)\)`')
BROKEN_SLASH_LINK_RE = re.compile(r'(?P<prefix>(?:[A-Za-z0-9][A-Za-z0-9 _.-]*/)+)\[(?P<text>[^\]]+\.(?:md|html))\]\((?P<url>[^)]+)\)')
BROKEN_WORD_LINK_RE = re.compile(r'(?P<prefix>\b[A-Z][A-Za-z0-9 +&_-]* )\[(?P<text>[^\]]+\.(?:md|html))\]\((?P<url>[^)]+)\)')
ALLOWED_CHARS = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _./-#')
PLACEHOLDER_MARKERS = ('PROJECT_NAME', '<Project>', '<YYYY', 'YYYY-MM-DD', 'YYYY-MM', '<topic>', '<Project Name>')


def visible(path: Path) -> bool:
    return not any(part.startswith('.') for part in path.relative_to(VAULT_ROOT).parts)


def all_files() -> list[Path]:
    return [p for p in VAULT_ROOT.rglob('*') if p.is_file() and visible(p)]


FILES = all_files()
NOTES = [p for p in FILES if p.suffix.lower() == '.md']
BY_NAME: dict[str, list[Path]] = {}
for p in FILES:
    BY_NAME.setdefault(p.name, []).append(p)

RESOLVE_CACHE: dict[tuple[str, str], str | None] = {}


def markdown_link(from_dir: Path, target: Path, frag: str = '') -> str:
    rel = os.path.relpath(target, from_dir).replace('\\', '/')
    link = quote(rel, safe='/')
    if frag:
        link += '#' + quote(frag, safe='')
    return link


def resolve(note_path: Path, ref: str) -> str | None:
    key = (str(note_path.parent), ref)
    if key in RESOLVE_CACHE:
        return RESOLVE_CACHE[key]

    file_part, frag = (ref.split('#', 1) + [''])[:2]
    file_part = file_part.strip()
    frag = frag.strip()

    if file_part in SKIP_EXACT or file_part.startswith('/') or '://' in file_part:
        RESOLVE_CACHE[key] = None
        return None

    note_dir = note_path.parent
    candidates: list[Path] = []
    seen: set[Path] = set()

    if '/' in file_part or file_part.startswith('.'):
        rel = Path(file_part)
        base = note_dir
        while True:
            cand = (base / rel).resolve(strict=False)
            try:
                cand.relative_to(VAULT_ROOT)
            except Exception:
                pass
            else:
                if cand.exists() and cand.is_file() and cand.suffix.lower() in SUPPORTED_EXTS and cand not in seen:
                    seen.add(cand)
                    candidates.append(cand)
            if base == VAULT_ROOT:
                break
            base = base.parent

        cand = (VAULT_ROOT / rel).resolve(strict=False)
        try:
            cand.relative_to(VAULT_ROOT)
        except Exception:
            pass
        else:
            if cand.exists() and cand.is_file() and cand.suffix.lower() in SUPPORTED_EXTS and cand not in seen:
                seen.add(cand)
                candidates.append(cand)
    else:
        cand = note_dir / file_part
        if cand.exists() and cand.is_file() and cand.suffix.lower() in SUPPORTED_EXTS:
            candidates = [cand]
        else:
            matches = [p for p in BY_NAME.get(file_part, []) if p.suffix.lower() in SUPPORTED_EXTS]
            if len(matches) == 1:
                candidates = matches[:]

    if len(candidates) != 1:
        RESOLVE_CACHE[key] = None
        return None

    link = markdown_link(note_dir, candidates[0], frag)
    RESOLVE_CACHE[key] = link
    return link


def protected_ranges(line: str) -> list[tuple[int, int]]:
    ranges = [(m.start(), m.end()) for m in LINK_RE.finditer(line)]
    ranges.extend((m.start(), m.end()) for m in CODE_RE.finditer(line))
    return ranges


def in_ranges(index: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start <= index < end for start, end in ranges)


def best_resolvable_substring(note_path: Path, raw: str) -> tuple[int, int, str, str] | None:
    best: tuple[int, int, str, str] | None = None
    for start in range(len(raw)):
        if raw[start] not in '._/0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz':
            continue
        if start > 0 and raw[start - 1] == '/':
            continue
        candidate = raw[start:].strip().rstrip('.,;:')
        if not candidate or '[' in candidate or ']' in candidate or '`' in candidate:
            continue
        link = resolve(note_path, candidate)
        if link:
            trimmed_left = len(raw[start:]) - len(raw[start:].lstrip())
            actual_start = start + trimmed_left
            actual_end = actual_start + len(candidate)
            if best is None or len(candidate) > len(best[2]):
                best = (actual_start, actual_end, candidate, link)
    return best


def is_placeholder_ref(ref: str) -> bool:
    return any(marker in ref for marker in PLACEHOLDER_MARKERS)


def repair_replacement(note_path: Path, prefix: str, text: str, existing_url: str, *, code: bool) -> str | None:
    candidate = f'{prefix}{text}'.strip()
    if not candidate:
        return None

    if is_placeholder_ref(candidate):
        return f'`{candidate}`' if code else candidate

    link = resolve(note_path, candidate)
    if link:
        return f'[`{candidate}`]({link})' if code else f'[{candidate}]({link})'

    if '/' in prefix and ('/' in existing_url or '%2F' in existing_url or existing_url.startswith('..')):
        return f'[`{candidate}`]({existing_url})' if code else f'[{candidate}]({existing_url})'

    return f'`{candidate}`' if code else candidate


def repair_broken_links(note_path: Path, line: str) -> tuple[str, int]:
    count = 0

    for regex, is_code in (
        (BROKEN_CODE_LINK_RE, True),
        (BROKEN_SLASH_LINK_RE, False),
        (BROKEN_WORD_LINK_RE, False),
    ):
        while True:
            match = regex.search(line)
            if not match:
                break
            replacement = repair_replacement(
                note_path,
                match.group('prefix'),
                match.group('text'),
                match.group('url'),
                code=is_code,
            )
            if not replacement or replacement == match.group(0):
                break
            line = line[:match.start()] + replacement + line[match.end():]
            count += 1

    return line, count


def process_line(note_path: Path, line: str) -> tuple[str, int]:
    line, repaired = repair_broken_links(note_path, line)
    replacements: list[tuple[int, int, str]] = []
    ranges = protected_ranges(line)

    for match in CODE_RE.finditer(line):
        if in_ranges(match.start(), ranges):
            continue
        inner = match.group(1).strip()
        if not any(ext in inner for ext in SUPPORTED_EXTS):
            continue
        link = resolve(note_path, inner)
        if link:
            replacements.append((match.start(), match.end(), f'[`{inner}`]({link})'))

    if replacements:
        for start, end, new_text in sorted(replacements, reverse=True):
            line = line[:start] + new_text + line[end:]

    count = repaired + len(replacements)
    replacements = []
    ranges = protected_ranges(line)
    index = 0

    while index < len(line):
        if in_ranges(index, ranges):
            index += 1
            continue
        if line.startswith('http://', index) or line.startswith('https://', index):
            next_space = line.find(' ', index)
            index = len(line) if next_space == -1 else next_space + 1
            continue

        matched_ext = None
        for ext in SUPPORTED_EXTS:
            if line.startswith(ext, index):
                matched_ext = ext
                break
        if not matched_ext:
            index += 1
            continue

        left = index - 1
        while left >= 0 and line[left] in ALLOWED_CHARS:
            left -= 1
        right = index + len(matched_ext)
        if right < len(line) and line[right] == '#':
            right += 1
            while right < len(line) and line[right] in ALLOWED_CHARS:
                right += 1

        raw = line[left + 1:right]
        best = best_resolvable_substring(note_path, raw)
        if best:
            local_start, local_end, candidate, link = best
            start = left + 1 + local_start
            end = left + 1 + local_end
            replacements.append((start, end, f'[{candidate}]({link})'))
            index = right
            continue

        index = right

    if replacements:
        for start, end, new_text in sorted(replacements, reverse=True):
            line = line[:start] + new_text + line[end:]

    count += len(replacements)
    return line, count


def process_note(note_path: Path) -> tuple[bool, int]:
    lines = note_path.read_text(encoding='utf-8', errors='ignore').splitlines()
    changed = False
    replacements = 0
    output: list[str] = []
    in_frontmatter = False
    in_fence = False

    for line_no, line in enumerate(lines, start=1):
        if line_no == 1 and line.strip() == '---':
            in_frontmatter = True
            output.append(line)
            continue
        if in_frontmatter:
            output.append(line)
            if line.strip() == '---':
                in_frontmatter = False
            continue
        if line.strip().startswith('```'):
            in_fence = not in_fence
            output.append(line)
            continue
        if in_fence:
            output.append(line)
            continue

        new_line, local_count = process_line(note_path, line)
        if new_line != line:
            changed = True
            replacements += local_count
        output.append(new_line)

    if changed:
        note_path.write_text('\n'.join(output) + ('\n' if note_path.read_text(encoding='utf-8', errors='ignore').endswith('\n') else ''), encoding='utf-8')
    return changed, replacements


def main() -> None:
    changed_files = 0
    replacement_count = 0
    for note in NOTES:
        changed, replacements = process_note(note)
        if changed:
            changed_files += 1
            replacement_count += replacements
            print(f'updated {note.relative_to(VAULT_ROOT)} ({replacements} replacements)')
    print(f'changed_files={changed_files}')
    print(f'replacements={replacement_count}')


if __name__ == '__main__':
    main()
