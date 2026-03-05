"""DynamoDB helpers for checkDK – users and analysis history."""

from __future__ import annotations

import logging
import os
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Optional

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger(__name__)

# ── Table names ────────────────────────────────────────────────────────────────
USERS_TABLE = os.getenv("DYNAMODB_USERS_TABLE", "checkdk_users")
HISTORY_TABLE = os.getenv("DYNAMODB_HISTORY_TABLE", "checkdk_history")
DYNAMODB_REGION = os.getenv("DYNAMODB_REGION", "us-east-1")

# Maximum history items to keep per user
MAX_HISTORY = 10

# TTL for history items: 90 days
HISTORY_TTL_SECONDS = 90 * 24 * 60 * 60

# Human-readable labels for issue categories shown in patterns
CATEGORY_LABELS: dict[str, str] = {
    "security": "Security issues",
    "hardcoded_secret": "Hardcoded secrets",
    "resource_limits": "Missing resource limits",
    "image_tag": "Unpinned image tags",
    "missing_image": "Missing image / build",
    "port_conflict": "Port conflicts",
    "structure": "Structural problems",
    "syntax": "YAML syntax errors",
    "networking": "Networking misconfiguration",
    "health_check": "Missing health checks",
    "privileged": "Privileged containers",
    "probe": "Missing liveness / readiness probes",
    "rbac": "RBAC / permissions",
    "storage": "Storage / volume issues",
}


def _get_table(name: str):
    """Return a DynamoDB Table resource.  Lazy import keeps startup fast."""
    dynamodb = boto3.resource("dynamodb", region_name=DYNAMODB_REGION)
    return dynamodb.Table(name)


# ── Users ──────────────────────────────────────────────────────────────────────

def _build_user_id(provider: str, provider_id: str) -> str:
    """Composite PK avoids a secondary index lookup: e.g. 'github#12345'."""
    return f"{provider}#{provider_id}"


def get_user_by_provider_id(provider: str, provider_id: str) -> Optional[dict]:
    """Return the user item or *None* if not found."""
    user_id = _build_user_id(provider, provider_id)
    try:
        table = _get_table(USERS_TABLE)
        response = table.get_item(Key={"userId": user_id})
        return response.get("Item")
    except Exception:
        logger.exception("DynamoDB get_user failed for %s", user_id)
        return None


def upsert_user(
    provider: str,
    provider_id: str,
    email: Optional[str],
    name: Optional[str],
    avatar_url: Optional[str],
) -> dict:
    """Create or update a user record; returns the final item."""
    user_id = _build_user_id(provider, provider_id)
    now_iso = datetime.now(timezone.utc).isoformat()

    table = _get_table(USERS_TABLE)

    # Attempt an update so we preserve createdAt on existing records.
    update_expr = (
        "SET #n = :name, email = :email, avatarUrl = :avatar, "
        "provider = :provider, providerId = :pid, updatedAt = :now, "
        "createdAt = if_not_exists(createdAt, :now)"
    )
    expr_names = {"#n": "name"}  # 'name' is a reserved word in DynamoDB
    expr_values = {
        ":name": name or "",
        ":email": email or "",
        ":avatar": avatar_url or "",
        ":provider": provider,
        ":pid": provider_id,
        ":now": now_iso,
    }

    try:
        response = table.update_item(
            Key={"userId": user_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
            ReturnValues="ALL_NEW",
        )
        return response["Attributes"]
    except Exception:
        logger.exception("DynamoDB upsert_user failed for %s", user_id)
        raise


# ── History ────────────────────────────────────────────────────────────────────

def _make_analysis_id() -> str:
    """Sort key: ISO timestamp + '#' + uuid hex  →  lexicographic DESC == time DESC."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"{ts}#{uuid.uuid4().hex}"


def save_history(
    user_id: str,
    config_type: str,
    filename: Optional[str],
    score: int,
    status: str,
    issue_count: int,
    top_categories: list[str],
    provider: Optional[str] = None,
) -> None:
    """
    Persist one analysis result and prune old items so the user keeps ≤ MAX_HISTORY.

    Designed to run in a FastAPI BackgroundTask (non-blocking).
    """
    analysis_id = _make_analysis_id()
    ttl = int(time.time()) + HISTORY_TTL_SECONDS

    item: dict[str, Any] = {
        "userId": user_id,
        "analysisId": analysis_id,
        "configType": config_type,
        "filename": filename or "unknown",
        "score": score,
        "status": status,
        "issueCount": issue_count,
        "topCategories": top_categories,
        "analyzedAt": datetime.now(timezone.utc).isoformat(),
        "ttl": ttl,
    }
    if provider:
        item["aiProvider"] = provider

    try:
        table = _get_table(HISTORY_TABLE)
        table.put_item(Item=item)
        _prune_history(user_id, table)
    except Exception:
        logger.exception("DynamoDB save_history failed for user %s", user_id)


def _prune_history(user_id: str, table) -> None:
    """Delete items beyond MAX_HISTORY (sorted newest-first)."""
    try:
        response = table.query(
            KeyConditionExpression=Key("userId").eq(user_id),
            ScanIndexForward=False,  # newest first
            ProjectionExpression="userId, analysisId",
        )
        items = response.get("Items", [])
        to_delete = items[MAX_HISTORY:]
        for item in to_delete:
            table.delete_item(Key={"userId": item["userId"], "analysisId": item["analysisId"]})
    except Exception:
        logger.exception("DynamoDB _prune_history failed for user %s", user_id)


def get_history(user_id: str) -> list[dict]:
    """Return the most-recent MAX_HISTORY analysis items for *user_id*."""
    try:
        table = _get_table(HISTORY_TABLE)
        response = table.query(
            KeyConditionExpression=Key("userId").eq(user_id),
            ScanIndexForward=False,
            Limit=MAX_HISTORY,
        )
        return response.get("Items", [])
    except Exception:
        logger.exception("DynamoDB get_history failed for user %s", user_id)
        return []


def get_patterns(user_id: str) -> list[dict]:
    """
    Return the top-5 recurring issue categories across the last 50 analyses.

    Each entry: ``{"category": str, "label": str, "count": int}``
    """
    try:
        table = _get_table(HISTORY_TABLE)
        response = table.query(
            KeyConditionExpression=Key("userId").eq(user_id),
            ScanIndexForward=False,
            Limit=50,
            ProjectionExpression="topCategories",
        )
        counter: Counter = Counter()
        for item in response.get("Items", []):
            for cat in item.get("topCategories", []):
                counter[cat] += 1

        return [
            {
                "category": cat,
                "label": CATEGORY_LABELS.get(cat, cat.replace("_", " ").title()),
                "count": count,
            }
            for cat, count in counter.most_common(5)
        ]
    except Exception:
        logger.exception("DynamoDB get_patterns failed for user %s", user_id)
        return []
