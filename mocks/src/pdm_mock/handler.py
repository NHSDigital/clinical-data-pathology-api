import os
from datetime import datetime, timezone
from time import time
from typing import Any
from uuid import uuid4

import boto3

PDM_TABLE_NAME = os.environ.get("PDM_TABLE_NAME", "table_name")
BRANCH_NAME = os.environ.get("DDB_INDEX_TAG", "branch_name")


def handle_post_request(payload: dict[str, Any]) -> dict[str, Any]:

    document_id = str(uuid4())
    created_document = {
        **payload,
        "id": document_id,
        "meta": {
            "versionId": "1",
            "last_updated": datetime.now(tz=timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
        },
    }
    item = {
        "sessionId": document_id,
        "expiresAt": int(time()) + 600,
        "document": created_document,
        "ddb_index": BRANCH_NAME,
        "type": "pdm_document",
    }

    write_document_to_table(item)

    return created_document


def handle_get_request(document_id: str) -> Any:

    table_item = get_document_from_table(document_id)
    document = table_item["document"]

    return document


def write_document_to_table(item: dict[str, Any]) -> None:
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(PDM_TABLE_NAME)
    table.put_item(Item=item)


def get_document_from_table(document_id: str) -> Any:
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(PDM_TABLE_NAME)

    response = table.get_item(Key={"sessionId": document_id})

    if "Item" not in response:
        return {"error": "Document not found"}

    return response["Item"]
