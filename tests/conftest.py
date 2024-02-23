from pathlib import Path

import pytest
from nonebug import NONEBOT_INIT_KWARGS

import nonebot
import nonebot.adapters

nonebot.adapters.__path__.append(  # type: ignore
    str((Path(__file__).parent.parent / "nonebot" / "adapters").resolve())
)

from nonebot.adapters.onebot import V11Adapter, V12Adapter


def pytest_configure(config: pytest.Config) -> None:
    config.stash[NONEBOT_INIT_KWARGS] = {
        "onebot_access_token": "test1",
        "onebot_v12_access_token": "test2",
    }


@pytest.fixture(scope="session", autouse=True)
def _init_adapter(nonebug_init: None):
    driver = nonebot.get_driver()
    driver.register_adapter(V11Adapter)
    driver.register_adapter(V12Adapter)


# @pytest.fixture
# def app(nonebug_init: None):
#     yield App()

#     from nonebot.adapters.onebot.v11 import Adapter as AdapterV11
#     from nonebot.adapters.onebot.v12 import Adapter as AdapterV12

#     nonebot.get_adapter(AdapterV11).bots.clear()
#     nonebot.get_adapter(AdapterV12).bots.clear()
#     nonebot.get_driver().bots.clear()
