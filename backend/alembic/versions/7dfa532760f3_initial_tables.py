"""Initial_tables

Revision ID: 7dfa532760f3
Revises: 
Create Date: 2026-02-16 23:57:29.345811

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '7dfa532760f3'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('users',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('email_verified', sa.Boolean(), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('avatar_url', sa.String(), nullable=True),
    sa.Column('plan', sa.String(length=20), nullable=False),
    sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('last_login_at', sa.TIMESTAMP(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('deleted_at', sa.TIMESTAMP(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_plan'), 'users', ['plan'], unique=False)
    op.create_table('api_keys',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('key_prefix', sa.String(length=20), nullable=False),
    sa.Column('key_hash', sa.String(length=64), nullable=False),
    sa.Column('environment', sa.String(length=10), nullable=False),
    sa.Column('permissions', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text('\'["qr:read", "qr:write"]\''), nullable=False),
    sa.Column('ip_allowlist', sa.ARRAY(sa.String()), nullable=True),
    sa.Column('last_used_at', sa.TIMESTAMP(), nullable=True),
    sa.Column('expires_at', sa.TIMESTAMP(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('revoked_at', sa.TIMESTAMP(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_api_keys_key_hash'), 'api_keys', ['key_hash'], unique=False)
    op.create_index(op.f('ix_api_keys_key_prefix'), 'api_keys', ['key_prefix'], unique=False)
    op.create_index(op.f('ix_api_keys_user_id'), 'api_keys', ['user_id'], unique=False)
    op.create_table('qr_codes',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('type', sa.String(length=20), nullable=False),
    sa.Column('content', sa.String(), nullable=False),
    sa.Column('content_hash', sa.String(length=64), nullable=True),
    sa.Column('is_dynamic', sa.Boolean(), nullable=False),
    sa.Column('short_code', sa.String(length=10), nullable=True),
    sa.Column('options', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('storage_paths', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=True),
    sa.Column('folder_id', sa.UUID(), nullable=True),
    sa.Column('tags', sa.ARRAY(sa.String()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('expires_at', sa.TIMESTAMP(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('deleted_at', sa.TIMESTAMP(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_qr_codes_created_at'), 'qr_codes', ['created_at'], unique=False)
    op.create_index(op.f('ix_qr_codes_folder_id'), 'qr_codes', ['folder_id'], unique=False)
    op.create_index(op.f('ix_qr_codes_is_active'), 'qr_codes', ['is_active'], unique=False)
    op.create_index(op.f('ix_qr_codes_short_code'), 'qr_codes', ['short_code'], unique=True)
    op.create_index(op.f('ix_qr_codes_tags'), 'qr_codes', ['tags'], unique=False)
    op.create_index(op.f('ix_qr_codes_type'), 'qr_codes', ['type'], unique=False)
    op.create_index(op.f('ix_qr_codes_user_id'), 'qr_codes', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_qr_codes_user_id'), table_name='qr_codes')
    op.drop_index(op.f('ix_qr_codes_type'), table_name='qr_codes')
    op.drop_index(op.f('ix_qr_codes_tags'), table_name='qr_codes')
    op.drop_index(op.f('ix_qr_codes_short_code'), table_name='qr_codes')
    op.drop_index(op.f('ix_qr_codes_is_active'), table_name='qr_codes')
    op.drop_index(op.f('ix_qr_codes_folder_id'), table_name='qr_codes')
    op.drop_index(op.f('ix_qr_codes_created_at'), table_name='qr_codes')
    op.drop_table('qr_codes')
    op.drop_index(op.f('ix_api_keys_user_id'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_key_prefix'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_key_hash'), table_name='api_keys')
    op.drop_table('api_keys')
    op.drop_index(op.f('ix_users_plan'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
