import json
from datetime import datetime

import requests

# Configuration
APPSYNC_URL = "https://3i5kvvtqmjhr7bxwxxtqz7ehbm.appsync-api.eu-west-1.amazonaws.com/graphql"  # Get this from CDK output
APPSYNC_API_KEY = "da2-4vt6y32jofeitg53xf2q7dgxhu"  # Get this from CDK output

headers = {"Content-Type": "application/json", "x-api-key": APPSYNC_API_KEY}


def test_send_instruction():
    # GraphQL mutation
    mutation = """
    mutation SendInstruction($conversationId: String!, $playerId: String!, $instruction: String!) {
        sendInstruction(
            conversationId: $conversationId
            playerId: $playerId
            instruction: $instruction
        ) {
            statusCode
            message
            error
        }
    }
    """

    # Test variables
    variables = {
        "conversationId": "test-conversation-id",  # Replace with actual conversation ID
        "playerId": "test-player-id",  # Replace with actual player ID
        "instruction": "Greet the other player warmly",
    }

    # Request body
    request_body = {"query": mutation, "variables": variables}

    try:
        # Make the request
        response = requests.post(APPSYNC_URL, headers=headers, json=request_body)

        # Parse and print response
        result = response.json()
        print("\nResponse:")
        print(json.dumps(result, indent=2))

        if "errors" in result:
            print("\nErrors found:")
            print(json.dumps(result["errors"], indent=2))

        return result

    except Exception as e:
        print(f"Error making request: {str(e)}")
        return None


def test_create_encounter():
    mutation = """
    mutation CreateEncounter($player1Id: ID!, $player2Id: ID!, $realm: String!) {
        createEncounter(
            player1Id: $player1Id
            player2Id: $player2Id
            realm: $realm
        ) {
            id
            messageLog    # No sub-selection needed for [String] type
            activePlayer
            realm
            participants
            createdAt
        }
    }
    """

    variables = {
        "player1Id": "test-player-3",
        "player2Id": "test-player-4",
        "realm": "Shadowrealm",
    }

    request_body = {"query": mutation, "variables": variables}

    try:
        response = requests.post(APPSYNC_URL, headers=headers, json=request_body)

        result = response.json()
        print("\nCreate Encounter Response:")
        print(json.dumps(result, indent=2))

        if "errors" in result:
            print("\nErrors found:")
            print(json.dumps(result["errors"], indent=2))
            return None  # Added to prevent None access when there are errors

        return result

    except Exception as e:
        print(f"Error making request: {str(e)}")
        return None


if __name__ == "__main__":
    print("Creating test encounter...")
    encounter_result = test_create_encounter()

    if encounter_result and "data" in encounter_result:
        conversation_id = encounter_result["data"]["createEncounter"]["id"]
        player_id = encounter_result["data"]["createEncounter"]["activePlayer"]

        print("\nTesting send instruction with created encounter...")
        test_send_instruction()
    else:
        print("Skipping instruction test due to encounter creation failure")


# Helper function to save response data for debugging
def save_test_results(result, filename="test_results.json"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{filename}"

    with open(filename, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\nResults saved to {filename}")
