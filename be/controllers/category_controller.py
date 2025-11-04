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


@category_bp.route("/<int:category_id>", methods=["PUT"])
def update_category(category_id):
    db = SessionLocal()
    data = request.get_json()

    try:
        # Ensure user_id is provided
        if "user_id" not in data:
            return jsonify({"error": "user_id is required"}), 400

        category = db.query(models.Category).filter(
            models.Category.id == category_id,
            models.Category.user_id == data["user_id"]
        ).first()

        if not category:
            return jsonify({"error": "Category not found or not owned by this user"}), 404

        # Update only allowed fields
        if "name" in data:
            category.name = data["name"]
        if "type" in data:
            category.type = models.TransactionType(data["type"].lower())

        db.commit()
        db.refresh(category)

        return jsonify({
            "message": f"Category with ID {category_id} updated successfully",
            "data": {
                "id": category.id,
                "name": category.name,
                "type": category.type.value
            }
        }), 200

    except Exception as e:
        print(f"Error updating category: {e}")
        db.rollback()
        return jsonify({"error": "Failed to update category"}), 400
    finally:
        db.close()


@category_bp.route("/<int:category_id>", methods=["DELETE"])
def delete_category(category_id):
    db = SessionLocal()
    data = request.get_json()  

    try:
        if not data or "user_id" not in data:
            return jsonify({"error": "user_id is required"}), 400

        category = db.query(models.Category).filter(
            models.Category.id == category_id,
            models.Category.user_id == data["user_id"]
        ).first()

        if not category:
            return jsonify({"error": "Category not found or not owned by this user"}), 404

        db.delete(category)
        db.commit()

        return jsonify({
            "message": f"Category with ID {category_id} deleted successfully"
        }), 200

    except Exception as e:
        print(f"Error deleting category: {e}")
        db.rollback()
        return jsonify({"error": "Failed to delete category"}), 400
    finally:
        db.close()
