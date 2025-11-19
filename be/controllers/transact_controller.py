# Transactions Controller File

import models
from db import SessionLocal
from utils.common import check_exists
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.sql import func
from datetime import datetime


transact_bp = Blueprint("transact_bp", __name__, url_prefix="/transactions")

@transact_bp.route("", methods=["GET"])
@jwt_required()
def get_transactions():
    user_id = int(get_jwt_identity())
    db = SessionLocal()
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if not user:
        db.close()
        return jsonify({"error": "User not found"}), 404

    if user.role == "admin":
        transactions = db.query(models.Transaction).all()
    else:
        transactions = (
            db.query(models.Transaction)
            .filter(models.Transaction.user_id == user_id)
            .all()
        )

    db.close()
    return jsonify(
        [
            {
                "id": t.id,
                "user_id": t.user_id,
                "amount": float(t.amount),
                "category_id": t.category_id,
                "description": t.description,
                "type": t.type.value,
                "transaction-date": (
                    t.transaction_date.isoformat() if t.transaction_date else None
                ),
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            }
            for t in transactions
        ]
    )


@transact_bp.route("", methods=["POST"])
@jwt_required()
def create_transact():
    db = SessionLocal()
    user_id = int(get_jwt_identity())    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user: 
        return jsonify({"error": "User not found"}), 404
    
    data = request.get_json()
    
    checker = {
        "user_id": user_id,
        "category_id": data["category_id"],
        "amount": data["amount"],
        "description": data.get("description"),
        "type": models.TransactionType(data["type"].lower()),
        "transaction_date": datetime.strptime(data["transaction_date"], "%d-%m-%Y"),
    }

    if check_exists(db, models.Transaction, checker):
        return jsonify({"error": "this transaction already exists"}), 400

    new_transact = models.Transaction(**checker)

    try:
        db.add(new_transact)
        db.commit()
        db.refresh(new_transact)
        response = jsonify(
            {"message": f"New Transaction added with ID {new_transact.id}"}
        )
        status_code = 201
    except Exception as e:
        print(f"Error adding transaction: {e}")
        db.rollback()
        response = jsonify({"error": "Failed to add transaction"})
        status_code = 400
    finally:
        db.close()

    return response, status_code


@transact_bp.route("/group/type", methods=["GET"])
@jwt_required()
def group_transactions_by_type():
    db = SessionLocal()
    
    user_id = int(get_jwt_identity())
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user: 
        return jsonify({"error": "User not found"}), 404

    try:
        if user.role == "admin": 
            results = (db.query(models.Transaction.type, func.sum(models.Transaction.amount))
                       .group_by(models.Transaction.type)
                       .all()
                       )
        else:
            # GROUP BY type for ONLY that user
            results = (
                db.query(models.Transaction.type, func.sum(models.Transaction.amount))
                .filter(models.Transaction.user_id == user_id)
                .group_by(models.Transaction.type)
                .all()
            )

        grouped = {t.value: float(total) for t, total in results}

        return jsonify(grouped), 200

    except Exception as e:
        print(f"Error grouping transactions by type: {e}")
        return jsonify({"error": "Failed to group transactions"}), 500

    finally:
        db.close()


@transact_bp.route("/group/type-category", methods=["GET"])
@jwt_required()
def group_transacts_by_type_cat():
    db = SessionLocal()
    user_id = int(get_jwt_identity())
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if not user: 
        return jsonify({"error": "User not found"}), 404

    try:
        if user.role == "admin": 
            results = (
                db.query(
                    models.Transaction.type, 
                    models.Transaction.category_id, 
                    func.sum(models.Transaction.amount),
                )
                .group_by(models.Transaction.type, models.Transaction.category_id)
                .all()
            )
        else: 
            # GROUP BY type and category for ONLY that user
            results = (
                db.query(
                    models.Transaction.type,
                    models.Transaction.category_id,
                    func.sum(models.Transaction.amount),
                )
                .filter(models.Transaction.user_id == user_id)
                .group_by(models.Transaction.type, models.Transaction.category_id)
                .all()
            )

        grouped = {}
        for tx_type, category_id, total in results:
            tx_type = tx_type.value  # enum → string

            if tx_type not in grouped:
                grouped[tx_type] = []

            grouped[tx_type].append(
                {"category_id": category_id, "total_amount": float(total)}
            )

        return jsonify(grouped), 200

    except Exception as e:
        print(f"Error grouping transactions by type+category: {e}")
        return jsonify({"error": "Failed to group transactions"}), 500

    finally:
        db.close()
