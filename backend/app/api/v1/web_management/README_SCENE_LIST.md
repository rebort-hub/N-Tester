# 场景管理列表不显示 - 自检说明

## 1. 数据库表与字段

场景列表来自表 **`web_management_groups`**，所需字段如下（与 `WebGroupModel` + Base 一致）：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| name | String(255) | 脚本集名称 |
| script | JSON | 脚本集配置 |
| description | String(255) | 描述 |
| creation_date | DateTime | 创建时间 |
| created_by | BigInteger | 创建人ID |
| updation_date | DateTime | 更新时间 |
| updated_by | BigInteger | 更新人ID |
| enabled_flag | Boolean | 是否有效：1 有效，0 已删 |
| trace_id | String(255) | 可选 |

若表不存在或缺少上述字段，列表会查不到数据或报错。

## 2. 确认表是否已创建

- **已用 Alembic 迁移**：执行  
  `alembic upgrade head`  
  会创建/更新 `web_management_groups`（见 `app/alembic/versions/20260313_1530_a1b2c3d4e5f6_create_web_management_tables.py`）。

- **手动检查（MySQL）**：  
  ```sql
  SHOW TABLES LIKE 'web_management_groups';
  DESC web_management_groups;
  ```

## 3. 为何会“共 N 条但列表空白”

- **接口返回正常**：`total` 来自 `len(data)`，若为 4 说明接口查到了 4 条。
- **前端不展示** 常见原因：  
  1. 响应里 `content` 被拦截器改坏 → 已在 `request.ts` 对 `{ content, total }` 单独处理。  
  2. 某行/某字段为 `undefined`，表格渲染时调 `.toString()` 报错 → 已在 `web_group.vue` 做 row-key 和字段兜底。  
  3. 后端返回的 `creation_date`/`updation_date` 为 datetime 对象，序列化或前端使用不当 → 已在 `service.get_web_groups` 中改为返回 ISO 字符串。

## 4. 建议自检步骤

1. 执行迁移（若未执行）：  
   `cd backend && alembic upgrade head`
2. 确认当前登录用户是否有数据：  
   `SELECT id, name, created_by, enabled_flag FROM web_management_groups WHERE enabled_flag = 1 AND created_by = <当前用户ID>;`
3. 浏览器 F12 → Network → 找到 `web_group_list` 请求，看响应 `data.content` 是否为数组且长度为 4，每条是否有 `id、name、script、description、creation_date、updation_date、username`。
4. 若表存在且接口返回正常仍不显示，请查看控制台是否有 `Cannot read properties of undefined (reading 'toString')` 等报错（已通过 row-key 与字段兜底修复）。
