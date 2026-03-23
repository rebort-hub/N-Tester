"""seed sys_menu for web management (L-Tester Web UI automation)

Revision ID: 20260313_1601
Revises: 20260313_1200
Create Date: 2026-03-13 16:01:00.000000

为新架构添加 WEB 管理相关菜单：
- 一级目录：WEB管理
- 二级菜单：元素管理 / Web 自动化 / Web 场景管理 / Web 结果
- 常用按钮权限（元素 CRUD、脚本保存&执行、场景 CRUD&执行、结果查看）
并将上述菜单/权限分配给 admin 角色。
"""

from alembic import op
import sqlalchemy as sa


revision = "20260313_1601"
down_revision = "20260313_1200"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1) 一级目录：WEB管理
    conn.execute(
        sa.text(
            """
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component,
                              is_frame, is_cache, menu_type, visible, status,
                              perms, icon, remark, enabled_flag)
        SELECT 'WEB管理', 0, 35, '/web-management', 'layout/routerView/parent',
               1, 0, 'M', 1, 1,
               NULL, 'ele-Chrome', NULL, 1
        WHERE NOT EXISTS (
            SELECT 1 FROM sys_menu
            WHERE path = '/web-management' AND enabled_flag = 1
        )
        """
        )
    )

    # 2) 二级菜单：元素管理
    conn.execute(
        sa.text(
            """
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component,
                              is_frame, is_cache, menu_type, visible, status,
                              perms, icon, remark, enabled_flag)
        SELECT '元素管理',
               (SELECT id FROM sys_menu
                 WHERE path = '/web-management' AND enabled_flag = 1
                 ORDER BY id LIMIT 1),
               1, '/web/element', 'web_view/element_manager',
               1, 0, 'C', 1, 1,
               NULL, 'ele-Grid', NULL, 1
        WHERE NOT EXISTS (
            SELECT 1 FROM sys_menu
            WHERE path = '/web/element' AND enabled_flag = 1
        )
        """
        )
    )

    # 3) 二级菜单：Web 自动化（脚本）
    conn.execute(
        sa.text(
            """
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component,
                              is_frame, is_cache, menu_type, visible, status,
                              perms, icon, remark, enabled_flag)
        SELECT 'Web 自动化',
               (SELECT id FROM sys_menu
                 WHERE path = '/web-management' AND enabled_flag = 1
                 ORDER BY id LIMIT 1),
               2, '/web/automation', 'web_view/web',
               1, 0, 'C', 1, 1,
               NULL, 'ele-ChromeFilled', NULL, 1
        WHERE NOT EXISTS (
            SELECT 1 FROM sys_menu
            WHERE path = '/web/automation' AND enabled_flag = 1
        )
        """
        )
    )

    # 4) 二级菜单：Web 场景管理
    conn.execute(
        sa.text(
            """
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component,
                              is_frame, is_cache, menu_type, visible, status,
                              perms, icon, remark, enabled_flag)
        SELECT 'Web 场景管理',
               (SELECT id FROM sys_menu
                 WHERE path = '/web-management' AND enabled_flag = 1
                 ORDER BY id LIMIT 1),
               3, '/web/group', 'web_view/web_group',
               1, 0, 'C', 1, 1,
               NULL, 'ele-Collection', NULL, 1
        WHERE NOT EXISTS (
            SELECT 1 FROM sys_menu
            WHERE path = '/web/group' AND enabled_flag = 1
        )
        """
        )
    )

    # 5) 二级菜单：Web 结果
    conn.execute(
        sa.text(
            """
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component,
                              is_frame, is_cache, menu_type, visible, status,
                              perms, icon, remark, enabled_flag)
        SELECT 'Web 结果',
               (SELECT id FROM sys_menu
                 WHERE path = '/web-management' AND enabled_flag = 1
                 ORDER BY id LIMIT 1),
               4, '/web/result', 'web_view/web_result_list',
               1, 0, 'C', 1, 1,
               NULL, 'ele-Document', NULL, 1
        WHERE NOT EXISTS (
            SELECT 1 FROM sys_menu
            WHERE path = '/web/result' AND enabled_flag = 1
        )
        """
        )
    )

    # 6) 元素管理按钮
    conn.execute(
        sa.text(
            """
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component,
                              is_frame, is_cache, menu_type, visible, status,
                              perms, icon, remark, enabled_flag)
        SELECT '元素查询',
               (SELECT id FROM sys_menu WHERE path = '/web/element' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               1, NULL, NULL,
               1, 0, 'F', 0, 1,
               'web:element:list', NULL, NULL, 1
        WHERE NOT EXISTS (
            SELECT 1 FROM sys_menu WHERE perms = 'web:element:list' AND enabled_flag = 1
        )
        """
        )
    )

    conn.execute(
        sa.text(
            """
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component,
                              is_frame, is_cache, menu_type, visible, status,
                              perms, icon, remark, enabled_flag)
        SELECT '元素新增',
               (SELECT id FROM sys_menu WHERE path = '/web/element' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               2, NULL, NULL,
               1, 0, 'F', 0, 1,
               'web:element:add', NULL, NULL, 1
        WHERE NOT EXISTS (
            SELECT 1 FROM sys_menu WHERE perms = 'web:element:add' AND enabled_flag = 1
        )
        """
        )
    )

    conn.execute(
        sa.text(
            """
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component,
                              is_frame, is_cache, menu_type, visible, status,
                              perms, icon, remark, enabled_flag)
        SELECT '元素编辑',
               (SELECT id FROM sys_menu WHERE path = '/web/element' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               3, NULL, NULL,
               1, 0, 'F', 0, 1,
               'web:element:edit', NULL, NULL, 1
        WHERE NOT EXISTS (
            SELECT 1 FROM sys_menu WHERE perms = 'web:element:edit' AND enabled_flag = 1
        )
        """
        )
    )

    conn.execute(
        sa.text(
            """
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component,
                              is_frame, is_cache, menu_type, visible, status,
                              perms, icon, remark, enabled_flag)
        SELECT '元素删除',
               (SELECT id FROM sys_menu WHERE path = '/web/element' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               4, NULL, NULL,
               1, 0, 'F', 0, 1,
               'web:element:delete', NULL, NULL, 1
        WHERE NOT EXISTS (
            SELECT 1 FROM sys_menu WHERE perms = 'web:element:delete' AND enabled_flag = 1
        )
        """
        )
    )

    # 7) Web 脚本按钮
    conn.execute(
        sa.text(
            """
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component,
                              is_frame, is_cache, menu_type, visible, status,
                              perms, icon, remark, enabled_flag)
        SELECT '脚本查询',
               (SELECT id FROM sys_menu WHERE path = '/web/automation' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               1, NULL, NULL,
               1, 0, 'F', 0, 1,
               'web:script:list', NULL, NULL, 1
        WHERE NOT EXISTS (
            SELECT 1 FROM sys_menu WHERE perms = 'web:script:list' AND enabled_flag = 1
        )
        """
        )
    )

    conn.execute(
        sa.text(
            """
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component,
                              is_frame, is_cache, menu_type, visible, status,
                              perms, icon, remark, enabled_flag)
        SELECT '脚本保存',
               (SELECT id FROM sys_menu WHERE path = '/web/automation' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               2, NULL, NULL,
               1, 0, 'F', 0, 1,
               'web:script:save', NULL, NULL, 1
        WHERE NOT EXISTS (
            SELECT 1 FROM sys_menu WHERE perms = 'web:script:save' AND enabled_flag = 1
        )
        """
        )
    )

    conn.execute(
        sa.text(
            """
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component,
                              is_frame, is_cache, menu_type, visible, status,
                              perms, icon, remark, enabled_flag)
        SELECT '脚本执行',
               (SELECT id FROM sys_menu WHERE path = '/web/automation' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               3, NULL, NULL,
               1, 0, 'F', 0, 1,
               'web:script:run', NULL, NULL, 1
        WHERE NOT EXISTS (
            SELECT 1 FROM sys_menu WHERE perms = 'web:script:run' AND enabled_flag = 1
        )
        """
        )
    )

    # 8) Web 场景按钮
    conn.execute(
        sa.text(
            """
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component,
                              is_frame, is_cache, menu_type, visible, status,
                              perms, icon, remark, enabled_flag)
        SELECT '场景查询',
               (SELECT id FROM sys_menu WHERE path = '/web/group' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               1, NULL, NULL,
               1, 0, 'F', 0, 1,
               'web:group:list', NULL, NULL, 1
        WHERE NOT EXISTS (
            SELECT 1 FROM sys_menu WHERE perms = 'web:group:list' AND enabled_flag = 1
        )
        """
        )
    )

    conn.execute(
        sa.text(
            """
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component,
                              is_frame, is_cache, menu_type, visible, status,
                              perms, icon, remark, enabled_flag)
        SELECT '场景新增',
               (SELECT id FROM sys_menu WHERE path = '/web/group' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               2, NULL, NULL,
               1, 0, 'F', 0, 1,
               'web:group:add', NULL, NULL, 1
        WHERE NOT EXISTS (
            SELECT 1 FROM sys_menu WHERE perms = 'web:group:add' AND enabled_flag = 1
        )
        """
        )
    )

    conn.execute(
        sa.text(
            """
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component,
                              is_frame, is_cache, menu_type, visible, status,
                              perms, icon, remark, enabled_flag)
        SELECT '场景编辑',
               (SELECT id FROM sys_menu WHERE path = '/web/group' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               3, NULL, NULL,
               1, 0, 'F', 0, 1,
               'web:group:edit', NULL, NULL, 1
        WHERE NOT EXISTS (
            SELECT 1 FROM sys_menu WHERE perms = 'web:group:edit' AND enabled_flag = 1
        )
        """
        )
    )

    conn.execute(
        sa.text(
            """
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component,
                              is_frame, is_cache, menu_type, visible, status,
                              perms, icon, remark, enabled_flag)
        SELECT '场景删除',
               (SELECT id FROM sys_menu WHERE path = '/web/group' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               4, NULL, NULL,
               1, 0, 'F', 0, 1,
               'web:group:delete', NULL, NULL, 1
        WHERE NOT EXISTS (
            SELECT 1 FROM sys_menu WHERE perms = 'web:group:delete' AND enabled_flag = 1
        )
        """
        )
    )

    conn.execute(
        sa.text(
            """
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component,
                              is_frame, is_cache, menu_type, visible, status,
                              perms, icon, remark, enabled_flag)
        SELECT '场景执行',
               (SELECT id FROM sys_menu WHERE path = '/web/group' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               5, NULL, NULL,
               1, 0, 'F', 0, 1,
               'web:group:run', NULL, NULL, 1
        WHERE NOT EXISTS (
            SELECT 1 FROM sys_menu WHERE perms = 'web:group:run' AND enabled_flag = 1
        )
        """
        )
    )

    # 9) Web 结果按钮
    conn.execute(
        sa.text(
            """
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component,
                              is_frame, is_cache, menu_type, visible, status,
                              perms, icon, remark, enabled_flag)
        SELECT '结果查询',
               (SELECT id FROM sys_menu WHERE path = '/web/result' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               1, NULL, NULL,
               1, 0, 'F', 0, 1,
               'web:result:list', NULL, NULL, 1
        WHERE NOT EXISTS (
            SELECT 1 FROM sys_menu WHERE perms = 'web:result:list' AND enabled_flag = 1
        )
        """
        )
    )

    conn.execute(
        sa.text(
            """
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component,
                              is_frame, is_cache, menu_type, visible, status,
                              perms, icon, remark, enabled_flag)
        SELECT '结果详情',
               (SELECT id FROM sys_menu WHERE path = '/web/result' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               2, NULL, NULL,
               1, 0, 'F', 0, 1,
               'web:result:detail', NULL, NULL, 1
        WHERE NOT EXISTS (
            SELECT 1 FROM sys_menu WHERE perms = 'web:result:detail' AND enabled_flag = 1
        )
        """
        )
    )

    conn.execute(
        sa.text(
            """
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component,
                              is_frame, is_cache, menu_type, visible, status,
                              perms, icon, remark, enabled_flag)
        SELECT '结果报告',
               (SELECT id FROM sys_menu WHERE path = '/web/result' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               3, NULL, NULL,
               1, 0, 'F', 0, 1,
               'web:result:report', NULL, NULL, 1
        WHERE NOT EXISTS (
            SELECT 1 FROM sys_menu WHERE perms = 'web:result:report' AND enabled_flag = 1
        )
        """
        )
    )

    # 10) 绑定到 admin 角色
    conn.execute(
        sa.text(
            """
        INSERT INTO sys_role_menu (role_id, menu_id)
        SELECT r.id, m.id
        FROM sys_role r
        JOIN sys_menu m ON m.enabled_flag = 1
        WHERE r.role_key = 'admin'
          AND (
            m.path IN (
              '/web-management',
              '/web/element',
              '/web/automation',
              '/web/group',
              '/web/result'
            )
            OR m.perms IN (
              'web:element:list','web:element:add','web:element:edit','web:element:delete',
              'web:script:list','web:script:save','web:script:run',
              'web:group:list','web:group:add','web:group:edit','web:group:delete','web:group:run',
              'web:result:list','web:result:detail','web:result:report'
            )
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
                path IN (
                  '/web-management',
                  '/web/element',
                  '/web/automation',
                  '/web/group',
                  '/web/result'
                )
                OR perms IN (
                  'web:element:list','web:element:add','web:element:edit','web:element:delete',
                  'web:script:list','web:script:save','web:script:run',
                  'web:group:list','web:group:add','web:group:edit','web:group:delete','web:group:run',
                  'web:result:list','web:result:detail','web:result:report'
                )
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
          AND perms IN (
            'web:element:list','web:element:add','web:element:edit','web:element:delete',
            'web:script:list','web:script:save','web:script:run',
            'web:group:list','web:group:add','web:group:edit','web:group:delete','web:group:run',
            'web:result:list','web:result:detail','web:result:report'
          )
        """
        )
    )

    # 删除二级菜单和一级目录
    conn.execute(
        sa.text(
            """
        DELETE FROM sys_menu
        WHERE enabled_flag = 1 AND path IN (
          '/web/element',
          '/web/automation',
          '/web/group',
          '/web/result'
        )
        """
        )
    )

    conn.execute(
        sa.text(
            """
        DELETE FROM sys_menu
        WHERE enabled_flag = 1 AND path = '/web-management'
        """
        )
    )

