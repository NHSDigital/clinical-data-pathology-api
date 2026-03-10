from typing import Any

import boto3


class DynamoHelper:
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(self.table_name)

    def put_item(self, document: dict[str, Any]) -> None:
        self.table.put_item(Item=document)
