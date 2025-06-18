"""update template unique constraint

Revision ID: 003
Revises: 002
Create Date: 2024-01-15 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade():
    # 删除旧的组合唯一约束
    try:
        op.drop_constraint('uix_name_not_deleted', 'prompt_templates', type_='unique')
    except:
        pass
    
    # 创建新的部分索引
    op.create_index(
        'ix_prompt_templates_name_active',
        'prompt_templates',
        ['name'],
        unique=True,
        sqlite_where=sa.text('is_deleted = 0'),
        postgresql_where=sa.text('is_deleted = false')
    )

def downgrade():
    # 删除部分索引
    op.drop_index('ix_prompt_templates_name_active', table_name='prompt_templates')
    
    # 恢复旧的组合唯一约束
    op.create_unique_constraint(
        'uix_name_not_deleted',
        'prompt_templates',
        ['name', 'is_deleted']
    ) 