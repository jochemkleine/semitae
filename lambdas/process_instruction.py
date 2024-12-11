def handler(event, context):
    """
    Simple handler that returns a hello world message
    """
    print(f"Received event: {event}")  # For debugging in CloudWatch

    return {
        "statusCode": 200,
        "message": f"Hello! Received instruction: {event.get('instruction')} for encounter {event.get('encounterId')} from player {event.get('playerId')}",
    }
