"""add task scheduler menus

Revision ID: 20260313_1200
Revises: 3d0a9f2a7b1c
Create Date: 2026-03-13 12:00:00.000000

为新架构定时任务页面添加菜单：
- 一级目录：任务管理
- 二级菜单：定时任务
并为 admin 角色分配相应权限（含按钮级权限）。
"""

from alembic import op
import sqlalchemy as sa


revision = "20260313_1200"
down_revision = "3d0a9f2a7b1c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1) 一级目录：任务管理
    conn.execute(
        sa.text(
            """
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache,
                              menu_type, visible, status, perms, icon, remark, enabled_flag)
        SELECT '任务管理', 0, 40, '/task', 'layout/routerView/parent', 1, 0,
               'M', 1, 1, NULL, 'ele-Calendar', NULL, 1
        WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE path = '/task' AND enabled_flag = 1)
        """
        )
    )

    # 2) 二级菜单：定时任务页面
    conn.execute(
        sa.text(
            """
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache,
                              menu_type, visible, status, perms, icon, remark, enabled_flag)
        SELECT '定时任务',
               (SELECT id FROM sys_menu WHERE path = '/task' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               1, '/task/scheduler', 'testing/scheduler/index', 1, 0,
               'C', 1, 1, NULL, 'ele-Timer', NULL, 1
        WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE path = '/task/scheduler' AND enabled_flag = 1)
        """
        )
    )

    # 3) 按钮权限：新增 / 编辑 / 删除 定时任务
    conn.execute(
        sa.text(
            """
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache,
                              menu_type, visible, status, perms, icon, remark, enabled_flag)
        SELECT '新增任务',
               (SELECT id FROM sys_menu WHERE path = '/task/scheduler' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               1, NULL, NULL, 1, 0,
               'F', 0, 1, 'scheduler:task:add', NULL, NULL, 1
        WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE perms = 'scheduler:task:add' AND enabled_flag = 1)
        """
        )
    )

    conn.execute(
        sa.text(
            """
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache,
                              menu_type, visible, status, perms, icon, remark, enabled_flag)
        SELECT '编辑任务',
               (SELECT id FROM sys_menu WHERE path = '/task/scheduler' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               2, NULL, NULL, 1, 0,
               'F', 0, 1, 'scheduler:task:edit', NULL, NULL, 1
        WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE perms = 'scheduler:task:edit' AND enabled_flag = 1)
        """
        )
    )

    conn.execute(
        sa.text(
            """
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache,
                              menu_type, visible, status, perms, icon, remark, enabled_flag)
        SELECT '删除任务',
               (SELECT id FROM sys_menu WHERE path = '/task/scheduler' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               3, NULL, NULL, 1, 0,
               'F', 0, 1, 'scheduler:task:delete', NULL, NULL, 1
        WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE perms = 'scheduler:task:delete' AND enabled_flag = 1)
        """
        )
    )

    # 4) 将菜单及按钮分配给 admin 角色
    conn.execute(
        sa.text(
            """
        INSERT INTO sys_role_menu (role_id, menu_id)
        SELECT r.id, m.id
        FROM sys_role r
        JOIN sys_menu m ON m.enabled_flag = 1
        WHERE r.role_key = 'admin'
          AND (
            m.path IN ('/task', '/task/scheduler')
            OR m.perms IN ('scheduler:task:add', 'scheduler:task:edit', 'scheduler:task:delete')
          )
          AND NOT EXISTS (
              SELECT 1 FROM sys_role_menu rm
              WHERE rm.role_id = r.id AND rm.menu_id = m.id
          )
        """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()

    # 删除 admin 角色与这些菜单的绑定
    conn.execute(
        sa.text(
            """
        DELETE FROM sys_role_menu
        WHERE role_id IN (SELECT id FROM sys_role WHERE role_key = 'admin')
          AND menu_id IN (
            SELECT id FROM sys_menu
            WHERE enabled_flag = 1
              AND (
                path IN ('/task', '/task/scheduler')
                OR perms IN ('scheduler:task:add', 'scheduler:task:edit', 'scheduler:task:delete')
              )
          )
        """
        )
    )

    # 删除按钮
    conn.execute(
        sa.text(
            """
        DELETE FROM sys_menu
        WHERE enabled_flag = 1
          AND perms IN ('scheduler:task:add', 'scheduler:task:edit', 'scheduler:task:delete')
        """
        )
    )

    # 删除二级菜单和一级目录（谨慎，仅删除本次新增且无其他引用的）
    conn.execute(
        sa.text(
            """
        DELETE FROM sys_menu
        WHERE enabled_flag = 1 AND path = '/task/scheduler'
        """
        )
    )
    conn.execute(
        sa.text(
            """
        DELETE FROM sys_menu
        WHERE enabled_flag = 1 AND path = '/task'
        """
        )
    )

