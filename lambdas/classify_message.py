import json
import os

from openai import OpenAI


def handler(event, context):
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    instruction = event.get("instruction", "")
    message = event.get("message", "")

    system_prompt = """Classify the following player instruction and character response into a single event type.
    Example event types: Attack, Intimidate, Persuade, Threaten, Partner up, Ally, Negotiate, Ponder, Wonder, Befriend, etc.
    Respond with only the event type, no explanation."""

    content = f"""Player instruction: {instruction}
Character response: {message}"""

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            model="gpt-4o-mini",
            temperature=0.3,
            max_tokens=20,
        )

        classification = response.choices[0].message.content.strip()

        return {
            "statusCode": 200,
            "classification": classification,
            "message": message,
            "instruction": instruction,
        }

    except Exception as e:
        print(f"Error in classify_message: {str(e)}")
        return {"statusCode": 500, "error": str(e)}
