"""api_automation refactor: extend ApiServiceModel, add ApiSuiteModel/ApiCaseModel, extend ApiScriptResultListModel

Revision ID: 20260415_1000
Revises: 20260412_1000
Create Date: 2026-04-15 10:00:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260415_1000"
down_revision = "20260412_1000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. 扩展 api_automation_services ──────────────────────────────
    op.add_column("api_automation_services", sa.Column("source_type", sa.String(50), nullable=True, comment="接口文档类型：swagger/apifox"))
    op.add_column("api_automation_services", sa.Column("source_addr", sa.String(500), nullable=True, comment="接口文档地址"))
    op.add_column("api_automation_services", sa.Column("last_pull_status", sa.Integer(), nullable=True, server_default="0", comment="拉取状态：0=未拉取，1=成功，2=失败"))
    op.add_column("api_automation_services", sa.Column("manager", sa.BigInteger(), nullable=True, comment="负责人用户ID"))
    op.add_column("api_automation_services", sa.Column("business_id", sa.BigInteger(), nullable=True, comment="业务线ID"))
    op.add_column("api_automation_services", sa.Column("sort", sa.Integer(), nullable=True, server_default="0", comment="排序权重"))

    # ── 2. 扩展 api_automation_script_result_lists ───────────────────
    op.add_column("api_automation_script_result_lists", sa.Column("api_service_id", sa.BigInteger(), nullable=True, comment="关联服务ID，可为空（兼容历史数据）"))

    # ── 3. 新建 api_automation_suites ────────────────────────────────
    op.create_table(
        "api_automation_suites",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, comment="主键"),
        sa.Column("name", sa.String(255), nullable=False, comment="用例集名称"),
        sa.Column("parent", sa.BigInteger(), nullable=True, comment="父用例集ID，顶级为null"),
        sa.Column("api_service_id", sa.BigInteger(), nullable=False, comment="所属服务ID"),
        sa.Column("sort", sa.Integer(), nullable=True, server_default="0", comment="同级排序权重"),
        sa.Column("creation_date", sa.DateTime(), server_default=sa.text("NOW()"), comment="创建时间"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人ID"),
        sa.Column("updation_date", sa.DateTime(), server_default=sa.text("NOW()"), onupdate=sa.text("NOW()"), comment="更新时间"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="更新人ID"),
        sa.Column("enabled_flag", sa.Boolean(), nullable=False, server_default="1", comment="是否删除，0删除1非删除"),
        sa.Column("trace_id", sa.String(255), nullable=True, comment="trace_id"),
        mysql_charset="utf8",
    )

    # ── 4. 新建 api_automation_cases ─────────────────────────────────
    op.create_table(
        "api_automation_cases",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, comment="主键"),
        sa.Column("name", sa.String(255), nullable=False, comment="用例名称"),
        sa.Column("description", sa.String(500), nullable=True, comment="用例描述"),
        sa.Column("suite_id", sa.BigInteger(), nullable=False, comment="所属用例集ID"),
        sa.Column("script", sa.JSON(), nullable=True, comment="步骤列表"),
        sa.Column("status", sa.Integer(), nullable=True, server_default="0", comment="状态：0=未执行，1=通过，2=失败"),
        sa.Column("creation_date", sa.DateTime(), server_default=sa.text("NOW()"), comment="创建时间"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人ID"),
        sa.Column("updation_date", sa.DateTime(), server_default=sa.text("NOW()"), onupdate=sa.text("NOW()"), comment="更新时间"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="更新人ID"),
        sa.Column("enabled_flag", sa.Boolean(), nullable=False, server_default="1", comment="是否删除，0删除1非删除"),
        sa.Column("trace_id", sa.String(255), nullable=True, comment="trace_id"),
        mysql_charset="utf8",
    )


def downgrade() -> None:
    op.drop_table("api_automation_cases")
    op.drop_table("api_automation_suites")
    op.drop_column("api_automation_script_result_lists", "api_service_id")
    op.drop_column("api_automation_services", "sort")
    op.drop_column("api_automation_services", "business_id")
    op.drop_column("api_automation_services", "manager")
    op.drop_column("api_automation_services", "last_pull_status")
    op.drop_column("api_automation_services", "source_addr")
    op.drop_column("api_automation_services", "source_type")
