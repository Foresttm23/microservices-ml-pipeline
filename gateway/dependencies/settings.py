from gateway.core.config import get_settings
from gateway.core.config import GatewaySettings
from typing import Annotated
from fastapi import Depends

GatewaySettingsDep = Annotated[GatewaySettings, Depends(get_settings)]
