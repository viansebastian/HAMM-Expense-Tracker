# Categories Controllers File

import models
from db import SessionLocal
from utils.common import check_exists
from flask import Blueprint, jsonify, request


category_bp = Blueprint("category_bp", __name__, url_prefix="/categories")

@category_bp.route("", methods=["GET"])
def get_categories():
    db = SessionLocal()
    categories = db.query(models.Category).all()
    db.close()
    return jsonify(
        [
            {
                "id": c.id,
                "user_id": c.user_id,
                "name": c.name,
                "type": c.type.value,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in categories
        ]
    )


@category_bp.route("", methods=["POST"])
def create_category(): 
    db = SessionLocal() 
    data = request.get_json()
    
    checker = {
        "user_id" : data['user_id'],
        "name": data['name'], 
        "type": models.TransactionType(data['type'].lower())
    }
    
    if check_exists(db, models.Category, checker): 
        return jsonify({
            "error": "this category already exists"
        }), 400
        
    new_category = models.Category(**checker)
    
    try:
        db.add(new_category)
        db.commit()
        db.refresh(new_category)
        response = jsonify({
            "message": f"Category created successfully with ID {new_category.id}",
            "data" : {
                "category_name": new_category.name, 
                "type": new_category.type
            }
        })
        status_code = 201
    except Exception as e: 
        print(f'Error creating Category: {e}')
        db.rollback()
        response = jsonify({
            "error": "Failed to create Category"
        })
        status_code = 400
    finally: 
        db.close()

    return response, status_code
