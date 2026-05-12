from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.db.models import RefreshTokenModel
from auth.schemas.token import RefreshTokenEntity
from shared.repositories import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshTokenModel, RefreshTokenEntity]):
    """Repository for refresh tokens."""

    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session, model_class=RefreshTokenModel, entity_class=RefreshTokenEntity
        )

    async def get_by_jti(self, jti: UUID) -> RefreshTokenEntity | None:
        stmt = select(RefreshTokenModel).where(RefreshTokenModel.jti == jti)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self.map_model_to_entity(model) if model else None

    async def get_by_id(self, entity_id: UUID) -> RefreshTokenEntity | None:
        model = await self.session.get(RefreshTokenModel, entity_id)
        return self.map_model_to_entity(model) if model else None

    async def get_all(
        self, skip: int = 0, limit: int = 100
    ) -> list[RefreshTokenEntity]:
        stmt = select(RefreshTokenModel).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return [self.map_model_to_entity(model) for model in result.scalars().all()]

    async def create(self, entity: RefreshTokenEntity) -> RefreshTokenEntity:
        model = self.map_entity_to_model(entity)
        self.session.add(model)
        await self.session.flush()
        return self.map_model_to_entity(model)

    async def update(
        self, entity_id: UUID, entity: RefreshTokenEntity
    ) -> RefreshTokenEntity | None:
        model = await self.session.get(RefreshTokenModel, entity_id)
        if not model:
            return None
        self.update_model_from_entity(model, entity)
        await self.session.flush()
        return self.map_model_to_entity(model)

    async def delete(self, entity_id: UUID) -> bool:
        model = await self.session.get(RefreshTokenModel, entity_id)
        if not model:
            return False
        await self.session.delete(model)
        await self.session.flush()
        return True

    async def revoke(self, jti: UUID, replaced_by: UUID | None = None) -> None:
        stmt = select(RefreshTokenModel).where(RefreshTokenModel.jti == jti)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return
        if model.revoked_at is None:
            model.revoked_at = datetime.now(timezone.utc)
        model.replaced_by = replaced_by
        await self.session.flush()

    async def revoke_lineage(self, jti: UUID) -> None:
        current_jti: UUID | None = jti
        now = datetime.now(timezone.utc)
        while current_jti is not None:
            stmt = select(RefreshTokenModel).where(RefreshTokenModel.jti == current_jti)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            if not model:
                break
            if model.revoked_at is None:
                model.revoked_at = now
            current_jti = model.replaced_by
        await self.session.flush()

