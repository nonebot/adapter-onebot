import warnings

warnings.warn(
    '"nonebot-adapter-cqhttp" is deprecated, use "nonebot-adapter-onebot" instead.',
    DeprecationWarning,
)

from nonebot.adapters.onebot.v11 import *  # type: ignore
