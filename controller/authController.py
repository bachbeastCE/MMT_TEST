import json
from models.authModel import UserRegister, UserLogin, Visitor
from services.authService import register_user, login_user, visitor_mode, logout_user

def register(data):
    user = UserRegister(**data)
    result = register_user(user)

    return json.dumps(result)

def login(data, peer_ip, peer_port):
    user = UserLogin(**data)
    result = login_user(user, peer_ip, peer_port)
    return json.dumps(result)


def visitor(data):
    visitor_data = Visitor(**data)
    result = visitor_mode(visitor_data)

    return json.dumps(result)

def logout(data):
    session_id = data.get("session_id")
    if not session_id:
        return json.dumps({"status": "error", "message": "Session ID is required"})
    
    result = logout_user(session_id)
    return json.dumps(result)