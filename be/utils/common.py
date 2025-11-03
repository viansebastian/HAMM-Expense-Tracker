# contains common helper functions 

from sqlalchemy.exc import SQLAlchemyError


# def check_exists(db, model, filters: dict): 
#     """
#     Checks if a record already exists in the database for the given model and filters.

#     Args:
#         db: SQLAlchemy session
#         model: SQLAlchemy model class (e.g., models.User)
#         filters (dict): Key-value pairs for filtering (e.g., {"email": "test@example.com"})

#     Returns:
#         bool: True if record exists, False otherwise

#     Raises:
#         SQLAlchemyError: If query fails
#     """
#     try: 
#         query = db.query(model)
#         for key, value in filters.items():
#             if hasattr(model, key): 
#                 query = query.filter(getattr(model, key) == value)
#             else: 
#                 raise AttributeError(f'{model.__name__} has no attribute {key}')
#         return db.query(db.query(model).filter(filters).exists()).scalar()
#     except SQLAlchemyError as e: 
#         print(f'DB error while checking existence: {e}')
#         raise

def check_exists(db, model, filters: dict): 
    """
    Checks if a record already exists in the database for the given model and filters.
    """
    try: 
        query = db.query(model)
        for key, value in filters.items():
            if hasattr(model, key): 
                query = query.filter(getattr(model, key) == value)
            else: 
                raise AttributeError(f'{model.__name__} has no attribute {key}')

        # ✅ Build EXISTS subquery using the filtered query
        exists_query = query.exists()
        return db.query(exists_query).scalar()

    except SQLAlchemyError as e: 
        print(f'DB error while checking existence: {e}')
        raise
