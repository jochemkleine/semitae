def handler(event, context):
    """
    Test handler that retrieves saved Step Functions variables
    """
    print(f"Received event: {event}")

    # Extract the variables passed from Step Functions
    encounter_id = event.get("encounter_id")
    player_id = event.get("player_id")
    instruction = event.get("instruction")

    return {
        "statusCode": 200,
        "message": f"Retrieved variables - encounterId: {encounter_id}, playerId: {player_id}, instruction: {instruction}",
        "variables": {
            "encounterId": encounter_id,
            "playerId": player_id,
            "instruction": instruction,
        },
    }
