import server

def test_fetch():
    response = server.fetch_route("123")
    assert response == {"id": 123, "name": "Alice"}
