from db_connector import DatabaseConnector  # type: ignore
from utils import validate_data, format_response  # type: ignore

class UserService:
    def __init__(self):
        self.db = DatabaseConnector("sqlite://dummy.db")
        self.db.connect()

    def get_user_info(self, request_data):
        validate_data(request_data)
        user_id = request_data.get("user_id")
        user = self.db.fetch_user(user_id)
        if user:
            return format_response(200, user)
        return format_response(404, "User not found")
