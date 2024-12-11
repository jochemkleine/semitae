import json
import os
from datetime import datetime
from typing import Optional

import requests


class SemitaeApiTester:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.headers = {"Content-Type": "application/json", "x-api-key": api_key}

    def execute_query(self, query: str, variables: Optional[dict] = None) -> dict:
        """Execute a GraphQL query and return the response"""
        payload = {"query": query, "variables": variables or {}}

        response = requests.post(self.api_url, headers=self.headers, json=payload)

        if response.status_code != 200:
            raise Exception(f"Query failed with status code: {response.status_code}")

        return response.json()

    def create_encounter(self, player1_id: str, player2_id: str, realm: str) -> dict:
        """Create a new encounter between two players"""
        mutation = """
        mutation CreateEncounter($player1Id: ID!, $player2Id: ID!, $realm: String!) {
            createEncounter(
                player1Id: $player1Id
                player2Id: $player2Id
                realm: $realm
            ) {
                id
                messageLog
                activePlayer
                realm
                participants
                createdAt
            }
        }
        """

        variables = {"player1Id": player1_id, "player2Id": player2_id, "realm": realm}

        return self.execute_query(mutation, variables)


def main():
    # Load configuration from environment variables
    api_url = (
        "https://3i5kvvtqmjhr7bxwxxtqz7ehbm.appsync-api.eu-west-1.amazonaws.com/graphql"
    )
    api_key = "da2-4vt6y32jofeitg53xf2q7dgxhu"

    if not api_url or not api_key:
        raise ValueError(
            "Please set SEMITAE_API_URL and SEMITAE_API_KEY environment variables"
        )

    # Initialize the tester
    tester = SemitaeApiTester(api_url, api_key)

    # Test cases
    test_cases = [
        {
            "player1_id": "test-player-1",
            "player2_id": "test-player-2",
            "realm": "Eldaria",
        },
        {
            "player1_id": "test-player-3",
            "player2_id": "test-player-4",
            "realm": "Shadowrealm",
        },
    ]

    # Run tests
    print("Starting integration tests...")
    print("-" * 50)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(
            f"Creating encounter between {test_case['player1_id']} and {test_case['player2_id']}"
        )
        print(f"Realm: {test_case['realm']}")

        try:
            result = tester.create_encounter(
                test_case["player1_id"], test_case["player2_id"], test_case["realm"]
            )

            print("\nResult:")
            print(json.dumps(result, indent=2))
            print("\nTest case successful! ✅")

        except Exception as e:
            print(f"\nTest case failed! ❌")
            print(f"Error: {str(e)}")

        print("-" * 50)


if __name__ == "__main__":
    main()
