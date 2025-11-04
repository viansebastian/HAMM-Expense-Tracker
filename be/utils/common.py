# contains common helper functions 

from sqlalchemy.exc import SQLAlchemyError


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
