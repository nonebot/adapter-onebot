from typing import Set, Optional

from pydantic import Field, AnyUrl, BaseModel


class WSUrl(AnyUrl):
    allow_schemes = {"ws", "wss"}


class Config(BaseModel):
    """
    OneBot 配置类

    :配置项:

      - ``onebot_access_token``: OneBot 协议授权令牌
      - ``onebot_secret``: OneBot HTTP 上报数据签名口令
      - ``onebot_ws_urls``: OneBot 正向 Websocket 连接目标 URL 集合
    """

    onebot_access_token: Optional[str] = Field(
        default=None, alias="onebot_access_token"
    )
    onebot_secret: Optional[str] = Field(default=None)
    onebot_ws_urls: Set[WSUrl] = Field(default_factory=set)

    class Config:
        extra = "ignore"
