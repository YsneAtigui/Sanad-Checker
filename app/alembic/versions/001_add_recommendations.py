"""Add audit_recommendations table

Revision ID: 001
Revises: 
Create Date: 2026-02-08 19:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_add_recommendations'
down_revision: Union[str, None] = '000_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create audit_recommendations table
    op.create_table(
        'audit_recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('audit_job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('severity', sa.Enum('CRITICAL', 'WARNING', 'LOW', name='recommendationseverity'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('code_example', sa.Text(), nullable=True),
        sa.Column('impact', sa.String(), nullable=False),
        sa.Column('category', sa.Enum('PROTOCOL', 'SCHEMA', 'CONTENT', 'EDGE', name='recommendationcategory'), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['audit_job_id'], ['audit_jobs.id', ], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_audit_recommendations_audit_job_id', 'audit_recommendations', ['audit_job_id'])
    op.create_index('ix_audit_recommendations_severity', 'audit_recommendations', ['severity'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_audit_recommendations_severity', table_name='audit_recommendations')
    op.drop_index('ix_audit_recommendations_audit_job_id', table_name='audit_recommendations')
    
    # Drop table
    op.drop_table('audit_recommendations')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS recommendationcategory')
    op.execute('DROP TYPE IF EXISTS recommendationseverity')
