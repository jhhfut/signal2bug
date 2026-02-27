from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List

from elasticsearch import Elasticsearch, helpers

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"

INDEX_CONFIGS: Dict[str, Dict[str, Any]] = {
    "bugs": {
        "mappings": {
            "properties": {
                "incident_id": {"type": "keyword"},
                "bug_id": {"type": "keyword"},
                "external_ticket_id": {"type": "keyword"},
                "source_system": {"type": "keyword"},
                "status": {"type": "keyword"},
                "lifecycle_stage": {"type": "keyword"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "first_seen": {"type": "date"},
                "last_seen": {"type": "date"},
                "resolved_at": {"type": "date"},
                "title": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
                "summary": {"type": "text"},
                "description": {"type": "text"},
                "user_report_text": {"type": "text"},
                "normalized_report": {"type": "text"},
                "symptoms": {"type": "keyword"},
                "observed_behavior": {"type": "text"},
                "expected_behavior": {"type": "text"},
                "error_signature": {"type": "keyword"},
                "error_type": {"type": "keyword"},
                "error_codes": {"type": "keyword"},
                "error_message_sample": {"type": "text"},
                "service": {"type": "keyword"},
                "component": {"type": "keyword"},
                "subsystem": {"type": "keyword"},
                "endpoint": {"type": "keyword"},
                "ui_route": {"type": "keyword"},
                "platform": {"type": "keyword"},
                "environment": {"type": "keyword"},
                "region": {"type": "keyword"},
                "tenant": {"type": "keyword"},
                "release_version": {"type": "keyword"},
                "build_number": {"type": "keyword"},
                "deployment_id": {"type": "keyword"},
                "release_channel": {"type": "keyword"},
                "feature_flags": {"type": "keyword"},
                "introduced_after_change": {"type": "boolean"},
                "suspected_change_type": {"type": "keyword"},
                "severity": {"type": "keyword"},
                "priority": {"type": "keyword"},
                "impact_scope": {"type": "keyword"},
                "affected_user_count_estimate": {"type": "integer"},
                "affected_transaction_type": {"type": "keyword"},
                "business_impact": {"type": "text"},
                "is_customer_visible": {"type": "boolean"},
                "is_revenue_blocking": {"type": "boolean"},
                "owner_team": {"type": "keyword"},
                "owner_service": {"type": "keyword"},
                "triage_decision": {"type": "keyword"},
                "triage_confidence": {"type": "float"},
                "triaged_by": {"type": "keyword"},
                "duplicate_of": {"type": "keyword"},
                "related_incidents": {"type": "keyword"},
                "escalation_level": {"type": "keyword"},
                "suspected_root_cause": {"type": "text"},
                "confirmed_root_cause": {"type": "text"},
                "root_cause_category": {"type": "keyword"},
                "reproduction_steps": {"type": "text"},
                "workaround": {"type": "text"},
                "resolution_summary": {"type": "text"},
                "resolution_type": {"type": "keyword"},
                "tags": {"type": "keyword"},
                "keywords": {"type": "keyword"},
                "known_issue": {"type": "boolean"},
            }
        },
        "seed_files": ["bugs_expanded.json", "bugs.json"],
    },
    "releases": {
        "mappings": {
            "properties": {
                "release_version": {"type": "keyword"},
                "release_name": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
                "build_number": {"type": "keyword"},
                "deployment_id": {"type": "keyword"},
                "release_type": {"type": "keyword"},
                "deployed_at": {"type": "date"},
                "deployment_started_at": {"type": "date"},
                "deployment_finished_at": {"type": "date"},
                "environment": {"type": "keyword"},
                "release_channel": {"type": "keyword"},
                "rollout_strategy": {"type": "keyword"},
                "rollout_percentage": {"type": "float"},
                "canary_group": {"type": "keyword"},
                "summary": {"type": "text"},
                "release_notes": {"type": "text"},
                "services_changed": {"type": "keyword"},
                "changed_components": {"type": "keyword"},
                "endpoints_changed": {"type": "keyword"},
                "database_changes": {"type": "text"},
                "schema_migrations": {"type": "text"},
                "config_changes": {"type": "text"},
                "owner_team": {"type": "keyword"},
                "approver": {"type": "keyword"},
                "deployed_by": {"type": "keyword"},
                "oncall_team": {"type": "keyword"},
                "rollback_owner": {"type": "keyword"},
                "risk_level": {"type": "keyword"},
                "breaking_change": {"type": "boolean"},
                "requires_migration": {"type": "boolean"},
                "requires_cache_invalidation": {"type": "boolean"},
                "rollback_supported": {"type": "boolean"},
                "rollback_instructions": {"type": "text"},
                "feature_flags_enabled": {"type": "keyword"},
                "feature_flags_disabled": {"type": "keyword"},
                "linked_prs": {"type": "keyword"},
                "linked_commits": {"type": "keyword"},
                "linked_change_requests": {"type": "keyword"},
                "expected_error_budget_impact": {"type": "keyword"},
                "post_deploy_monitoring_window_minutes": {"type": "integer"},
                "observability_dashboard_id": {"type": "keyword"},
                "runbook_link_text": {"type": "text"},
                "known_risks": {"type": "text"},
            }
        },
        "seed_files": ["releases_expanded.json", "releases.json"],
    },
    "logs": {
        "mappings": {
            "properties": {
                "event_id": {"type": "keyword"},
                "@timestamp": {"type": "date"},
                "trace_id": {"type": "keyword"},
                "span_id": {"type": "keyword"},
                "request_id": {"type": "keyword"},
                "correlation_id": {"type": "keyword"},
                "service": {"type": "keyword"},
                "component": {"type": "keyword"},
                "subsystem": {"type": "keyword"},
                "host": {"type": "keyword"},
                "instance_id": {"type": "keyword"},
                "region": {"type": "keyword"},
                "environment": {"type": "keyword"},
                "availability_zone": {"type": "keyword"},
                "endpoint": {"type": "keyword"},
                "http_method": {"type": "keyword"},
                "status_code": {"type": "integer"},
                "status_family": {"type": "keyword"},
                "latency_ms": {"type": "integer"},
                "upstream_service": {"type": "keyword"},
                "downstream_service": {"type": "keyword"},
                "error_type": {"type": "keyword"},
                "error_code": {"type": "keyword"},
                "error_message": {"type": "text"},
                "error_signature": {"type": "keyword"},
                "stack_hash": {"type": "keyword"},
                "exception_class": {"type": "keyword"},
                "is_timeout": {"type": "boolean"},
                "is_retryable": {"type": "boolean"},
                "release_version": {"type": "keyword"},
                "build_number": {"type": "keyword"},
                "deployment_id": {"type": "keyword"},
                "feature_flags_active": {"type": "keyword"},
                "user_id_hash": {"type": "keyword"},
                "session_id_hash": {"type": "keyword"},
                "customer_tier": {"type": "keyword"},
                "transaction_type": {"type": "keyword"},
                "cart_value": {"type": "float"},
                "currency": {"type": "keyword"},
                "count": {"type": "integer"},
                "error_rate_percent": {"type": "float"},
                "sample_size": {"type": "integer"},
                "is_aggregated_record": {"type": "boolean"},
                "log_level": {"type": "keyword"},
                "signal_type": {"type": "keyword"},
                "alert_source": {"type": "keyword"},
                "anomaly_flag": {"type": "boolean"},
            }
        },
        "seed_files": ["logs_expanded.json", "logs.json"],
    },
    "runbooks": {
        "mappings": {
            "properties": {
                "runbook_id": {"type": "keyword"},
                "title": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
                "summary": {"type": "text"},
                "incident_type": {"type": "keyword"},
                "severity_scope": {"type": "keyword"},
                "service": {"type": "keyword"},
                "component": {"type": "keyword"},
                "environment": {"type": "keyword"},
                "applicability_conditions": {"type": "text"},
                "trigger_signals": {"type": "keyword"},
                "recommended_actions": {"type": "text"},
                "rollback_steps": {"type": "text"},
                "verification_steps": {"type": "text"},
                "safe_actions_only": {"type": "boolean"},
                "requires_human_approval": {"type": "boolean"},
                "owner_team": {"type": "keyword"},
                "oncall_team": {"type": "keyword"},
                "escalation_path": {"type": "text"},
                "related_services": {"type": "keyword"},
                "linked_release_types": {"type": "keyword"},
                "known_limitations": {"type": "text"},
                "updated_at": {"type": "date"},
                "version": {"type": "keyword"},
                "tags": {"type": "keyword"},
            }
        },
        "seed_files": ["runbooks.json"],
    },
    "bug_intake_records": {
        "mappings": {
            "properties": {
                "record_id": {"type": "keyword"},
                "created_at": {"type": "date"},
                "created_by": {"type": "keyword"},
                "agent_version": {"type": "keyword"},
                "source_signal_type": {"type": "keyword"},
                "source_signal_text": {"type": "text"},
                "title": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
                "summary": {"type": "text"},
                "description": {"type": "text"},
                "classification": {"type": "keyword"},
                "severity": {"type": "keyword"},
                "priority": {"type": "keyword"},
                "confidence": {"type": "float"},
                "likely_owner_team": {"type": "keyword"},
                "likely_owner_service": {"type": "keyword"},
                "service": {"type": "keyword"},
                "component": {"type": "keyword"},
                "subsystem": {"type": "keyword"},
                "endpoint": {"type": "keyword"},
                "platform": {"type": "keyword"},
                "environment": {"type": "keyword"},
                "region": {"type": "keyword"},
                "release_version": {"type": "keyword"},
                "build_number": {"type": "keyword"},
                "deployment_id": {"type": "keyword"},
                "observed_behavior": {"type": "text"},
                "expected_behavior": {"type": "text"},
                "related_incidents": {"type": "keyword"},
                "duplicate_of": {"type": "keyword"},
                "top_evidence": {"type": "text"},
                "evidence_sources": {"type": "keyword"},
                "recommended_next_step": {"type": "text"},
                "missing_information": {"type": "text"},
                "review_status": {"type": "keyword"},
                "reviewed_by": {"type": "keyword"},
                "reviewed_at": {"type": "date"},
                "safe_to_execute": {"type": "boolean"},
                "labels": {"type": "keyword"},
            }
        },
        "seed_files": ["bug_intake_records.json"],
    },
}


def make_client() -> Elasticsearch:
    cloud_id = os.getenv("ELASTIC_CLOUD_ID")
    api_key = os.getenv("ELASTIC_API_KEY")
    url = os.getenv("ELASTIC_URL")
    username = os.getenv("ELASTIC_USERNAME")
    password = os.getenv("ELASTIC_PASSWORD")

    if cloud_id and api_key:
        return Elasticsearch(cloud_id=cloud_id, api_key=api_key)
    if url and api_key:
        return Elasticsearch(url, api_key=api_key)
    if url and username and password:
        return Elasticsearch(url, basic_auth=(username, password))

    raise RuntimeError(
        "Set either (ELASTIC_CLOUD_ID + ELASTIC_API_KEY) or (ELASTIC_URL + ELASTIC_API_KEY) "
        "or (ELASTIC_URL + ELASTIC_USERNAME + ELASTIC_PASSWORD)."
    )


def load_docs_for_index(seed_files: List[str]) -> List[Dict[str, Any]]:
    for file_name in seed_files:
        path = DATA_DIR / file_name
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
    return []


def ensure_index(client: Elasticsearch, index_name: str, mappings: Dict[str, Any]) -> None:
    if client.indices.exists(index=index_name):
        print(f"Index '{index_name}' already exists. Updating mappings...")
        client.indices.put_mapping(index=index_name, properties=mappings["properties"])
    else:
        print(f"Creating index '{index_name}'...")
        client.indices.create(index=index_name, mappings=mappings)


def to_actions(index_name: str, docs: Iterable[Dict[str, Any]]) -> Iterable[Dict[str, Any]]:
    for doc in docs:
        yield {"_index": index_name, "_source": doc}


def main() -> None:
    client = make_client()
    print("Connected to Elasticsearch")

    for index_name, config in INDEX_CONFIGS.items():
        ensure_index(client, index_name, config["mappings"])
        docs = load_docs_for_index(config["seed_files"])
        if docs:
            print(f"Indexing {len(docs)} docs into '{index_name}'...")
            success, errors = helpers.bulk(
                client,
                to_actions(index_name, docs),
                refresh="wait_for",
                raise_on_error=False,
                request_timeout=120,
            )
            print(f"  Indexed: {success}")
            if errors:
                print(f"  Errors: {len(errors)} (showing first 2)")
                for err in errors[:2]:
                    print(json.dumps(err, indent=2))
        else:
            print(f"No seed file found for '{index_name}'. Index created with zero documents.")
        count = client.count(index=index_name)["count"]
        print(f"  Total docs now in '{index_name}': {count}")

    print("\nDone.")
    print("You can now create Agent Builder tools for:")
    print("- bugs")
    print("- logs")
    print("- releases")
    print("- runbooks")
    print("- bug_intake_records (written by MCP when safe)")


if __name__ == "__main__":
    main()
