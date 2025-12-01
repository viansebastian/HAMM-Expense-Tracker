# Budgets Controllers File

from be import models
from be.db import SessionLocal
from be.utils.common import check_exists
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime


budget_bp = Blueprint("budget_bp", __name__, url_prefix="/budgets")

@budget_bp.route("", methods=["GET"])
@jwt_required()
def get_budgets():
    db = SessionLocal()
    user_id = int(get_jwt_identity())
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if not user: 
        return jsonify({"error": "User not found"}), 404
    
    if user.role == "admin": 
        budgets = db.query(models.Budget).all()
    else: 
        budgets = (
            db.query(models.Budget)
            .filter(models.Budget.user_id == user_id)
            .all()
        )
        
    db.close()
    
    return jsonify(
        [
            {
                "id": b.id,
                "user_id": b.user_id,
                "category_id": b.category_id,
                "budget_amount": float(b.budget_amount),
                "start_date": b.start_date.isoformat() if b.start_date else None,
                "end_date": b.end_date.isoformat() if b.end_date else None,
                "created_at": b.created_at.isoformat() if b.created_at else None,
                "updated_at": b.updated_at.isoformat() if b.updated_at else None,
            }
            for b in budgets
        ]
    )


@budget_bp.route("", methods=["POST"])
@jwt_required()
def create_budget():
    db = SessionLocal()
    user_id = int(get_jwt_identity())
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()

    # Admin can create budget for any user_id
    if user.role == "admin" and "user_id" in data:
        owner_id = data["user_id"]
    else:
        owner_id = user_id

    try:
        new_budget = models.Budget(
            user_id=owner_id,
            category_id=data["category_id"],
            budget_amount=data["budget_amount"],
            start_date=datetime.strptime(data["start_date"], "%d-%m-%Y"),
            end_date=datetime.strptime(data["end_date"], "%d-%m-%Y"),
        )

        # Prevent duplicates
        checker = {
            "user_id": owner_id,
            "category_id": data["category_id"],
            "start_date": datetime.strptime(data["start_date"], "%d-%m-%Y"),
            "end_date": datetime.strptime(data["end_date"], "%d-%m-%Y"),
        }

        if check_exists(db, models.Budget, checker):
            return jsonify({"error": "This budget already exists"}), 400

        db.add(new_budget)
        db.commit()
        db.refresh(new_budget)

        return jsonify({
            "message": f"Budget created successfully with ID {new_budget.id}",
            "data": {
                "id": new_budget.id,
                "budget_amount": float(new_budget.budget_amount),
                "start_date": new_budget.start_date.isoformat(),
                "end_date": new_budget.end_date.isoformat(),
                "user_id": new_budget.user_id,
                "category_id": new_budget.category_id
            }
        }), 201

    except Exception as e:
        print(f"Error creating budget: {e}")
        db.rollback()
        return jsonify({"error": "Failed to create budget"}), 400

    finally:
        db.close()


@budget_bp.route("/<int:budget_id>", methods=["PUT"])
@jwt_required()
def update_budget(budget_id):
    db = SessionLocal()
    user_id = int(get_jwt_identity())
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()

    try:
        # If admin → can edit any budget; normal user → only own budgets
        if user.role == "admin":
            budget = db.query(models.Budget).filter(models.Budget.id == budget_id).first()
        else:
            budget = db.query(models.Budget).filter(
                models.Budget.id == budget_id,
                models.Budget.user_id == user_id
            ).first()

        if not budget:
            return jsonify({"error": "Budget not found or not owned by this user"}), 404

        # Update fields only if provided
        if "budget_amount" in data:
            budget.budget_amount = data["budget_amount"]
        if "start_date" in data:
            budget.start_date = datetime.strptime(data["start_date"], "%d-%m-%Y")
        if "end_date" in data:
            budget.end_date = datetime.strptime(data["end_date"], "%d-%m-%Y")

        db.commit()
        db.refresh(budget)

        return jsonify({
            "message": f"Budget with ID {budget_id} updated successfully",
            "data": {
                "id": budget.id,
                "user_id": budget.user_id,
                "category_id": budget.category_id,
                "budget_amount": float(budget.budget_amount),
                "start_date": budget.start_date.isoformat(),
                "end_date": budget.end_date.isoformat()
            }
        }), 200

    except Exception as e:
        print(f"Error updating budget: {e}")
        db.rollback()
        return jsonify({"error": "Failed to update budget"}), 400

    finally:
        db.close()


@budget_bp.route("/<int:budget_id>", methods=["DELETE"])
@jwt_required()
def delete_budget(budget_id):
    db = SessionLocal()

    user_id = int(get_jwt_identity())
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        if user.role == "admin":
            budget = db.query(models.Budget).filter(models.Budget.id == budget_id).first()
        else:
            budget = db.query(models.Budget).filter(
                models.Budget.id == budget_id,
                models.Budget.user_id == user_id
            ).first()

        if not budget:
            return jsonify({"error": "Budget not found or not owned by this user"}), 404

        db.delete(budget)
        db.commit()

        return jsonify({"message": f"Budget with ID {budget_id} deleted successfully"}), 200

    except Exception as e:
        print(f"Error deleting budget: {e}")
        db.rollback()
        return jsonify({"error": "Failed to delete budget"}), 400

    finally:
        db.close()
        
        