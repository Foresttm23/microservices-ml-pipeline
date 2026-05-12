from typing import Annotated
from uuid import UUID

from fastapi import Header

from shared.core import CORRELATION_ID_HEADER, USER_ID_HEADER

CorrelationIdDep = Annotated[UUID, Header(..., alias=CORRELATION_ID_HEADER)]
UserIdDep = Annotated[str, Header(..., alias=USER_ID_HEADER)]
