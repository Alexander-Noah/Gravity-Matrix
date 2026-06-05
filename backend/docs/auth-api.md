# 登录注册接口文档

本文档定义前端登录注册页当前使用的认证接口。前端默认请求地址为：

```text
http://127.0.0.1:8000/api/v1
```

可通过前端环境变量覆盖：

```text
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

## 1. 注册账号

### 请求

```http
POST /auth/register
Content-Type: application/json
```

### 请求参数

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| name | string | 是 | 创作者名称 |
| email | string | 是 | 登录邮箱 |
| password | string | 是 | 登录密码，前端要求至少 6 位 |

### 请求示例

```json
{
  "name": "林默",
  "email": "creator@example.com",
  "password": "123456"
}
```

### 成功响应

```json
{
  "access_token": "token-string",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "林默",
    "email": "creator@example.com"
  }
}
```

## 2. 登录账号

### 请求

```http
POST /auth/login
Content-Type: application/json
```

### 请求参数

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| email | string | 是 | 登录邮箱 |
| password | string | 是 | 登录密码 |

### 请求示例

```json
{
  "email": "creator@example.com",
  "password": "123456"
}
```

### 成功响应

```json
{
  "access_token": "token-string",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "林默",
    "email": "creator@example.com"
  }
}
```

## 3. 获取当前用户

### 请求

```http
GET /auth/me
Authorization: Bearer <access_token>
```

### 成功响应

```json
{
  "id": 1,
  "name": "林默",
  "email": "creator@example.com"
}
```

## 4. 前端会话处理

前端登录或注册成功后会保存：

| localStorage key | 说明 |
| --- | --- |
| gm_auth_token | 接口返回的 access_token |
| gm_auth_user | 接口返回的 user JSON |

之后 axios 请求会自动携带：

```http
Authorization: Bearer <access_token>
```

## 5. 错误响应约定

推荐后端使用 FastAPI 常见错误结构：

```json
{
  "detail": "邮箱或密码错误"
}
```

前端会优先展示 `detail`。如果后端不可用，前端提示：

```text
暂时无法连接服务，请确认后端接口已启动。
```
