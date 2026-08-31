from typing import Generic, TypeVar, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.repository.base import BaseRepository
from app.core.exceptions import DatabaseError, ValidationError
from app.core.logging import logger

RepositoryType = TypeVar("RepositoryType", bound=BaseRepository)

class BaseService(Generic[RepositoryType]):
    """Base service with common business logic"""
    
    def __init__(self, repository: RepositoryType, db: Session):
        self.repository = repository
        self.db = db
    
    def get_by_id(self, id: Any) -> Optional[Any]:
        """Get record by ID"""
        try:
            return self.repository.get_by_id(id)
        except Exception as e:
            logger.error(f"Error in get_by_id: {e}")
            raise
    
    def get_all(self, skip: int = 0, limit: int = 100, **filters) -> List[Any]:
        """Get all records with pagination"""
        try:
            return self.repository.get_all(skip=skip, limit=limit, **filters)
        except Exception as e:
            logger.error(f"Error in get_all: {e}")
            raise
    
    def count(self, **filters) -> int:
        """Count records"""
        try:
            return self.repository.count(**filters)
        except Exception as e:
            logger.error(f"Error in count: {e}")
            raise
    
    def create(self, **kwargs) -> Any:
        """Create a new record"""
        try:
            # Validate before create
            self.validate_create(**kwargs)
            return self.repository.create(**kwargs)
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error in create: {e}")
            raise DatabaseError(f"Failed to create record: {str(e)}")
    
    def update(self, id: Any, **kwargs) -> Any:
        """Update a record"""
        try:
            # Validate before update
            self.validate_update(id, **kwargs)
            return self.repository.update(id, **kwargs)
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise DatabaseError(f"Failed to update record: {str(e)}")
    
    def delete(self, id: Any) -> bool:
        """Delete a record"""
        try:
            # Validate before delete
            self.validate_delete(id)
            return self.repository.delete(id)
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error in delete: {e}")
            raise DatabaseError(f"Failed to delete record: {str(e)}")
    
    def validate_create(self, **kwargs) -> None:
        """Validate data before create - override in child classes"""
        pass
    
    def validate_update(self, id: Any, **kwargs) -> None:
        """Validate data before update - override in child classes"""
        pass
    
    def validate_delete(self, id: Any) -> None:
        """Validate before delete - override in child classes"""
        pass