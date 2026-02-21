class DatabaseConnector:
    def __init__(self, uri):
        self.uri = uri
    
    def connect(self):
        print("Connected to DB")

    def fetch_user(self, user_id):
        # Simulated DB fetch
        return {"id": user_id, "name": "John Doe", "active": True}
        
    def execute_query(self, query):
        print(f"Executing: {query}")
        return True
