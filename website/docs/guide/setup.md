---
sidebar_position: 2
description: 配置连接

options:
  menu:
    weight: 20
    category: guide
---

# 配置连接

基于你的使用场景和偏好，在下列数种连接方式中选择一种配置单个协议实现端与 NoneBot 的连接。

## OneBot V11

### 反向 WebSocket 连接（推荐）

配置 OneBot 实现的 `ws reverse` 相关配置，使用 `universal-client` 并将上报地址改为以下地址其一：

- `ws://127.0.0.1:8080/onebot/v11/`
- `ws://127.0.0.1:8080/onebot/v11/ws`
- `ws://127.0.0.1:8080/onebot/v11/ws/`

其中，`127.0.0.1` 和 `8080` 分别对应 NoneBot 配置的 HOST 和 PORT。

:::warning 注意
请确保你的 NoneBot 使用的是 `ReverseDriver`，否则无法使用此连接方式。

如何选择驱动器：[选择驱动器](https://nonebot.dev/docs/advanced/driver)
:::

### HTTP POST

配置 OneBot 实现的 `http post` 相关配置，将上报地址改为以下地址其一：

- `http://127.0.0.1:8080/onebot/v11/`
- `http://127.0.0.1:8080/onebot/v11/http`
- `http://127.0.0.1:8080/onebot/v11/http/`

其中，`127.0.0.1` 和 `8080` 分别对应 NoneBot 配置的 HOST 和 PORT。

配置 OneBot 实现的 `http server` 相关配置，开启 HTTP 服务器监听，用于调用 API。

配置 NoneBot 设置，提供指定机器人的 API 地址：

```dotenv title=.env
ONEBOT_API_ROOTS={"你的QQ号": "http://127.0.0.1:5700/"}
```

其中，`127.0.0.1` 和 `5700` 分别对应 OneBot 实现配置的 HTTP 服务器监听的 HOST 和 PORT。

:::warning 注意
请确保你的 NoneBot 使用了 `HTTPClient` 和 `ASGI` 类型的驱动器，否则无法使用此连接方式。

如何选择驱动器：[选择驱动器](https://nonebot.dev/docs/advanced/driver)
:::

### 正向 WebSocket 连接

配置 OneBot 实现的 `ws server` 相关配置，开启 WebSocket 服务器监听。

配置 NoneBot 配置，提供机器人的 WebSocket 地址：

```dotenv title=.env
ONEBOT_WS_URLS=["ws://127.0.0.1:6700"]
```

其中，`127.0.0.1` 和 `6700` 分别对应 OneBot 实现配置的 WebSocket 服务器的 HOST 和 PORT。

:::warning 注意
请确保你的 NoneBot 使用了 `WebSocketClient` 类型的驱动器，否则无法使用此连接方式。

如何选择驱动器：[选择驱动器](https://nonebot.dev/docs/advanced/driver)
:::

## OneBot V12

### 反向 WebSocket 连接（推荐）

配置 OneBot 实现的 `ws reverse` 相关配置，将推送地址改为以下地址其一：

- `ws://127.0.0.1:8080/onebot/v12/`
- `ws://127.0.0.1:8080/onebot/v12/ws`
- `ws://127.0.0.1:8080/onebot/v12/ws/`

其中，`127.0.0.1` 和 `8080` 分别对应 NoneBot 配置的 HOST 和 PORT。

:::warning 注意
请确保你的 NoneBot 使用了 `ASGI` 类型的驱动器，否则无法使用此连接方式。

如何选择驱动器：[选择驱动器](https://nonebot.dev/docs/advanced/driver)
:::

### HTTP Webhook

配置 OneBot 实现的 `http webhook` 相关配置，将推送地址改为以下地址其一：

- `http://127.0.0.1:8080/onebot/v12/`
- `http://127.0.0.1:8080/onebot/v12/http`
- `http://127.0.0.1:8080/onebot/v12/http/`

其中，`127.0.0.1` 和 `8080` 分别对应 NoneBot 配置的 HOST 和 PORT。

配置 OneBot 实现的 `http server` 相关配置，开启 HTTP 服务器监听，用于调用 API。

配置 NoneBot 设置，提供指定机器人的 API 地址：

```dotenv title=.env
ONEBOT_V12_API_ROOTS={"你的QQ号": "http://127.0.0.1:5700/"}
```

其中，`127.0.0.1` 和 `5700` 分别对应 OneBot 实现配置的 HTTP 服务器监听的 HOST 和 PORT。

:::warning 注意
请确保你的 NoneBot 使用了 `HTTPClient` 和 `ASGI` 类型的驱动器，否则无法使用此连接方式。

如何选择驱动器：[选择驱动器](https://nonebot.dev/docs/advanced/driver)
:::

### 正向 WebSocket 连接

配置 OneBot 实现的 `ws server` 相关配置，开启 WebSocket 服务器监听。

配置 NoneBot 配置，提供机器人的 WebSocket 地址：

```dotenv title=.env
ONEBOT_V12_WS_URLS=["ws://127.0.0.1:6700"]
```

其中，`127.0.0.1` 和 `6700` 分别对应 OneBot 实现配置的 WebSocket 服务器的 HOST 和 PORT。

:::warning 注意
请确保你的 NoneBot 使用了 `WebSocketClient` 类型的驱动器，否则无法使用此连接方式。

如何选择驱动器：[选择驱动器](https://nonebot.dev/docs/advanced/driver)
:::
