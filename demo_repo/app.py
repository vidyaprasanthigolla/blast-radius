from user_service import UserService  # type: ignore

def main():
    service = UserService()
    response = service.get_user_info({"user_id": 123})
    print(response)

if __name__ == "__main__":
    main()
