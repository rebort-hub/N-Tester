"""update api automation menus to 3 pages

Revision ID: 3d0a9f2a7b1c
Revises: 9b3a2c1d0e4f
Create Date: 2026-03-12 16:30:00.000000

将“接口自动化”一级目录下的子菜单调整为：
- 接口管理（旧版完整 UI）
- 场景管理
- 结果列表
并确保 admin 角色拥有这些菜单。
"""

from alembic import op
import sqlalchemy as sa


revision = "3d0a9f2a7b1c"
down_revision = "9b3a2c1d0e4f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # ensure root exists
    conn.execute(sa.text("""
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, remark, enabled_flag)
        SELECT '接口自动化', 0, 30, '/api-automation', 'layout/routerView/parent', 1, 0, 'M', 1, 1, NULL, 'ele-Connection', NULL, 1
        WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE path = '/api-automation' AND enabled_flag = 1)
    """))

    # hide the old single page if present (keep data to avoid breaking references)
    conn.execute(sa.text("""
        UPDATE sys_menu
        SET visible = 0
        WHERE path = '/api-automation/index' AND enabled_flag = 1
    """))

    # upsert 3 child pages
    conn.execute(sa.text("""
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, remark, enabled_flag)
        SELECT '接口管理',
               (SELECT id FROM sys_menu WHERE path = '/api-automation' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               1, '/api-automation/project', 'testing/api-automation/api_project', 1, 0, 'C', 1, 1, NULL, 'ele-Connection', NULL, 1
        WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE path = '/api-automation/project' AND enabled_flag = 1)
    """))

    conn.execute(sa.text("""
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, remark, enabled_flag)
        SELECT '场景管理',
               (SELECT id FROM sys_menu WHERE path = '/api-automation' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               2, '/api-automation/script', 'testing/api-automation/api_script', 1, 0, 'C', 1, 1, NULL, 'ele-Memo', NULL, 1
        WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE path = '/api-automation/script' AND enabled_flag = 1)
    """))

    conn.execute(sa.text("""
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, remark, enabled_flag)
        SELECT '结果列表',
               (SELECT id FROM sys_menu WHERE path = '/api-automation' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               3, '/api-automation/results', 'testing/api-automation/api_result_list', 1, 0, 'C', 1, 1, NULL, 'ele-Document', NULL, 1
        WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE path = '/api-automation/results' AND enabled_flag = 1)
    """))

    # assign to admin role
    conn.execute(sa.text("""
        INSERT INTO sys_role_menu (role_id, menu_id)
        SELECT r.id, m.id
        FROM sys_role r
        JOIN sys_menu m ON m.enabled_flag = 1
        WHERE r.role_key = 'admin'
          AND m.path IN ('/api-automation', '/api-automation/project', '/api-automation/script', '/api-automation/results')
          AND NOT EXISTS (
              SELECT 1 FROM sys_role_menu rm
              WHERE rm.role_id = r.id AND rm.menu_id = m.id
          )
    """))


def downgrade() -> None:
    conn = op.get_bind()
    # best-effort: remove the 3 child menus and restore old page visibility
    conn.execute(sa.text("""
        UPDATE sys_menu
        SET visible = 1
        WHERE path = '/api-automation/index' AND enabled_flag = 1
    """))
    conn.execute(sa.text("DELETE FROM sys_menu WHERE path IN ('/api-automation/project', '/api-automation/script', '/api-automation/results')"))

