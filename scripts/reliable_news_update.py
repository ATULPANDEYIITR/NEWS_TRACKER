from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text

from app.database.session import SessionLocal


PROJECT_ROOT = Path(__file__).resolve().parent.parent
COLLECTOR_SCRIPT = PROJECT_ROOT / "scripts" / "run_news_update.py"

MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 30
LOCK_FILE = PROJECT_ROOT / "data" / "news_collection.lock"


def create_reliability_table():

    db = SessionLocal()

    try:

        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS collection_reliability_log (
                    id BIGSERIAL PRIMARY KEY,
                    started_at TIMESTAMPTZ NOT NULL,
                    finished_at TIMESTAMPTZ,
                    attempt INTEGER NOT NULL,
                    status VARCHAR(30) NOT NULL,
                    exit_code INTEGER,
                    duration_seconds DOUBLE PRECISION,
                    message TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        )

        db.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS
                ix_collection_reliability_started
                ON collection_reliability_log(started_at)
                """
            )
        )

        db.commit()

    finally:

        db.close()


def write_log(
    started_at,
    finished_at,
    attempt,
    status,
    exit_code,
    duration_seconds,
    message,
):

    db = SessionLocal()

    try:

        db.execute(
            text(
                """
                INSERT INTO collection_reliability_log
                (
                    started_at,
                    finished_at,
                    attempt,
                    status,
                    exit_code,
                    duration_seconds,
                    message
                )
                VALUES
                (
                    :started_at,
                    :finished_at,
                    :attempt,
                    :status,
                    :exit_code,
                    :duration_seconds,
                    :message
                )
                """
            ),
            {
                "started_at": started_at,
                "finished_at": finished_at,
                "attempt": attempt,
                "status": status,
                "exit_code": exit_code,
                "duration_seconds": duration_seconds,
                "message": message[:10000],
            },
        )

        db.commit()

    finally:

        db.close()


def acquire_lock():

    LOCK_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:

        fd = os.open(
            str(LOCK_FILE),
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
        )

        with os.fdopen(fd, "w", encoding="utf-8") as file:

            file.write(
                json.dumps(
                    {
                        "pid": os.getpid(),
                        "started_at":
                            datetime.now(
                                timezone.utc
                            ).isoformat(),
                    }
                )
            )

        return True

    except FileExistsError:

        try:

            lock_age = (
                time.time()
                - LOCK_FILE.stat().st_mtime
            )

            # Remove abandoned lock older than 2 hours.
            if lock_age > 7200:

                LOCK_FILE.unlink(
                    missing_ok=True
                )

                return acquire_lock()

        except OSError:
            pass

        return False


def release_lock():

    try:

        LOCK_FILE.unlink(
            missing_ok=True
        )

    except OSError:
        pass


def run_collector():

    command = [
        sys.executable,
        str(COLLECTOR_SCRIPT),
    ]

    process = subprocess.run(
        command,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    output = (
        (process.stdout or "")
        + "\n"
        + (process.stderr or "")
    ).strip()

    return process.returncode, output


def main():

    print()
    print(
        "LIVE NEWS COLLECTION RELIABILITY ENGINE"
    )
    print(
        "========================================"
    )

    create_reliability_table()

    if not acquire_lock():

        message = (
            "Another news collection process "
            "is already running."
        )

        print()
        print(message)
        print(
            "Current collection skipped safely."
        )

        write_log(
            started_at=datetime.now(
                timezone.utc
            ),
            finished_at=datetime.now(
                timezone.utc
            ),
            attempt=0,
            status="skipped_locked",
            exit_code=None,
            duration_seconds=0,
            message=message,
        )

        return 0

    try:

        overall_started = datetime.now(
            timezone.utc
        )

        for attempt in range(
            1,
            MAX_ATTEMPTS + 1,
        ):

            started = datetime.now(
                timezone.utc
            )

            print()
            print(
                f"Collection attempt "
                f"{attempt}/{MAX_ATTEMPTS}"
            )
            print(
                "------------------------------"
            )

            try:

                exit_code, output = run_collector()

            except Exception as exc:

                exit_code = 1

                output = (
                    f"Collector execution error: "
                    f"{type(exc).__name__}: {exc}"
                )

            finished = datetime.now(
                timezone.utc
            )

            duration = (
                finished - started
            ).total_seconds()

            if exit_code == 0:

                status = "success"

                print()
                print(
                    "COLLECTION ATTEMPT: SUCCESS"
                )

                write_log(
                    started_at=started,
                    finished_at=finished,
                    attempt=attempt,
                    status=status,
                    exit_code=exit_code,
                    duration_seconds=duration,
                    message=output,
                )

                print()
                print(
                    "Reliability engine completed "
                    "successfully."
                )

                return 0

            status = (
                "failed_retrying"
                if attempt < MAX_ATTEMPTS
                else "failed"
            )

            write_log(
                started_at=started,
                finished_at=finished,
                attempt=attempt,
                status=status,
                exit_code=exit_code,
                duration_seconds=duration,
                message=output,
            )

            print()
            print(
                f"COLLECTION ATTEMPT FAILED "
                f"(exit code {exit_code})"
            )

            if output:

                print()
                print(
                    "Collector output:"
                )

                print(
                    output[-5000:]
                )

            if attempt < MAX_ATTEMPTS:

                print()
                print(
                    f"Retrying in "
                    f"{RETRY_DELAY_SECONDS} seconds..."
                )

                time.sleep(
                    RETRY_DELAY_SECONDS
                )

        finished_overall = datetime.now(
            timezone.utc
        )

        print()
        print(
            "========================================"
        )
        print(
            "ALL COLLECTION ATTEMPTS FAILED"
        )
        print(
            "========================================"
        )

        print(
            f"Duration: "
            f"{(
                finished_overall
                - overall_started
            ).total_seconds():.1f} seconds"
        )

        return 1

    finally:

        release_lock()


if __name__ == "__main__":

    raise SystemExit(
        main()
    )
