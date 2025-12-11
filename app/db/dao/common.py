from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CommonDAO(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        **Parameters**
        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    async def refresh(self, session: AsyncSession, db_obj: ModelType) -> ModelType:
        await session.refresh(db_obj)
        return db_obj

    async def get_first(self, session: AsyncSession) -> Optional[ModelType]:
        return (await session.execute(select(self.model))).scalars().first()

    async def get(self, session: AsyncSession, id: int) -> Optional[ModelType]:
        result = await session.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_all(self, session: AsyncSession, *, offset: int = 0, limit: int = 25) -> List[ModelType]:
        result = await session.execute(select(self.model).offset(offset).limit(limit))
        return result.scalars().unique().all()

    async def filter(self, session: AsyncSession, *, offset: int = 0, limit: int = 25, **kwargs) -> List[ModelType]:
        query = select(self.model).offset(offset).limit(limit)

        # Create a list of filter conditions for each field provided in kwargs
        filter_conditions = []
        for field, values in kwargs.items():
            if isinstance(values, list):
                # If values is a list, create an OR condition for the field
                field_filter = or_(*[getattr(self.model, field) == value for value in values])
            else:
                # If a single value is provided, create a simple equality condition
                field_filter = getattr(self.model, field) == values

            filter_conditions.append(field_filter)

        if filter_conditions:
            query = query.filter(and_(*filter_conditions))

        result = await session.execute(query)
        return result.scalars().unique().all()

    async def create(self, session: AsyncSession, *, obj_in: CreateSchemaType, autocommit: bool = True) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        session.add(db_obj)
        if autocommit:
            await session.commit()
            await session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        session: AsyncSession,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
        autocommit: bool = True
    ) -> ModelType:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        session.add(db_obj)
        if autocommit:
            await session.commit()
            await session.refresh(db_obj)
        return db_obj

    async def remove(self, session: AsyncSession, *, id: int) -> ModelType:
        obj = await session.get(self.model, id)
        await session.delete(obj)
        await session.commit()
        return obj
