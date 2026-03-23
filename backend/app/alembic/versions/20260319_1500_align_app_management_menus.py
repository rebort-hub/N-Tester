"""align APP management menus to old structure

Revision ID: 20260319_1500
Revises: 20260319_1400
Create Date: 2026-03-19 15:00:00.000000

按旧前端结构对齐 sys_menu：
- 一级目录：APP管理 (/app_manage)
- 二级菜单：
  - 包体管理 (/app_manage/package) component: testing/app-management/package/index
  - APP自动化 (/app_manage/automation) component: testing/app-management/automation/index
  - 图像库   (/app_manage/images) component: testing/app-management/images/index
  - APP结果   (/app_manage/results) component: testing/app-management/results/index
- 隐藏页：
  - APP测试报告 (/app_report) component: testing/app-management/results/report

并同步 admin 角色授权。
"""

from alembic import op
import sqlalchemy as sa


revision = "20260319_1500"
down_revision = "20260319_1400"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # ensure admin role exists
    conn.execute(sa.text("""
        INSERT INTO sys_role (role_name, role_key, role_sort, data_scope, status, remark, enabled_flag)
        SELECT '管理员', 'admin', 1, 4, 1, '系统初始化角色', 1
        WHERE NOT EXISTS (SELECT 1 FROM sys_role WHERE role_key = 'admin' AND enabled_flag = 1)
    """))

    # 1) 一级目录：APP管理
    conn.execute(sa.text("""
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache,
                              menu_type, visible, status, perms, icon, remark, enabled_flag)
        SELECT 'APP管理', 0, 35, '/app_manage', 'layout/routerView/parent', 1, 0,
               'M', 1, 1, NULL, 'ele-Iphone', NULL, 1
        WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE path = '/app_manage' AND enabled_flag = 1)
    """))

    # 2) 二级菜单
    menus = [
        ("包体管理", 1, "/app_manage/package", "testing/app-management/package/index", "ele-SetUp"),
        ("APP自动化", 2, "/app_manage/automation", "testing/app-management/automation/index", "ele-Iphone"),
        ("图像库", 3, "/app_manage/images", "testing/app-management/images/index", "ele-PictureFilled"),
        ("APP结果", 4, "/app_manage/results", "testing/app-management/results/index", "ele-Document"),
    ]

    for name, order_num, path, component, icon in menus:
        conn.execute(sa.text("""
            INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache,
                                  menu_type, visible, status, perms, icon, remark, enabled_flag)
            SELECT :name,
                   (SELECT id FROM sys_menu WHERE path = '/app_manage' AND enabled_flag = 1 ORDER BY id LIMIT 1),
                   :order_num, :path, :component, 1, 0,
                   'C', 1, 1, NULL, :icon, NULL, 1
            WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE path = :path AND enabled_flag = 1)
        """), {"name": name, "order_num": order_num, "path": path, "component": component, "icon": icon})

    # 3) 报告页（隐藏）
    conn.execute(sa.text("""
        INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache,
                              menu_type, visible, status, perms, icon, remark, enabled_flag)
        SELECT 'APP测试报告', 0, 999, '/app_report', 'testing/app-management/results/report', 1, 0,
               'C', 0, 1, NULL, 'ele-Document', NULL, 1
        WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE path = '/app_report' AND enabled_flag = 1)
    """))

    # 4) 赋权给 admin
    conn.execute(sa.text("""
        INSERT INTO sys_role_menu (role_id, menu_id)
        SELECT r.id, m.id
        FROM sys_role r
        JOIN sys_menu m ON m.enabled_flag = 1
        WHERE r.role_key = 'admin'
          AND m.path IN (
            '/app_manage',
            '/app_manage/package',
            '/app_manage/automation',
            '/app_manage/images',
            '/app_manage/results',
            '/app_report'
          )
          AND NOT EXISTS (
              SELECT 1 FROM sys_role_menu rm
              WHERE rm.role_id = r.id AND rm.menu_id = m.id
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
              AND path IN (
                '/app_manage',
                '/app_manage/package',
                '/app_manage/automation',
                '/app_manage/images',
                '/app_manage/results',
                '/app_report'
              )
          )
    """))

    conn.execute(sa.text("""
        DELETE FROM sys_menu
        WHERE enabled_flag = 1
          AND path IN (
            '/app_manage/package',
            '/app_manage/automation',
            '/app_manage/images',
            '/app_manage/results',
            '/app_report',
            '/app_manage'
          )
    """))

