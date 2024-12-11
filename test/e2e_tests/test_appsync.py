import json
import os
from typing import Dict

import requests


def test_submit_message(
    api_url: str, api_key: str, conversation_id: str, player_id: str, instruction: str
) -> Dict:
    """Submit a message through the AppSync endpoint"""

    headers = {"Content-Type": "application/json", "x-api-key": api_key}

    mutation = """
    mutation SubmitMessage($input: SubmitMessageInput!) {
        submitMessage(input: $input) {
            id
            executionArn
        }
    }
    """

    variables = {
        "input": {
            "conversationId": conversation_id,
            "playerId": player_id,
            "instruction": instruction,
        }
    }

    response = requests.post(
        api_url, headers=headers, json={"query": mutation, "variables": variables}
    )

    return response.json()


def main():
    # Load configuration
    api_url = os.getenv("SEMITAE_API_URL")
    api_key = os.getenv("SEMITAE_API_KEY")

    if not api_url or not api_key:
        raise ValueError(
            "Please set SEMITAE_API_URL and SEMITAE_API_KEY environment variables"
        )

    # Test case
    test_data = {
        "conversation_id": "test-conversation-1",
        "player_id": "test-player-1",
        "instruction": "Greet the other player warmly",
    }

    print("Testing submitMessage mutation...")
    print(f"Conversation ID: {test_data['conversation_id']}")
    print(f"Player ID: {test_data['player_id']}")
    print(f"Instruction: {test_data['instruction']}")
    print("-" * 50)

    try:
        result = test_submit_message(
            api_url,
            api_key,
            test_data["conversation_id"],
            test_data["player_id"],
            test_data["instruction"],
        )

        print("\nResult:")
        print(json.dumps(result, indent=2))

        if "errors" in result:
            print("\nTest failed! ❌")
        else:
            print("\nTest successful! ✅")
            print(f"Execution ARN: {result['data']['submitMessage']['executionArn']}")

    except Exception as e:
        print(f"\nTest failed! ❌")
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
