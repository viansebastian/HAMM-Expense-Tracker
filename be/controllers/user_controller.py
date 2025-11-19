# Users Controller File

import models
from db import SessionLocal
from utils.common import check_exists
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta


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


@user_bp.route("/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            return jsonify({"error": f"User with ID {user_id} not found"}), 404
        
        db.delete(user)
        db.commit()
        return jsonify({"message": f"User with ID {user_id} deleted successfully"}), 200
    except Exception as e:
        print(f"Error deleting user: {e}")
        db.rollback()
        return jsonify({"error": "Failed to delete user"}), 400
    finally:
        db.close()


@user_bp.route("/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    db = SessionLocal()
    data = request.get_json()

    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            return jsonify({"error": f"User with ID {user_id} not found"}), 404

        # Update fields if provided
        if "email" in data:
            user.email = data["email"]
        if "first_name" in data:
            user.first_name = data["first_name"]
        if "last_name" in data:
            user.last_name = data["last_name"]
        if "password" in data:
            user.password_hash = generate_password_hash(data["password"])

        db.commit()
        db.refresh(user)

        return jsonify({
            "message": f"User with ID {user_id} updated successfully",
            "data": {
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        }), 200
    except Exception as e:
        print(f"Error updating user: {e}")
        db.rollback()
        return jsonify({"error": "Failed to update user"}), 400
    finally:
        db.close()


@user_bp.route("/login", methods=["POST"])
def login_user(): 
    db = SessionLocal()  
    data = request.get_json()
    
    email = data.get("email")
    password = data.get("password")
    
    user = db.query(models.User).filter(models.User.email == email).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid email or password"}), 401
    
    access_token = create_access_token(
        identity=str(user.id), 
        expires_delta=timedelta(hours=2)
    )
    
    return jsonify({
        "message": "Login successful", 
        "access_token": access_token,
        "user_id": user.id, 
        "role": user.role
    }), 200