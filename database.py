import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Database:
    def __init__(self, path: str) -> None:
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
        self._seed_defaults()

    def close(self) -> None:
        self.conn.close()

    def _execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        cur = self.conn.execute(query, params)
        self.conn.commit()
        return cur

    def _fetchone(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        cur = self.conn.execute(query, params)
        return cur.fetchone()

    def _fetchall(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        cur = self.conn.execute(query, params)
        return cur.fetchall()

    def _ensure_column(self, table_name: str, column_name: str, definition: str) -> None:
        rows = self._fetchall(f"PRAGMA table_info({table_name})")
        existing = {str(row["name"]) for row in rows}
        if column_name in existing:
            return
        self._execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER NOT NULL UNIQUE,
                username TEXT,
                full_name TEXT,
                language TEXT,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                birth_date TEXT,
                registered_at TEXT,
                no_payment_attempts INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS admins (
                tg_id INTEGER PRIMARY KEY
            );

            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_ref TEXT NOT NULL UNIQUE,
                join_url TEXT,
                title TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_name TEXT NOT NULL,
                card_number TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_tg_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                receipt_file_id TEXT NOT NULL,
                receipt_type TEXT NOT NULL,
                receipt_caption TEXT,
                admin_tg_id INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS user_credits (
                user_tg_id INTEGER PRIMARY KEY,
                credits INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS message_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_tg_id INTEGER NOT NULL,
                user_message_id INTEGER,
                admin_chat_id INTEGER NOT NULL,
                admin_message_id INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS birthday_notifications (
                user_tg_id INTEGER NOT NULL,
                year INTEGER NOT NULL,
                notified_at TEXT NOT NULL,
                PRIMARY KEY (user_tg_id, year)
            );
            """
        )
        self._ensure_column("users", "first_name", "TEXT")
        self._ensure_column("users", "last_name", "TEXT")
        self._ensure_column("users", "phone", "TEXT")
        self._ensure_column("users", "birth_date", "TEXT")
        self._ensure_column("users", "registered_at", "TEXT")
        self._ensure_column("users", "language", "TEXT")
        self._ensure_column("message_links", "user_message_id", "INTEGER")
        self.conn.commit()

    def _seed_defaults(self) -> None:
        self.set_setting_if_missing("instagram_url", "")
        self.set_setting_if_missing("suspicious_threshold", "3")
        self.set_setting_if_missing("inbox_chat_id", "")

    def set_setting_if_missing(self, key: str, value: str) -> None:
        self._execute("INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)", (key, value))

    def set_setting(self, key: str, value: str) -> None:
        self._execute(
            """
            INSERT INTO settings(key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )

    def get_setting(self, key: str, default: str = "") -> str:
        row = self._fetchone("SELECT value FROM settings WHERE key = ?", (key,))
        if not row:
            return default
        return row["value"] if row["value"] is not None else default

    def get_int_setting(self, key: str, default: int) -> int:
        value = self.get_setting(key, str(default))
        try:
            return int(value)
        except ValueError:
            return default

    def ensure_super_admin(self, tg_id: int) -> None:
        self._execute("INSERT OR IGNORE INTO admins(tg_id) VALUES (?)", (tg_id,))

    def is_admin(self, tg_id: int) -> bool:
        row = self._fetchone("SELECT 1 FROM admins WHERE tg_id = ?", (tg_id,))
        return bool(row)

    def add_admin(self, tg_id: int) -> None:
        self._execute("INSERT OR IGNORE INTO admins(tg_id) VALUES (?)", (tg_id,))

    def remove_admin(self, tg_id: int) -> int:
        cur = self._execute("DELETE FROM admins WHERE tg_id = ?", (tg_id,))
        return cur.rowcount

    def list_admins(self) -> List[int]:
        rows = self._fetchall("SELECT tg_id FROM admins ORDER BY tg_id")
        return [int(row["tg_id"]) for row in rows]

    def upsert_user(self, tg_id: int, username: Optional[str], full_name: str) -> None:
        self._execute(
            """
            INSERT INTO users(tg_id, username, full_name, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(tg_id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name
            """,
            (tg_id, username, full_name, utc_now()),
        )

    def total_users(self) -> int:
        row = self._fetchone("SELECT COUNT(*) AS cnt FROM users")
        return int(row["cnt"]) if row else 0

    def increment_no_payment_attempt(self, tg_id: int) -> int:
        self._execute(
            """
            UPDATE users
            SET no_payment_attempts = no_payment_attempts + 1
            WHERE tg_id = ?
            """,
            (tg_id,),
        )
        row = self._fetchone("SELECT no_payment_attempts FROM users WHERE tg_id = ?", (tg_id,))
        return int(row["no_payment_attempts"]) if row else 0

    def reset_no_payment_attempts(self, tg_id: int) -> None:
        self._execute(
            "UPDATE users SET no_payment_attempts = 0 WHERE tg_id = ?",
            (tg_id,),
        )

    def add_channel(self, chat_ref: str, join_url: Optional[str], title: Optional[str]) -> None:
        self._execute(
            """
            INSERT INTO channels(chat_ref, join_url, title, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(chat_ref) DO UPDATE SET
                join_url = excluded.join_url,
                title = COALESCE(excluded.title, channels.title)
            """,
            (chat_ref, join_url, title, utc_now()),
        )

    def list_channels(self) -> List[sqlite3.Row]:
        return self._fetchall("SELECT * FROM channels ORDER BY id ASC")

    def remove_channel(self, channel_id: int) -> int:
        cur = self._execute("DELETE FROM channels WHERE id = ?", (channel_id,))
        return cur.rowcount

    def add_card(self, owner_name: str, card_number: str, activate: bool) -> int:
        if activate:
            self._execute("UPDATE cards SET is_active = 0")
        else:
            row = self._fetchone("SELECT id FROM cards LIMIT 1")
            if not row:
                activate = True

        cur = self._execute(
            """
            INSERT INTO cards(owner_name, card_number, is_active, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (owner_name, card_number, 1 if activate else 0, utc_now()),
        )
        return int(cur.lastrowid)

    def list_cards(self) -> List[sqlite3.Row]:
        return self._fetchall("SELECT * FROM cards ORDER BY id ASC")

    def set_active_card(self, card_id: int) -> bool:
        exists = self._fetchone("SELECT id FROM cards WHERE id = ?", (card_id,))
        if not exists:
            return False
        self._execute("UPDATE cards SET is_active = 0")
        self._execute("UPDATE cards SET is_active = 1 WHERE id = ?", (card_id,))
        return True

    def get_active_card(self) -> Optional[sqlite3.Row]:
        row = self._fetchone("SELECT * FROM cards WHERE is_active = 1 LIMIT 1")
        if row:
            return row
        row = self._fetchone("SELECT * FROM cards ORDER BY id ASC LIMIT 1")
        if row:
            self.set_active_card(int(row["id"]))
        return row

    def remove_card(self, card_id: int) -> bool:
        row = self._fetchone("SELECT id, is_active FROM cards WHERE id = ?", (card_id,))
        if not row:
            return False

        was_active = int(row["is_active"]) == 1
        self._execute("DELETE FROM cards WHERE id = ?", (card_id,))
        if was_active:
            replacement = self._fetchone("SELECT id FROM cards ORDER BY id ASC LIMIT 1")
            if replacement:
                self.set_active_card(int(replacement["id"]))
        return True

    def get_credits(self, user_tg_id: int) -> int:
        row = self._fetchone("SELECT credits FROM user_credits WHERE user_tg_id = ?", (user_tg_id,))
        return int(row["credits"]) if row else 0

    def add_credits(self, user_tg_id: int, amount: int = 1) -> None:
        self._execute(
            """
            INSERT INTO user_credits(user_tg_id, credits)
            VALUES (?, ?)
            ON CONFLICT(user_tg_id) DO UPDATE SET credits = credits + excluded.credits
            """,
            (user_tg_id, amount),
        )

    def consume_credit(self, user_tg_id: int, amount: int = 1) -> bool:
        self._execute(
            "INSERT OR IGNORE INTO user_credits(user_tg_id, credits) VALUES (?, 0)",
            (user_tg_id,),
        )
        cur = self._execute(
            """
            UPDATE user_credits
            SET credits = credits - ?
            WHERE user_tg_id = ? AND credits >= ?
            """,
            (amount, user_tg_id, amount),
        )
        return cur.rowcount > 0

    def create_payment(
        self,
        user_tg_id: int,
        receipt_file_id: str,
        receipt_type: str,
        receipt_caption: Optional[str],
    ) -> int:
        now = utc_now()
        cur = self._execute(
            """
            INSERT INTO payments(
                user_tg_id, status, receipt_file_id, receipt_type, receipt_caption,
                admin_tg_id, created_at, updated_at
            )
            VALUES (?, 'pending', ?, ?, ?, NULL, ?, ?)
            """,
            (user_tg_id, receipt_file_id, receipt_type, receipt_caption, now, now),
        )
        return int(cur.lastrowid)

    def get_payment(self, payment_id: int) -> Optional[sqlite3.Row]:
        return self._fetchone("SELECT * FROM payments WHERE id = ?", (payment_id,))

    def get_pending_payment(self, user_tg_id: int) -> Optional[sqlite3.Row]:
        return self._fetchone(
            """
            SELECT * FROM payments
            WHERE user_tg_id = ? AND status = 'pending'
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_tg_id,),
        )

    def update_payment_status(self, payment_id: int, status: str, admin_tg_id: int) -> bool:
        cur = self._execute(
            """
            UPDATE payments
            SET status = ?, admin_tg_id = ?, updated_at = ?
            WHERE id = ? AND status = 'pending'
            """,
            (status, admin_tg_id, utc_now(), payment_id),
        )
        return cur.rowcount > 0

    def payment_stats(self) -> Dict[str, int]:
        rows = self._fetchall(
            """
            SELECT status, COUNT(*) AS cnt
            FROM payments
            GROUP BY status
            """
        )
        result: Dict[str, int] = {"pending": 0, "approved": 0, "rejected": 0}
        for row in rows:
            result[str(row["status"])] = int(row["cnt"])
        return result

    def save_message_link(
        self,
        user_tg_id: int,
        admin_chat_id: int,
        admin_message_id: int,
        user_message_id: Optional[int] = None,
    ) -> int:
        cur = self._execute(
            """
            INSERT INTO message_links(
                user_tg_id, user_message_id, admin_chat_id, admin_message_id, created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_tg_id, user_message_id, admin_chat_id, admin_message_id, utc_now()),
        )
        return int(cur.lastrowid)

    def get_message_link(self, admin_chat_id: int, admin_message_id: int) -> Optional[sqlite3.Row]:
        return self._fetchone(
            """
            SELECT *
            FROM message_links
            WHERE admin_chat_id = ? AND admin_message_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (admin_chat_id, admin_message_id),
        )

    def get_user_for_admin_message(self, admin_chat_id: int, admin_message_id: int) -> Optional[int]:
        row = self.get_message_link(admin_chat_id, admin_message_id)
        if not row:
            return None
        return int(row["user_tg_id"])

    def get_user_message_for_admin_message(
        self, admin_chat_id: int, admin_message_id: int
    ) -> Optional[int]:
        row = self._fetchone(
            """
            SELECT user_message_id
            FROM message_links
            WHERE admin_chat_id = ? AND admin_message_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (admin_chat_id, admin_message_id),
        )
        if not row:
            return None
        if row["user_message_id"] is None:
            return None
        return int(row["user_message_id"])

    def total_user_messages(self) -> int:
        row = self._fetchone("SELECT COUNT(*) AS cnt FROM message_links")
        return int(row["cnt"]) if row else 0

    def get_user(self, tg_id: int) -> Optional[sqlite3.Row]:
        return self._fetchone("SELECT * FROM users WHERE tg_id = ?", (tg_id,))

    def get_user_profile(self, tg_id: int) -> Optional[sqlite3.Row]:
        return self._fetchone(
            """
            SELECT tg_id, username, first_name, last_name, phone, birth_date, language
            FROM users
            WHERE tg_id = ?
            """,
            (tg_id,),
        )

    def delete_user_data(self, tg_id: int) -> bool:
        self._execute("DELETE FROM birthday_notifications WHERE user_tg_id = ?", (tg_id,))
        self._execute("DELETE FROM message_links WHERE user_tg_id = ?", (tg_id,))
        self._execute("DELETE FROM user_credits WHERE user_tg_id = ?", (tg_id,))
        self._execute("DELETE FROM payments WHERE user_tg_id = ?", (tg_id,))
        cur = self._execute("DELETE FROM users WHERE tg_id = ?", (tg_id,))
        return cur.rowcount > 0

    def _refresh_user_full_name(self, tg_id: int) -> None:
        row = self._fetchone(
            "SELECT first_name, last_name FROM users WHERE tg_id = ?",
            (tg_id,),
        )
        if not row:
            return
        first_name = str(row["first_name"] or "").strip()
        last_name = str(row["last_name"] or "").strip()
        full_name = f"{first_name} {last_name}".strip()
        self._execute(
            "UPDATE users SET full_name = ? WHERE tg_id = ?",
            (full_name, tg_id),
        )

    def update_user_first_name(self, tg_id: int, first_name: str) -> None:
        self._execute(
            "UPDATE users SET first_name = ? WHERE tg_id = ?",
            (first_name, tg_id),
        )
        self._refresh_user_full_name(tg_id)

    def update_user_last_name(self, tg_id: int, last_name: str) -> None:
        self._execute(
            "UPDATE users SET last_name = ? WHERE tg_id = ?",
            (last_name, tg_id),
        )
        self._refresh_user_full_name(tg_id)

    def update_user_phone(self, tg_id: int, phone: str) -> None:
        self._execute(
            "UPDATE users SET phone = ? WHERE tg_id = ?",
            (phone, tg_id),
        )

    def update_user_birth_date(self, tg_id: int, birth_date: str) -> None:
        self._execute(
            "UPDATE users SET birth_date = ? WHERE tg_id = ?",
            (birth_date, tg_id),
        )

    def get_user_language(self, tg_id: int) -> str:
        row = self._fetchone("SELECT language FROM users WHERE tg_id = ?", (tg_id,))
        if not row or not row["language"]:
            return ""
        return str(row["language"])

    def set_user_language(self, tg_id: int, language: str) -> None:
        self._execute("UPDATE users SET language = ? WHERE tg_id = ?", (language, tg_id))

    def is_user_registered(self, tg_id: int) -> bool:
        row = self._fetchone(
            """
            SELECT first_name, last_name, phone, birth_date
            FROM users
            WHERE tg_id = ?
            """,
            (tg_id,),
        )
        if not row:
            return False
        return bool(row["first_name"] and row["last_name"] and row["phone"] and row["birth_date"])

    def save_user_registration(
        self,
        tg_id: int,
        first_name: str,
        last_name: str,
        phone: str,
        birth_date: str,
    ) -> None:
        self._execute(
            """
            UPDATE users
            SET first_name = ?, last_name = ?, phone = ?, birth_date = ?,
                full_name = ?, registered_at = ?
            WHERE tg_id = ?
            """,
            (first_name, last_name, phone, birth_date, f"{first_name} {last_name}".strip(), utc_now(), tg_id),
        )

    def list_today_birthdays(self, month_day: str) -> List[sqlite3.Row]:
        return self._fetchall(
            """
            SELECT tg_id, username, first_name, last_name, phone, birth_date
            FROM users
            WHERE birth_date IS NOT NULL
              AND substr(birth_date, 6, 5) = ?
            ORDER BY first_name, last_name
            """,
            (month_day,),
        )

    def is_birthday_notified(self, user_tg_id: int, year: int) -> bool:
        row = self._fetchone(
            """
            SELECT 1
            FROM birthday_notifications
            WHERE user_tg_id = ? AND year = ?
            """,
            (user_tg_id, year),
        )
        return bool(row)

    def mark_birthday_notified(self, user_tg_id: int, year: int) -> None:
        self._execute(
            """
            INSERT OR IGNORE INTO birthday_notifications(user_tg_id, year, notified_at)
            VALUES (?, ?, ?)
            """,
            (user_tg_id, year, utc_now()),
        )
