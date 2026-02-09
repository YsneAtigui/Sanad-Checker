"""Initial schema - all base tables

Revision ID: 000_initial
Revises: 
Create Date: 2026-02-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '000_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create initial database schema.
    
    Note: Enum types are automatically created by SQLAlchemy from
    the Column definitions. No manual CREATE TYPE needed.
    """
    
    # Create audit_jobs table
    # SQLAlchemy will auto-create the enum types from the Column definitions
    op.create_table(
        'audit_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('platform', sa.String(), nullable=True),
        sa.Column('status', sa.Enum('queued', 'in_progress', 'completed', 'failed', name='auditstatus'), 
                  nullable=False, server_default='queued'),
        sa.Column('protocol_results', postgresql.JSONB(), nullable=True),
        sa.Column('schema_results', postgresql.JSONB(), nullable=True),
        sa.Column('content_results', postgresql.JSONB(), nullable=True),
        sa.Column('edge_results', postgresql.JSONB(), nullable=True),
        sa.Column('bilingual_results', postgresql.JSONB(), nullable=True),
        sa.Column('overall_score', sa.Integer(), nullable=True),
        sa.Column('severity_counts', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('raw_html_path', sa.String(), nullable=True),
        sa.Column('screenshot_path', sa.String(), nullable=True),
        sa.Column('report_markdown', sa.Text(), nullable=True),
    )
    
    # Create indexes for audit_jobs
    op.create_index('ix_audit_jobs_status', 'audit_jobs', ['status'])
    op.create_index('ix_audit_jobs_created_at', 'audit_jobs', ['created_at'])
    op.create_index('ix_audit_jobs_url', 'audit_jobs', ['url'])
    
    # Create audit_issues table
    op.create_table(
        'audit_issues',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('audit_job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('issue_type', sa.String(), nullable=False),
        sa.Column('severity', sa.Enum('critical', 'high', 'medium', 'low', name='issueseverity'), 
                  nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('recommendation', sa.Text(), nullable=True),
        sa.Column('affected_field', sa.String(), nullable=True),
        sa.Column('expected_value', sa.String(), nullable=True),
        sa.Column('actual_value', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['audit_job_id'], ['audit_jobs.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for audit_issues
    op.create_index('ix_audit_issues_audit_job_id', 'audit_issues', ['audit_job_id'])
    op.create_index('ix_audit_issues_severity', 'audit_issues', ['severity'])


def downgrade():
    """Drop all tables and enum types."""
    # Drop indexes
    op.drop_index('ix_audit_issues_severity', table_name='audit_issues')
    op.drop_index('ix_audit_issues_audit_job_id', table_name='audit_issues')
    op.drop_table('audit_issues')
    
    op.drop_index('ix_audit_jobs_url', table_name='audit_jobs')
    op.drop_index('ix_audit_jobs_created_at', table_name='audit_jobs')
    op.drop_index('ix_audit_jobs_status', table_name='audit_jobs')
    op.drop_table('audit_jobs')
    
    # Drop enum types (SQLAlchemy handles this automatically, but explicit is better)
    op.execute("DROP TYPE IF EXISTS issueseverity")
    op.execute("DROP TYPE IF EXISTS auditstatus")
