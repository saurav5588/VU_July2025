import os, json, time, uuid, boto3
from decimal import Decimal

table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])

def replace_floats(obj):
    """Recursively replace float with Decimal."""
    if isinstance(obj, list):
        return [replace_floats(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: replace_floats(v) for k, v in obj.items()}
    elif isinstance(obj, float):
        return Decimal(str(obj))
    else:
        return obj

def lambda_handler(event, context):
    stored = 0
    for rec in event.get("Records", []):
        msg = rec.get("Sns", {}).get("Message", "{}")
        try:
            payload = json.loads(msg)
            payload = replace_floats(payload)   # <<< fix
        except Exception:
            payload = {"raw": msg}
        item = {
            "alarmEventId": str(uuid.uuid4()),
            "receivedAt": int(time.time()),
            "message": payload,
            "ttl": int(time.time()) + 60 * 60 * 24 * 30,  # 30 days
        }
        table.put_item(Item=item)
        stored += 1
    return {"stored": stored}
