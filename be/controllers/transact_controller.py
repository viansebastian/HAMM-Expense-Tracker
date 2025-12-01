# Transactions Controller File

import models
import numpy as np 
from db import SessionLocal
from utils.common import check_exists
from sqlalchemy.sql import func
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sklearn.linear_model import LinearRegression


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

    # 1️⃣ Validate category exists and belongs to this user (unless admin)
    category = db.query(models.Category).filter(models.Category.id == data["category_id"]).first()

    if not category:
        return jsonify({"error": "Category not found"}), 400

    if user.role != "admin" and category.user_id != user_id:
        return jsonify({"error": "You do not have access to this category"}), 403

    # 2️⃣ Validate category type matches transaction type
    # Example: category.type = "expense" but user inputs "income"
    input_type = models.TransactionType(data["type"].lower())

    if category.type.value.lower() != input_type.value.lower():
        return jsonify({
            "error": f"Category type mismatch: '{category.name}' is '{category.type.value}', "
                     f"but you submitted '{input_type.value}'"
        }), 400

    # 3️⃣ Prepare fields
    checker = {
        "user_id": user_id,
        "category_id": data["category_id"],
        "amount": data["amount"],
        "description": data.get("description"),
        "type": input_type,
        "transaction_date": datetime.strptime(data["transaction_date"], "%d-%m-%Y"),
    }

    # 4️⃣ Check if transaction already exists
    if check_exists(db, models.Transaction, checker):
        return jsonify({"error": "This transaction already exists"}), 400

    # 5️⃣ Create the transaction
    new_transact = models.Transaction(**checker)

    try:
        db.add(new_transact)
        db.commit()
        db.refresh(new_transact)
        response = jsonify({"message": f"New Transaction added with ID {new_transact.id}"})
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


@transact_bp.route("/predict/type", methods=["GET"])
@jwt_required()
def predict_by_type(): 
    db = SessionLocal() 
    user_id = int(get_jwt_identity())
    
    tx_type = request.args.get("type")
    if tx_type not in ["income", "expense"]: 
        return jsonify({"error": "Invalid type"}), 400
    
    try: 
        transactions = (
            db.query(models.Transaction)
            .filter(
                models.Transaction.user_id == user_id, 
                models.Transaction.type == tx_type
            )
            .all()
        )
        if not transactions:
            return jsonify({"error": "No transactions found"}), 404
        
        monthly = {} 
        for t in transactions: 
            ym = extract_year_month(t.transaction_date)
            monthly[ym] = monthly.get(ym, 0) + t.amount
        
        if len(monthly) < 3: 
            return jsonify({"error": "Not enough data. Need more than 3 months"}), 400
        
        sorted_items = sorted(monthly.items())
        months_idx = list(range(len(sorted_items)))
        amounts = [amt for _, amt in sorted_items]
        
        predictions = predict_linear_reg(months_idx, amounts, future=2)
        
        return jsonify({
            "history": sorted_items, 
            "predicted_next_months": predictions
        }), 200
            
    except Exception as e: 
        print("Prediction error: ", str(e))
        return jsonify({"error": f"Prediction Failed: {str(e)}"}), 500
    
    finally: 
        db.close()


@transact_bp.route("/predict/type-category", methods=["GET"])
@jwt_required()
def predict_by_type_category():
    db = SessionLocal() 
    user_id = int(get_jwt_identity())
    
    category_id = request.args.get("category_id", type=int)
    
    if category_id is None: 
        return jsonify({"error": "category_id is required"}), 400
    
    try: 
        transactions = (
            db.query(models.Transaction)
            .filter(
                models.Transaction.user_id == user_id, 
                models.Transaction.category_id == category_id
            )
            .all()
        )
        if not transactions: 
            return jsonify({"error": "No data for this category"}), 404
        
        monthly = {}
        for t in transactions: 
            ym = extract_year_month(t.transaction_date)
            monthly[ym] = monthly.get(ym, 0) + t.amount
            
        if len(monthly) < 3: 
            return jsonify({"error": "Not enough data. Need more than 3 months."}), 400 
        
        sorted_items = sorted(monthly.items())
        months_idx = list(range(len(sorted_items)))
        amounts = [amt for _, amt in sorted_items]
        
        predictions = predict_linear_reg(months_idx, amounts, future=2)

        return jsonify({
            "history": sorted_items, 
            "predicted_next_months": predictions
        }), 200 
        
    except Exception as e: 
        print("prediction category error: ", str(e))
        return jsonify({"error": "Failed to predict"}), 500
    
    finally: 
        db.close()
    

def predict_linear_reg(months_list, amounts_list, future=2): 
    x = np.array(months_list).reshape(-1, 1)
    y = np.array(amounts_list)
    
    model = LinearRegression() 
    model.fit(x, y)
    
    future_x = np.arange(len(months_list), len(months_list) + future).reshape(-1, 1)
    predicted = model.predict(future_x)
    
    return predicted.tolist() 

def extract_year_month(date_obj): 
    return date_obj.year * 100 + date_obj.month