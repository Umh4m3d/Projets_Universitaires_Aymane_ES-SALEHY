"""sync missing schema for current models

Revision ID: f2c9a3f0d7b1
Revises: d5843f804702
Create Date: 2026-05-29 16:25:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f2c9a3f0d7b1"
down_revision: Union[str, Sequence[str], None] = "d5843f804702"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE student_profiles
        ADD COLUMN IF NOT EXISTS parent_email VARCHAR(255)
        """
    )

    op.execute(
        """
        ALTER TABLE sessions
        ADD COLUMN IF NOT EXISTS cancellation_reason VARCHAR(500),
        ADD COLUMN IF NOT EXISTS cancelled_by_id UUID,
        ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMPTZ
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_sessions_cancelled_by_id_users'
            ) THEN
                ALTER TABLE sessions
                ADD CONSTRAINT fk_sessions_cancelled_by_id_users
                FOREIGN KEY (cancelled_by_id) REFERENCES users (id);
            END IF;
        END $$;
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS progress_entries (
            id UUID PRIMARY KEY,
            course_id UUID NOT NULL REFERENCES courses (id),
            group_id UUID NOT NULL REFERENCES groups (id),
            teacher_id UUID NOT NULL REFERENCES users (id),
            chapter VARCHAR(255) NOT NULL,
            entry_type VARCHAR(50) NOT NULL,
            notes TEXT,
            completion DOUBLE PRECISION NOT NULL DEFAULT 0.0,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS followup_tasks (
            id UUID PRIMARY KEY,
            assigned_to_id UUID REFERENCES users (id),
            subject_user_id UUID REFERENCES users (id),
            payment_id UUID REFERENCES payments (id),
            session_id UUID REFERENCES sessions (id),
            task_type VARCHAR(50) NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            status VARCHAR(20) NOT NULL DEFAULT 'open',
            due_date TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL,
            resolved_at TIMESTAMPTZ
        )
        """
    )


def downgrade() -> None:
    pass
