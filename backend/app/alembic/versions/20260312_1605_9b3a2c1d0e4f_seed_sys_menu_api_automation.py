"""seed sys_menu for menu management and api automation

Revision ID: 9b3a2c1d0e4f
Revises: 587c5ffd5ff7
Create Date: 2026-03-12 16:05:00.000000

为新架构（sys_*）初始化必要菜单与按钮权限：
- 系统设置 -> 菜单管理
- 测试管理 -> 接口自动化
- 接口自动化按钮权限（v-auth）
并将上述菜单/权限分配给 admin 角色（若不存在则创建）。
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9b3a2c1d0e4f"
down_revision = "587c5ffd5ff7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1) ensure admin role exists
    conn.execute(sa.text("""
        INSERT INTO sys_role (role_name, role_key, role_sort, data_scope, status, remark, enabled_flag)
        SELECT '管理员', 'admin', 1, 4, 1, '系统初始化角色', 1
        WHERE NOT EXISTS (SELECT 1 FROM sys_role WHERE role_key = 'admin' AND enabled_flag = 1)
    """))

    # 2) ensure system directory and menu management exist
    conn.execute(sa.text("""
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, remark, enabled_flag)
        SELECT '系统设置', 0, 60, '/system', 'layout/routerView/parent', 1, 0, 'M', 1, 1, NULL, 'iconfont icon-xitongshezhi', NULL, 1
        WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE path = '/system' AND enabled_flag = 1)
    """))

    conn.execute(sa.text("""
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, remark, enabled_flag)
        SELECT '菜单管理',
               (SELECT id FROM sys_menu WHERE path = '/system' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               1, '/system/menu', 'system/menu/index', 1, 0, 'C', 1, 1, NULL, 'iconfont icon-caidan', NULL, 1
        WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE path = '/system/menu' AND enabled_flag = 1)
    """))

    # 3) ensure api automation as top-level directory and its page menu exist
    # 一级目录：用于侧边栏展示与展开
    conn.execute(sa.text("""
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, remark, enabled_flag)
        SELECT '接口自动化', 0, 30, '/api-automation', 'layout/routerView/parent', 1, 0, 'M', 1, 1, NULL, 'ele-Connection', NULL, 1
        WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE path = '/api-automation' AND enabled_flag = 1)
    """))

    # 二级菜单页：真正加载组件
    conn.execute(sa.text("""
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, remark, enabled_flag)
        SELECT '接口自动化',
               (SELECT id FROM sys_menu WHERE path = '/api-automation' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               1, '/api-automation/index', 'testing/api-automation/index', 1, 0, 'C', 1, 1, NULL, 'ele-Connection', NULL, 1
        WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE path = '/api-automation/index' AND enabled_flag = 1)
    """))

    # 4) buttons under api automation page menu (type F, invisible)
    conn.execute(sa.text("""
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, remark, enabled_flag)
        SELECT '新增项目',
               (SELECT id FROM sys_menu WHERE path = '/api-automation/index' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               1, NULL, NULL, 1, 0, 'F', 0, 1, 'apiAutomation:project:add', NULL, NULL, 1
        WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE perms = 'apiAutomation:project:add' AND enabled_flag = 1)
    """))

    conn.execute(sa.text("""
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, remark, enabled_flag)
        SELECT '删除项目',
               (SELECT id FROM sys_menu WHERE path = '/api-automation/index' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               2, NULL, NULL, 1, 0, 'F', 0, 1, 'apiAutomation:project:delete', NULL, NULL, 1
        WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE perms = 'apiAutomation:project:delete' AND enabled_flag = 1)
    """))

    conn.execute(sa.text("""
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, remark, enabled_flag)
        SELECT '新增服务',
               (SELECT id FROM sys_menu WHERE path = '/api-automation/index' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               3, NULL, NULL, 1, 0, 'F', 0, 1, 'apiAutomation:service:add', NULL, NULL, 1
        WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE perms = 'apiAutomation:service:add' AND enabled_flag = 1)
    """))

    conn.execute(sa.text("""
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, remark, enabled_flag)
        SELECT '删除服务',
               (SELECT id FROM sys_menu WHERE path = '/api-automation/index' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               4, NULL, NULL, 1, 0, 'F', 0, 1, 'apiAutomation:service:delete', NULL, NULL, 1
        WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE perms = 'apiAutomation:service:delete' AND enabled_flag = 1)
    """))

    conn.execute(sa.text("""
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, remark, enabled_flag)
        SELECT '新建菜单节点',
               (SELECT id FROM sys_menu WHERE path = '/api-automation/index' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               5, NULL, NULL, 1, 0, 'F', 0, 1, 'apiAutomation:tree:add', NULL, NULL, 1
        WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE perms = 'apiAutomation:tree:add' AND enabled_flag = 1)
    """))

    conn.execute(sa.text("""
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, remark, enabled_flag)
        SELECT '重命名菜单节点',
               (SELECT id FROM sys_menu WHERE path = '/api-automation/index' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               6, NULL, NULL, 1, 0, 'F', 0, 1, 'apiAutomation:tree:edit', NULL, NULL, 1
        WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE perms = 'apiAutomation:tree:edit' AND enabled_flag = 1)
    """))

    conn.execute(sa.text("""
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, remark, enabled_flag)
        SELECT '删除菜单节点',
               (SELECT id FROM sys_menu WHERE path = '/api-automation/index' AND enabled_flag = 1 ORDER BY id LIMIT 1),
               7, NULL, NULL, 1, 0, 'F', 0, 1, 'apiAutomation:tree:delete', NULL, NULL, 1
        WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE perms = 'apiAutomation:tree:delete' AND enabled_flag = 1)
    """))

    # 5) assign these menus to admin role; also bind admin role to super-admin users if present
    conn.execute(sa.text("""
        INSERT INTO sys_role_menu (role_id, menu_id)
        SELECT r.id, m.id
        FROM sys_role r
        JOIN sys_menu m ON m.enabled_flag = 1
        WHERE r.role_key = 'admin'
          AND m.path IN ('/system', '/system/menu', '/api-automation', '/api-automation/index')
          AND NOT EXISTS (
              SELECT 1 FROM sys_role_menu rm
              WHERE rm.role_id = r.id AND rm.menu_id = m.id
          )
    """))

    conn.execute(sa.text("""
        INSERT INTO sys_role_menu (role_id, menu_id)
        SELECT r.id, m.id
        FROM sys_role r
        JOIN sys_menu m ON m.enabled_flag = 1
        WHERE r.role_key = 'admin'
          AND m.perms IN (
              'apiAutomation:project:add',
              'apiAutomation:project:delete',
              'apiAutomation:service:add',
              'apiAutomation:service:delete',
              'apiAutomation:tree:add',
              'apiAutomation:tree:edit',
              'apiAutomation:tree:delete'
          )
          AND NOT EXISTS (
              SELECT 1 FROM sys_role_menu rm
              WHERE rm.role_id = r.id AND rm.menu_id = m.id
          )
    """))

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

    # remove role-menu bindings for the seeded entries
    conn.execute(sa.text("""
        DELETE FROM sys_role_menu
        WHERE role_id IN (SELECT id FROM sys_role WHERE role_key = 'admin' AND enabled_flag = 1)
          AND menu_id IN (
              SELECT id FROM sys_menu
              WHERE path IN ('/system', '/system/menu', '/api-automation', '/api-automation/index')
                 OR perms LIKE 'apiAutomation:%'
          )
    """))

    # remove seeded buttons and menus (keep admin role)
    conn.execute(sa.text("DELETE FROM sys_menu WHERE perms LIKE 'apiAutomation:%'"))
    conn.execute(sa.text("DELETE FROM sys_menu WHERE path IN ('/api-automation/index', '/api-automation', '/system/menu', '/system')"))

