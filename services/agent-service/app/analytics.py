"""Request analytics: streams one row per API request to BigQuery.

Falls back to a local analytics_log.jsonl file until GCP is configured
(Phase 9). Must NEVER crash a user request — everything is best-effort.
"""
import json
import logging
import pathlib

from .config import settings

logger = logging.getLogger("agent-service.analytics")
_bq_client = None


def _bigquery():
    global _bq_client
    if _bq_client is None:
        from google.cloud import bigquery

        _bq_client = bigquery.Client(project=settings.gcp_project_id)
    return _bq_client


def log_request(row: dict) -> None:
    try:
        if settings.gcp_project_id:
            table = f"{settings.gcp_project_id}.{settings.bq_dataset}.{settings.bq_table}"
            errors = _bigquery().insert_rows_json(table, [row])
            if errors:
                logger.warning("BigQuery insert errors: %s", errors)
        else:
            with pathlib.Path("analytics_log.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps(row) + "\n")
    except Exception as e:
        logger.warning("analytics logging failed: %s", e)
