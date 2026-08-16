#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 The LITS steward
# SPDX-License-Identifier: Apache-2.0

"""Validate the LITS OpenAPI contract and example payloads.

This is the repository's quality gate: it runs in CI on every push/PR and is
runnable locally with `python3 scripts/validate.py`. It is dependency-light — only
PyYAML is required; if `openapi-spec-validator` is installed it also runs a full
spec validation.

Checks:
  1. No YAML file carries a duplicated mapping key.
  2. Every `openapi*.yaml` (client + admin) parses and is OpenAPI 3.1.
  3. Every internal $ref resolves, per spec.
  4. Every tag an operation references is declared in the top-level `tags:` list.
  5. Every examples/*.json file parses.
  6. Every examples/*.json file conforms to the schema it illustrates.
  7. The standards register conforms to the shared control vocabulary.
  8. Every open, comment-capable artifact carries an SPDX licence header.
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


# Files whose duplicate keys would silently change the published contract.
DUPLICATE_KEY_GLOBS = ("openapi*.yaml", "standards/registry.yaml")


def check_duplicate_keys(yaml_mod) -> None:
    """Reject a duplicated mapping key in any contract YAML.

    YAML keeps the LAST occurrence of a duplicated key and discards the earlier
    ones without a word, so every other check in this gate runs against a
    document that is missing something the file plainly contains. That is not
    hypothetical here: `openapi.yaml` defined /authorized-keepers and
    /keepers/resolve twice, and `standards/registry.yaml` carried `notes` twice
    on one control — silently dropping the record of that control's downgrade
    from `implemented` to `partial`, while the "a status needs a reason" check
    below passed on the surviving note.

    Nothing else catches this class. The $ref, tag and register checks all read
    the already-deduplicated document, and `@redocly/cli` does not lint the
    standards register at all. A duplicate can therefore DELETE a path from the
    published contract while this gate reports OK, which is exactly what it did.
    """
    problems: list[str] = []
    scanned = 0

    for pattern in DUPLICATE_KEY_GLOBS:
        for path in sorted(ROOT.glob(pattern)):
            scanned += 1
            seen_here: list[str] = []

            class StrictLoader(yaml_mod.SafeLoader):
                pass

            def construct_mapping(loader, node, deep=False, _found=seen_here):
                first_seen: dict = {}
                for key_node, _value_node in node.value:
                    try:
                        key = loader.construct_object(key_node, deep=True)
                        hash(key)
                    except Exception:  # unhashable or unconstructable — not our concern
                        continue
                    line = key_node.start_mark.line + 1
                    if key in first_seen:
                        _found.append(
                            f"duplicate key {key!r} at line {line} "
                            f"(first defined at line {first_seen[key]}; YAML keeps the last and "
                            f"discards the rest)"
                        )
                    first_seen[key] = line
                return yaml_mod.SafeLoader.construct_mapping(loader, node, deep)

            StrictLoader.add_constructor(
                yaml_mod.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping
            )
            yaml_mod.load(path.read_text(), StrictLoader)

            problems.extend(f"{path.relative_to(ROOT)}: {p}" for p in seen_here)

    if problems:
        fail("duplicated mapping key(s):\n  " + "\n  ".join(problems))
    print(f"OK duplicate keys: {scanned} YAML file(s) carry no duplicated mapping key")


def check_tags_declared(yaml_mod) -> None:
    """Every tag an operation references must be declared at the top level.

    An undeclared tag still groups operations, so nothing breaks loudly — the
    operations simply render in an untitled section with no description, which
    is how `campaigns` and `trust-admin` both went unnoticed. Redocly's
    recommended ruleset does not enable `operation-tag-defined`, so this is the
    only place it is checked.
    """
    problems: list[str] = []
    checked = 0

    for path in sorted(ROOT.glob("openapi*.yaml")):
        doc = yaml_mod.safe_load(path.read_text())
        if not isinstance(doc, dict):
            continue
        declared = {
            t.get("name") for t in (doc.get("tags") or []) if isinstance(t, dict)
        }
        reported: set[str] = set()
        for route, operations in (doc.get("paths") or {}).items():
            if not isinstance(operations, dict):
                continue
            for method, op in operations.items():
                if not isinstance(op, dict):
                    continue
                for tag in op.get("tags") or []:
                    checked += 1
                    if tag not in declared and tag not in reported:
                        reported.add(tag)
                        problems.append(
                            f"{path.name}: {method.upper()} {route} uses tag {tag!r}, "
                            f"which is not declared in the top-level tags: list"
                        )

    if problems:
        fail("undeclared tag(s):\n  " + "\n  ".join(problems))
    print(f"OK tags: {checked} operation tag reference(s), all declared")


# Which schema each published example illustrates. An example with no entry here
# is a FAILURE, not a skip — otherwise adding an example silently opts it out of
# the check, which is the hole this closes.
EXAMPLE_SCHEMAS = {
    "register-animal.json": "AnimalRegistration",
    "record-movement.json": "Movement",
    "record-vaccination.json": "Vaccination",
    "issue-certificate.json": "CertificateRequest",
    "zone-delta.response.json": "ZoneDelta",
}

# bool is a subclass of int in Python, so integer/number must exclude it explicitly.
_JSON_TYPES = {
    "string": lambda v: isinstance(v, str),
    "boolean": lambda v: isinstance(v, bool),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "null": lambda v: v is None,
}


def _resolve_schema(schema: object, doc: dict) -> object:
    """Follow internal $refs. Bounded, so a circular $ref cannot hang the gate."""
    for _ in range(20):
        if not (isinstance(schema, dict) and isinstance(schema.get("$ref"), str)):
            return schema
        ref = schema["$ref"]
        if not ref.startswith("#/"):
            return schema
        cur: object = doc
        for part in ref[2:].split("/"):
            part = part.replace("~1", "/").replace("~0", "~")
            if not isinstance(cur, dict) or part not in cur:
                return schema
            cur = cur[part]
        schema = cur
    return schema


def _check_value(value: object, schema: object, doc: dict, where: str, problems: list) -> None:
    """Structural conformance: declared type, enum membership, required, additionalProperties."""
    schema = _resolve_schema(schema, doc)
    if not isinstance(schema, dict):
        return

    declared = schema.get("type")
    if declared is not None:
        types = declared if isinstance(declared, list) else [declared]
        if not any(_JSON_TYPES.get(t, lambda _v: True)(value) for t in types):
            got = "null" if value is None else type(value).__name__
            problems.append(f"{where}: expected type {'|'.join(str(t) for t in types)}, got {got}")
            return

    choices = schema.get("enum")
    if isinstance(choices, list) and value not in choices:
        problems.append(f"{where}: value {value!r} is not one of {choices}")

    if isinstance(value, dict):
        props = schema.get("properties") or {}
        for name in schema.get("required") or []:
            if name not in value:
                problems.append(f"{where}: missing required property {name!r}")
        if schema.get("additionalProperties") is False:
            for extra in sorted(set(value) - set(props)):
                problems.append(
                    f"{where}: property {extra!r} is not declared in the schema, "
                    f"which sets additionalProperties: false"
                )
        for key, item in value.items():
            if key in props:
                _check_value(item, props[key], doc, f"{where}.{key}", problems)
    elif isinstance(value, list):
        items = schema.get("items")
        if items is not None:
            for index, item in enumerate(value):
                _check_value(item, items, doc, f"{where}[{index}]", problems)


def check_examples_conform(yaml_mod) -> None:
    """Every published example must satisfy the schema it illustrates.

    CONTRIBUTING.md already requires this ("update any affected `examples/*.json`
    so they never drift from the contract") — until now nothing enforced it. The
    parse check above proves only that an example is JSON, so an example could
    carry an undeclared property, or a wrong-typed value, and ship green. The
    examples are the first thing an integrator copies, which makes drift here
    more expensive than drift almost anywhere else in the repo.
    """
    doc = yaml_mod.safe_load((ROOT / "openapi.yaml").read_text())
    schemas = ((doc or {}).get("components") or {}).get("schemas") or {}

    problems: list[str] = []
    checked = 0

    for path in sorted((ROOT / "examples").glob("*.json")):
        schema_name = EXAMPLE_SCHEMAS.get(path.name)
        if schema_name is None:
            problems.append(
                f"{path.name}: no entry in EXAMPLE_SCHEMAS, so this example is validated by "
                f"nothing — map it to the schema it illustrates"
            )
            continue
        if schema_name not in schemas:
            problems.append(
                f"{path.name}: mapped to schema {schema_name!r}, which openapi.yaml does not define"
            )
            continue
        _check_value(json.loads(path.read_text()), schemas[schema_name], doc, path.name, problems)
        checked += 1

    if problems:
        fail("example(s) do not conform to the contract:\n  " + "\n  ".join(problems))
    print(f"OK examples conform: {checked} payload(s) validated against their schemas")


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

    # First — every check below reads an already-deduplicated document, so a
    # duplicate key must be caught before anything is believed about the parse.
    check_duplicate_keys(yaml)

    specs = sorted(ROOT.glob("openapi*.yaml"))
    if not specs:
        fail("no openapi*.yaml specs found")
    for spec in specs:
        validate_spec(spec, yaml)

    check_tags_declared(yaml)

    # Example JSON files must parse.
    examples = sorted(glob.glob(str(ROOT / "examples" / "*.json")))
    for path in examples:
        try:
            json.loads(Path(path).read_text())
        except json.JSONDecodeError as exc:
            fail(f"invalid JSON {path}: {exc}")
    print(f"OK examples: {len(examples)} JSON payload(s) parse")

    # Parsing only proves it is JSON. This proves it is the contract's JSON.
    check_examples_conform(yaml)

    validate_standards_register(yaml)
    check_license_headers()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
