# 保险精准营销系统 · API 接口文档

| 文档属性    | 内容                             |
| ------- | ------------------------------ |
| 文档版本    | v1.0                           |
| 编写日期    | 2026-07-26                     |
| 文档状态    | **已通过三方评审**（业务方 / 前端组 / 测试组）   |
| BaseURL | `http://127.0.0.1:5000/api/v1` |
| 维护人     | 后端组                            |

> 本文档为前后端对接的正式契约。如需新增/修改接口，需发起变更评审，更新版本号并通知各方。

---

## 0. 通用约定

### 0.1 统一响应格式

所有 JSON 接口统一返回如下结构：

```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

| 字段      | 类型                | 说明                         |
| ------- | ----------------- | -------------------------- |
| code    | int               | 业务码，`0` 成功，非 `0` 失败（见 0.5） |
| message | string            | 提示信息，失败时给用户看               |
| data    | object/array/null | 业务数据，失败时为 `null`           |

### 0.2 认证机制

- 登录接口返回 `access_token`（JWT）；
- 需鉴权的接口必须在请求头携带：`Authorization: Bearer <token>`；
- Token 默认有效期 24 小时；
- Token 无效/过期返回 `401` + `code=1002`。

### 0.3 分页约定

分页接口的 `data` 统一为：

```json
{
  "items": [ ... ],
  "total": 1110,
  "page": 1,
  "per_page": 20,
  "pages": 56
}
```

查询参数：`page`（从 1 开始，默认 1）、`per_page`（默认 20/50，见各接口）。

### 0.4 时间格式

所有时间字段为 ISO 8601 字符串，如 `2026-07-26T11:00:08`。

### 0.5 业务码表

| code | 含义             | HTTP      |
| ---- | -------------- | --------- |
| 0    | 成功             | 200       |
| 1001 | 参数校验错误         | 400       |
| 1002 | 未授权 / 用户名或密码错误 | 401       |
| 1003 | 权限不足           | 403       |
| 1004 | 用户名已存在         | 400       |
| 2001 | 资源不存在          | 404       |
| 2002 | Excel 解析失败     | 400       |
| 3001 | 训练失败           | 500       |
| 3002 | 无最佳模型 / 预测失败   | 400 / 500 |
| 4001 | 邮件生成失败         | 500       |
| 5000 | 服务器内部错误        | 500       |

### 0.6 角色说明

| 角色    | 说明                      |
| ----- | ----------------------- |
| admin | 管理员，全部接口可用              |
| user  | 普通用户，训练/导入导出/日志接口返回 403 |

### 0.7 默认账号

首次启动自动创建：`admin` / `admin123`。

---

## 1. 认证模块 `/auth`

### 1.1 用户登录

| 项            | 值                  |
| ------------ | ------------------ |
| 方法 URL       | `POST /auth/login` |
| 鉴权           | 否                  |
| Content-Type | application/json   |

**请求体**

| 字段       | 类型     | 必填  | 说明   |
| -------- | ------ | --- | ---- |
| username | string | 是   | 用户名  |
| password | string | 是   | 明文密码 |

**响应 data**

| 字段            | 类型     | 说明                |
| ------------- | ------ | ----------------- |
| access_token  | string | JWT 令牌            |
| token_type    | string | 固定 `bearer`       |
| expires_in    | int    | 有效期（秒），默认 86400   |
| user.id       | int    | 用户 ID             |
| user.username | string | 用户名               |
| user.role     | string | 角色 `admin`/`user` |

**示例**

```json
// 请求
{ "username": "admin", "password": "admin123" }

// 响应
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user": { "id": 1, "username": "admin", "role": "admin" }
  }
}
```

**错误**：用户名或密码错误 → `401` / `code=1002`。

### 1.2 用户注册

| 项      | 值                     |
| ------ | --------------------- |
| 方法 URL | `POST /auth/register` |
| 鉴权     | 否                     |

**请求体**：`username`（string）、`password`（string）。不含 `role`（服务端硬编码 `user`）。

**响应 data**：同登录。

**错误**：用户名已存在 → `400` / `code=1004`。

### 1.3 获取当前用户

| 项      | 值              |
| ------ | -------------- |
| 方法 URL | `GET /auth/me` |
| 鉴权     | 是              |

**响应 data**：`{ id, username, role }`。

**错误**：未带 Token → `401` / `code=1002`。

### 1.4 退出登录

| 项      | 值                   |
| ------ | ------------------- |
| 方法 URL | `POST /auth/logout` |
| 鉴权     | 是                   |

**响应**：`{ code: 0, data: null, message: "已登出" }`。JWT 无状态，前端丢弃 Token 即可。

---

## 2. 数据模块 `/data`

> 本模块所有接口需登录（`Authorization: Bearer <token>`）。

### 2.1 上传 Excel 数据

| 项            | 值                   |
| ------------ | ------------------- |
| 方法 URL       | `POST /data/upload` |
| 鉴权           | 是                   |
| Content-Type | multipart/form-data |

**请求体**：`file`（File，.xlsx/.xls），字段须含：id/Gender/Age/Driving_License/Region_Code/Previously_Insured/Vehicle_Age/Vehicle_Damage/Annual_Premium/Policy_Sales_Channel/Vintage/Response。

**响应 data**

| 字段                            | 类型     | 说明    |
| ----------------------------- | ------ | ----- |
| imported_count                | int    | 入库行数  |
| quality_report.total_rows     | int    | 总行数   |
| quality_report.total_cols     | int    | 总列数   |
| quality_report.missing_values | object | 各列缺失数 |
| quality_report.duplicates     | int    | 重复行数  |
| quality_report.dtypes         | object | 各列类型  |

**说明**：上传会清空 `customers` 旧数据后重新导入（教学版覆盖策略）。

**错误**：未上传文件 → `400` / `code=1001`；Excel 解析失败 → `400` / `code=2002`。

### 2.2 客户列表分页

| 项      | 值                     |
| ------ | --------------------- |
| 方法 URL | `GET /data/customers` |
| 鉴权     | 是                     |

**查询参数**

| 参数                 | 类型     | 默认  | 说明                |
| ------------------ | ------ | --- | ----------------- |
| page               | int    | 1   | 页码                |
| per_page           | int    | 50  | 每页条数              |
| gender             | string | —   | 性别过滤（Male/Female） |
| age_min            | int    | —   | 年龄下限              |
| age_max            | int    | —   | 年龄上限              |
| previously_insured | int    | —   | 是否已投保（0/1）        |
| keyword            | string | —   | 按 id 搜索（数字字符串）    |

**响应 data**：分页结构，`items` 元素含全字段（id/gender/age/.../response/predicted_prob）。

### 2.3 数据概览统计

| 项      | 值                      |
| ------ | ---------------------- |
| 方法 URL | `GET /data/statistics` |
| 鉴权     | 是                      |

**响应 data**

| 字段                    | 类型     | 说明                               |
| --------------------- | ------ | -------------------------------- |
| total                 | int    | 客户总数                             |
| gender_distribution   | object | `{Male: n, Female: n}`           |
| response_distribution | object | `{"0": n, "1": n}`（可见 87:13 不平衡） |
| age_stats             | object | `{min, max, avg}`                |

### 2.4 数据质量报告

| 项      | 值                   |
| ------ | ------------------- |
| 方法 URL | `GET /data/quality` |
| 鉴权     | 是                   |

**响应 data**：`{ total_rows, total_cols, missing_values, duplicates, dtypes }`。

### 2.5 EDA 可视化

| 项      | 值                                      |
| ------ | -------------------------------------- |
| 方法 URL | `GET /data/visualization/{chart_type}` |
| 鉴权     | 是                                      |

**路径参数**：`chart_type` ∈ `response_distribution` / `gender_response` / `age_distribution` / `premium_distribution`。

**响应 data**：`{ chart_type, image_base64, format: "png" }`，前端 `<img src="data:image/png;base64,...">` 直接显示。

**错误**：未知图表类型 → `400` / `code=1001`。

---

## 3. 模型模块 `/model`

### 3.1 训练模型

| 项      | 值                   |
| ------ | ------------------- |
| 方法 URL | `POST /model/train` |
| 鉴权     | 是（仅 admin）          |

**请求体**（可选，不传用默认值）

| 字段           | 类型              | 默认   | 说明                                            |
| ------------ | --------------- | ---- | --------------------------------------------- |
| models       | array\<string\> | null | null=训练全部三算法；可传 `["xgboost"]` 子集              |
| test_size    | float           | 0.2  | 测试集比例                                         |
| random_state | int             | 42   | 随机种子                                          |
| params       | object          | null | 按模型名覆盖超参，如 `{"xgboost":{"n_estimators":200}}` |

**响应 data**

| 字段                        | 类型     | 说明               |
| ------------------------- | ------ | ---------------- |
| best_model                | string | 最佳模型名（按 ROC-AUC） |
| results.{model}.accuracy  | float  | 准确率              |
| results.{model}.precision | float  | 精确率              |
| results.{model}.recall    | float  | 召回率              |
| results.{model}.f1_score  | float  | F1               |
| results.{model}.roc_auc   | float  | ROC-AUC          |

**错误**：普通用户 → `403` / `code=1003`；无数据 → `400` / `code=2001`；训练异常 → `500` / `code=3001`。

### 3.2 实验记录分页

| 项      | 值                        |
| ------ | ------------------------ |
| 方法 URL | `GET /model/experiments` |
| 鉴权     | 是                        |

**查询参数**：`page`、`per_page`（默认 50）、`model_name`（可选过滤）。

**响应 data**：分页结构，`items` 含 id/model_name/accuracy/precision/recall/f1_score/roc_auc/params/model_path/is_best/created_at。

### 3.3 获取最佳模型

| 项      | 值                 |
| ------ | ----------------- |
| 方法 URL | `GET /model/best` |
| 鉴权     | 是                 |

**响应 data**：`{ model_name, roc_auc, experiment_id }`。

**错误**：无最佳模型 → `400` / `code=3002`。

### 3.4 全量预测

| 项      | 值                     |
| ------ | --------------------- |
| 方法 URL | `POST /model/predict` |
| 鉴权     | 是                     |

**请求体**（可选）：`model_name`（string，缺省用最佳模型）。

**响应 data**：`{ model_name, predicted_count }`。预测概率回写到 `customers.predicted_prob`。

**错误**：无最佳模型/模型文件丢失 → `code=3002`；预测异常 → `500` / `code=3002`。

### 3.5 上传数据预测

| 项            | 值                            |
| ------------ | ---------------------------- |
| 方法 URL       | `POST /model/predict_upload` |
| 鉴权           | 是                            |
| Content-Type | multipart/form-data          |

**请求体**：`file`（Excel）；可选表单字段 `model`（模型名，缺省用最佳模型）。

**响应 data**：`{ model_name, total_count, statistics, predictions }`，直接返回预测结果，不入库。

**说明**：与 `/predict` 区别——本接口对上传的新一批客户预测并返回，不覆盖训练数据。

**错误**：文件格式错 → `code=1001`；解析失败 → `code=2002`。

### 3.6 模型评估可视化

| 项      | 值                                       |
| ------ | --------------------------------------- |
| 方法 URL | `GET /model/visualization/{chart_type}` |
| 鉴权     | 是                                       |

**路径参数**：`chart_type` ∈ `roc_curve` / `metrics_comparison` / `confusion_matrix` / `feature_importance`。

**查询参数**：`model`（confusion_matrix / feature_importance 必填，可选 `logistic_regression`/`xgboost`/`random_forest`）。

**响应 data**：`{ chart_type, image_base64, format: "png" }`。

### 3.7 导出模型文件

| 项      | 值                                |
| ------ | -------------------------------- |
| 方法 URL | `GET /model/export/{model_name}` |
| 鉴权     | 是（仅 admin）                       |

**响应**：二进制文件流（.joblib），`Content-Disposition: attachment`。

**错误**：模型不存在 → `code=3002`；普通用户 → `403` / `code=1003`。

### 3.8 导入模型文件

| 项            | 值                    |
| ------------ | -------------------- |
| 方法 URL       | `POST /model/import` |
| 鉴权           | 是（仅 admin）           |
| Content-Type | multipart/form-data  |

**请求体**：`file`（.joblib 文件）。

**响应 data**：`{ model_name, path }`。

**错误**：非 .joblib → `code=1001`；普通用户 → `403` / `code=1003`。

---

## 4. 邮件模块 `/email`

> 本模块所有接口需登录。

### 4.1 筛选高潜客户

| 项      | 值                    |
| ------ | -------------------- |
| 方法 URL | `GET /email/targets` |
| 鉴权     | 是                    |

**查询参数**

| 参数         | 类型    | 默认  | 说明                |
| ---------- | ----- | --- | ----------------- |
| percentile | float | 0.9 | 分位阈值（0.9=top 10%） |
| page       | int   | 1   | 页码                |
| per_page   | int   | 20  | 每页条数              |

**响应 data**：`{ threshold, total, customers: [...] }`，customers 含 id/gender/age/annual_premium/predicted_prob。

**错误**：无预测数据 → `code=3002`。

### 4.2 生成营销邮件

| 项      | 值                      |
| ------ | ---------------------- |
| 方法 URL | `POST /email/generate` |
| 鉴权     | 是                      |

**请求体**（二选一）

| 字段           | 类型           | 默认   | 说明                            |
| ------------ | ------------ | ---- | ----------------------------- |
| customer_ids | array\<int\> | null | 指定客户；缺省自动取 top                |
| limit        | int          | 5    | 自动取 top N（customer_ids 为空时生效） |

**响应 data**

| 字段              | 类型    | 说明                                  |
| --------------- | ----- | ----------------------------------- |
| generated_count | int   | 成功生成数                               |
| failed_count    | int   | 失败数                                 |
| records         | array | 每条 `{customer_id, status, subject}` |

**说明**：未配置 `LLM_API_KEY` 时 status=failed。

### 4.3 获取 Prompt 模板

| 项      | 值                   |
| ------ | ------------------- |
| 方法 URL | `GET /email/prompt` |
| 鉴权     | 是                   |

**响应 data**：`{ name, content }`，content 含 `{gender}`/`{age}` 等占位符。

### 4.4 更新 Prompt 模板

| 项      | 值                   |
| ------ | ------------------- |
| 方法 URL | `PUT /email/prompt` |
| 鉴权     | 是                   |

**请求体**：`{ content: string }`（须含占位符）。

**响应 data**：`{ name, content }`。

### 4.5 邮件记录列表

| 项      | 值                    |
| ------ | -------------------- |
| 方法 URL | `GET /email/records` |
| 鉴权     | 是                    |

**查询参数**：`page`、`per_page`（默认 50）、`status`（可选 `generated`/`failed`）。

**响应 data**：分页结构，`items` 含 id/customer_id/subject/status/created_at。普通用户只看自己生成的；admin 看全部并附 `created_by_username`。

### 4.6 邮件详情

| 项      | 值                                |
| ------ | -------------------------------- |
| 方法 URL | `GET /email/records/{record_id}` |
| 鉴权     | 是                                |

**响应 data**：含完整 `content` 正文。

**错误**：记录不存在 → `code=2001`。

### 4.7 更新邮件记录

| 项      | 值                                |
| ------ | -------------------------------- |
| 方法 URL | `PUT /email/records/{record_id}` |
| 鉴权     | 是                                |

**请求体**：`{ email_subject?, email_content? }`。

### 4.8 标记邮件状态

| 项      | 值                                  |
| ------ | ---------------------------------- |
| 方法 URL | `PATCH /email/records/{record_id}` |
| 鉴权     | 是                                  |

**请求体**：`{ status: string }`（如 `sent`/`failed`）。

### 4.9 删除单条邮件

| 项      | 值                                   |
| ------ | ----------------------------------- |
| 方法 URL | `DELETE /email/records/{record_id}` |
| 鉴权     | 是                                   |

**响应 data**：`{ success: true }`。

### 4.10 批量删除邮件

| 项      | 值                       |
| ------ | ----------------------- |
| 方法 URL | `DELETE /email/records` |
| 鉴权     | 是                       |

**请求体**：`{ record_ids: array<int> }`。

**响应 data**：`{ deleted_count: int }`。

---

## 5. 日志模块 `/logs`

### 5.1 操作日志查询

| 项      | 值           |
| ------ | ----------- |
| 方法 URL | `GET /logs` |
| 鉴权     | 是（仅 admin）  |

**查询参数**

| 参数       | 类型     | 默认  | 说明      |
| -------- | ------ | --- | ------- |
| page     | int    | 1   | 页码      |
| per_page | int    | 50  | 每页条数    |
| user_id  | int    | —   | 按用户过滤   |
| action   | string | —   | 按操作类型过滤 |

`action` 取值：`model_training` / `prediction` / `model_import` / `email_generation` / `email_update` / `email_mark` / `email_delete`。

**响应 data**：分页结构，`items` 含 id/user_id/action/details/created_at。

**错误**：普通用户 → `403` / `code=1003`。

---

## 6. 根路由

### 6.1 前端 SPA 入口

| 项      | 值       |
| ------ | ------- |
| 方法 URL | `GET /` |
| 鉴权     | 否       |

**响应**：HTML 页面（前端 SPA 入口）。

---

## 7. 接口清单速查

| #   | 方法     | URL                                  | 鉴权  | 角色    |
| --- | ------ | ------------------------------------ | --- | ----- |
| 1   | POST   | /auth/login                          | 否   | —     |
| 2   | POST   | /auth/register                       | 否   | —     |
| 3   | GET    | /auth/me | 是   | 已登录   |
| 4   | POST   | /auth/logout                         | 是   | 已登录   |
| 5   | POST   | /data/upload                         | 是   | 已登录   |
| 6   | GET    | /data/customers                      | 是   | 已登录   |
| 7   | GET    | /data/statistics                     | 是   | 已登录   |
| 8   | GET    | /data/quality                        | 是   | 已登录   |
| 9   | GET    | /data/visualization/{chart_type}     | 是   | 已登录   |
| 10  | POST   | /model/train                         | 是   | admin |
| 11  | GET    | /model/experiments                   | 是   | 已登录   |
| 12  | GET    | /model/best                          | 是   | 已登录   |
| 13  | POST   | /model/predict                       | 是   | 已登录   |
| 14  | POST   | /model/predict_upload                | 是   | 已登录   |
| 15  | GET    | /model/visualization/{chart_type}    | 是   | 已登录   |
| 16  | GET    | /model/export/{model_name}           | 是   | admin |
| 17  | POST   | /model/import                        | 是   | admin |
| 18  | GET    | /email/targets                       | 是   | 已登录   |
| 19  | POST   | /email/generate                      | 是   | 已登录   |
| 20  | GET    | /email/prompt                        | 是   | 已登录   |
| 21  | PUT    | /email/prompt                        | 是   | 已登录   |
| 22  | GET    | /email/records                       | 是   | 已登录   |
| 23  | GET    | /email/records/{record_id}           | 是   | 已登录   |
| 24  | PUT    | /email/records/{record_id}           | 是   | 已登录   |
| 25  | PATCH  | /email/records/{record_id}           | 是   | 已登录   |
| 26  | DELETE | /email/records/{record_id}           | 是   | 已登录   |
| 27  | DELETE | /email/records                       | 是   | 已登录   |
| 28  | GET    | /logs                                | 是   | admin |
| 29  | GET    | /                                    | 否   | —     |

---

## 8. 变更记录

| 版本   | 日期         | 变更内容             | 评审人         |
| ---- | ---------- | ---------------- | ----------- |
| v1.0 | 2026-07-26 | 首版发布，覆盖全部 29 个接口 | 业务方/前端组/测试组 |
