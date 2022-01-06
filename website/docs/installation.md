---
sidebar_position: 1
description: 安装

options:
  menu:
    weight: 10
    category: guide
---

# 安装

## 安装 NoneBot OneBot 适配器

```bash
nb adapter install nonebot-adpater-onebot
```

或者使用 pip

```bash
pip install nonebot-adapter-onebot
```

## 加载适配器

### OneBot V11

```python title=bot.py {2,7}
import nonebot
from nonebot.adapters.onebot.v11 import Adapter

nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(Adapter)
```
