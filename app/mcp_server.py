from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from elasticsearch import Elasticsearch
from fastmcp import FastMCP

mcp = FastMCP("Signal2Bug MCP Server")


ELASTIC_URL = os.getenv("ELASTIC_URL")
ELASTIC_CLOUD_ID = os.getenv("ELASTIC_CLOUD_ID")
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")
ELASTIC_USERNAME = os.getenv("ELASTIC_USERNAME")
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD")
BUG_RECORD_INDEX = os.getenv("BUG_RECORD_INDEX", "bug_intake_records")


def _make_client() -> Elasticsearch:
    if ELASTIC_CLOUD_ID and ELASTIC_API_KEY:
        return Elasticsearch(cloud_id=ELASTIC_CLOUD_ID, api_key=ELASTIC_API_KEY)
    if ELASTIC_URL and ELASTIC_API_KEY:
        return Elasticsearch(ELASTIC_URL, api_key=ELASTIC_API_KEY)
    if ELASTIC_URL and ELASTIC_USERNAME and ELASTIC_PASSWORD:
        return Elasticsearch(ELASTIC_URL, basic_auth=(ELASTIC_USERNAME, ELASTIC_PASSWORD))
    raise RuntimeError(
        "Set either (ELASTIC_CLOUD_ID + ELASTIC_API_KEY) or (ELASTIC_URL + ELASTIC_API_KEY) "
        "or (ELASTIC_URL + ELASTIC_USERNAME + ELASTIC_PASSWORD)."
    )


es = _make_client()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@mcp.tool
def create_bug_intake_record(
    title: str,
    summary: str,
    classification: str,
    severity: str,
    confidence: float,
    likely_owner_team: Optional[str] = None,
    likely_owner_service: Optional[str] = None,
    service: Optional[str] = None,
    component: Optional[str] = None,
    subsystem: Optional[str] = None,
    endpoint: Optional[str] = None,
    platform: Optional[str] = None,
    environment: Optional[str] = None,
    region: Optional[str] = None,
    release_version: Optional[str] = None,
    build_number: Optional[str] = None,
    deployment_id: Optional[str] = None,
    observed_behavior: Optional[str] = None,
    expected_behavior: Optional[str] = None,
    priority: Optional[str] = None,
    source_signal_type: Optional[str] = None,
    source_signal_text: Optional[str] = None,
    duplicate_of: Optional[str] = None,
    related_incidents: Optional[List[str]] = None,
    evidence_sources: Optional[List[str]] = None,
    top_evidence: Optional[List[str]] = None,
    recommended_next_step: Optional[str] = None,
    missing_information: Optional[List[str]] = None,
    labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Create a structured bug intake record in Elasticsearch.

    Use this tool only when:
    - the issue is classified as Regression or New issue,
    - confidence is high,
    - and no active duplicate exists.

    Do not use this tool for known active duplicates.
    """

    record_id = f"intake-{uuid4().hex[:12]}"
    review_status = "needs_review" if confidence < 85 else "pending_triage_review"

    doc = {
        "record_id": record_id,
        "created_at": _now_iso(),
        "created_by": "signal2bug-agent",
        "agent_version": "v1",
        "source_signal_type": source_signal_type or "unknown",
        "source_signal_text": source_signal_text,
        "title": title,
        "summary": summary,
        "description": summary,
        "classification": classification,
        "severity": severity,
        "priority": priority,
        "confidence": confidence,
        "likely_owner_team": likely_owner_team,
        "likely_owner_service": likely_owner_service,
        "service": service,
        "component": component,
        "subsystem": subsystem,
        "endpoint": endpoint,
        "platform": platform,
        "environment": environment,
        "region": region,
        "release_version": release_version,
        "build_number": build_number,
        "deployment_id": deployment_id,
        "observed_behavior": observed_behavior,
        "expected_behavior": expected_behavior,
        "related_incidents": related_incidents or [],
        "duplicate_of": duplicate_of,
        "top_evidence": top_evidence or [],
        "evidence_sources": evidence_sources or [],
        "recommended_next_step": recommended_next_step,
        "missing_information": missing_information or [],
        "review_status": review_status,
        "reviewed_by": None,
        "reviewed_at": None,
        "safe_to_execute": confidence >= 85 and not duplicate_of,
        "labels": labels or [],
    }

    result = es.index(index=BUG_RECORD_INDEX, document=doc, refresh="wait_for")

    return {
        "status": "created",
        "index": BUG_RECORD_INDEX,
        "document_id": result["_id"],
        "record_id": record_id,
        "classification": classification,
        "severity": severity,
        "confidence": confidence,
        "review_status": review_status,
    }


@mcp.tool
def link_signal_to_existing_incident(
    existing_incident_id: str,
    source_signal_text: str,
    summary: Optional[str] = None,
    confidence: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Return a structured link result when a new signal is determined to be a duplicate of an active incident.

    This tool does not create a new bug record. It returns a normalized confirmation payload
    that can be logged by the caller or attached to the existing incident in an external system.
    """

    return {
        "status": "linked",
        "existing_incident_id": existing_incident_id,
        "linked_at": _now_iso(),
        "summary": summary,
        "confidence": confidence,
        "source_signal_text": source_signal_text,
        "note": "Signal matched an active incident. No new intake record created.",
    }


if __name__ == "__main__":
    # Exposes an HTTP endpoint at /mcp for use by remote MCP connectors.
    mcp.run(transport="http", host="0.0.0.0", port=8000)
