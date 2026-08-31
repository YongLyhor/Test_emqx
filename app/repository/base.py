from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
from app.core.database import Base

from app.core.exceptions import DatabaseError, RecordNotFoundError
from app.core.logging import logger



ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations"""
    
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db
    
    def get_by_id(self, id: Any) -> Optional[ModelType]:
        """Get record by ID"""
        try:
            return self.db.query(self.model).filter(self.model.id == id).first()
        except Exception as e:
            logger.error(f"Error fetching {self.model.__name__} by ID {id}: {e}")
            raise DatabaseError(f"Failed to fetch record: {str(e)}")
    
    def get_all(self, skip: int = 0, limit: int = 100, **filters) -> List[ModelType]:
        """Get all records with pagination and filters"""
        try:
            query = self.db.query(self.model)
            
            # Apply filters
            for key, value in filters.items():
                if value is not None:
                    if hasattr(self.model, key):
                        query = query.filter(getattr(self.model, key) == value)
            
            return query.offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error fetching {self.model.__name__}: {e}")
            raise DatabaseError(f"Failed to fetch records: {str(e)}")
    
    def count(self, **filters) -> int:
        """Count records with filters"""
        try:
            query = self.db.query(self.model)
            for key, value in filters.items():
                if value is not None:
                    if hasattr(self.model, key):
                        query = query.filter(getattr(self.model, key) == value)
            return query.count()
        except Exception as e:
            logger.error(f"Error counting {self.model.__name__}: {e}")
            raise DatabaseError(f"Failed to count records: {str(e)}")
    
    def create(self, **kwargs) -> ModelType:
        """Create a new record"""
        try:
            instance = self.model(**kwargs)
            self.db.add(instance)
            self.db.commit()
            self.db.refresh(instance)
            logger.info(f"Created {self.model.__name__}: {instance}")
            return instance
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise DatabaseError(f"Failed to create record: {str(e)}")
    
    def create_bulk(self, items: List[Dict[str, Any]]) -> List[ModelType]:
        """Create multiple records"""
        try:
            instances = [self.model(**item) for item in items]
            self.db.add_all(instances)
            self.db.commit()
            for instance in instances:
                self.db.refresh(instance)
            logger.info(f"Created {len(instances)} {self.model.__name__} records")
            return instances
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error bulk creating {self.model.__name__}: {e}")
            raise DatabaseError(f"Failed to bulk create records: {str(e)}")
    
    def update(self, id: Any, **kwargs) -> ModelType:
        """Update a record"""
        try:
            instance = self.get_by_id(id)
            if not instance:
                raise RecordNotFoundError(self.model.__name__, id)
            
            for key, value in kwargs.items():
                if value is not None and hasattr(instance, key):
                    setattr(instance, key, value)
            
            self.db.commit()
            self.db.refresh(instance)
            logger.info(f"Updated {self.model.__name__} {id}")
            return instance
        except RecordNotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating {self.model.__name__} {id}: {e}")
            raise DatabaseError(f"Failed to update record: {str(e)}")
    
    def delete(self, id: Any) -> bool:
        """Delete a record"""
        try:
            instance = self.get_by_id(id)
            if not instance:
                raise RecordNotFoundError(self.model.__name__, id)
            
            self.db.delete(instance)
            self.db.commit()
            logger.info(f"Deleted {self.model.__name__} {id}")
            return True
        except RecordNotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting {self.model.__name__} {id}: {e}")
            raise DatabaseError(f"Failed to delete record: {str(e)}")
    
    def delete_bulk(self, ids: List[Any]) -> int:
        """Delete multiple records"""
        try:
            deleted = self.db.query(self.model).filter(self.model.id.in_(ids)).delete(synchronize_session=False)
            self.db.commit()
            logger.info(f"Deleted {deleted} {self.model.__name__} records")
            return deleted
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error bulk deleting {self.model.__name__}: {e}")
            raise DatabaseError(f"Failed to bulk delete records: {str(e)}")
    
    def exists(self, **filters) -> bool:
        """Check if record exists with filters"""
        try:
            query = self.db.query(self.model)
            for key, value in filters.items():
                if value is not None:
                    if hasattr(self.model, key):
                        query = query.filter(getattr(self.model, key) == value)
            return query.first() is not None
        except Exception as e:
            logger.error(f"Error checking existence {self.model.__name__}: {e}")
            return False
    
    def get_or_create(self, defaults: Dict[str, Any] = None, **kwargs) -> tuple[ModelType, bool]:
        """Get or create a record"""
        try:
            instance = self.db.query(self.model).filter_by(**kwargs).first()
            if instance:
                return instance, False
            
            # Merge defaults with kwargs
            if defaults:
                kwargs.update(defaults)
            
            instance = self.model(**kwargs)
            self.db.add(instance)
            self.db.commit()
            self.db.refresh(instance)
            logger.info(f"Created {self.model.__name__}: {instance}")
            return instance, True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in get_or_create {self.model.__name__}: {e}")
            raise DatabaseError(f"Failed to get or create record: {str(e)}")