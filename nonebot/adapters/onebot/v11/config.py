from typing import Dict, Optional

from pydantic import Field, AnyUrl, BaseModel


# priority: alias > origin
class Config(BaseModel):
    """
    OneBot 配置类

    :配置项:

      - ``access_token`` / ``onebot_access_token``: OneBot 协议授权令牌
      - ``secret`` / ``onebot_secret``: OneBot HTTP 上报数据签名口令
      - ``ws_urls`` / ``onebot_ws_urls``: OneBot 正向 Websocket 连接 Bot ID、目标 URL 字典
    """

    access_token: Optional[str] = Field(default=None, alias="onebot_access_token")
    secret: Optional[str] = Field(default=None, alias="onebot_secret")
    ws_urls: Dict[str, AnyUrl] = Field(default_factory=set, alias="onebot_ws_urls")

    class Config:
        extra = "ignore"
        allow_population_by_field_name = True
