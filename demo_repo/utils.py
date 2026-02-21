def validate_data(data):
    if not isinstance(data, dict):
        raise ValueError("Invalid data format")
    return True

def format_response(status, message):
    return {"status": status, "message": message}
