#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 The LITS steward
# SPDX-License-Identifier: Apache-2.0

"""Validate the LITS OpenAPI contract and example payloads.

This is the repository's quality gate: it runs in CI on every push/PR and is
runnable locally with `python3 scripts/validate.py`. It is dependency-light — only
PyYAML is required; if `openapi-spec-validator` is installed it also runs a full
spec validation.

Checks:
  1. Every `openapi*.yaml` (client + admin) parses and is OpenAPI 3.1.
  2. Every internal $ref resolves, per spec.
  3. Every examples/*.json file parses.
  4. The standards register conforms to the shared control vocabulary.
  5. Every open, comment-capable artifact carries an SPDX licence header.
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def validate_spec(path: Path, yaml_mod) -> None:
    doc = yaml_mod.safe_load(path.read_text())
    if not isinstance(doc, dict):
        fail(f"{path.name} root is not a mapping")
    for key in ("openapi", "info", "paths", "components"):
        if key not in doc:
            fail(f"{path.name}: missing top-level key: {key}")
    if not str(doc["openapi"]).startswith("3.1"):
        fail(f"{path.name}: expected OpenAPI 3.1, got {doc['openapi']}")

    refs: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "$ref" and isinstance(v, str) and v.startswith("#/"):
                    refs.append(v)
                else:
                    walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(doc)

    def resolve(ref: str) -> bool:
        cur: object = doc
        for part in ref[2:].split("/"):
            part = part.replace("~1", "/").replace("~0", "~")
            if not isinstance(cur, dict) or part not in cur:
                return False
            cur = cur[part]
        return True

    broken = sorted({r for r in refs if not resolve(r)})
    if broken:
        fail(f"{path.name}: broken $refs:\n  " + "\n  ".join(broken))

    full = "spec-validator: not installed"
    try:
        from openapi_spec_validator import validate  # type: ignore

        validate(doc)
        full = "spec-validator: VALID"
    except ImportError:
        pass
    except Exception as exc:  # pragma: no cover - surfaced as a gate failure
        fail(f"{path.name}: openapi-spec-validator rejected the spec: {exc}")

    print(
        f"OK {path.name}: OpenAPI {doc['openapi']} · "
        f"{len(doc['paths'])} paths · {len(doc['components'].get('schemas', {}))} schemas · "
        f"{len(set(refs))} unique $refs (0 broken) · {full}"
    )


SPDX_REQUIRED_GLOBS = (
    "openapi*.yaml",
    "scripts/*.py",
    "conformance/*.py",
    "standards/registry.yaml",
)


def validate_standards_register(yaml_mod) -> None:
    """Validate standards/registry.yaml against the shared control vocabulary.

    The vocabulary (standards/vocabulary.v1.json) is byte-identical in four
    repositories — this one, FuroField, FuroTrack and the operator's platform.
    That is what lets a seam like the EUDR geometry rule or the E&S attestation
    category list be pinned on both sides and actually checked, rather than
    pinned in prose and left to drift.

    The checks below are the ones the vocabulary calls conformance failures:
    a resolvable standard for every control, a proof behind every "implemented"
    claim, a justification behind every "not applicable", and a citation on
    every standard. They are deliberately dependency-light — no JSON Schema
    validator is required, in keeping with the rest of this gate.
    """
    vocab_path = ROOT / "standards" / "vocabulary.v1.json"
    register_path = ROOT / "standards" / "registry.yaml"
    if not vocab_path.exists():
        fail("standards/vocabulary.v1.json is missing — the shared vocabulary is not optional")
    if not register_path.exists():
        fail("standards/registry.yaml is missing")

    vocab = json.loads(vocab_path.read_text())
    register = yaml_mod.safe_load(register_path.read_text())
    if not isinstance(register, dict):
        fail("standards/registry.yaml root is not a mapping")

    if register.get("vocabularyVersion") != vocab.get("vocabularyVersion"):
        fail(
            "standards/registry.yaml declares vocabularyVersion "
            f"{register.get('vocabularyVersion')!r} but the schema is "
            f"{vocab.get('vocabularyVersion')!r} — edit the vocabulary in all four repos or none"
        )
    if register.get("repo") != "lits":
        fail(f"standards/registry.yaml declares repo {register.get('repo')!r}, expected 'lits'")

    defs = vocab["$defs"]
    statuses = set(defs["Status"]["enum"])
    tiers = set(defs["EvidenceTier"]["enum"])
    families = set(defs["Family"]["enum"])
    applies_to = set(defs["AppliesTo"]["enum"])

    standards = register.get("standards") or []
    controls = register.get("controls") or []
    if not standards or not controls:
        fail("standards/registry.yaml carries no standards or no controls")

    problems: list[str] = []
    standard_ids: set[str] = set()

    for entry in standards:
        sid = entry.get("id")
        if not sid:
            problems.append("a standard has no id")
            continue
        if sid in standard_ids:
            problems.append(f"{sid}: duplicate standard id")
        standard_ids.add(sid)
        if entry.get("family") not in families:
            problems.append(f"{sid}: family {entry.get('family')!r} is not in the vocabulary")
        if not str(entry.get("citationUrl", "")).startswith(("http://", "https://")):
            problems.append(f"{sid}: a standard without a citation cannot be verified before print")

    control_ids: set[str] = set()
    cited_standards: set[str] = set()

    for entry in controls:
        cid = entry.get("id")
        if not cid:
            problems.append("a control has no id")
            continue
        if cid in control_ids:
            problems.append(f"{cid}: duplicate control id")
        control_ids.add(cid)

        sid = entry.get("standardId")
        cited_standards.add(sid)
        if sid not in standard_ids:
            problems.append(f"{cid}: standardId {sid!r} does not resolve")

        status = entry.get("status")
        if status not in statuses:
            problems.append(f"{cid}: status {status!r} is not in the vocabulary")
        if entry.get("evidenceTier") not in tiers:
            problems.append(f"{cid}: evidenceTier {entry.get('evidenceTier')!r} is not in the vocabulary")
        for target in entry.get("appliesTo") or []:
            if target not in applies_to:
                problems.append(f"{cid}: appliesTo {target!r} is not in the vocabulary")
        if not entry.get("appliesTo"):
            problems.append(f"{cid}: appliesTo is empty")

        paraphrase = (entry.get("paraphrase") or "").strip()
        if len(paraphrase) < 20:
            problems.append(f"{cid}: paraphrase is too short to state the requirement")
        if len(paraphrase) > 600:
            # Normative text is copyrighted; a long entry is the signal someone pasted.
            problems.append(f"{cid}: paraphrase is too long to be a paraphrase")
        if '"' in paraphrase:
            problems.append(f"{cid}: paraphrase quotes normative text, which may not be reproduced")

        if not entry.get("clauseRef"):
            problems.append(f"{cid}: no clauseRef")
        if not entry.get("owner"):
            problems.append(f"{cid}: no accountable owner")
        if not entry.get("lastReviewed"):
            problems.append(f"{cid}: no lastReviewed date")

        # A claim needs a proof.
        if status == "implemented" and not (entry.get("testRefs") or entry.get("codePaths")):
            problems.append(f"{cid}: implemented with neither a testRef nor a codePath behind it")

        # "Not applicable" and "awaiting assessment" need a stated reason.
        if status in ("not_applicable", "external_assessment") and len((entry.get("notes") or "").strip()) < 20:
            problems.append(f"{cid}: {status} without a substantive justification")

        # Cited repo paths must still exist.
        for rel in entry.get("codePaths") or []:
            if not (ROOT / rel).exists():
                problems.append(f"{cid}: codePath {rel!r} does not exist")

    orphans = standard_ids - cited_standards
    if orphans:
        problems.append(
            "standard(s) with no control, which is a name on a list rather than a register entry: "
            + ", ".join(sorted(orphans))
        )

    if problems:
        fail("standards register:\n  " + "\n  ".join(problems))

    seams = sorted({c["seamPin"] for c in controls if c.get("seamPin")})
    print(
        f"OK standards register: {len(standards)} standard(s) · {len(controls)} control(s) · "
        f"vocabulary {register['vocabularyVersion']} · pinned seams: {', '.join(seams) or 'none'}"
    )


def check_license_headers() -> None:
    """Every open, comment-capable artifact must declare its licence with an SPDX header."""
    missing: list[str] = []
    count = 0
    for pattern in SPDX_REQUIRED_GLOBS:
        for path in sorted(ROOT.glob(pattern)):
            count += 1
            head = "\n".join(path.read_text(errors="replace").splitlines()[:6])
            if "SPDX-License-Identifier" not in head:
                missing.append(str(path.relative_to(ROOT)))
    if missing:
        fail("missing SPDX-License-Identifier header in:\n  " + "\n  ".join(missing))
    print(f"OK license headers: {count} open file(s) carry an SPDX-License-Identifier")


def main() -> int:
    try:
        import yaml
    except ImportError:
        fail("PyYAML is required (pip install pyyaml)")

    specs = sorted(ROOT.glob("openapi*.yaml"))
    if not specs:
        fail("no openapi*.yaml specs found")
    for spec in specs:
        validate_spec(spec, yaml)

    # Example JSON files must parse.
    examples = sorted(glob.glob(str(ROOT / "examples" / "*.json")))
    for path in examples:
        try:
            json.loads(Path(path).read_text())
        except json.JSONDecodeError as exc:
            fail(f"invalid JSON {path}: {exc}")
    print(f"OK examples: {len(examples)} JSON payload(s) parse")

    validate_standards_register(yaml)
    check_license_headers()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
