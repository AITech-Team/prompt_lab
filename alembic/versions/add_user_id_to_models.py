"""add user_id to models for user isolation

Revision ID: add_user_id_to_models
Revises: be8440705f4b
Create Date: 2025-06-16 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = 'add_user_id_to_models'
down_revision = 'be8440705f4b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 使用批处理模式为SQLite添加外键约束
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()
    
    # 添加user_id字段到各个表
    # 添加到llm_models表
    with op.batch_alter_table('llm_models') as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_llm_models_user_id', 'users', ['user_id'], ['id'])
    
    # 添加到prompt_templates表
    with op.batch_alter_table('prompt_templates') as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_prompt_templates_user_id', 'users', ['user_id'], ['id'])
    
    # 添加到prompts表
    with op.batch_alter_table('prompts') as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_prompts_user_id', 'users', ['user_id'], ['id'])
    
    # 添加到prompt_history表
    with op.batch_alter_table('prompt_history') as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_prompt_history_user_id', 'users', ['user_id'], ['id'])
    
    # 添加到responses表
    with op.batch_alter_table('responses') as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_responses_user_id', 'users', ['user_id'], ['id'])
    
    # 添加到prompt_evaluations表
    with op.batch_alter_table('prompt_evaluations') as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_prompt_evaluations_user_id', 'users', ['user_id'], ['id'])
    
    # 添加到test_records表
    with op.batch_alter_table('test_records') as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_test_records_user_id', 'users', ['user_id'], ['id'])
    
    # 创建复合唯一约束和索引
    with op.batch_alter_table('llm_models') as batch_op:
        batch_op.drop_index('ix_llm_models_name')
        batch_op.create_index('ix_llm_models_name_user_id', ['name', 'user_id'], unique=False)
        batch_op.create_index('ix_llm_models_user_id', ['user_id'], unique=False)
        batch_op.create_unique_constraint('uq_model_user_name', ['user_id', 'name'])
        batch_op.create_index('ix_model_user_id_name_is_deleted', ['user_id', 'name', 'is_deleted'], unique=True)
    
    with op.batch_alter_table('prompt_templates') as batch_op:
        batch_op.drop_index('ix_prompt_templates_name')
        batch_op.create_index('ix_prompt_templates_name_user_id', ['name', 'user_id'], unique=False)
        batch_op.create_index('ix_prompt_templates_user_id', ['user_id'], unique=False)
        batch_op.create_unique_constraint('uq_template_user_name', ['user_id', 'name'])
        batch_op.create_index('ix_template_user_id_name_is_deleted', ['user_id', 'name', 'is_deleted'], unique=True)
    
    with op.batch_alter_table('prompts') as batch_op:
        batch_op.drop_index('ix_prompts_name')
        batch_op.create_index('ix_prompts_name_user_id', ['name', 'user_id'], unique=False)
        batch_op.create_index('ix_prompts_user_id', ['user_id'], unique=False)
        batch_op.create_unique_constraint('uq_prompt_user_name', ['user_id', 'name'])
        batch_op.create_index('ix_prompt_user_id_name_is_deleted', ['user_id', 'name', 'is_deleted'], unique=True)
    
    # 为现有记录设置默认管理员用户ID
    op.execute("UPDATE llm_models SET user_id = 1 WHERE user_id IS NULL")
    op.execute("UPDATE prompt_templates SET user_id = 1 WHERE user_id IS NULL")
    op.execute("UPDATE prompts SET user_id = 1 WHERE user_id IS NULL")
    op.execute("UPDATE prompt_history SET user_id = 1 WHERE user_id IS NULL")
    op.execute("UPDATE responses SET user_id = 1 WHERE user_id IS NULL")
    op.execute("UPDATE prompt_evaluations SET user_id = 1 WHERE user_id IS NULL")
    op.execute("UPDATE test_records SET user_id = 1 WHERE user_id IS NULL")
    
    # 将字段设置为非空
    with op.batch_alter_table('llm_models') as batch_op:
        batch_op.alter_column('user_id', nullable=False)
    
    with op.batch_alter_table('prompt_templates') as batch_op:
        batch_op.alter_column('user_id', nullable=False)
    
    with op.batch_alter_table('prompts') as batch_op:
        batch_op.alter_column('user_id', nullable=False)
    
    with op.batch_alter_table('prompt_history') as batch_op:
        batch_op.alter_column('user_id', nullable=False)
    
    with op.batch_alter_table('responses') as batch_op:
        batch_op.alter_column('user_id', nullable=False)
    
    with op.batch_alter_table('prompt_evaluations') as batch_op:
        batch_op.alter_column('user_id', nullable=False)
    
    with op.batch_alter_table('test_records') as batch_op:
        batch_op.alter_column('user_id', nullable=False)


def downgrade() -> None:
    # 删除索引和约束
    with op.batch_alter_table('llm_models') as batch_op:
        batch_op.drop_index('ix_model_user_id_name_is_deleted')
        batch_op.drop_constraint('uq_model_user_name', type_='unique')
        batch_op.drop_index('ix_llm_models_name_user_id')
        batch_op.drop_index('ix_llm_models_user_id')
        batch_op.create_index('ix_llm_models_name', ['name'], unique=True)
        batch_op.drop_constraint('fk_llm_models_user_id', type_='foreignkey')
        batch_op.drop_column('user_id')
    
    with op.batch_alter_table('prompt_templates') as batch_op:
        batch_op.drop_index('ix_template_user_id_name_is_deleted')
        batch_op.drop_constraint('uq_template_user_name', type_='unique')
        batch_op.drop_index('ix_prompt_templates_name_user_id')
        batch_op.drop_index('ix_prompt_templates_user_id')
        batch_op.create_index('ix_prompt_templates_name', ['name'], unique=True)
        batch_op.drop_constraint('fk_prompt_templates_user_id', type_='foreignkey')
        batch_op.drop_column('user_id')
    
    with op.batch_alter_table('prompts') as batch_op:
        batch_op.drop_index('ix_prompt_user_id_name_is_deleted')
        batch_op.drop_constraint('uq_prompt_user_name', type_='unique')
        batch_op.drop_index('ix_prompts_name_user_id')
        batch_op.drop_index('ix_prompts_user_id')
        batch_op.create_index('ix_prompts_name', ['name'], unique=True)
        batch_op.drop_constraint('fk_prompts_user_id', type_='foreignkey')
        batch_op.drop_column('user_id')
    
    with op.batch_alter_table('prompt_history') as batch_op:
        batch_op.drop_constraint('fk_prompt_history_user_id', type_='foreignkey')
        batch_op.drop_column('user_id')
    
    with op.batch_alter_table('responses') as batch_op:
        batch_op.drop_constraint('fk_responses_user_id', type_='foreignkey')
        batch_op.drop_column('user_id')
    
    with op.batch_alter_table('prompt_evaluations') as batch_op:
        batch_op.drop_constraint('fk_prompt_evaluations_user_id', type_='foreignkey')
        batch_op.drop_column('user_id')
    
    with op.batch_alter_table('test_records') as batch_op:
        batch_op.drop_constraint('fk_test_records_user_id', type_='foreignkey')
        batch_op.drop_column('user_id') 