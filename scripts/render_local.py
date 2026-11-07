# -*- coding: utf-8 -*-
"""Render a local rules snippet from the public core (single source of truth).

The file core/inspect-task-mode.md is the ONLY authority for the inspect/task
(alpha/beta) two-state rule. Never hand-edit a rendered copy: edit core and
re-render, otherwise the public and local copies drift apart.

Usage:
    python scripts/render_local.py                  # dry-run: print snippet
    python scripts/render_local.py --out FILE       # write snippet to FILE
    python scripts/render_local.py --apply FILE     # replace the section in FILE

--apply is deliberately opt-in and always writes a .bak backup first. It is
never run automatically as part of a build, so this script cannot silently
rewrite a live agent configuration.
"""
import argparse
import pathlib
import re
import shutil
import sys

# Windows consoles default to a legacy codepage (GBK/cp936); the rendered
# snippet contains CJK + emoji. Force UTF-8 bytes so a dry-run cannot die with
# UnicodeEncodeError when piped/captured (cross-process text mangling).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:
    pass

ROOT = pathlib.Path(__file__).resolve().parent.parent
CORE = ROOT / "core" / "inspect-task-mode.md"
HEADING = "### 二、顶层意图二态（解析「用 A 执行 T」）"
NEXT_HEADING = "\n### 三、"


def fail(msg):
    print("[FAIL] " + msg, file=sys.stderr)
    sys.exit(1)


def build_snippet():
    if not CORE.is_file():
        fail("core not found: %s" % CORE)
    text = CORE.read_text(encoding="utf-8")
    m = re.search(r"(?ms)^## §1[^\n]*\n(.*?)(?=^## §2|\Z)", text)
    if not m:
        fail("section '## §1' not found in core; refuse to render")
    body = m.group(1).strip()
    if not body:
        fail("section '## §1' is empty; refuse to render")
    if "mode=inspect" not in body or "mode=task" not in body:
        fail("core lost the alpha/beta markers; refuse to render a broken copy")
    if "禁止把「调用 B」作为当前测试流程的一个可选项" not in body:
        fail("core lost the hard 'no B as an option' clause; refuse to render")
    return HEADING + "\n\n" + body + "\n"


def apply_to(path, snippet):
    p = pathlib.Path(path)
    if not p.is_file():
        fail("target file not found: %s" % p)
    t = p.read_text(encoding="utf-8")
    start = t.find(HEADING)
    if start < 0:
        fail("heading not found in target; abort (no partial edit)")
    nxt = t.find(NEXT_HEADING, start)
    if nxt < 0:
        fail("next heading not found; abort (no partial edit)")
    bak = p.with_name(p.name + ".bak")
    shutil.copy2(p, bak)
    p.write_text(t[:start] + snippet.rstrip() + "\n" + t[nxt:], encoding="utf-8")
    print("[OK] applied; backup -> %s" % bak)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="write the rendered snippet to this file")
    ap.add_argument("--apply", help="replace the section inside this rules file")
    args = ap.parse_args()
    snippet = build_snippet()
    if args.apply:
        apply_to(args.apply, snippet)
    elif args.out:
        pathlib.Path(args.out).write_text(snippet, encoding="utf-8")
        print("[OK] wrote snippet -> %s" % args.out)
    else:
        sys.stdout.write(snippet)


if __name__ == "__main__":
    main()
