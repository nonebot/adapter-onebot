from nonebot import get_adapter
from nonebot.adapters.onebot.v12 import Adapter


def test_config():
    adapter = get_adapter(Adapter)
    config = adapter.onebot_config

    assert config.onebot_access_token == "test2"
