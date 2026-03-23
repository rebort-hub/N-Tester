"""add web report menu under WEB管理

Revision ID: 20260313_1800
Revises: 20260313_1700
Create Date: 2026-03-13 18:00:00.000000

为 WEB 管理模块添加独立的「Web 报告」菜单页：
- 路由 path: /web/report
- 组件 component: web_view/web_report
并将其授权给 admin 角色。
"""

from alembic import op
import sqlalchemy as sa


revision = "20260313_1800"
down_revision = "20260313_1700"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # 在 WEB管理 目录下新增一个二级菜单：Web 报告
    conn.execute(
        sa.text(
            """
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component,
                              is_frame, is_cache, menu_type, visible, status,
                              perms, icon, remark, enabled_flag)
        SELECT 'Web 报告',
               (SELECT id FROM sys_menu
                 WHERE path = '/web-management' AND enabled_flag = 1
                 ORDER BY id LIMIT 1),
               5, '/web/report', 'web_view/web_report',
               1, 0, 'C', 1, 1,
               NULL, 'ele-Document', NULL, 1
        WHERE NOT EXISTS (
            SELECT 1 FROM sys_menu
            WHERE path = '/web/report' AND enabled_flag = 1
        )
        """
        )
    )

    # 赋权给 admin 角色
    conn.execute(
        sa.text(
            """
        INSERT INTO sys_role_menu (role_id, menu_id)
        SELECT r.id, m.id
        FROM sys_role r
        JOIN sys_menu m ON m.enabled_flag = 1
        WHERE r.role_key = 'admin'
          AND m.path = '/web/report'
          AND NOT EXISTS (
              SELECT 1 FROM sys_role_menu rm
              WHERE rm.role_id = r.id AND rm.menu_id = m.id
          )
        """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()

    # 删除 admin 角色的绑定
    conn.execute(
        sa.text(
            """
        DELETE FROM sys_role_menu
        WHERE role_id IN (SELECT id FROM sys_role WHERE role_key = 'admin')
          AND menu_id IN (
            SELECT id FROM sys_menu
            WHERE enabled_flag = 1 AND path = '/web/report'
          )
        """
        )
    )

    # 删除菜单本身
    conn.execute(
        sa.text(
            """
        DELETE FROM sys_menu
        WHERE enabled_flag = 1 AND path = '/web/report'
        """
        )
    )

