import json
from typing import Any, Dict

import boto3

dynamodb = boto3.resource("dynamodb")
player_table = dynamodb.Table("PlayerTable")
encounter_table = dynamodb.Table("EncounterTable")


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    First step in the instruction processing workflow.
    Retrieves relevant player and encounter data and prepares it for the message generation step.
    """
    try:
        # Extract parameters from event
        conversation_id = event["conversationId"]
        player_id = event["playerId"]
        instruction = event["instruction"]

        # Get encounter data
        encounter_response = encounter_table.get_item(Key={"id": conversation_id})
        encounter_data = encounter_response.get("Item", {})

        # Verify this player is part of the encounter
        participants = encounter_data.get("participants", "").split(",")
        if player_id not in participants:
            raise ValueError(
                f"Player {player_id} is not part of encounter {conversation_id}"
            )

        # Verify it's this player's turn
        if encounter_data.get("activePlayer") != player_id:
            raise ValueError(f"It's not player {player_id}'s turn")

        # Get player data
        player_response = player_table.get_item(Key={"id": player_id})
        player_data = player_response.get("Item", {})

        # Prepare data for next step
        return {
            "statusCode": 200,
            "encounter": encounter_data,
            "player": player_data,
            "instruction": instruction,
            "playerId": player_id,
            "conversationId": conversation_id,
        }

    except Exception as e:
        print(f"Error in process_instruction: {str(e)}")
        return {"statusCode": 500, "error": str(e)}
