#!/usr/bin/env python3
"""
Deploy the `risk_propagation` query (and optionally the global schema) to TigerGraph.

Loads `.env` from the repo root (override=True).

Authentication for GSQL (POST /gsql/v1/statements):
  1) **Bearer TG_TOKEN** — same JWT as REST++; TigerGraph Cloud usually accepts this for GSQL.
  2) If that returns 401, **HTTP Basic** with TG_USER + TG_PASSWORD (GraphStudio DB user).

You need **TG_TOKEN** for method (1). TG_PASSWORD is only a fallback.

Usage:
  py -3 scripts/deploy_tigergraph.py
  py -3 scripts/deploy_tigergraph.py --verify
  py -3 scripts/deploy_tigergraph.py --verify-only
  py -3 scripts/deploy_tigergraph.py --schema
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        print("Install python-dotenv: pip install python-dotenv", file=sys.stderr)
        sys.exit(1)
    load_dotenv(REPO_ROOT / ".env", override=True)


def _host() -> str:
    load_env()
    host = (os.getenv("TG_HOST") or "").strip().rstrip("/")
    if not host.startswith("http"):
        host = "https://" + host
    return host


def _parse_gsql_response(r: requests.Response) -> str:
    if not r.ok:
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            body = (r.text or "")[:1500]
            raise RuntimeError(f"HTTP {r.status_code}: {body}") from e
    ct = (r.headers.get("Content-Type") or "").lower()
    if "json" in ct:
        try:
            j = r.json()
        except json.JSONDecodeError:
            return r.text
        if isinstance(j, dict):
            if j.get("error"):
                raise RuntimeError(j.get("message") or str(j.get("results") or j))
            res = j.get("results")
            if isinstance(res, str):
                return res
            if res is not None:
                return json.dumps(res, indent=2)
        return json.dumps(j, indent=2)
    return r.text


def gsql_http(statements: str, timeout: int = 180) -> tuple[str, str]:
    """
    Run GSQL via TigerGraph 4.x `POST /gsql/v1/statements`.
    Returns (auth_method_used, output_text).
    """
    load_env()
    host = _host()
    token = (os.getenv("TG_TOKEN") or "").strip()
    user = (os.getenv("TG_USER") or os.getenv("TG_USERNAME") or "tigergraph").strip()
    password = (os.getenv("TG_PASSWORD") or "").strip().strip('"').strip("'")

    if not token and not password:
        print(
            "Set at least TG_TOKEN (recommended) or TG_USER+TG_PASSWORD in .env",
            file=sys.stderr,
        )
        sys.exit(1)

    url = f"{host}/gsql/v1/statements"
    params = {"async": "false", "timeout": str(timeout)}
    data = statements.encode("utf-8")

    # 1) Bearer JWT (same token as REST++ — works on many TigerGraph Cloud orgs)
    if token:
        r = requests.post(
            url,
            params=params,
            data=data,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "text/plain",
            },
            timeout=timeout + 60,
        )
        if r.status_code != 401:
            return ("Bearer TG_TOKEN", _parse_gsql_response(r))

    # 2) Basic auth (fallback when Cloud rejects password-based pyTigerGraph / Bearer)
    if password:
        r = requests.post(
            url,
            params=params,
            data=data,
            auth=HTTPBasicAuth(user, password),
            headers={"Content-Type": "text/plain"},
            timeout=timeout + 60,
        )
        return (f"Basic {user}", _parse_gsql_response(r))

    # Bearer was 401 and no password to try
    if token:
        r = requests.Response()
        r.status_code = 401
        r._content = b"Bearer token rejected and TG_PASSWORD not set"
        raise RuntimeError(
            "GSQL returned 401 for Bearer TG_TOKEN. "
            "Add TG_PASSWORD (GraphStudio DB user) to .env for Basic-auth fallback, "
            "or run the query manually in GraphStudio."
        )

    sys.exit(1)


def read_query_file() -> str:
    path = REPO_ROOT / "graph" / "queries" / "risk_propagation.gsql"
    if not path.is_file():
        print(f"Missing {path}", file=sys.stderr)
        sys.exit(1)
    return path.read_text(encoding="utf-8")


def read_schema_file() -> str:
    path = REPO_ROOT / "graph" / "schema" / "schema.gsql"
    if not path.is_file():
        print(f"Missing {path}", file=sys.stderr)
        sys.exit(1)
    return path.read_text(encoding="utf-8")


def deploy_schema(graph: str, dry_run: bool) -> None:
    body = read_schema_file()
    if dry_run:
        print("--- schema (dry run) ---\n", body[:800], "...\n")
        return
    print("Running global schema + CREATE GRAPH (fails if graph already exists)...")
    how, out = gsql_http(body, timeout=300)
    print(f"(auth: {how})\n{out}")


def deploy_query(graph: str, dry_run: bool) -> None:
    create_body = read_query_file()
    if dry_run:
        print("--- query (dry run) ---\n", create_body)
        return

    print(f"USE GRAPH {graph} … DROP QUERY risk_propagation (if any)")
    try:
        how, out = gsql_http(f"USE GRAPH {graph}\nDROP QUERY risk_propagation")
        print(f"(auth: {how})\n{out}")
    except Exception as e:
        print("(drop may be expected if query missing)", e)

    print("CREATE QUERY risk_propagation …")
    how, out = gsql_http(f"USE GRAPH {graph}\n{create_body}")
    print(f"(auth: {how})\n{out}")

    print("INSTALL QUERY risk_propagation …")
    how, out = gsql_http(f"USE GRAPH {graph}\nINSTALL QUERY risk_propagation")
    print(f"(auth: {how})\n{out}")

    print("Done. REST++:")
    print(f"  GET {{TG_HOST}}/restpp/query/{graph}/risk_propagation?prompt_id=<Prompt_id>")


def _first_prompt_vertex_id(vertices_json: dict) -> str | None:
    """Parse GET .../vertices/Prompt response and return one primary id."""
    if not isinstance(vertices_json, dict) or vertices_json.get("error"):
        return None
    results = vertices_json.get("results")
    if not isinstance(results, list) or not results:
        return None
    row = results[0]
    if not isinstance(row, dict):
        return None
    if row.get("v_id") and row.get("v_type") == "Prompt":
        return str(row["v_id"])
    verts = row.get("vertices")
    if isinstance(verts, dict) and "Prompt" in verts:
        pmap = verts["Prompt"]
        if isinstance(pmap, dict) and pmap:
            return next(iter(pmap.keys()))
    return None


def verify_rest() -> None:
    load_env()
    host = _host()
    graph = (os.getenv("TG_GRAPH") or "").strip()
    token = (os.getenv("TG_TOKEN") or "").strip()
    if not graph or not token:
        print("TG_GRAPH and TG_TOKEN required for --verify", file=sys.stderr)
        sys.exit(1)

    hdrs = {"Authorization": f"Bearer {token}"}
    vurl = f"{host}/restpp/graph/{graph}/vertices/Prompt"
    prompt_id = None
    try:
        rv = requests.get(vurl, headers=hdrs, timeout=15)
        if rv.ok:
            prompt_id = _first_prompt_vertex_id(rv.json())
    except Exception as e:
        print(f"(could not list Prompt vertices: {e})")

    qurl = f"{host}/restpp/query/{graph}/risk_propagation"
    if prompt_id:
        print(f"REST++ probe using existing Prompt id: {prompt_id[:36]}…")
        r = requests.get(
            qurl,
            headers=hdrs,
            params={"prompt_id": prompt_id},
            timeout=15,
        )
    else:
        print(
            "No Prompt vertices in the graph yet (normal on a fresh deploy). "
            "Using a placeholder id only checks connectivity — expect error in body.\n"
            "After you run the app once (POST /analyze), Prompt rows exist and this check will use a real id.",
        )
        r = requests.get(
            qurl,
            headers=hdrs,
            params={"prompt_id": "00000000-0000-0000-0000-000000000000"},
            timeout=15,
        )

    print("HTTP status:", r.status_code)
    body = r.text[:2500]
    print(body)

    try:
        j = r.json()
    except json.JSONDecodeError:
        return
    if isinstance(j, dict) and j.get("error") and not prompt_id:
        print(
            "\n(Above JSON error is expected until at least one /analyze run creates a Prompt vertex.)"
        )
    elif isinstance(j, dict) and j.get("error") and prompt_id:
        print("\nQuery returned error even with a real Prompt id — check GSQL / graph data:", j.get("message"))


def main() -> None:
    ap = argparse.ArgumentParser(description="Deploy TigerGraph GSQL from repo")
    ap.add_argument(
        "--schema",
        action="store_true",
        help="Run graph/schema/schema.gsql (fresh instance only)",
    )
    ap.add_argument("--dry-run", action="store_true", help="Print files only")
    ap.add_argument(
        "--verify",
        action="store_true",
        help="After deploy, probe REST++ with TG_TOKEN",
    )
    ap.add_argument(
        "--verify-only",
        action="store_true",
        help="Only probe REST++ (no GSQL)",
    )
    args = ap.parse_args()

    load_env()
    graph = (os.getenv("TG_GRAPH") or "").strip()
    if not graph:
        print("Set TG_GRAPH in .env", file=sys.stderr)
        sys.exit(1)

    if args.verify_only:
        verify_rest()
        return

    if args.dry_run:
        if args.schema:
            deploy_schema(graph, True)
        deploy_query(graph, True)
        return

    if args.schema:
        print(
            "WARNING: --schema will fail if the graph already exists. "
            "Ctrl+C within 3s to abort.",
        )
        try:
            import time

            time.sleep(3)
        except KeyboardInterrupt:
            print("Aborted.")
            sys.exit(1)

    try:
        if args.schema:
            deploy_schema(graph, False)
        deploy_query(graph, False)
    except Exception as e:
        print(f"\nDeploy failed: {e}", file=sys.stderr)
        sys.exit(1)

    if args.verify:
        verify_rest()


if __name__ == "__main__":
    main()
