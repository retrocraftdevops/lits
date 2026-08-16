#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 The LITS steward
# SPDX-License-Identifier: Apache-2.0

"""Standards-vocabulary parity gate, owned by this repository.

`standards/vocabulary.v1.json` is the shared control vocabulary behind four
registers — this one, FuroField, FuroTrack and Dzinza (`standards/README.md`).
It is byte-identical in every repo, and a `seamPin` recorded on a control names
an interchange vocabulary the repos agree on. Drift is declared a conformance
failure; until now nothing *in this repository* detected it.

## What this is, and what it is not

`~/projects/FuroField/scripts/check-standards-parity.sh` already exists, works,
and reads this repo. It is the cross-repo check, and it stays authoritative for
the per-seam VALUE assertions (the EUDR hectare threshold, the E&S category
enum). This script does not duplicate that logic — vendoring a fourth copy of
the four-repo topology is the exact drift the program exists to prevent.

What this script adds is ownership: detection that runs *here*, on a runner that
has checked out only this repository, so a drift introduced in this repo is
caught by this repo's own pipeline instead of only by a sibling's.

## Standalone first

A standards repo cannot assume four sibling checkouts exist, so checks 1-3 need
nothing but this repo, and checks 4-5 report honestly when the siblings are not
there. An absent sibling is NEVER counted as agreement: it is named in the
output and in the summary line, and `--require-siblings` turns absence into a
failure for the case where you expect them (adding a seam pin locally).

## Checks

  1. `standards/vocabulary.v1.json` hashes to the canonical digest recorded in
     CANONICAL_SHA256 below.
  2. The vocabulary still has the structure the rest of this gate reads —
     `scripts/validate.py` indexes `$defs.Status.enum` and three siblings
     directly, so a vocabulary missing one of them raises a KeyError traceback
     rather than reporting a cause.
  3. `standards/registry.yaml` declares this repo (`lits`) and the same
     vocabulary version as the schema's own `const`.
  4. Every sibling checkout present carries a byte-identical vocabulary.
  5. Every `seamPin` this register declares is named by at least one sibling
     register that is present — "a pin that exists on one side only is not a
     pin; it is a claim" (docs/roadmap.md). Only a STANDARDS artifact counts;
     see STANDARDS_PATH_HINT for the radio button that used to satisfy this.

## The honest limit of check 1

A digest recorded in the same repository as the file it pins can be updated in
the same edit, so check 1 alone cannot stop a determined change — no in-repo
tripwire can. What gives it teeth is the combination:

  * a SILENT edit (no version bump) fails check 1, which is the realistic drift
    mode — a reformat, an editor rewriting the file, a hand-merged conflict;
  * a DELIBERATE edit must bump `vocabularyVersion` per standards/README.md,
    which check 3 ties to the register and check 4 ties to the siblings, so the
    change cannot land in one repo alone and still pass anywhere;
  * and the digest is printed on every run, so the value a reviewer compares
    across the four repos is in the log rather than in someone's recollection.

Exit 0 = agreement, as far as this run could see, and the summary line states
how far that was. Exit 1 = drift, with the file named.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The canonical digest of standards/vocabulary.v1.json, recorded here so this
# repository can detect drift with no sibling checkout present. Verify it by
# hand with:  sha256sum standards/vocabulary.v1.json
#
# Changing this value is changing the shared vocabulary. Per standards/README.md
# that lands byte-identically in all four repos in ONE change, with a version
# bump — never here alone.
CANONICAL_SHA256 = "737b5e9f721506cecb03560f0e2df8921db16eeb1f8a4b76c1ab6cad44e572a4"
CANONICAL_VERSION = "1.0.0"

# `$defs` entries scripts/validate.py indexes directly. Losing one of these is a
# KeyError in the gate, not a diagnosis, which is why they are checked by name.
REQUIRED_DEFS = ("Status", "EvidenceTier", "Family", "AppliesTo")

# Directory names each register repo may be checked out under, relative to the
# projects directory. `furotrack` carries two: the engine moved from
# ~/projects/furotrack/apps/api-core to ~/projects/furotech on 2026-08-12, and
# both checkouts still carry a copy of the vocabulary, so both are compared
# rather than one being guessed at.
SIBLING_DIRS = {
    "furofield": ("FuroField", "furofield"),
    "furotrack": ("furotech", "furotrack"),
    "dzinza": ("dzinza",),
}

# Pruned when searching a sibling for a seam pin: build output and dependency
# trees, which can contain a stale vendored copy of anything.
PRUNE_DIRS = {
    ".git", "node_modules", ".next", ".venv", "venv", "__pycache__", "dist",
    "build", "coverage", ".turbo", ".vercel", "out", "target", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", ".tox", "htmlcov", ".idea", ".gradle",
}
SEARCHABLE_SUFFIXES = {".ts", ".tsx", ".py", ".yaml", ".yml", ".json", ".sh"}
MAX_SEARCH_BYTES = 2 * 1024 * 1024

# A seam pin only counts when a sibling names it in a STANDARDS artifact.
#
# The search below cannot simply read each sibling's `standards/registry.yaml`,
# because only Dzinza keeps its register in that shape: FuroField's lives in
# `apps/app/lib/standards/*.ts` and the engine's in
# `apps/api-core/furotech_api/standards/*.py`. So the search stays broad by
# necessity — and a broad substring search over a whole application is how an
# incidental string satisfies a conformance obligation.
#
# That is not hypothetical. Probing this gate with the (then unlanded) pin
# `order-status` returned "named by furotrack" and exited 0. The match was
# `name="order-status"` — a RADIO-BUTTON GROUP in
# apps/web-dashboard/src/app/(dashboard)/orders/page.tsx. A form control had
# satisfied a four-repo standards obligation, and the gate said PASS.
#
# A pin is a standards artifact, so it counts when it is named in one: a path
# component containing "standards", or a register file. Verified to keep every
# genuine match for both existing pins (Dzinza's registry.yaml and standards.py,
# FuroField's lib/standards/*.ts, the engine's standards/*.py) while rejecting
# the dashboard page.
STANDARDS_PATH_HINT = "standards"
REGISTER_FILENAMES = {"registry.yaml", "registry.yml", "registry.json"}


def _is_standards_artifact(path: Path, repo_root: Path) -> bool:
    """True when `path` is somewhere a seam pin can be DECLARED, not merely typed."""
    try:
        parts = [p.lower() for p in path.relative_to(repo_root).parts]
    except ValueError:  # pragma: no cover - path outside the tree we walked
        return False
    if parts and parts[-1] in REGISTER_FILENAMES:
        return True
    return any(STANDARDS_PATH_HINT in part for part in parts)


class Report:
    """Counts failures so one run names every drift, not just the first.

    A failure is printed WHERE it happens rather than only in a summary block:
    a section that printed nothing at all is indistinguishable from a section
    that was skipped, and this gate exists to make an unmeasured thing look
    unmeasured.
    """

    def __init__(self) -> None:
        self.problems: list[str] = []

    def fail(self, msg: str) -> None:
        self.problems.append(msg)
        print(f"   FAIL {msg}")


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# 1. This repo's vocabulary against the recorded canonical digest.
# ---------------------------------------------------------------------------
def check_own_digest(report: Report) -> str | None:
    path = ROOT / "standards" / "vocabulary.v1.json"
    if not path.exists():
        report.fail(
            "standards/vocabulary.v1.json is missing — the shared vocabulary is not optional"
        )
        return None

    digest = sha256_of(path)
    if digest != CANONICAL_SHA256:
        report.fail(
            "standards/vocabulary.v1.json has DRIFTED from the canonical vocabulary.\n"
            f"       expected {CANONICAL_SHA256}\n"
            f"       found    {digest}\n"
            "       The vocabulary is edited in all four repos in one change, or in none\n"
            "       (standards/README.md, 'Changing the vocabulary'). If this change is\n"
            "       intended, bump vocabularyVersion, land the identical file in FuroField,\n"
            "       FuroTrack and Dzinza, and update CANONICAL_SHA256 in this script."
        )
    else:
        print(f"   OK  standards/vocabulary.v1.json: {digest}")
    return digest


# ---------------------------------------------------------------------------
# 2. The vocabulary's structure.
# ---------------------------------------------------------------------------
def check_own_structure(report: Report) -> dict | None:
    path = ROOT / "standards" / "vocabulary.v1.json"
    if not path.exists():
        return None
    # Count only what THIS check finds. Reading report.problems would suppress
    # this section's OK line whenever an earlier check had already failed,
    # printing an empty section that reads as "not checked".
    before = len(report.problems)
    try:
        vocab = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        report.fail(f"standards/vocabulary.v1.json is not valid JSON: {exc}")
        return None

    if not isinstance(vocab, dict):
        report.fail("standards/vocabulary.v1.json root is not an object")
        return None

    declared = vocab.get("vocabularyVersion")
    if declared != CANONICAL_VERSION:
        report.fail(
            f"standards/vocabulary.v1.json declares vocabularyVersion {declared!r}, "
            f"this gate is pinned to {CANONICAL_VERSION!r}"
        )

    # The schema pins its own version twice — as a value and as the `const` every
    # register is validated against. They must not disagree.
    const = (((vocab.get("properties") or {}).get("vocabularyVersion")) or {}).get("const")
    if const != declared:
        report.fail(
            f"standards/vocabulary.v1.json: properties.vocabularyVersion.const is {const!r} "
            f"but the document declares {declared!r} — a register can satisfy one and not the other"
        )

    repo_enum = (((vocab.get("properties") or {}).get("repo")) or {}).get("enum")
    if not isinstance(repo_enum, list) or "lits" not in repo_enum:
        report.fail(
            f"standards/vocabulary.v1.json: properties.repo.enum is {repo_enum!r}, "
            "which does not admit this repo ('lits')"
        )

    defs = vocab.get("$defs")
    if not isinstance(defs, dict):
        report.fail("standards/vocabulary.v1.json has no $defs — scripts/validate.py reads it")
        return vocab

    for name in REQUIRED_DEFS:
        entry = defs.get(name)
        if not isinstance(entry, dict):
            report.fail(f"standards/vocabulary.v1.json: $defs.{name} is missing")
            continue
        choices = entry.get("enum")
        if not isinstance(choices, list) or not choices:
            report.fail(
                f"standards/vocabulary.v1.json: $defs.{name}.enum is missing or empty — "
                "scripts/validate.py validates every register entry against it"
            )

    for name in ("StandardEntry", "ControlEntry"):
        entry = defs.get(name)
        if not isinstance(entry, dict):
            report.fail(f"standards/vocabulary.v1.json: $defs.{name} is missing")
            continue
        if entry.get("additionalProperties") is not False:
            report.fail(
                f"standards/vocabulary.v1.json: $defs.{name} no longer sets "
                "additionalProperties: false, so an undeclared field would ship unnoticed"
            )

    if len(report.problems) == before:
        enums = ", ".join(f"{n}({len(defs[n]['enum'])})" for n in REQUIRED_DEFS)
        print(f"   OK  structure: version {declared} · $defs {enums}")
    return vocab


# ---------------------------------------------------------------------------
# 3. This repo's register against the vocabulary.
# ---------------------------------------------------------------------------
def _yaml_scalar(text: str, key: str) -> str | None:
    """Read a top-level scalar without requiring PyYAML.

    This gate is deliberately dependency-free so it can run before, or without,
    the validator's PyYAML install. scripts/validate.py does the full parse.
    """
    m = re.search(rf'^{re.escape(key)}:\s*"?([^"\n#]+?)"?\s*(?:#.*)?$', text, re.MULTILINE)
    return m.group(1) if m else None


def check_own_register(report: Report) -> list[str]:
    path = ROOT / "standards" / "registry.yaml"
    if not path.exists():
        report.fail("standards/registry.yaml is missing")
        return []

    before = len(report.problems)
    text = path.read_text()
    repo = _yaml_scalar(text, "repo")
    version = _yaml_scalar(text, "vocabularyVersion")

    if repo != "lits":
        report.fail(f"standards/registry.yaml declares repo {repo!r}, expected 'lits'")
    if version != CANONICAL_VERSION:
        report.fail(
            f"standards/registry.yaml declares vocabularyVersion {version!r}, "
            f"the pinned vocabulary is {CANONICAL_VERSION!r}"
        )

    pins = sorted({m.group(1) for m in re.finditer(r"^\s*seamPin:\s*(\S+)\s*$", text, re.MULTILINE)})
    marker = "OK " if len(report.problems) == before else "   "
    print(f"   {marker} standards/registry.yaml: repo {repo} · vocabulary {version} · "
          f"{len(pins)} seam pin(s): {', '.join(pins) or 'none'}")
    return pins


# ---------------------------------------------------------------------------
# 4 + 5. Siblings, when they are there.
# ---------------------------------------------------------------------------
def resolve_siblings(projects_dir: Path) -> tuple[dict[str, Path], list[str]]:
    """Map repo id -> every checkout of it that is present. Absent ids are returned."""
    present: dict[str, Path] = {}
    absent: list[str] = []
    for repo_id, candidates in SIBLING_DIRS.items():
        found = [projects_dir / name for name in candidates if (projects_dir / name).is_dir()]
        if not found:
            absent.append(repo_id)
            continue
        for path in found:
            label = repo_id if path.name.lower() == repo_id.lower() else f"{repo_id}@{path.name}"
            present[label] = path
    return present, absent


def check_sibling_vocabularies(
    report: Report, present: dict[str, Path], absent: list[str], own_digest: str | None
) -> tuple[int, list[str]]:
    compared = 0
    not_compared: list[str] = list(absent)

    for label, path in sorted(present.items()):
        vocab = path / "standards" / "vocabulary.v1.json"
        if not vocab.exists():
            not_compared.append(f"{label} (checked out, but has no standards/vocabulary.v1.json)")
            continue
        digest = sha256_of(vocab)
        compared += 1
        if own_digest is not None and digest != own_digest:
            report.fail(
                f"{label}: {vocab} differs from this repo's vocabulary.\n"
                f"       this repo {own_digest}\n"
                f"       {label:<9} {digest}\n"
                "       The vocabulary is edited in all four repos in one change, or in none."
            )
        else:
            print(f"   OK  {label}: matches ({path})")

    for entry in not_compared:
        print(f"   --  {entry}: NOT COMPARED — no checkout found, so this run says "
              f"nothing about it")
    return compared, not_compared


def _names_pin(repo_root: Path, pins: list[str]) -> dict[str, str]:
    """Which of `pins` this checkout DECLARES, and in which file.

    Returns pin -> the repo-relative path that named it, so the evidence is in
    the log. "named by furotrack" is not checkable by a reviewer;
    "furotrack: standards/registry.yaml" is, and the difference is what caught
    the radio button described at STANDARDS_PATH_HINT above.

    `standards/vocabulary.v1.json` is excluded on purpose: its `seamPin`
    description carries 'es-attestation-category' and 'eudr-geometry' as
    examples, so counting it would report every repo as agreeing on those two
    pins purely because it holds the schema — a check that passes without
    measuring anything. Markdown is excluded for the same reason: the four
    repos share the text of standards/README.md, which names both pins.
    """
    found: dict[str, str] = {}
    remaining = set(pins)
    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [d for d in dirnames if d not in PRUNE_DIRS]
        for name in filenames:
            if name == "vocabulary.v1.json":
                continue
            path = Path(dirpath) / name
            if path.suffix not in SEARCHABLE_SUFFIXES:
                continue
            if not _is_standards_artifact(path, repo_root):
                continue
            try:
                if path.stat().st_size > MAX_SEARCH_BYTES:
                    continue
                text = path.read_text(errors="replace")
            except OSError:
                continue
            for pin in list(remaining):
                if pin in text:
                    found[pin] = str(path.relative_to(repo_root))
                    remaining.discard(pin)
            if not remaining:
                return found
    return found


def check_seam_pins(report: Report, present: dict[str, Path], pins: list[str]) -> None:
    if not pins:
        print("   --  this register declares no seam pin, so there is nothing to match")
        return
    if not present:
        print("   --  NOT COMPARED — no sibling checkout, so nothing here shows whether "
              f"{', '.join(pins)} exist on the other side")
        return

    by_pin: dict[str, list[str]] = {pin: [] for pin in pins}
    for label, path in sorted(present.items()):
        for pin, where in _names_pin(path, pins).items():
            by_pin[pin].append(f"{label}:{where}")

    for pin, repos in sorted(by_pin.items()):
        if repos:
            print(f"   OK  {pin}: declared in {', '.join(repos)}")
        else:
            report.fail(
                f"seam pin {pin!r} is declared in standards/registry.yaml and declared by NONE of "
                f"the sibling registers present ({', '.join(sorted(present))}).\n"
                "       A pin that exists on one side only is not a pin; it is a claim\n"
                "       (docs/roadmap.md, 'The cross-repo seam-pin obligation').\n"
                "       Only a STANDARDS artifact counts — a path component containing\n"
                "       'standards', or a register file. An incidental occurrence elsewhere\n"
                "       in a sibling application is not a declaration."
            )


# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--projects-dir",
        default=os.environ.get("LITS_PROJECTS_DIR", str(ROOT.parent)),
        help="directory holding the sibling checkouts (default: this repo's parent)",
    )
    parser.add_argument(
        "--require-siblings",
        action="store_true",
        help="fail when a sibling repo is not checked out, instead of reporting it as "
             "not compared. Use this locally when adding a seam pin.",
    )
    args = parser.parse_args(argv)
    projects_dir = Path(args.projects_dir).resolve()

    report = Report()
    print("LITS standards-vocabulary parity")
    print(f"  projects dir: {projects_dir}")
    print()

    print("1. This repo's vocabulary against the recorded canonical digest")
    own_digest = check_own_digest(report)
    print()

    print("2. Vocabulary structure")
    check_own_structure(report)
    print()

    print("3. This repo's register against the vocabulary")
    pins = check_own_register(report)
    print()

    present, absent = resolve_siblings(projects_dir)

    print("4. Sibling vocabularies")
    compared, not_compared = check_sibling_vocabularies(report, present, absent, own_digest)
    print()

    print("5. Seam pins")
    check_seam_pins(report, present, pins)
    print()

    if args.require_siblings and not_compared:
        report.fail(
            "--require-siblings was given and these were not compared: "
            + "; ".join(not_compared)
        )

    if report.problems:
        print(f"FAIL — {len(report.problems)} parity check(s) failed (detail above).")
        return 1

    digest_short = (own_digest or "unknown")[:8]
    if compared:
        print(
            f"PASS — vocabulary {CANONICAL_VERSION} pinned at {digest_short}…; "
            f"{compared} sibling copy/copies compared, all identical."
        )
    else:
        # An absent sibling must never read as agreement.
        print(
            f"PASS (SELF-CHECK ONLY) — vocabulary {CANONICAL_VERSION} pinned at "
            f"{digest_short}…; 0 sibling copies compared, so this run shows NOTHING about "
            "cross-repo agreement."
        )
    if not_compared:
        print(f"  NOT COMPARED: {'; '.join(not_compared)}")
        print("  Run this from a machine holding the sibling checkouts, or run "
              "~/projects/FuroField/scripts/check-standards-parity.sh, to compare them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
