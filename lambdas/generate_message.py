import json
import os
import uuid
from datetime import datetime, timedelta

import boto3
from openai import OpenAI

dynamodb = boto3.resource("dynamodb")
conversations_table = dynamodb.Table(os.environ["CONVERSATIONS_TABLE"])
characters_table = dynamodb.Table(os.environ["CHARACTERS_TABLE"])


def handler(event, context):
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    instruction = event.get("instruction", "")

    try:
        # Generate message
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are roleplaying as a character in a text-based game. Always stay in character and respond based on the instruction given. Keep responses concise and character-appropriate.",
                },
                {"role": "user", "content": instruction},
            ],
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=150,
        )

        message = response.choices[0].message.content

        # For now, just return the message and instruction
        return {"statusCode": 200, "message": message, "instruction": instruction}

    except Exception as e:
        print(f"Error in create_message: {str(e)}")
        return {"statusCode": 500, "error": str(e)}
