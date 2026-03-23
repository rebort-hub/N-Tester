"""add app automation menus and button perms

Revision ID: 20260319_1300
Revises: 20260319_1200
Create Date: 2026-03-19 13:00:00.000000

为新架构 APP 自动化模块添加独立菜单与按钮权限：
- 一级目录：APP自动化
- 二级菜单：APP自动化
- 按钮权限（v-auth perms）：新增目录、删除目录、重命名、保存脚本、执行、停止、查看结果
并将上述菜单/按钮授权给 admin 角色。
"""

from alembic import op
import sqlalchemy as sa


revision = "20260319_1300"
down_revision = "20260319_1200"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # 0) ensure admin role exists (idempotent)
    conn.execute(sa.text("""
        INSERT INTO sys_role (role_name, role_key, role_sort, data_scope, status, remark, enabled_flag)
        SELECT '管理员', 'admin', 1, 4, 1, '系统初始化角色', 1
        WHERE NOT EXISTS (SELECT 1 FROM sys_role WHERE role_key = 'admin' AND enabled_flag = 1)
    """))

    # 1) 一级目录：APP自动化
    conn.execute(sa.text("""
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache,
                              menu_type, visible, status, perms, icon, remark, enabled_flag)
        SELECT 'APP自动化', 0, 35, '/app-automation', 'layout/routerView/parent', 1, 0,
               'M', 1, 1, NULL, 'ele-MobilePhone', NULL, 1
        WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE path = '/app-automation' AND enabled_flag = 1)
    """))

    # 2) 二级菜单：APP自动化页面
    conn.execute(sa.text("""
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache,
                              menu_type, visible, status, perms, icon, remark, enabled_flag)
        SELECT 'APP自动化',
               (SELECT id FROM sys_menu WHERE path = '/app-automation' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               1, '/app-automation/index', 'testing/app-automation/index', 1, 0,
               'C', 1, 1, NULL, 'ele-MobilePhone', NULL, 1
        WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE path = '/app-automation/index' AND enabled_flag = 1)
    """))

    # 3) buttons (type F, invisible)
    buttons = [
        ("新增目录", 1, "appAutomation:menu:add"),
        ("删除目录", 2, "appAutomation:menu:delete"),
        ("重命名目录", 3, "appAutomation:menu:rename"),
        ("保存脚本", 4, "appAutomation:script:save"),
        ("执行脚本", 5, "appAutomation:script:run"),
        ("停止执行", 6, "appAutomation:process:stop"),
        ("查看结果", 7, "appAutomation:result:view"),
    ]

    for name, order_num, perms in buttons:
        conn.execute(sa.text("""
            INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache,
                                  menu_type, visible, status, perms, icon, remark, enabled_flag)
            SELECT :name,
                   (SELECT id FROM sys_menu WHERE path = '/app-automation/index' AND enabled_flag = 1 ORDER BY id LIMIT 1),
                   :order_num, NULL, NULL, 1, 0,
                   'F', 0, 1, :perms, NULL, NULL, 1
            WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE perms = :perms AND enabled_flag = 1)
        """), {"name": name, "order_num": order_num, "perms": perms})

    # 4) assign menus + buttons to admin role
    conn.execute(sa.text("""
        INSERT INTO sys_role_menu (role_id, menu_id)
        SELECT r.id, m.id
        FROM sys_role r
        JOIN sys_menu m ON m.enabled_flag = 1
        WHERE r.role_key = 'admin'
          AND (
            m.path IN ('/app-automation', '/app-automation/index')
            OR m.perms LIKE 'appAutomation:%'
          )
          AND NOT EXISTS (
              SELECT 1 FROM sys_role_menu rm
              WHERE rm.role_id = r.id AND rm.menu_id = m.id
          )
    """))

    # 5) bind admin role to admin user (if exists)
    conn.execute(sa.text("""
        INSERT INTO sys_user_role (user_id, role_id)
        SELECT u.id, r.id
        FROM sys_user u
        JOIN sys_role r ON r.role_key = 'admin' AND r.enabled_flag = 1
        WHERE u.enabled_flag = 1
          AND (u.user_type = 10 OR u.username = 'admin')
          AND NOT EXISTS (
              SELECT 1 FROM sys_user_role ur
              WHERE ur.user_id = u.id AND ur.role_id = r.id
          )
    """))


def downgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text("""
        DELETE FROM sys_role_menu
        WHERE role_id IN (SELECT id FROM sys_role WHERE role_key = 'admin')
          AND menu_id IN (
            SELECT id FROM sys_menu
            WHERE enabled_flag = 1
              AND (path IN ('/app-automation', '/app-automation/index') OR perms LIKE 'appAutomation:%')
          )
    """))

    conn.execute(sa.text("DELETE FROM sys_menu WHERE enabled_flag = 1 AND perms LIKE 'appAutomation:%'"))
    conn.execute(sa.text("DELETE FROM sys_menu WHERE enabled_flag = 1 AND path IN ('/app-automation/index', '/app-automation')"))

