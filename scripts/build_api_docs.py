from pathlib import Path

from nb_autodoc import Module
from nb_autodoc.builders.markdown import MarkdownBuilder

import nonebot.adapters

nonebot.adapters.__path__.append(  # type: ignore
    str((Path(__file__).parent.parent / "nonebot" / "adapters").resolve())
)

module = Module("nonebot.adapters.onebot")
builder = MarkdownBuilder(
    module, output_dir=str((Path(__file__).parent.parent / "build").resolve())
)
builder.write()
