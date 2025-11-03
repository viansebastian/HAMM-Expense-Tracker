# Transactions Controller File

import models
from db import SessionLocal
from utils.common import check_exists
from flask import Blueprint, jsonify, request
from datetime import datetime


transact_bp = Blueprint("transact_bp", __name__, url_prefix="/transactions")

@transact_bp.route("", methods=["GET"])
def get_transactions():
    db = SessionLocal()
    transactions = db.query(models.Transaction).all()
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
def create_transact(): 
    db = SessionLocal() 
    data = request.get_json() 
    
    checker = {
        "user_id": data['user_id'], 
        "category_id": data['category_id'], 
        "amount": data['amount'], 
        "description": data.get('description'), 
        "type": models.TransactionType(data['type'].lower()), 
        "transaction_date": datetime.strptime(data['transaction_date'], '%d-%m-%Y')
    }
    
    if check_exists(db, models.Transaction, checker):
        return jsonify({
            "error": "this transaction already exists"
        }), 400 
        
    new_transact = models.Transaction(**checker)
    
    try:
        db.add(new_transact)
        db.commit()
        db.refresh(new_transact)
        response = jsonify({
            "message": f"New Transaction added with ID {new_transact.id}"
        })
        status_code = 201
    except Exception as e: 
        print(f'Error adding transaction: {e}')
        db.rollback()
        response = jsonify({
            "error": "Failed to add transaction"
        })
        status_code = 400
    finally: 
        db.close()

    return response, status_code
    