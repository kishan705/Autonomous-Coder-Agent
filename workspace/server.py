from database import get_user

def fetch_route(req_id: str):
    return get_user(int(req_id))
