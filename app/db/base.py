from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy.ext.asyncio import AsyncAttrs

class Base(AsyncAttrs, DeclarativeBase):
    """
    Base class for all SQLAlchemy models in the application.
    It automatically sets the __tablename__ based on the class name.
    """
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        # Converts class name from 'ModelName' to 'model_name_s'
        return cls.__name__.lower() + "s"