from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.db.models import UserModel
from auth.schemas.user import UserEntity
from shared.repositories import BaseRepository


class UserRepository(BaseRepository[UserModel, UserEntity]):
    """Repository for User entities."""

    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session, model_class=UserModel, entity_class=UserEntity
        )

    async def get_by_email(self, email: str) -> UserEntity | None:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self.map_model_to_entity(model) if model else None
