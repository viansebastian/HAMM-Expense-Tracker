# API Controller file
import models
from db import SessionLocal, engine
from flask import Flask, jsonify, request


app = Flask(__name__)

# # create tables if not exist
models.Base.metadata.create_all(bind=engine)


# get requests
@app.route("/transactions", methods=["GET"])
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


@app.route("/users", methods=["GET"])
def get_users():
    db = SessionLocal()
    users = db.query(models.User).all()
    db.close()
    return jsonify(
        [
            {
                "id": u.id,
                "email": u.email,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "updated_at": u.updated_at.isoformat() if u.updated_at else None,
            }
            for u in users
        ]
    )


@app.route("/categories", methods=["GET"])
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


@app.route("/budgets", methods=["GET"])
def get_budgets():
    db = SessionLocal()
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


if __name__ == "__main__":
    app.run(debug=True)
