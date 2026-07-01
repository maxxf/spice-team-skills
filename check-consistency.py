#!/usr/bin/env python3
"""check-consistency.py — guardrail against skill divergence in spice-team-skills.

The disease this prevents: the same skill existing as multiple independently
editable copies (monolith skills/, role plugins, the Cowork authoring source),
where edits land in different copies and drift apart. That stranded the team on
a May version of weekly-reporting and split campaign-plan into two copies.

It hashes each skill's content and flags any skill that appears in more than one
location with DIFFERENT content. Single source of truth = every skill resolves to
exactly one content hash.

Usage:
  python3 check-consistency.py                          # scan repo; exit 1 on divergence
  python3 check-consistency.py --extra cowork=/path/to/Cowork/Skills  # also check authoring source

As a git pre-push hook: run with no args; a non-zero exit blocks the push.
"""
import argparse, datetime, hashlib, os, sys
from collections import defaultdict

REPO = os.path.dirname(os.path.abspath(__file__))
IGNORE_DIRS = {".venv", "__pycache__", "node_modules", ".git", ".pytest_cache"}


def skill_hash(skill_dir):
    """Stable content hash of a skill (all files, path-sorted)."""
    h = hashlib.sha256()
    files = []
    for root, dirs, fnames in os.walk(skill_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for fn in fnames:
            if fn.endswith(".pyc"):
                continue
            files.append(os.path.join(root, fn))
    for fp in sorted(files):
        h.update(os.path.relpath(fp, skill_dir).encode())
        try:
            with open(fp, "rb") as f:
                h.update(f.read())
        except OSError:
            pass
    return h.hexdigest()[:12]


def newest_mtime(skill_dir):
    times = [os.path.getmtime(os.path.join(r, f))
             for r, d, fs in os.walk(skill_dir)
             for f in fs if not any(p in r for p in IGNORE_DIRS)]
    return max(times, default=0.0)


def collect(roots):
    """skill_name -> { location_label: (hash, path, mtime) }"""
    skills = defaultdict(dict)
    for label, root in roots:
        if not os.path.isdir(root):
            continue
        for name in sorted(os.listdir(root)):
            d = os.path.join(root, name)
            if not os.path.isdir(d) or not os.path.exists(os.path.join(d, "SKILL.md")):
                continue
            skills[name][label] = (skill_hash(d), d, newest_mtime(d))
    return skills


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extra", nargs="*", default=[],
                    help="extra authoring roots: label=path (or just path)")
    args = ap.parse_args()

    roots = [("monolith", os.path.join(REPO, "skills"))]
    pdir = os.path.join(REPO, "plugins")
    if os.path.isdir(pdir):
        for p in sorted(os.listdir(pdir)):
            sd = os.path.join(pdir, p, "skills")
            if os.path.isdir(sd):
                roots.append((f"plugin:{p}", sd))
    for ex in args.extra:
        lbl, path = ex.split("=", 1) if "=" in ex else (os.path.basename(ex.rstrip("/")), ex)
        roots.append((f"extra:{lbl}", path))

    skills = collect(roots)
    divergent, dup_ok, unique = [], [], []
    for name, locs in sorted(skills.items()):
        hashes = {v[0] for v in locs.values()}
        if len(locs) == 1:
            unique.append((name, locs))
        elif len(hashes) == 1:
            dup_ok.append((name, locs))
        else:
            divergent.append((name, locs))

    print(f"Scanned {len(skills)} skills across {len(roots)} locations: {[r[0] for r in roots]}")
    print(f"  DIVERGENT (same skill, different content): {len(divergent)}")
    print(f"  duplicated-but-identical:                  {len(dup_ok)}")
    print(f"  single-location:                           {len(unique)}")

    if divergent:
        print("\n=== DIVERGENT — reconcile each to ONE source ===")
        for name, locs in divergent:
            newest = max(locs.items(), key=lambda kv: kv[1][2])[0]
            print(f"\n  {name}:")
            for lbl, (hsh, _path, mt) in sorted(locs.items()):
                stamp = datetime.datetime.fromtimestamp(mt).strftime("%Y-%m-%d %H:%M")
                print(f"    {lbl:26s} {hsh}  {stamp}{'   <- newest' if lbl == newest else ''}")

    only_plugin = [(n, l) for n, l in unique if "monolith" not in l]
    if only_plugin:
        print("\n=== ONLY in a plugin — fold into monolith BEFORE retiring the plugin ===")
        for name, locs in only_plugin:
            print(f"  {name}: {', '.join(locs)}")

    extra_only = [(n, l) for n, l in unique if list(l)[0].startswith("extra:")]
    if extra_only:
        print("\n=== ONLY in an authoring source (personal / not yet a team skill) ===")
        for name, locs in extra_only:
            print(f"  {name}: {', '.join(locs)}")

    sys.exit(1 if divergent else 0)


if __name__ == "__main__":
    main()
