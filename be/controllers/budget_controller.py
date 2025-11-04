# Budgets Controllers File

import models
from db import SessionLocal
from utils.common import check_exists
from flask import Blueprint, jsonify, request
from datetime import datetime


budget_bp = Blueprint("budget_bp", __name__, url_prefix="/budgets")

@budget_bp.route("", methods=["GET"])
def get_budgets():
    db = SessionLocal()
    print(db.bind.url)
    budgets = db.query(models.Budget).all()
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
def create_budget(): 
    db = SessionLocal()
    data = request.get_json()
    
    checker = {
        "user_id": data['user_id'], 
        "category_id": data['category_id'],
        "budget_amount": data['budget_amount'], 
        "start_date": datetime.strptime(data['start_date'], '%d-%m-%Y'),
        "end_date": datetime.strptime(data['end_date'], '%d-%m-%Y')
    }
    
    if check_exists(db, models.Budget, checker): 
        return jsonify({
            "error": "this budget already exists"
        }), 400
    
    new_budget = models.Budget(**checker)
    
    try:
        db.add(new_budget)
        db.commit()
        db.refresh(new_budget)
        response = jsonify({
            "message": f"Budget created successfully with ID {new_budget.id}",
            "data": {
                "budget_amount": new_budget.budget_amount, 
                "start": new_budget.start_date, 
                "end": new_budget.end_date
            } 
        })
        status_code = 201
    except Exception as e: 
        print(f'Error creating Budget: {e}')
        db.rollback()
        response = jsonify({
            "error": "Failed to create Budget"
        })
        status_code = 400
    finally: 
        db.close()

    return response, status_code
    

@budget_bp.route("/<int:budget_id>", methods=["PUT"])
def update_budget(budget_id):
    db = SessionLocal()
    data = request.get_json()

    try:
        if "user_id" not in data:
            return jsonify({"error": "user_id is required"}), 400

        # Find budget owned by this user
        budget = db.query(models.Budget).filter(
            models.Budget.id == budget_id,
            models.Budget.user_id == data["user_id"]
        ).first()

        if not budget:
            return jsonify({"error": "Budget not found or not owned by this user"}), 404

        # Update only allowed fields
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
                "budget_amount": budget.budget_amount,
                "start_date": budget.start_date.strftime("%Y-%m-%d"),
                "end_date": budget.end_date.strftime("%Y-%m-%d")
            }
        }), 200

    except Exception as e:
        print(f"Error updating Budget: {e}")
        db.rollback()
        return jsonify({"error": "Failed to update Budget"}), 400
    finally:
        db.close()


@budget_bp.route("/<int:budget_id>", methods=["DELETE"])
def delete_budget(budget_id):
    db = SessionLocal()
    data = request.get_json()  # expects { "user_id": <int> }

    try:
        if not data or "user_id" not in data:
            return jsonify({"error": "user_id is required"}), 400

        budget = db.query(models.Budget).filter(
            models.Budget.id == budget_id,
            models.Budget.user_id == data["user_id"]
        ).first()

        if not budget:
            return jsonify({"error": "Budget not found or not owned by this user"}), 404

        db.delete(budget)
        db.commit()

        return jsonify({
            "message": f"Budget with ID {budget_id} deleted successfully"
        }), 200

    except Exception as e:
        print(f"Error deleting Budget: {e}")
        db.rollback()
        return jsonify({"error": "Failed to delete Budget"}), 400
    finally:
        db.close()
