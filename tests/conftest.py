from pathlib import Path

import pytest
from nonebug import App


@pytest.fixture
def import_hook():
    import nonebot.adapters

    nonebot.adapters.__path__.append(  # type: ignore
        str((Path(__file__).parent.parent / "nonebot" / "adapters").resolve())
    )


@pytest.fixture
async def init_adapter(app: App, import_hook):
    import nonebot
    from nonebot.adapters.onebot import V11Adapter, V12Adapter

    driver = nonebot.get_driver()
    driver.register_adapter(V11Adapter)
    driver.register_adapter(V12Adapter)
