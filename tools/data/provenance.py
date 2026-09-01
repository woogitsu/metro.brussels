#!/usr/bin/env python3
"""Shared provenance helpers for downloaded and generated Metro BXL data.

Standard-library only so every downloader can reuse this module in CI and locally.
"""
from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

SENSITIVE_QUERY_KEYS = {
    "access_token", "api_key", "apikey", "auth", "authorization", "bearer",
    "key", "password", "secret", "signature", "sig", "token",
}
SENSITIVE_HEADER_KEYS = {"authorization", "proxy-authorization", "x-api-key", "api-key"}
HTML_PREFIX_RE = re.compile(br"^\s*(?:<!doctype\s+html\b|<html\b)", re.I)


class ProvenanceError(ValueError):
    """Raised when an input cannot safely be represented as provenance."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sanitize_url(url: str) -> str:
    """Remove credentials and sensitive query values while preserving useful routing info."""
    parsed = urllib.parse.urlsplit(url)
    if parsed.username is not None or parsed.password is not None:
        raise ProvenanceError("credentials in URL userinfo are not allowed")
    clean_query = []
    for key, value in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True):
        if key.lower() in SENSITIVE_QUERY_KEYS:
            clean_query.append((key, "REDACTED"))
        else:
            clean_query.append((key, value))
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path,
                                    urllib.parse.urlencode(clean_query), parsed.fragment))


def sanitize_headers(headers: Mapping[str, str] | None) -> dict[str, str]:
    """Return a safe copy; secret-bearing headers are rejected rather than persisted."""
    out: dict[str, str] = {}
    for key, value in (headers or {}).items():
        if key.lower() in SENSITIVE_HEADER_KEYS:
            raise ProvenanceError(f"sensitive header cannot be stored: {key}")
        out[str(key)] = str(value)
    return out


def _looks_like_html(data: bytes, content_type: str | None = None) -> bool:
    ct = (content_type or "").lower()
    return "text/html" in ct or bool(HTML_PREFIX_RE.match(data[:512]))


def validate_payload(data: bytes, expected_format: str, content_type: str | None = None) -> None:
    """Reject common login/error pages and validate basic format structure/magic bytes."""
    fmt = expected_format.lower().lstrip(".")
    if _looks_like_html(data, content_type):
        raise ProvenanceError(f"HTML response received where {fmt} was expected")
    if fmt == "zip":
        if not data.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
            raise ProvenanceError("invalid ZIP magic bytes")
    elif fmt == "json":
        try:
            json.loads(data.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProvenanceError("invalid JSON payload") from exc
    elif fmt in {"xml", "netex"}:
        try:
            ET.fromstring(data)
        except ET.ParseError as exc:
            raise ProvenanceError("invalid XML payload") from exc
    elif fmt in {"csv", "txt", "text"}:
        try:
            data.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ProvenanceError("text payload is not UTF-8") from exc
    elif fmt in {"pbf", "osm.pbf"}:
        if len(data) < 8:
            raise ProvenanceError("PBF payload is too small")
    elif fmt in {"gpkg", "sqlite"}:
        if not data.startswith(b"SQLite format 3\x00"):
            raise ProvenanceError("invalid GeoPackage/SQLite magic bytes")
    elif fmt in {"las", "laz"}:
        if not data.startswith(b"LASF"):
            raise ProvenanceError("invalid LAS/LAZ magic bytes")
    elif not data:
        raise ProvenanceError("empty payload")


def load_source_registry(path: str) -> dict[str, dict[str, Any]]:
    with open(path, encoding="utf-8") as handle:
        raw = json.load(handle)
    return {row["id"]: row for row in raw.get("sources", [])}


def build_manifest(
    *, source_id: str, requested_url: str, final_url: str, content: bytes,
    retrieved_at: str | None = None, dataset_version: str | None = None,
    etag: str | None = None, last_modified: str | None = None,
    mime_type: str | None = None, data_format: str,
    crs: str | None = None, parser_version: str = "raw/v1",
    artifact: bytes | None = None, transformations: Iterable[str] = (),
    input_sources: Iterable[str] = (), source_metadata: Mapping[str, Any] | None = None,
    stats: Mapping[str, Any] | None = None, query_text: str | None = None,
) -> dict[str, Any]:
    safe_requested = sanitize_url(requested_url)
    safe_final = sanitize_url(final_url)
    manifest: dict[str, Any] = {
        "manifest_version": 1,
        "source_id": source_id,
        "requested_url": safe_requested,
        "final_url": safe_final,
        "retrieved_at": retrieved_at or utc_now_iso(),
        "dataset_version": dataset_version,
        "etag": etag,
        "last_modified": last_modified,
        "content_sha256": sha256_bytes(content),
        "size_bytes": len(content),
        "mime_type": mime_type,
        "format": data_format,
        "crs": crs,
        "parser_version": parser_version,
        "artifact_sha256": sha256_bytes(artifact) if artifact is not None else None,
        "transformations": list(transformations),
        "input_sources": list(input_sources),
        "source_metadata": dict(source_metadata or {}),
        "stats": dict(stats or {}),
    }
    if query_text is not None:
        manifest["query_sha256"] = sha256_bytes(query_text.encode("utf-8"))
    return manifest


def canonical_json(data: Mapping[str, Any]) -> bytes:
    """Deterministic serialization for versioned canonical outputs/manifests."""
    return (json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def diff_manifests(old: Mapping[str, Any], new: Mapping[str, Any]) -> dict[str, Any]:
    changes: dict[str, Any] = {}
    tracked = (
        "content_sha256", "final_url", "source_id", "dataset_version", "parser_version",
        "artifact_sha256", "source_metadata", "stats", "query_sha256",
    )
    for key in tracked:
        if old.get(key) != new.get(key):
            changes[key] = {"old": old.get(key), "new": new.get(key)}
    return {
        "status": "changed" if changes else "unchanged",
        "source_changed": old.get("content_sha256") != new.get("content_sha256"),
        "url_changed": old.get("final_url") != new.get("final_url"),
        "changes": changes,
    }


def fetch_url(url: str, *, expected_format: str, headers: Mapping[str, str] | None = None,
              timeout: float = 30.0) -> tuple[bytes, str, dict[str, str]]:
    safe_headers = sanitize_headers(headers)
    request = urllib.request.Request(url, headers=safe_headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = response.read()
        final_url = response.geturl()
        response_headers = {str(k): str(v) for k, v in response.headers.items()}
    validate_payload(data, expected_format, response_headers.get("Content-Type"))
    return data, final_url, response_headers
