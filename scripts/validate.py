#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 The ZLITS steward
# SPDX-License-Identifier: Apache-2.0

"""Validate the ZLITS OpenAPI contract and example payloads.

This is the repository's quality gate: it runs in CI on every push/PR and is
runnable locally with `python3 scripts/validate.py`. It is dependency-light — only
PyYAML is required; if `openapi-spec-validator` is installed it also runs a full
spec validation.

Checks:
  1. Every `openapi*.yaml` (client + admin) parses and is OpenAPI 3.1.
  2. Every internal $ref resolves, per spec.
  3. Every examples/*.json file parses.
  4. Every open, comment-capable artifact carries an SPDX licence header.
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


SPDX_REQUIRED_GLOBS = ("openapi*.yaml", "scripts/*.py", "conformance/*.py")


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

    check_license_headers()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
