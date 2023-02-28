from pathlib import Path

from nb_autodoc import ModuleManager
from nb_autodoc.config import Config
from nb_autodoc.builders.markdown import MarkdownBuilder

import nonebot.adapters

nonebot.adapters.__path__.append(  # type: ignore
    str((Path(__file__).parent.parent / "nonebot" / "adapters").resolve())
)

config = Config(output_dir=str((Path(__file__).parent.parent / "build").resolve()))
module = ModuleManager("nonebot.adapters.onebot", config=config)
builder = MarkdownBuilder(module)
builder.write()
