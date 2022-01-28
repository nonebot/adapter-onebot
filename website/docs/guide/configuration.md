---
sidebar_position: 3
description: 配置访问令牌、签名

options:
  menu:
    weight: 30
    category: guide
---

# 配置访问权限

## access_token

配置 NoneBot 设置，提供的访问令牌将用于访问 API 接口或 WebSocket 双向鉴权。

```dotenv title=.env
ONEBOT_ACCESS_TOKEN=你的访问令牌
```

配置 OneBot 实现的 `access_token` 相关配置，令牌应与 NoneBot 配置中的访问令牌一致。

## secret (OneBot V11)

```dotenv title=.env
ONEBOT_SECRET=你的签名
```

配置 OneBot V11 实现的 `secret` 相关配置，签名应与 NoneBot 配置中的签名一致。
