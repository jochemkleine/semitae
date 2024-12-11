import json
import os
from typing import Any, Dict

import boto3

dynamodb = boto3.resource("dynamodb")
encounter_table = dynamodb.Table(os.environ["ENCOUNTER_TABLE"])
player_table = dynamodb.Table(os.environ["PLAYER_TABLE"])


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        conversation_id = event["conversationId"]
        player_id = event["playerId"]
        instruction = event["instruction"]

        # Get encounter data
        encounter_response = encounter_table.get_item(Key={"id": conversation_id})

        if "Item" not in encounter_response:
            raise Exception(f"Encounter {conversation_id} not found")

        encounter = encounter_response["Item"]

        # Validate player is part of this encounter
        participants = encounter["participants"].split(",")
        if player_id not in participants:
            raise Exception(f"Player {player_id} is not part of this encounter")

        # Validate it's the player's turn
        if encounter["activePlayer"] != player_id:
            raise Exception(f"It's not player {player_id}'s turn")

        # Return all necessary information for the next steps
        return {
            "statusCode": 200,
            "encounterData": encounter,
            "instruction": instruction,
            "playerId": player_id,
            "otherPlayerId": (
                participants[0] if participants[1] == player_id else participants[1]
            ),
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {"statusCode": 500, "error": str(e)}
