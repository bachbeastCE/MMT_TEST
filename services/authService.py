from config.db import users_collection
import uuid
from datetime import datetime, timezone
from models.authModel import UserRegister, UserLogin, Visitor
##########################################################
def register_user(user: UserRegister) -> dict:
    try:
        if users_collection.find_one({"email": user.email}):
            return {"status": "error", "message": "Email already registered"}

        if users_collection.find_one({"username": user.username}):
            return {"status": "error", "message": "Username already taken"}

        new_user = user.model_dump()
        new_user["verified"] = True 

        result = users_collection.insert_one(new_user) 
        return {"status": "success", "message": "User registered successfully", "user_id": str(result.inserted_id)}

    except Exception as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}

##########################################################
def login_user(user: UserLogin, peer_ip: str, peer_port: int) -> dict:
    user_data = users_collection.find_one({"username": user.username, "password": user.password})

    if user_data:
        session_id = str(uuid.uuid4()) 
        new_session = {
            "peer_ip": peer_ip,
            "peer_port": peer_port,
            "session_id": session_id,
            "login_time": datetime.now(timezone.utc).isoformat() 
        }

        users_collection.update_one(
            {"username": user.username},
            {"$push": {"sessions": new_session}}
        )
        user_data = users_collection.find_one({"username": user.username})

        def serialize(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj
        
        return {
            "status": "success",
            "message": "Login successful",
            "user": {
                "username": user_data["username"],
                "email": user_data.get("email", ""),
                "channels_joined": user_data.get("channels_joined", []),
                "hosted_channels": user_data.get("hosted_channels", []),
                "sessions": [{**session, "login_time": serialize(session["login_time"])}
                             for session in user_data.get("sessions", [])]
            }
        }

    return {"status": "error", "message": "Invalid username or password"}

##########################################################
def visitor_mode(visitor_data: Visitor, ) -> dict:
    if users_collection.find_one({"username": visitor_data.name}):
            return {"status": "error", "message": "Username already taken"}
    if not visitor_data.name:
        return {"status": "error", "message": "Visitor name cannot be empty"}
    
    return {"status": "success", "message": f"Welcome, {visitor_data.name}! You are in visitor mode."}
##########################################################
def logout_user(session_id: str) -> dict:
    try:
        user = users_collection.find_one({"sessions.session_id": session_id})
        
        if not user:
            return {"status": "error", "message": "Invalid session_id"}

        users_collection.update_one(
            {"_id": user["_id"]},
            {"$pull": {"sessions": {"session_id": session_id}}}
        )

        return {"status": "success", "message": "Logout successful"}
    
    except Exception as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}