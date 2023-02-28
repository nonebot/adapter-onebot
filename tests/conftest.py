from pathlib import Path

import pytest
from nonebug import NONEBOT_INIT_KWARGS


def pytest_configure(config: pytest.Config) -> None:
    config.stash[NONEBOT_INIT_KWARGS] = {"onebot_v12_access_token": "test"}


@pytest.fixture(scope="session", autouse=True)
def init_adapter(nonebug_init: None):
    import nonebot
    import nonebot.adapters

    nonebot.adapters.__path__.append(  # type: ignore
        str((Path(__file__).parent.parent / "nonebot" / "adapters").resolve())
    )
    from nonebot.adapters.onebot import V11Adapter, V12Adapter

    driver = nonebot.get_driver()
    driver.register_adapter(V11Adapter)
    driver.register_adapter(V12Adapter)
