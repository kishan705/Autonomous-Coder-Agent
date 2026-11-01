def get_user(user_id: int):
    if not isinstance(user_id, int):
        raise TypeError("Database Error: user_id must be an integer!")
    return {"id": user_id, "name": "Alice"}
