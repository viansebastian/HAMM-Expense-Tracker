# Users Controller File

import models
from db import SessionLocal
from utils.common import check_exists
from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash


user_bp = Blueprint("user_bp", __name__, url_prefix="/users")

@user_bp.route("", methods=["GET"])
def get_users():
    db = SessionLocal()
    users = db.query(models.User).all()
    db.close()
    return jsonify([
        {
            "id": u.id,
            "email": u.email,
            "first_name": u.first_name,
            "last_name": u.last_name,
        }
        for u in users
    ])


@user_bp.route("", methods=["POST"])
def create_user(): 
    db = SessionLocal()
    data = request.get_json()
    
    checker = {
        "email": data["email"]
    }
    
    if check_exists(db, models.User, checker): 
        return jsonify({
            "error": "User with this email already exists"
        })
        
    hashed_pw = generate_password_hash(data["password"])
    new_user = models.User(
        email=data["email"],
        password_hash=hashed_pw,
        first_name=data.get("first_name"),
        last_name=data.get("last_name")
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        response = jsonify({
            "message": f"User created successfully with ID {new_user.id}",
            "data": {"email": new_user.email}
        })
        status_code = 201
    except Exception as e:
        print(f"Error creating user: {e}")
        db.rollback()
        response = jsonify({"error": "Failed to create user"})
        status_code = 400
    finally:
        db.close()
    return response, status_code
