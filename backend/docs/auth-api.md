# 认证接口说明

默认前缀：

```text
http://127.0.0.1:8000/api/v1
```

前端可通过 `VITE_API_BASE_URL` 覆盖后端地址。

## 注册

```http
POST /auth/register
Content-Type: application/json
```

请求体：

```json
{
  "name": "创作者",
  "email": "creator@example.com",
  "password": "123456"
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `name` | string | 是 | 用户名 |
| `email` | string | 是 | 登录邮箱 |
| `password` | string | 是 | 密码，前端要求至少 6 位 |

成功响应：

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "创作者",
    "email": "creator@example.com"
  }
}
```

常见错误：

- `409`：邮箱已注册。
- `422`：请求字段不合法。

## 登录

```http
POST /auth/login
Content-Type: application/json
```

请求体：

```json
{
  "email": "creator@example.com",
  "password": "123456"
}
```

成功响应同注册接口。

常见错误：

- `401`：邮箱或密码错误。

## 获取当前用户

```http
GET /auth/me
Authorization: Bearer <access_token>
```

响应：

```json
{
  "id": 1,
  "name": "创作者",
  "email": "creator@example.com"
}
```

## 个人中心摘要

```http
GET /profile/summary
Authorization: Bearer <access_token>
```

响应包含：

- 用户信息。
- 当前工作区。
- 当前项目。
- 当前流程阶段。
- 默认模板。
- 剧本库数量。
- YAML 校验状态。

该接口用于前端右上角个人中心弹窗。

## 前端会话存储

登录或注册成功后，前端保存：

| localStorage Key | 说明 |
| --- | --- |
| `gm_auth_token` | 后端返回的 `access_token` |
| `gm_auth_user` | 后端返回的 `user` JSON |

后续 Axios 请求会自动附加：

```http
Authorization: Bearer <access_token>
```

退出登录时清空以上内容并返回 `/auth`。

## 错误响应

后端错误统一优先使用 FastAPI 结构：

```json
{
  "detail": "错误说明"
}
```

前端会优先展示 `detail`，网络不可达时展示“暂时无法连接服务，请确认后端接口已启动”。
