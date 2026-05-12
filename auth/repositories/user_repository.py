from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.db.models import UserModel
from auth.schemas.user import UserEntity
from shared.repositories import BaseRepository


class UserRepository(BaseRepository[UserModel, UserEntity]):
    """Repository for User entities."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model_class=UserModel, entity_class=UserEntity)

    async def get_by_email(self, email: str) -> UserEntity | None:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self.map_model_to_entity(model) if model else None

    async def get_by_id(self, entity_id: UUID) -> UserEntity | None:
        model = await self.session.get(UserModel, entity_id)
        return self.map_model_to_entity(model) if model else None

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[UserEntity]:
        stmt = select(UserModel).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return [self.map_model_to_entity(model) for model in result.scalars().all()]

    async def create(self, entity: UserEntity) -> UserEntity:
        model = self.map_entity_to_model(entity)
        self.session.add(model)
        await self.session.flush()
        return self.map_model_to_entity(model)

    async def update(self, entity_id: UUID, entity: UserEntity) -> UserEntity | None:
        model = await self.session.get(UserModel, entity_id)
        if not model:
            return None
        self.update_model_from_entity(model, entity)
        await self.session.flush()
        return self.map_model_to_entity(model)

    async def delete(self, entity_id: UUID) -> bool:
        model = await self.session.get(UserModel, entity_id)
        if not model:
            return False
        await self.session.delete(model)
        await self.session.flush()
        return True
