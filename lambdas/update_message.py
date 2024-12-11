import json
import os
from datetime import datetime

import boto3

dynamodb = boto3.resource("dynamodb")
conversations_table = dynamodb.Table(os.environ["CONVERSATIONS_TABLE"])


def handler(event, context):
    try:
        # Extract data from previous steps
        message_result = event["messageResult"]
        classification_result = event["classificationResult"]

        conversation_id = message_result["conversationId"]
        message_id = message_result["messageId"]
        timestamp = message_result["timestamp"]

        # Update the message item with the classification
        response = conversations_table.update_item(
            Key={
                "pk": f"CONV#{conversation_id}",
                "sk": f"MSG#{timestamp}#{message_id}",
            },
            UpdateExpression="SET classification = :classification, lastUpdated = :now",
            ExpressionAttributeValues={
                ":classification": classification_result["classification"],
                ":now": datetime.utcnow().isoformat(),
            },
            ReturnValues="ALL_NEW",
        )

        return {
            "statusCode": 200,
            "message": "Classification stored successfully",
            "updatedItem": response.get("Attributes", {}),
        }

    except Exception as e:
        print(f"Error in update_message: {str(e)}")  # Log the error
        return {"statusCode": 500, "error": str(e)}
