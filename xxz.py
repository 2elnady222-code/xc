"""
Telegram Multi-Account Manager Bot  —  v9.1.0
==============================================
Runtime : Python 3.10+
Engine  : Pyrogram 2.0+
License : Private / Personal use only

New in v9.1.0:
  - Security & Protection System
    · Auto backup sessions (encrypted)
    · Session expiry alerts
    · Login tracking & notifications
    · Early ban detection
  - Advanced Analytics Dashboard
    · Account health scores (0-100)
    · Detailed statistics per account
    · Change history tracking
    · Export reports
  - Smart Automation
    · Task scheduling (cron-like)
    · AI auto-reply system
    · Account rotation for tasks
    · Sleep mode scheduling
  - Chat Management
    · Bulk archive chats
    · Delete old messages
    · Mute all notifications
    · Export important chats
  - Advanced Profile Customization
    · Profile templates (name + photo + bio)
    · Auto-rotate profile photos
    · Remove old profile photos
    · Premium emoji support
  - Anti-Ban Protection
    · Smart delays between operations
    · Human behavior simulation
    · Load distribution across accounts
    · Emergency mode (auto-stop)
"""

# ==============================================================================
# Imports
# ==============================================================================

from __future__ import annotations

import asyncio
import base64
import hashlib
import io
import json
import logging
import os
import random
import re
import signal
import sqlite3
import string
import time
from datetime import datetime, timedelta
from typing import Any, Callable
from cryptography.fernet import Fernet
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import httpx
import pyrogram.raw.functions.auth as raw_auth
import pyrogram.raw.functions.account as raw_account
import pyrogram.raw.types as raw_types
from pyrogram import Client, filters, idle
from pyrogram.enums import ChatType, MessagesFilter
from pyrogram.errors import (
    FloodWait,
    PeerIdInvalid,
    PeerInvalid,
    PhoneCodeExpired,
    PhoneCodeInvalid,
    RPCError,
    SessionPasswordNeeded,
    UserBannedInChannel,
    UsernameOccupied,
    UsernameInvalid,
    UsernameNotModified,
    UserDeactivated,
    UserDeactivatedBan,
    AuthKeyUnregistered,
    SessionRevoked,
)
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

# ==============================================================================
# Logging
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("TGManager")

# ==============================================================================
# Configuration  —  عدّل هذا القسم فقط
# ==============================================================================

BOT_TOKEN: str = "8823933721:AAH214jXlqpfzT5K-dDXuzIoP2t4QYxpZ_0"
ADMIN_ID: int = 8656554442

API_ID: int = 34064876
API_HASH: str = "173ebd38d731f1be5f6a0ba6b44093ab"

DB_PATH: str = "bot_data.db"
BACKUP_PATH: str = "backups"
ENCRYPTION_KEY: str = ""  # Will be auto-generated if empty

PROXY_TIMEOUT_SECONDS: int = 15
AUTO_TERMINATE_ENABLED: bool = True
AUTO_TERMINATE_INTERVAL: int = 3600
CAPTCHA_REQUIRED: bool = True
CAPTCHA_TTL_SECONDS: int = 300
ACCOUNTS_PER_PAGE: int = 10

# Gemini API Configuration
GEMINI_API_KEY: str = "AIzaSyAQXwKZTBb3nIuqTiibF9S-44ia_Mi6-SE"
GEMINI_API_URL: str = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# GitHub Repository for Profile Photos (photos directly in repo root)
GITHUB_PHOTOS_REPO: str = "2elnady222-code/photos"
GITHUB_PHOTOS_PATH: str = ""  # Empty = root of repo
GITHUB_TOKEN: str = "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"

# Anti-Ban Settings
MIN_DELAY_SECONDS: float = 1.0
MAX_DELAY_SECONDS: float = 5.0
HUMAN_TYPING_SPEED: float = 0.05  # seconds per character
MAX_ACTIONS_PER_HOUR: int = 30
EMERGENCY_COOLDOWN_MINUTES: int = 60

# Automation Settings
AUTO_BACKUP_INTERVAL_HOURS: int = 24
HEALTH_CHECK_INTERVAL_MINUTES: int = 30
SESSION_EXPIRY_WARNING_DAYS: int = 7

DEVICE_PROFILES: list[dict[str, str]] = [
    {"device_model": "Samsung Galaxy S23",   "system_version": "Android 13", "app_version": "9.6.7"},
    {"device_model": "Samsung Galaxy A54",   "system_version": "Android 13", "app_version": "9.6.7"},
    {"device_model": "Samsung Galaxy A34",   "system_version": "Android 13", "app_version": "9.6.5"},
    {"device_model": "Xiaomi Redmi Note 12", "system_version": "Android 12", "app_version": "9.5.9"},
    {"device_model": "OPPO A78",             "system_version": "Android 13", "app_version": "9.6.3"},
    {"device_model": "Tecno Camon 20",       "system_version": "Android 13", "app_version": "9.6.2"},
]

# ==============================================================================
# Random Names Pool - Separated by Gender
# ==============================================================================

# Male Arabic Names
ARABIC_MALE_NAMES: list[str] = [
    "أحمد", "محمد", "علي", "حسن", "حسين", "عمر", "خالد", "يوسف", "إبراهيم", "عبدالله",
    "سعد", "فهد", "سلطان", "ناصر", "بندر", "سعود", "تركي", "فيصل", "عبدالرحمن", "مشاري",
    "كريم", "طارق", "وليد", "سامي", "ماجد", "راشد", "حمد", "زياد", "عادل", "بدر",
    "عبدالعزيز", "سالم", "ماهر", "نواف", "مساعد", "عبدالملك", "أنس", "ياسر", "هاني", "رامي",
]

# Female Arabic Names
ARABIC_FEMALE_NAMES: list[str] = [
    "سارة", "فاطمة", "نورة", "هند", "ريم", "منى", "لمى", "دانة", "لينا", "رنا",
    "عائشة", "مريم", "زينب", "هالة", "سلمى", "ليلى", "نادية", "هدى", "أمل", "سمر",
    "نورا", "ديما", "غادة", "مها", "هيفاء", "أسماء", "ندى", "رغد", "جنى", "شهد",
    "لجين", "رهف", "وعد", "تالا", "يارا", "ملك", "جود", "سدن", "لين", "روان",
]

ARABIC_LAST_NAMES: list[str] = [
    "العلي", "المحمد", "السعيد", "الحسن", "الأحمد", "الخالد", "العمر", "الناصر", "السلطان", "الفهد",
    "القحطاني", "العتيبي", "الشمري", "المطيري", "الدوسري", "الحربي", "الزهراني", "الغامدي", "البلوي", "العنزي",
    "الشهري", "الرشيدي", "السبيعي", "الجهني", "الحازمي", "اليامي", "الصاعدي", "المالكي", "الثبيتي", "البقمي",
]

# Male English Names
ENGLISH_MALE_NAMES: list[str] = [
    "James", "John", "Robert", "Michael", "David", "William", "Richard", "Joseph", "Thomas", "Charles",
    "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven", "Paul", "Andrew", "Joshua", "Kenneth",
    "Christopher", "Brian", "Kevin", "Jason", "Ryan", "Jacob", "Ethan", "Noah", "Liam", "Mason",
    "Alexander", "Benjamin", "Lucas", "Henry", "Sebastian", "Jack", "Oliver", "Leo", "Max", "Owen",
]

# Female English Names
ENGLISH_FEMALE_NAMES: list[str] = [
    "Emma", "Olivia", "Ava", "Isabella", "Sophia", "Mia", "Charlotte", "Amelia", "Harper", "Evelyn",
    "Emily", "Elizabeth", "Sofia", "Avery", "Ella", "Scarlett", "Grace", "Chloe", "Victoria", "Riley",
    "Abigail", "Madison", "Lily", "Zoey", "Hannah", "Natalie", "Addison", "Leah", "Savannah", "Audrey",
    "Brooklyn", "Claire", "Skylar", "Lucy", "Paisley", "Anna", "Caroline", "Genesis", "Aaliyah", "Kennedy",
]

ENGLISH_LAST_NAMES: list[str] = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Anderson", "Taylor", "Thomas", "Hernandez", "Moore", "Martin", "Jackson", "Thompson", "White", "Lopez",
    "Lee", "Harris", "Clark", "Lewis", "Robinson", "Walker", "Perez", "Hall", "Young", "Allen",
    "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green", "Adams", "Nelson",
]

# Combined lists for backwards compatibility
ARABIC_FIRST_NAMES: list[str] = ARABIC_MALE_NAMES + ARABIC_FEMALE_NAMES
ENGLISH_FIRST_NAMES: list[str] = ENGLISH_MALE_NAMES + ENGLISH_FEMALE_NAMES

# Auto-reply templates
AUTO_REPLY_TEMPLATES: dict[str, list[str]] = {
    "greeting": [
        "أهلاً وسهلاً! 👋",
        "مرحباً بك! كيف يمكنني مساعدتك؟",
        "أهلاً! سعيد بتواصلك 😊",
    ],
    "busy": [
        "أنا مشغول حالياً، سأرد عليك لاحقاً 🙏",
        "شكراً لرسالتك، سأتواصل معك قريباً",
        "أنا غير متاح الآن، سأرد في أقرب وقت",
    ],
    "thanks": [
        "شكراً لك! 🙏",
        "العفو، لا شكر على واجب",
        "تسلم! 😊",
    ],
}

# ==============================================================================
# Type aliases
# ==============================================================================

Row = sqlite3.Row
KV = dict[str, Any]

# ==============================================================================
# Global runtime state
# ==============================================================================

bot: Client | None = None
scheduler: AsyncIOScheduler | None = None
cloner_task: asyncio.Task | None = None
auto_terminate_task: asyncio.Task | None = None
health_monitor_task: asyncio.Task | None = None

_session_locks: dict[int, asyncio.Lock] = {}
_validation_locks: dict[str, asyncio.Lock] = {}
_active_temp_clients: dict[str, Client | None] = {}

background_clients: dict[str, Client] = {}
user_sessions: dict[int, KV] = {}
captcha_cache: dict[int, tuple[str, datetime]] = {}

# Track used resources
_used_photos: set[str] = set()
_used_usernames: set[str] = set()
_used_names: set[str] = set()

# Anti-ban tracking
_action_counts: dict[str, list[datetime]] = {}  # phone -> list of action timestamps
_emergency_mode: bool = False
_emergency_until: datetime | None = None

# Encryption
_fernet: Fernet | None = None


# ==============================================================================
# Encryption Utilities
# ==============================================================================

def _get_fernet() -> Fernet:
    global _fernet, ENCRYPTION_KEY
    if _fernet is None:
        if not ENCRYPTION_KEY:
            ENCRYPTION_KEY = Fernet.generate_key().decode()
            log.warning("Generated new encryption key. Save this: %s", ENCRYPTION_KEY)
        _fernet = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)
    return _fernet


def encrypt_data(data: str) -> str:
    return _get_fernet().encrypt(data.encode()).decode()


def decrypt_data(encrypted: str) -> str:
    return _get_fernet().decrypt(encrypted.encode()).decode()


# ==============================================================================
# Database
# ==============================================================================

def db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def db_init() -> None:
    with db_connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id                INTEGER PRIMARY KEY,
                username               TEXT,
                first_name             TEXT,
                is_banned              INTEGER DEFAULT 0,
                rank                   TEXT    DEFAULT 'free',
                points                 INTEGER DEFAULT 0,
                referred_by            INTEGER DEFAULT NULL,
                allowed_accounts_count INTEGER DEFAULT 5,
                joined_at              TEXT    DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS accounts (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                phone             TEXT    UNIQUE NOT NULL,
                session_string    TEXT    NOT NULL,
                device_profile    TEXT,
                proxy             TEXT,
                api_id            INTEGER,
                api_hash          TEXT,
                status            TEXT    DEFAULT 'active',
                added_by          INTEGER,
                pending_terminate INTEGER DEFAULT 0,
                health_score      INTEGER DEFAULT 100,
                last_health_check TEXT,
                last_active       TEXT    DEFAULT (datetime('now')),
                ban_risk_level    TEXT    DEFAULT 'low',
                total_actions     INTEGER DEFAULT 0,
                added_at          TEXT    DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE TABLE IF NOT EXISTS delegated_admins (
                user_id INTEGER PRIMARY KEY
            );

            CREATE TABLE IF NOT EXISTS cloner_config (
                id          INTEGER PRIMARY KEY DEFAULT 1,
                source      TEXT,
                destination TEXT,
                strip_links INTEGER DEFAULT 0,
                active      INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS cloner_checkpoint (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                source          TEXT NOT NULL,
                destination     TEXT NOT NULL,
                last_message_id INTEGER DEFAULT 0,
                last_update     TEXT    DEFAULT (datetime('now')),
                UNIQUE(source, destination)
            );

            CREATE TABLE IF NOT EXISTS admin_audit_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id    INTEGER NOT NULL,
                action      TEXT    NOT NULL,
                target_data TEXT,
                timestamp   TEXT    DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS generated_usernames (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                username  TEXT UNIQUE NOT NULL,
                is_used   INTEGER DEFAULT 0,
                generated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS used_photos (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                photo_url  TEXT UNIQUE NOT NULL,
                phone      TEXT,
                used_at    TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS profile_templates (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                first_name  TEXT,
                last_name   TEXT,
                bio         TEXT,
                photo_url   TEXT,
                created_by  INTEGER,
                created_at  TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type   TEXT NOT NULL,
                target      TEXT,
                params      TEXT,
                cron_expr   TEXT,
                is_active   INTEGER DEFAULT 1,
                last_run    TEXT,
                next_run    TEXT,
                created_by  INTEGER,
                created_at  TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS auto_reply_rules (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                phone       TEXT,
                trigger     TEXT NOT NULL,
                response    TEXT NOT NULL,
                is_regex    INTEGER DEFAULT 0,
                is_active   INTEGER DEFAULT 1,
                use_ai      INTEGER DEFAULT 0,
                created_at  TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS account_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                phone       TEXT NOT NULL,
                action      TEXT NOT NULL,
                old_value   TEXT,
                new_value   TEXT,
                changed_by  INTEGER,
                changed_at  TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS login_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                phone       TEXT NOT NULL,
                ip_address  TEXT,
                device_info TEXT,
                location    TEXT,
                login_at    TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS backups (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                filename    TEXT NOT NULL,
                encrypted   INTEGER DEFAULT 1,
                size_bytes  INTEGER,
                created_at  TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS account_stats (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                phone           TEXT NOT NULL,
                stat_date       TEXT NOT NULL,
                messages_sent   INTEGER DEFAULT 0,
                messages_recv   INTEGER DEFAULT 0,
                groups_joined   INTEGER DEFAULT 0,
                groups_left     INTEGER DEFAULT 0,
                channels_joined INTEGER DEFAULT 0,
                channels_left   INTEGER DEFAULT 0,
                UNIQUE(phone, stat_date)
            );

            CREATE TABLE IF NOT EXISTS sleep_schedules (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                phone       TEXT,
                start_hour  INTEGER NOT NULL,
                end_hour    INTEGER NOT NULL,
                days        TEXT DEFAULT '0,1,2,3,4,5,6',
                is_active   INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS photo_rotation (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                phone       TEXT NOT NULL,
                photos      TEXT NOT NULL,
                interval_hours INTEGER DEFAULT 24,
                current_index INTEGER DEFAULT 0,
                last_rotated TEXT,
                is_active   INTEGER DEFAULT 1
            );

            INSERT OR IGNORE INTO cloner_config (id) VALUES (1);
        """)
        _seed_settings(conn)
    
    # Create backup directory
    os.makedirs(BACKUP_PATH, exist_ok=True)
    log.info("Database ready — %s", DB_PATH)


def _seed_settings(conn: sqlite3.Connection) -> None:
    defaults = [
        ("forced_sub_status", "0"),
        ("forced_sub_channel", ""),
        ("bot_status_public", "1"),
        ("points_system_status", "1"),
        ("points_welcome", "100"),
        ("points_referral", "50"),
        ("points_sell_account", "500"),
        ("cost_join", "10"),
        ("cost_leave", "5"),
        ("cost_comment", "15"),
        ("cost_react", "8"),
        ("cost_poll", "10"),
        ("cost_contest", "12"),
        ("auto_responder_enabled", "0"),
        ("auto_terminate_feature", str(int(AUTO_TERMINATE_ENABLED))),
        ("anti_ban_enabled", "1"),
        ("emergency_mode_auto", "1"),
        ("auto_backup_enabled", "1"),
        ("health_monitoring_enabled", "1"),
        ("human_simulation_enabled", "1"),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", defaults
    )


# --  Settings helpers  --------------------------------------------------------

def setting(key: str, default: str = "0") -> str:
    with db_connect() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    with db_connect() as conn:
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))


def is_forced_sub_enabled() -> bool:     return setting("forced_sub_status") == "1"
def forced_sub_channel() -> str:         return setting("forced_sub_channel", "")
def is_bot_public() -> bool:             return setting("bot_status_public") == "1"
def is_points_enabled() -> bool:         return setting("points_system_status") == "1"
def is_auto_terminate_enabled() -> bool: return setting("auto_terminate_feature") == "1"
def is_anti_ban_enabled() -> bool:       return setting("anti_ban_enabled") == "1"
def is_human_sim_enabled() -> bool:      return setting("human_simulation_enabled") == "1"
def is_health_monitoring() -> bool:      return setting("health_monitoring_enabled") == "1"
def is_auto_backup_enabled() -> bool:    return setting("auto_backup_enabled") == "1"

def pts_welcome() -> int:  return int(setting("points_welcome", "100"))
def pts_sell() -> int:     return int(setting("points_sell_account", "500"))
def cost(key: str) -> int: return int(setting(key, "0"))


# --  User queries  ------------------------------------------------------------

def db_upsert_user(uid: int, username: str | None, first_name: str | None) -> bool:
    with db_connect() as conn:
        if conn.execute("SELECT 1 FROM users WHERE user_id=?", (uid,)).fetchone():
            return False
        conn.execute(
            "INSERT INTO users (user_id, username, first_name, points, allowed_accounts_count) "
            "VALUES (?, ?, ?, ?, ?)",
            (uid, username, first_name, pts_welcome(), 5),
        )
    return True


def db_get_user(uid: int) -> Row | None:
    with db_connect() as conn:
        return conn.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()


def db_get_points(uid: int) -> int:
    row = db_get_user(uid)
    return row["points"] if row else 0


def db_is_banned(uid: int) -> bool:
    row = db_get_user(uid)
    return bool(row and row["is_banned"])


def db_set_ban(uid: int, ban: bool) -> None:
    with db_connect() as conn:
        conn.execute("UPDATE users SET is_banned=? WHERE user_id=?", (int(ban), uid))


def db_all_users() -> list[Row]:
    with db_connect() as conn:
        return conn.execute("SELECT * FROM users WHERE is_banned=0").fetchall()


def db_is_vip(uid: int) -> bool:
    row = db_get_user(uid)
    return bool(row and row["rank"] == "vip")


def db_set_vip(uid: int, quota: int = 5) -> None:
    with db_connect() as conn:
        conn.execute(
            "UPDATE users SET rank='vip', allowed_accounts_count=? WHERE user_id=?",
            (quota, uid),
        )


def db_add_points(uid: int, amount: int) -> None:
    with db_connect() as conn:
        conn.execute("UPDATE users SET points=points+? WHERE user_id=?", (amount, uid))


def db_adjust_points(uid: int, delta: int) -> None:
    with db_connect() as conn:
        conn.execute(
            "UPDATE users SET points=MAX(0, points+?) WHERE user_id=?", (delta, uid)
        )


# --  Admin queries  -----------------------------------------------------------

def db_get_delegated_admins() -> list[int]:
    with db_connect() as conn:
        return [
            r["user_id"]
            for r in conn.execute("SELECT user_id FROM delegated_admins").fetchall()
        ]


def is_any_admin(uid: int) -> bool:
    if uid == ADMIN_ID:
        return True
    with db_connect() as conn:
        return (
            conn.execute(
                "SELECT 1 FROM delegated_admins WHERE user_id=?", (uid,)
            ).fetchone() is not None
        )


def is_primary_admin(uid: int) -> bool:
    return uid == ADMIN_ID


def db_add_audit_log(admin_id: int, action: str, target: str) -> None:
    with db_connect() as conn:
        conn.execute(
            "INSERT INTO admin_audit_log (admin_id, action, target_data) VALUES (?, ?, ?)",
            (admin_id, action, target),
        )


def db_get_activity_report(admin_id: int) -> dict[str, Any]:
    with db_connect() as conn:
        accts = conn.execute(
            "SELECT COUNT(*) AS cnt FROM accounts WHERE added_by=?", (admin_id,)
        ).fetchone()
        actions = conn.execute(
            "SELECT action, COUNT(*) AS cnt FROM admin_audit_log "
            "WHERE admin_id=? GROUP BY action",
            (admin_id,),
        ).fetchall()
    return {
        "accounts_added": accts["cnt"] if accts else 0,
        "actions": {r["action"]: r["cnt"] for r in actions} if actions else {},
    }


# --  Account queries  ---------------------------------------------------------

def db_save_account(
    phone: str,
    session_string: str,
    added_by: int,
    device_profile: dict | None = None,
    proxy: str | None = None,
    api_id: int | None = None,
    api_hash: str | None = None,
) -> None:
    dev = json.dumps(device_profile) if device_profile else None
    with db_connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO accounts "
            "(phone, session_string, device_profile, proxy, api_id, api_hash, "
            " added_by, status, pending_terminate, health_score) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 'active', 0, 100)",
            (phone, session_string, dev, proxy, api_id, api_hash, added_by),
        )


def db_get_all_accounts(active_only: bool = False) -> list[Row]:
    with db_connect() as conn:
        sql = (
            "SELECT * FROM accounts WHERE status='active'"
            if active_only
            else "SELECT * FROM accounts"
        )
        return conn.execute(sql).fetchall()


def db_get_account(phone: str) -> Row | None:
    with db_connect() as conn:
        return conn.execute(
            "SELECT * FROM accounts WHERE phone=?", (phone,)
        ).fetchone()


def db_delete_account(phone: str) -> None:
    with db_connect() as conn:
        conn.execute("DELETE FROM accounts WHERE phone=?", (phone,))


def db_get_pending_terminate() -> list[Row]:
    with db_connect() as conn:
        return conn.execute(
            "SELECT * FROM accounts WHERE pending_terminate=1"
        ).fetchall()


def db_set_pending_terminate(phone: str, pending: bool) -> None:
    with db_connect() as conn:
        conn.execute(
            "UPDATE accounts SET pending_terminate=? WHERE phone=?",
            (int(pending), phone),
        )


def db_update_account_health(phone: str, score: int, risk_level: str = "low") -> None:
    with db_connect() as conn:
        conn.execute(
            "UPDATE accounts SET health_score=?, ban_risk_level=?, last_health_check=datetime('now') WHERE phone=?",
            (score, risk_level, phone),
        )


def db_update_account_activity(phone: str) -> None:
    with db_connect() as conn:
        conn.execute(
            "UPDATE accounts SET last_active=datetime('now'), total_actions=total_actions+1 WHERE phone=?",
            (phone,),
        )


def db_set_account_status(phone: str, status: str) -> None:
    with db_connect() as conn:
        conn.execute("UPDATE accounts SET status=? WHERE phone=?", (status, phone))


# --  Account History  ---------------------------------------------------------

def db_add_account_history(phone: str, action: str, old_val: str | None, new_val: str | None, changed_by: int) -> None:
    with db_connect() as conn:
        conn.execute(
            "INSERT INTO account_history (phone, action, old_value, new_value, changed_by) VALUES (?, ?, ?, ?, ?)",
            (phone, action, old_val, new_val, changed_by),
        )


def db_get_account_history(phone: str, limit: int = 20) -> list[Row]:
    with db_connect() as conn:
        return conn.execute(
            "SELECT * FROM account_history WHERE phone=? ORDER BY changed_at DESC LIMIT ?",
            (phone, limit),
        ).fetchall()


# --  Profile Templates  -------------------------------------------------------

def db_save_template(name: str, first_name: str, last_name: str, bio: str, photo_url: str, created_by: int) -> int:
    with db_connect() as conn:
        cursor = conn.execute(
            "INSERT INTO profile_templates (name, first_name, last_name, bio, photo_url, created_by) VALUES (?, ?, ?, ?, ?, ?)",
            (name, first_name, last_name, bio, photo_url, created_by),
        )
        return cursor.lastrowid


def db_get_templates() -> list[Row]:
    with db_connect() as conn:
        return conn.execute("SELECT * FROM profile_templates ORDER BY created_at DESC").fetchall()


def db_get_template(template_id: int) -> Row | None:
    with db_connect() as conn:
        return conn.execute("SELECT * FROM profile_templates WHERE id=?", (template_id,)).fetchone()


def db_delete_template(template_id: int) -> None:
    with db_connect() as conn:
        conn.execute("DELETE FROM profile_templates WHERE id=?", (template_id,))


# --  Scheduled Tasks  ---------------------------------------------------------

def db_add_scheduled_task(task_type: str, target: str, params: dict, cron_expr: str, created_by: int) -> int:
    with db_connect() as conn:
        cursor = conn.execute(
            "INSERT INTO scheduled_tasks (task_type, target, params, cron_expr, created_by) VALUES (?, ?, ?, ?, ?)",
            (task_type, target, json.dumps(params), cron_expr, created_by),
        )
        return cursor.lastrowid


def db_get_scheduled_tasks(active_only: bool = True) -> list[Row]:
    with db_connect() as conn:
        if active_only:
            return conn.execute("SELECT * FROM scheduled_tasks WHERE is_active=1").fetchall()
        return conn.execute("SELECT * FROM scheduled_tasks").fetchall()


def db_update_task_run(task_id: int) -> None:
    with db_connect() as conn:
        conn.execute(
            "UPDATE scheduled_tasks SET last_run=datetime('now') WHERE id=?",
            (task_id,),
        )


def db_toggle_task(task_id: int, active: bool) -> None:
    with db_connect() as conn:
        conn.execute("UPDATE scheduled_tasks SET is_active=? WHERE id=?", (int(active), task_id))


def db_delete_task(task_id: int) -> None:
    with db_connect() as conn:
        conn.execute("DELETE FROM scheduled_tasks WHERE id=?", (task_id,))


# --  Auto Reply Rules  --------------------------------------------------------

def db_add_auto_reply(phone: str | None, trigger: str, response: str, is_regex: bool, use_ai: bool) -> int:
    with db_connect() as conn:
        cursor = conn.execute(
            "INSERT INTO auto_reply_rules (phone, trigger, response, is_regex, use_ai) VALUES (?, ?, ?, ?, ?)",
            (phone, trigger, response, int(is_regex), int(use_ai)),
        )
        return cursor.lastrowid


def db_get_auto_replies(phone: str | None = None) -> list[Row]:
    with db_connect() as conn:
        if phone:
            return conn.execute(
                "SELECT * FROM auto_reply_rules WHERE (phone=? OR phone IS NULL) AND is_active=1",
                (phone,),
            ).fetchall()
        return conn.execute("SELECT * FROM auto_reply_rules WHERE is_active=1").fetchall()


def db_delete_auto_reply(rule_id: int) -> None:
    with db_connect() as conn:
        conn.execute("DELETE FROM auto_reply_rules WHERE id=?", (rule_id,))


# --  Sleep Schedules  ---------------------------------------------------------

def db_add_sleep_schedule(phone: str | None, start_hour: int, end_hour: int, days: str = "0,1,2,3,4,5,6") -> int:
    with db_connect() as conn:
        cursor = conn.execute(
            "INSERT INTO sleep_schedules (phone, start_hour, end_hour, days) VALUES (?, ?, ?, ?)",
            (phone, start_hour, end_hour, days),
        )
        return cursor.lastrowid


def db_get_sleep_schedules(phone: str | None = None) -> list[Row]:
    with db_connect() as conn:
        if phone:
            return conn.execute(
                "SELECT * FROM sleep_schedules WHERE (phone=? OR phone IS NULL) AND is_active=1",
                (phone,),
            ).fetchall()
        return conn.execute("SELECT * FROM sleep_schedules WHERE is_active=1").fetchall()


def is_in_sleep_mode(phone: str) -> bool:
    schedules = db_get_sleep_schedules(phone)
    now = datetime.now()
    current_hour = now.hour
    current_day = str(now.weekday())
    
    for schedule in schedules:
        days = schedule["days"].split(",")
        if current_day in days:
            start = schedule["start_hour"]
            end = schedule["end_hour"]
            if start <= end:
                if start <= current_hour < end:
                    return True
            else:  # Overnight schedule (e.g., 22:00 - 06:00)
                if current_hour >= start or current_hour < end:
                    return True
    return False


# --  Photo Rotation  ----------------------------------------------------------

def db_add_photo_rotation(phone: str, photos: list[str], interval_hours: int) -> int:
    with db_connect() as conn:
        cursor = conn.execute(
            "INSERT INTO photo_rotation (phone, photos, interval_hours) VALUES (?, ?, ?)",
            (phone, json.dumps(photos), interval_hours),
        )
        return cursor.lastrowid


def db_get_photo_rotations(active_only: bool = True) -> list[Row]:
    with db_connect() as conn:
        if active_only:
            return conn.execute("SELECT * FROM photo_rotation WHERE is_active=1").fetchall()
        return conn.execute("SELECT * FROM photo_rotation").fetchall()


def db_update_photo_rotation(rotation_id: int, current_index: int) -> None:
    with db_connect() as conn:
        conn.execute(
            "UPDATE photo_rotation SET current_index=?, last_rotated=datetime('now') WHERE id=?",
            (current_index, rotation_id),
        )


# --  Backups  -----------------------------------------------------------------

def db_add_backup(filename: str, encrypted: bool, size_bytes: int) -> int:
    with db_connect() as conn:
        cursor = conn.execute(
            "INSERT INTO backups (filename, encrypted, size_bytes) VALUES (?, ?, ?)",
            (filename, int(encrypted), size_bytes),
        )
        return cursor.lastrowid


def db_get_backups(limit: int = 10) -> list[Row]:
    with db_connect() as conn:
        return conn.execute(
            "SELECT * FROM backups ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()


# --  Stats  -------------------------------------------------------------------

def db_update_stats(phone: str, stat_type: str, increment: int = 1) -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    with db_connect() as conn:
        conn.execute(
            f"INSERT INTO account_stats (phone, stat_date, {stat_type}) VALUES (?, ?, ?) "
            f"ON CONFLICT(phone, stat_date) DO UPDATE SET {stat_type}={stat_type}+?",
            (phone, today, increment, increment),
        )


def db_get_account_stats(phone: str, days: int = 7) -> list[Row]:
    with db_connect() as conn:
        return conn.execute(
            "SELECT * FROM account_stats WHERE phone=? AND stat_date >= date('now', ?) ORDER BY stat_date DESC",
            (phone, f"-{days} days"),
        ).fetchall()


# --  Username queries  --------------------------------------------------------

def db_save_username(username: str) -> None:
    with db_connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO generated_usernames (username) VALUES (?)",
            (username,),
        )


def db_get_available_username() -> str | None:
    with db_connect() as conn:
        row = conn.execute(
            "SELECT username FROM generated_usernames WHERE is_used=0 LIMIT 1"
        ).fetchone()
        return row["username"] if row else None


def db_mark_username_used(username: str) -> None:
    with db_connect() as conn:
        conn.execute(
            "UPDATE generated_usernames SET is_used=1 WHERE username=?",
            (username,),
        )


def db_get_username_count() -> tuple[int, int]:
    with db_connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM generated_usernames").fetchone()[0]
        available = conn.execute(
            "SELECT COUNT(*) FROM generated_usernames WHERE is_used=0"
        ).fetchone()[0]
    return total, available


# --  Photo tracking  ----------------------------------------------------------

def db_is_photo_used(photo_url: str) -> bool:
    with db_connect() as conn:
        return conn.execute(
            "SELECT 1 FROM used_photos WHERE photo_url=?", (photo_url,)
        ).fetchone() is not None


def db_mark_photo_used(photo_url: str, phone: str) -> None:
    with db_connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO used_photos (photo_url, phone) VALUES (?, ?)",
            (photo_url, phone),
        )


def db_get_used_photos_count() -> int:
    with db_connect() as conn:
        return conn.execute("SELECT COUNT(*) FROM used_photos").fetchone()[0]


# --  Cloner queries  ----------------------------------------------------------

def db_get_cloner_checkpoint(source: str, dest: str) -> int:
    with db_connect() as conn:
        row = conn.execute(
            "SELECT last_message_id FROM cloner_checkpoint WHERE source=? AND destination=?",
            (source, dest),
        ).fetchone()
    return row["last_message_id"] if row else 0


def db_set_cloner_checkpoint(source: str, dest: str, last_id: int) -> None:
    with db_connect() as conn:
        conn.execute(
            "INSERT INTO cloner_checkpoint (source, destination, last_message_id, last_update) "
            "VALUES (?, ?, ?, datetime('now')) "
            "ON CONFLICT(source, destination) DO UPDATE SET "
            "last_message_id=excluded.last_message_id, last_update=datetime('now')",
            (source, dest, last_id),
        )


# ==============================================================================
# Anti-Ban System
# ==============================================================================

def check_rate_limit(phone: str) -> bool:
    """Check if account has exceeded rate limits. Returns True if OK to proceed."""
    global _emergency_mode, _emergency_until
    
    # Check emergency mode
    if _emergency_mode:
        if _emergency_until and datetime.now() < _emergency_until:
            return False
        _emergency_mode = False
        _emergency_until = None
    
    if not is_anti_ban_enabled():
        return True
    
    now = datetime.now()
    hour_ago = now - timedelta(hours=1)
    
    if phone not in _action_counts:
        _action_counts[phone] = []
    
    # Clean old entries
    _action_counts[phone] = [t for t in _action_counts[phone] if t > hour_ago]
    
    if len(_action_counts[phone]) >= MAX_ACTIONS_PER_HOUR:
        return False
    
    return True


def record_action(phone: str) -> None:
    """Record an action for rate limiting."""
    if phone not in _action_counts:
        _action_counts[phone] = []
    _action_counts[phone].append(datetime.now())
    db_update_account_activity(phone)


async def smart_delay() -> None:
    """Apply a random delay to simulate human behavior."""
    if is_anti_ban_enabled():
        delay = random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
        await asyncio.sleep(delay)


async def simulate_typing(client: Client, chat_id: int, text: str) -> None:
    """Simulate human typing behavior."""
    if is_human_sim_enabled():
        typing_time = len(text) * HUMAN_TYPING_SPEED
        typing_time = min(typing_time, 5.0)  # Max 5 seconds
        await client.send_chat_action(chat_id, "typing")
        await asyncio.sleep(typing_time)


def trigger_emergency_mode(reason: str) -> None:
    """Activate emergency mode - stop all operations."""
    global _emergency_mode, _emergency_until
    _emergency_mode = True
    _emergency_until = datetime.now() + timedelta(minutes=EMERGENCY_COOLDOWN_MINUTES)
    log.warning("🚨 Emergency mode activated: %s. Cooldown until %s", reason, _emergency_until)


def get_emergency_status() -> tuple[bool, datetime | None]:
    return _emergency_mode, _emergency_until


# ==============================================================================
# Health Monitoring System
# ==============================================================================

async def check_account_health(account: Row) -> tuple[int, str]:
    """
    Check account health and return (score, risk_level).
    Score: 0-100, Risk: low/medium/high/critical
    """
    score = 100
    issues = []
    
    tmp = None
    try:
        tmp = await _account_client(account, "health_check")
        
        # Check if can get self
        me = await tmp.get_me()
        if not me:
            return 0, "critical"
        
        # Check restrictions
        if getattr(me, "restricted", False):
            score -= 30
            issues.append("restricted")
        
        if getattr(me, "scam", False):
            score -= 50
            issues.append("scam_flag")
        
        if getattr(me, "fake", False):
            score -= 40
            issues.append("fake_flag")
        
        # Check recent activity
        last_active = account.get("last_active")
        if last_active:
            try:
                last_dt = datetime.fromisoformat(last_active)
                days_inactive = (datetime.now() - last_dt).days
                if days_inactive > 30:
                    score -= 10
                    issues.append("inactive")
            except:
                pass
        
        # Check action count (too many = risky)
        total_actions = account.get("total_actions", 0)
        if total_actions > 1000:
            score -= 5
        
    except (UserDeactivated, UserDeactivatedBan):
        return 0, "critical"
    except (AuthKeyUnregistered, SessionRevoked):
        return 0, "critical"
    except FloodWait as e:
        score -= 20
        issues.append(f"flood_wait_{e.value}")
    except Exception as e:
        score -= 10
        issues.append(str(e)[:20])
    finally:
        await disconnect(tmp)
    
    # Determine risk level
    if score <= 20:
        risk = "critical"
    elif score <= 50:
        risk = "high"
    elif score <= 70:
        risk = "medium"
    else:
        risk = "low"
    
    return max(0, score), risk


async def run_health_check_all() -> dict[str, Any]:
    """Run health check on all active accounts."""
    accounts = db_get_all_accounts(active_only=True)
    results = {"healthy": 0, "warning": 0, "critical": 0, "details": []}
    
    for account in accounts:
        phone = account["phone"]
        try:
            score, risk = await check_account_health(account)
            db_update_account_health(phone, score, risk)
            
            if score >= 70:
                results["healthy"] += 1
            elif score >= 40:
                results["warning"] += 1
            else:
                results["critical"] += 1
            
            results["details"].append({
                "phone": phone,
                "score": score,
                "risk": risk,
            })
            
        except Exception as e:
            log.error("Health check failed for %s: %s", phone, e)
            results["critical"] += 1
        
        await asyncio.sleep(1)  # Rate limiting
    
    return results


# ==============================================================================
# Backup System
# ==============================================================================

async def create_backup(encrypted: bool = True) -> str:
    """Create a backup of all sessions."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.json"
    filepath = os.path.join(BACKUP_PATH, filename)
    
    accounts = db_get_all_accounts()
    backup_data = {
        "version": "9.1.0",
        "created_at": datetime.now().isoformat(),
        "accounts": []
    }
    
    for acc in accounts:
        acc_data = {
            "phone": acc["phone"],
            "session_string": acc["session_string"],
            "device_profile": acc["device_profile"],
            "proxy": acc["proxy"],
            "api_id": acc["api_id"],
            "api_hash": acc["api_hash"],
            "status": acc["status"],
        }
        backup_data["accounts"].append(acc_data)
    
    json_str = json.dumps(backup_data, ensure_ascii=False, indent=2)
    
    if encrypted:
        json_str = encrypt_data(json_str)
        filename = filename.replace(".json", ".enc")
        filepath = filepath.replace(".json", ".enc")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(json_str)
    
    size = os.path.getsize(filepath)
    db_add_backup(filename, encrypted, size)
    
    log.info("Backup created: %s (%d bytes)", filename, size)
    return filename


async def restore_backup(filename: str, encrypted: bool = True) -> int:
    """Restore accounts from backup. Returns number of restored accounts."""
    filepath = os.path.join(BACKUP_PATH, filename)
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    if encrypted:
        content = decrypt_data(content)
    
    data = json.loads(content)
    restored = 0
    
    for acc in data.get("accounts", []):
        try:
            db_save_account(
                phone=acc["phone"],
                session_string=acc["session_string"],
                added_by=ADMIN_ID,
                device_profile=json.loads(acc["device_profile"]) if acc.get("device_profile") else None,
                proxy=acc.get("proxy"),
                api_id=acc.get("api_id"),
                api_hash=acc.get("api_hash"),
            )
            restored += 1
        except Exception as e:
            log.error("Failed to restore account %s: %s", acc.get("phone"), e)
    
    log.info("Restored %d accounts from backup", restored)
    return restored


# ==============================================================================
# AI Auto-Reply System
# ==============================================================================

async def generate_ai_reply(message_text: str, context: str = "") -> str:
    """Generate an AI reply using Gemini."""
    if not GEMINI_API_KEY or "ضع" in GEMINI_API_KEY:
        return random.choice(AUTO_REPLY_TEMPLATES.get("greeting", ["مرحباً!"]))
    
    prompt = f"""أنت مساعد ذكي ترد على رسائل تليجرام بشكل طبيعي وودود.
الرسالة المستلمة: "{message_text}"
{f'السياق: {context}' if context else ''}

اكتب رداً قصيراً ومناسباً (أقل من 100 حرف). لا تستخدم علامات اقتباس."""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.8,
                        "maxOutputTokens": 150,
                    },
                },
                headers={"Content-Type": "application/json"},
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        log.error("AI reply error: %s", e)
    
    return random.choice(AUTO_REPLY_TEMPLATES.get("greeting", ["مرحباً!"]))


async def process_auto_reply(client: Client, message: Message, phone: str) -> bool:
    """Process incoming message for auto-reply. Returns True if replied."""
    if not message.text:
        return False
    
    rules = db_get_auto_replies(phone)
    
    for rule in rules:
        trigger = rule["trigger"]
        matched = False
        
        if rule["is_regex"]:
            if re.search(trigger, message.text, re.IGNORECASE):
                matched = True
        else:
            if trigger.lower() in message.text.lower():
                matched = True
        
        if matched:
            if rule["use_ai"]:
                reply_text = await generate_ai_reply(message.text)
            else:
                reply_text = rule["response"]
            
            await simulate_typing(client, message.chat.id, reply_text)
            await message.reply(reply_text)
            return True
    
    return False


# ==============================================================================
# Utility helpers
# ==============================================================================

def session_lock(acc_id: int) -> asyncio.Lock:
    if acc_id not in _session_locks:
        _session_locks[acc_id] = asyncio.Lock()
    return _session_locks[acc_id]


def validation_lock(session_string: str) -> asyncio.Lock:
    if session_string not in _validation_locks:
        _validation_locks[session_string] = asyncio.Lock()
    return _validation_locks[session_string]


def parse_proxy(proxy_str: str | None) -> dict | None:
    if not proxy_str:
        return None
    parts = proxy_str.strip().split(":")
    try:
        if len(parts) == 2:
            return {"scheme": "socks5", "hostname": parts[0], "port": int(parts[1])}
        if len(parts) == 4:
            return {
                "scheme": "socks5",
                "hostname": parts[0],
                "port": int(parts[1]),
                "username": parts[2],
                "password": parts[3],
            }
    except ValueError:
        pass
    return None


def resolve_device(account: Row) -> dict[str, str]:
    if account["device_profile"]:
        try:
            return json.loads(account["device_profile"])
        except (json.JSONDecodeError, TypeError):
            pass
    return random.choice(DEVICE_PROFILES)


def any_background_client() -> Client | None:
    return next(iter(background_clients.values()), None)


def rank_label(row: Row | None) -> str:
    if not row:
        return "🆓 مجاني"
    return "👑 VIP مميز" if row["rank"] == "vip" else "🆓 مجاني"


def make_captcha() -> tuple[str, str]:
    a, b = random.randint(1, 20), random.randint(1, 20)
    return f"{a} + {b} = ?", str(a + b)


def build_client(
    name: str,
    session_string: str,
    device: dict[str, str],
    proxy_str: str | None = None,
    acct_api_id: int | None = None,
    acct_api_hash: str | None = None,
) -> Client:
    kwargs: KV = dict(
        api_id=acct_api_id or API_ID,
        api_hash=acct_api_hash or API_HASH,
        session_string=session_string,
        in_memory=True,
        device_model=device["device_model"],
        system_version=device["system_version"],
        app_version=device["app_version"],
        connect_timeout=PROXY_TIMEOUT_SECONDS,
    )
    proxy = parse_proxy(proxy_str)
    if proxy:
        kwargs["proxy"] = proxy
    return Client(name, **kwargs)


async def disconnect(client: Client | None) -> None:
    if client is None:
        return
    try:
        await client.disconnect()
    except Exception:
        pass


def _phone_from_data(data: str) -> str:
    return data.split(":", 1)[1] if ":" in data else ""


async def _account_client(account: Row, label: str) -> Client:
    device = resolve_device(account)
    tmp = build_client(
        f"{label}_{account['phone']}",
        account["session_string"],
        device,
        account["proxy"],
        account["api_id"],
        account["api_hash"],
    )
    await asyncio.wait_for(tmp.connect(), timeout=PROXY_TIMEOUT_SECONDS)
    return tmp


# ==============================================================================
# Username Generation
# ==============================================================================

def generate_unique_username(length: int = 5) -> str:
    if length < 5:
        length = 5
    if length > 6:
        length = 6
    
    vowels = "aeiou"
    consonants = "bcdfghjklmnpqrstvwxyz"
    
    username = ""
    for i in range(length):
        if i % 2 == 0:
            username += random.choice(consonants)
        else:
            username += random.choice(vowels)
    
    return username


async def check_username_availability(username: str) -> bool:
    client = any_background_client()
    if client and client.is_connected:
        try:
            await client.get_users(f"@{username}")
            return False
        except (PeerIdInvalid, PeerInvalid):
            pass
        except Exception:
            pass
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            response = await http_client.get(
                f"https://fragment.com/username/{username}",
                follow_redirects=True,
            )
            if response.status_code == 200 and "This username is available" not in response.text:
                if username.lower() in response.text.lower():
                    return False
    except Exception:
        pass
    
    return True


async def generate_available_usernames(count: int = 50) -> list[str]:
    available: list[str] = []
    attempts = 0
    max_attempts = count * 10
    
    while len(available) < count and attempts < max_attempts:
        attempts += 1
        length = random.choice([5, 6])
        username = generate_unique_username(length)
        
        if username in _used_usernames:
            continue
        
        if await check_username_availability(username):
            available.append(username)
            _used_usernames.add(username)
            db_save_username(username)
        
        await asyncio.sleep(0.5)
    
    return available


# ==============================================================================
# Random Name Generation
# ==============================================================================

def generate_random_name(language: str = "mixed", gender: str = "random") -> tuple[str, str]:
    """
    Generate a random name with optional gender specification.
    
    Args:
        language: "arabic", "english", or "mixed"
        gender: "male", "female", or "random"
    
    Returns:
        tuple of (first_name, last_name)
    """
    global _used_names
    
    for _ in range(100):
        # Determine gender if random
        actual_gender = gender if gender in ("male", "female") else random.choice(["male", "female"])
        
        if language == "arabic":
            if actual_gender == "male":
                first = random.choice(ARABIC_MALE_NAMES)
            else:
                first = random.choice(ARABIC_FEMALE_NAMES)
            last = random.choice(ARABIC_LAST_NAMES)
        elif language == "english":
            if actual_gender == "male":
                first = random.choice(ENGLISH_MALE_NAMES)
            else:
                first = random.choice(ENGLISH_FEMALE_NAMES)
            last = random.choice(ENGLISH_LAST_NAMES)
        else:  # mixed
            if random.random() < 0.5:
                if actual_gender == "male":
                    first = random.choice(ARABIC_MALE_NAMES)
                else:
                    first = random.choice(ARABIC_FEMALE_NAMES)
                last = random.choice(ARABIC_LAST_NAMES)
            else:
                if actual_gender == "male":
                    first = random.choice(ENGLISH_MALE_NAMES)
                else:
                    first = random.choice(ENGLISH_FEMALE_NAMES)
                last = random.choice(ENGLISH_LAST_NAMES)
        
        full_name = f"{first} {last}"
        if full_name not in _used_names:
            _used_names.add(full_name)
            return first, last
    
    suffix = random.randint(1, 999)
    return f"{first}{suffix}", last


async def generate_smart_name_for_photo(account: Row, client: Client | None = None) -> tuple[str, str]:
    """
    Generate a name that matches the gender of the current profile photo.
    If no photo, generates a random name.
    """
    gender = await get_smart_gender(account, client)
    if gender == "unknown":
        gender = "random"
    return generate_random_name("mixed", gender)


async def get_smart_photo_for_name(account: Row, client: Client | None = None) -> str | None:
    """
    Get a photo URL that matches the gender of the current account name.
    If no name or unknown gender, returns any unused photo.
    """
    tmp = client
    should_disconnect = False
    
    try:
        if tmp is None:
            tmp = await _account_client(account, "smart_photo")
            should_disconnect = True
        
        me = await tmp.get_me()
        current_name = f"{me.first_name or ''} {me.last_name or ''}".strip()
        
        if current_name:
            # Detect gender from name
            gender = detect_name_gender(current_name)
            if gender == "unknown":
                gender = await detect_name_gender_ai(current_name)
            
            if gender in ("male", "female"):
                # Get photo matching gender
                return await get_unused_photo_by_gender(gender)
        
        # Fallback to any photo
        return await get_unused_photo()
        
    except Exception as e:
        log.error("Smart photo selection error: %s", e)
        return await get_unused_photo()
    finally:
        if should_disconnect and tmp:
            await disconnect(tmp)


# ==============================================================================
# Gemini AI Integration
# ==============================================================================

async def generate_bio_with_ai(language: str = "arabic") -> str:
    if not GEMINI_API_KEY or "ضع" in GEMINI_API_KEY:
        fallback_ar = [
            "الحياة جميلة بالتفاؤل ✨",
            "كن أنت التغيير الذي تريد رؤيته 🌟",
            "السعادة قرار وليست صدفة 💫",
            "ابتسم فالحياة أقصر من أن نقضيها حزينين 😊",
            "النجاح يبدأ بخطوة واحدة 🚀",
        ]
        fallback_en = [
            "Life is beautiful ✨",
            "Be the change you wish to see 🌟",
            "Happiness is a choice 💫",
            "Dream big, work hard 🚀",
            "Stay positive, stay happy 😊",
        ]
        return random.choice(fallback_ar if language == "arabic" else fallback_en)
    
    prompt = (
        "اكتب عبارة قصيرة وملهمة للبايو (الوصف الشخصي) في تليجرام. "
        "يجب أن تكون العبارة بالعربية، مختصرة (أقل من 70 حرف)، "
        "وتحتوي على إيموجي واحد أو اثنين. "
        "لا تستخدم علامات الاقتباس. أعطني العبارة فقط."
    ) if language == "arabic" else (
        "Write a short inspiring bio for Telegram profile. "
        "Keep it under 70 characters, include 1-2 emojis. "
        "Just give me the bio text without quotes."
    )
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.9,
                        "maxOutputTokens": 100,
                    },
                },
                headers={"Content-Type": "application/json"},
            )
            
            if response.status_code == 200:
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return text.strip().strip('"').strip("'")[:70]
    except Exception as e:
        log.error("Gemini API error: %s", e)
    
    fallback = ["الحياة جميلة ✨", "كن إيجابياً 🌟", "ابتسم للحياة 😊"]
    return random.choice(fallback)


# ==============================================================================
# GitHub Photos Integration
# ==============================================================================

# Cache for photo gender classification
_photo_gender_cache: dict[str, str] = {}  # url -> "male" | "female" | "unknown"


async def fetch_github_photos() -> list[str]:
    """Fetch all photos from GitHub repo root."""
    if not GITHUB_PHOTOS_REPO or "ضع" in GITHUB_PHOTOS_REPO:
        return []
    
    try:
        headers = {"Accept": "application/vnd.github.v3+json"}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"
        
        # If path is empty, fetch from root
        path = GITHUB_PHOTOS_PATH.strip("/") if GITHUB_PHOTOS_PATH else ""
        api_url = f"https://api.github.com/repos/{GITHUB_PHOTOS_REPO}/contents/{path}" if path else f"https://api.github.com/repos/{GITHUB_PHOTOS_REPO}/contents"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(api_url, headers=headers)
            
            if response.status_code == 200:
                files = response.json()
                photos = []
                for file in files:
                    if file["type"] == "file" and file["name"].lower().endswith((".jpg", ".jpeg", ".png")):
                        photos.append(file["download_url"])
                return photos
    except Exception as e:
        log.error("GitHub API error: %s", e)
    
    return []


async def fetch_github_photos_by_gender(gender: str) -> list[str]:
    """Fetch photos filtered by gender classification."""
    all_photos = await fetch_github_photos()
    if not all_photos:
        return []
    
    matching_photos = []
    for photo_url in all_photos:
        # Check cache first
        if photo_url in _photo_gender_cache:
            if _photo_gender_cache[photo_url] == gender:
                matching_photos.append(photo_url)
            continue
        
        # Classify photo using AI
        photo_gender = await analyze_photo_gender(photo_url)
        _photo_gender_cache[photo_url] = photo_gender
        
        if photo_gender == gender:
            matching_photos.append(photo_url)
    
    return matching_photos


async def get_unused_photo() -> str | None:
    """Get any unused photo."""
    photos = await fetch_github_photos()
    
    for photo_url in photos:
        if not db_is_photo_used(photo_url):
            return photo_url
    
    return None


async def get_unused_photo_by_gender(gender: str) -> str | None:
    """Get an unused photo matching the specified gender."""
    photos = await fetch_github_photos_by_gender(gender)
    
    for photo_url in photos:
        if not db_is_photo_used(photo_url):
            return photo_url
    
    # Fallback to any unused photo if no matching gender found
    return await get_unused_photo()


async def download_photo(url: str) -> bytes | None:
    """Download photo from URL."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return response.content
    except Exception as e:
        log.error("Photo download error: %s", e)
    return None


# ==============================================================================
# AI Gender Detection (Photo & Name Analysis)
# ==============================================================================

async def analyze_photo_gender(photo_url: str) -> str:
    """
    Analyze a photo using Gemini Vision API to determine gender.
    Returns: "male", "female", or "unknown"
    """
    if not GEMINI_API_KEY or "ضع" in GEMINI_API_KEY:
        return "unknown"
    
    try:
        # Download photo
        photo_data = await download_photo(photo_url)
        if not photo_data:
            return "unknown"
        
        # Convert to base64
        photo_base64 = base64.b64encode(photo_data).decode("utf-8")
        
        # Determine mime type
        if photo_url.lower().endswith(".png"):
            mime_type = "image/png"
        else:
            mime_type = "image/jpeg"
        
        prompt = """Analyze this profile photo and determine the gender of the person.
Reply with ONLY one word: "male" or "female" or "unknown" (if unclear or no person visible).
Do not add any other text or explanation."""

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                json={
                    "contents": [{
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": photo_base64
                                }
                            }
                        ]
                    }],
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 10,
                    },
                },
                headers={"Content-Type": "application/json"},
            )
            
            if response.status_code == 200:
                data = response.json()
                result = data["candidates"][0]["content"]["parts"][0]["text"].strip().lower()
                if "male" in result and "female" not in result:
                    return "male"
                elif "female" in result:
                    return "female"
                return "unknown"
                
    except Exception as e:
        log.error("Photo gender analysis error: %s", e)
    
    return "unknown"


async def analyze_photo_gender_from_bytes(photo_data: bytes) -> str:
    """
    Analyze photo bytes using Gemini Vision API to determine gender.
    Returns: "male", "female", or "unknown"
    """
    if not GEMINI_API_KEY or "ضع" in GEMINI_API_KEY:
        return "unknown"
    
    try:
        # Convert to base64
        photo_base64 = base64.b64encode(photo_data).decode("utf-8")
        
        prompt = """Analyze this profile photo and determine the gender of the person.
Reply with ONLY one word: "male" or "female" or "unknown" (if unclear or no person visible).
Do not add any other text or explanation."""

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                json={
                    "contents": [{
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": photo_base64
                                }
                            }
                        ]
                    }],
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 10,
                    },
                },
                headers={"Content-Type": "application/json"},
            )
            
            if response.status_code == 200:
                data = response.json()
                result = data["candidates"][0]["content"]["parts"][0]["text"].strip().lower()
                if "male" in result and "female" not in result:
                    return "male"
                elif "female" in result:
                    return "female"
                return "unknown"
                
    except Exception as e:
        log.error("Photo gender analysis error: %s", e)
    
    return "unknown"


def detect_name_gender(name: str) -> str:
    """
    Detect gender from a name by checking against known name lists.
    Returns: "male", "female", or "unknown"
    """
    if not name:
        return "unknown"
    
    # Clean the name
    first_name = name.split()[0].strip() if name.split() else name.strip()
    
    # Check Arabic male names
    if first_name in ARABIC_MALE_NAMES:
        return "male"
    
    # Check Arabic female names
    if first_name in ARABIC_FEMALE_NAMES:
        return "female"
    
    # Check English male names
    if first_name in ENGLISH_MALE_NAMES:
        return "male"
    
    # Check English female names
    if first_name in ENGLISH_FEMALE_NAMES:
        return "female"
    
    # Use AI as fallback
    return "unknown"


async def detect_name_gender_ai(name: str) -> str:
    """
    Use AI to detect gender from name when local detection fails.
    Returns: "male", "female", or "unknown"
    """
    if not name or not GEMINI_API_KEY or "ضع" in GEMINI_API_KEY:
        return "unknown"
    
    try:
        prompt = f"""Determine the gender typically associated with this name: "{name}"
Reply with ONLY one word: "male" or "female" or "unknown" (if the name is unisex or unclear).
Do not add any other text."""

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 10,
                    },
                },
                headers={"Content-Type": "application/json"},
            )
            
            if response.status_code == 200:
                data = response.json()
                result = data["candidates"][0]["content"]["parts"][0]["text"].strip().lower()
                if "male" in result and "female" not in result:
                    return "male"
                elif "female" in result:
                    return "female"
                return "unknown"
                
    except Exception as e:
        log.error("Name gender AI analysis error: %s", e)
    
    return "unknown"


async def get_smart_gender(account: Row, client: Client | None = None) -> str:
    """
    Intelligently determine gender for an account by analyzing:
    1. Current profile photo (if exists)
    2. Current name (if exists)
    Returns: "male", "female", or "unknown"
    """
    tmp = client
    should_disconnect = False
    
    try:
        if tmp is None:
            tmp = await _account_client(account, "gender_detect")
            should_disconnect = True
        
        me = await tmp.get_me()
        current_name = f"{me.first_name or ''} {me.last_name or ''}".strip()
        
        # Try to get profile photo
        photo_gender = "unknown"
        try:
            async for photo in tmp.get_chat_photos("me", limit=1):
                # Download the photo
                photo_file = await tmp.download_media(photo.file_id, in_memory=True)
                if photo_file:
                    photo_bytes = bytes(photo_file) if isinstance(photo_file, (bytes, bytearray)) else photo_file
                    if isinstance(photo_bytes, bytes):
                        photo_gender = await analyze_photo_gender_from_bytes(photo_bytes)
                break
        except Exception:
            pass
        
        # If photo analysis gave a result, use it
        if photo_gender != "unknown":
            return photo_gender
        
        # Try name-based detection
        if current_name:
            name_gender = detect_name_gender(current_name)
            if name_gender != "unknown":
                return name_gender
            
            # Use AI for name if local detection failed
            name_gender = await detect_name_gender_ai(current_name)
            if name_gender != "unknown":
                return name_gender
        
        return "unknown"
        
    except Exception as e:
        log.error("Smart gender detection error: %s", e)
        return "unknown"
    finally:
        if should_disconnect and tmp:
            await disconnect(tmp)


# ==============================================================================
# Chat Management
# ==============================================================================

async def archive_all_chats(client: Client) -> int:
    """Archive all chats for an account. Returns count."""
    archived = 0
    async for dialog in client.get_dialogs():
        try:
            await client.archive_chats(dialog.chat.id)
            archived += 1
            await smart_delay()
        except Exception:
            pass
    return archived


async def delete_old_messages(client: Client, days: int = 30) -> int:
    """Delete messages older than X days. Returns count."""
    deleted = 0
    cutoff = datetime.now() - timedelta(days=days)
    
    async for dialog in client.get_dialogs():
        try:
            async for message in client.get_chat_history(dialog.chat.id, limit=100):
                if message.date and message.date < cutoff and message.outgoing:
                    try:
                        await message.delete()
                        deleted += 1
                        await smart_delay()
                    except Exception:
                        pass
        except Exception:
            pass
    
    return deleted


async def mute_all_chats(client: Client) -> int:
    """Mute notifications for all chats. Returns count."""
    muted = 0
    async for dialog in client.get_dialogs():
        try:
            await client.update_chat_notifications(
                dialog.chat.id,
                mute=True
            )
            muted += 1
            await smart_delay()
        except Exception:
            pass
    return muted


async def remove_old_profile_photos(client: Client) -> int:
    """Remove all old profile photos. Returns count."""
    removed = 0
    try:
        photos = await client.get_chat_photos("me")
        async for photo in photos:
            if removed > 0:  # Keep the current one
                try:
                    await client.delete_profile_photos(photo.file_id)
                    removed += 1
                except Exception:
                    pass
    except Exception as e:
        log.error("Remove photos error: %s", e)
    return removed


# ==============================================================================
# Access control
# ==============================================================================

async def access_check(msg: Message) -> bool:
    uid = msg.from_user.id

    if db_is_banned(uid):
        await msg.reply("🚫 أنت محظور من استخدام هذا البوت.")
        return False

    if not is_any_admin(uid) and not is_bot_public():
        await msg.reply("⚠️ **البوت قيد الصيانة حالياً.**\n\nيرجى المحاولة لاحقاً.")
        return False

    if not is_any_admin(uid) and is_forced_sub_enabled():
        channel = forced_sub_channel()
        if channel:
            try:
                member = await bot.get_chat_member(channel, uid)
                if member.status.value not in ("member", "administrator", "creator"):
                    raise ValueError
            except Exception:
                await msg.reply(
                    f"⚠️ **يجب الاشتراك في القناة أولاً:**\n{channel}",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton(
                            "📢 اشترك الآن",
                            url=f"https://t.me/{channel.strip('@')}",
                        )
                    ]]),
                )
                return False

    return True


# ==============================================================================
# Inline keyboard builders
# ==============================================================================

def _kb_user_main(uid: int) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton("⚡ خدمات SMM", callback_data="menu_smm")]
    ]
    if is_points_enabled():
        rows.append([
            InlineKeyboardButton("💰 رصيدي ونقاطي", callback_data="menu_balance"),
            InlineKeyboardButton("🔗 رابط الإحالة", callback_data="menu_referral"),
        ])
        rows.append([
            InlineKeyboardButton("💰 بيع حساب تليجرام", callback_data="menu_sell_account")
        ])
    rows.append([InlineKeyboardButton("ℹ️ معلومات البوت", callback_data="menu_info")])
    if not db_is_vip(uid) and is_points_enabled():
        rows.append([InlineKeyboardButton("👑 ترقية لـ VIP", callback_data="menu_vip_info")])
    return InlineKeyboardMarkup(rows)


def _kb_smm() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 إضافة أعضاء", callback_data="act_join")],
        [InlineKeyboardButton("🚪 مغادرة جماعية", callback_data="act_leave")],
        [InlineKeyboardButton("💬 نشر تعليقات", callback_data="act_comment")],
        [InlineKeyboardButton("❤️ إضافة تفاعلات", callback_data="act_react")],
        [InlineKeyboardButton("📊 تصويت في استفتاء", callback_data="act_poll")],
        [InlineKeyboardButton("🏆 تصويت في مسابقة", callback_data="act_contest")],
        [InlineKeyboardButton("« رجوع", callback_data="menu_main")],
    ])


def _kb_admin_main() -> InlineKeyboardMarkup:
    f = "✅" if is_forced_sub_enabled() else "❌"
    p = "✅" if is_bot_public() else "❌"
    q = "✅" if is_points_enabled() else "❌"
    at = "✅" if is_auto_terminate_enabled() else "❌"
    em_status = "🔴" if _emergency_mode else "🟢"

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📱 الحسابات", callback_data="adm_accounts"),
            InlineKeyboardButton("➕ إضافة حساب", callback_data="adm_add_account"),
        ],
        [
            InlineKeyboardButton("🎛️ تحكم فردي", callback_data="adm_account_list:0"),
            InlineKeyboardButton("⚡ تغيير جماعي", callback_data="adm_bulk_changes"),
        ],
        [
            InlineKeyboardButton("📊 لوحة التحليلات", callback_data="adm_analytics"),
            InlineKeyboardButton("🔍 فحص الصحة", callback_data="adm_health_check"),
        ],
        [
            InlineKeyboardButton("🤖 الأتمتة", callback_data="adm_automation"),
            InlineKeyboardButton("💬 إدارة المحادثات", callback_data="adm_chat_mgmt"),
        ],
        [
            InlineKeyboardButton("🛡️ الحماية", callback_data="adm_protection"),
            InlineKeyboardButton("💾 النسخ الاحتياطي", callback_data="adm_backup"),
        ],
        [
            InlineKeyboardButton("📋 القوالب", callback_data="adm_templates"),
            InlineKeyboardButton("🛠️ أدوات التوليد", callback_data="adm_tools"),
        ],
        [
            InlineKeyboardButton("📡 نسخ قناة", callback_data="adm_cloner_panel"),
            InlineKeyboardButton("📥 استيراد JSON", callback_data="adm_import_info"),
        ],
        [
            InlineKeyboardButton("📢 بث عام", callback_data="adm_broadcast"),
            InlineKeyboardButton("✉️ رسالة لمستخدم", callback_data="adm_dm"),
        ],
        [
            InlineKeyboardButton("🚫 حظر", callback_data="adm_ban"),
            InlineKeyboardButton("✅ رفع الحظر", callback_data="adm_unban"),
        ],
        [
            InlineKeyboardButton("👑 منح VIP", callback_data="adm_grant_vip"),
            InlineKeyboardButton("💳 ضبط رصيد", callback_data="adm_adjust_points"),
        ],
        [
            InlineKeyboardButton(f"🔒 اشتراك إجباري {f}", callback_data="adm_toggle_forced"),
            InlineKeyboardButton(f"🌐 حالة البوت {p}", callback_data="adm_toggle_public"),
        ],
        [
            InlineKeyboardButton(f"💰 نقاط {q}", callback_data="adm_toggle_points"),
            InlineKeyboardButton(f"🔄 إنهاء تلقائي {at}", callback_data="adm_toggle_auto_terminate"),
        ],
        [
            InlineKeyboardButton(f"{em_status} وضع الطوارئ", callback_data="adm_emergency"),
            InlineKeyboardButton("👥 الأدمن المساعدون", callback_data="adm_delegated"),
        ],
    ])


def _kb_account_list(accounts: list[Row], page: int) -> InlineKeyboardMarkup:
    total = len(accounts)
    start = page * ACCOUNTS_PER_PAGE
    end = min(start + ACCOUNTS_PER_PAGE, total)
    total_pages = max(1, (total + ACCOUNTS_PER_PAGE - 1) // ACCOUNTS_PER_PAGE)

    rows: list[list[InlineKeyboardButton]] = []
    for acc in accounts[start:end]:
        health = acc.get("health_score", 100)
        risk = acc.get("ban_risk_level", "low")
        icon = "🟢" if health >= 70 else "🟡" if health >= 40 else "🔴"
        rows.append([InlineKeyboardButton(
            f"{icon} {acc['phone']} ({health}%)",
            callback_data=f"account_control:{acc['phone']}"
        )])

    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"adm_account_list:{page - 1}"))
    nav.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="noop"))
    if end < total:
        nav.append(InlineKeyboardButton("التالي ➡️", callback_data=f"adm_account_list:{page + 1}"))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton("« رجوع", callback_data="adm_main")])
    return InlineKeyboardMarkup(rows)


def _kb_account_control(phone: str) -> InlineKeyboardMarkup:
    p = phone
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏷️ تغيير الاسم", callback_data=f"acct_set_name:{p}")],
        [InlineKeyboardButton("@ تغيير اليوزرنيم", callback_data=f"acct_set_username:{p}")],
        [InlineKeyboardButton("📝 تغيير الوصف", callback_data=f"acct_set_bio:{p}")],
        [InlineKeyboardButton("🖼️ تغيير الصورة", callback_data=f"acct_set_photo:{p}")],
        [InlineKeyboardButton("🚪 مغادرة قناة / جروب", callback_data=f"acct_leave_chat:{p}")],
        [
            InlineKeyboardButton("📢 مغادرة كل القنوات", callback_data=f"acct_leave_channels:{p}"),
            InlineKeyboardButton("👥 مغادرة كل الجروبات", callback_data=f"acct_leave_groups:{p}"),
        ],
        [InlineKeyboardButton("🔐 إعداد التحقق بخطوتين", callback_data=f"acct_set_2fa:{p}")],
        [
            InlineKeyboardButton("📊 الإحصائيات", callback_data=f"acct_stats:{p}"),
            InlineKeyboardButton("📜 السجل", callback_data=f"acct_history:{p}"),
        ],
        [
            InlineKeyboardButton("🗄️ أرشفة المحادثات", callback_data=f"acct_archive:{p}"),
            InlineKeyboardButton("🔕 كتم الكل", callback_data=f"acct_mute_all:{p}"),
        ],
        [InlineKeyboardButton("🗑️ حذف الصور القديمة", callback_data=f"acct_del_photos:{p}")],
        [InlineKeyboardButton("« رجوع للقائمة", callback_data="adm_account_list:0")],
    ])


def _kb_bulk_changes() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏷️ تغيير الأسماء عشوائياً", callback_data="bulk_random_names")],
        [InlineKeyboardButton("@ تغيير اليوزرنيمات", callback_data="bulk_usernames")],
        [InlineKeyboardButton("📝 تغيير الأوصاف (AI)", callback_data="bulk_bios")],
        [InlineKeyboardButton("🖼️ تغيير الصور الجماعي", callback_data="bulk_photos")],
        [InlineKeyboardButton("🔐 تعيين 2FA لكل الحسابات", callback_data="bulk_set_2fa")],
        [InlineKeyboardButton("📢 مغادرة كل القنوات (جماعي)", callback_data="bulk_leave_channels")],
        [InlineKeyboardButton("👥 مغادرة كل الجروبات (جماعي)", callback_data="bulk_leave_groups")],
        [InlineKeyboardButton("🗄️ أرشفة الكل (جماعي)", callback_data="bulk_archive")],
        [InlineKeyboardButton("🔕 كتم الكل (جماعي)", callback_data="bulk_mute")],
        [InlineKeyboardButton("🗑️ حذف الصور القديمة (جماعي)", callback_data="bulk_del_photos")],
        [InlineKeyboardButton("« رجوع", callback_data="adm_main")],
    ])


def _kb_automation() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 المهام المجدولة", callback_data="auto_tasks")],
        [InlineKeyboardButton("💬 الرد التلقائي", callback_data="auto_reply")],
        [InlineKeyboardButton("😴 أوقات السكون", callback_data="auto_sleep")],
        [InlineKeyboardButton("🔄 تدوير الصور", callback_data="auto_photo_rotation")],
        [InlineKeyboardButton("🔀 تدوير الحسابات", callback_data="auto_account_rotation")],
        [InlineKeyboardButton("« رجوع", callback_data="adm_main")],
    ])


def _kb_protection() -> InlineKeyboardMarkup:
    ab = "✅" if is_anti_ban_enabled() else "❌"
    hs = "✅" if is_human_sim_enabled() else "❌"
    hm = "✅" if is_health_monitoring() else "❌"
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🛡️ مكافحة الحظر {ab}", callback_data="prot_toggle_antiban")],
        [InlineKeyboardButton(f"🧑 محاكاة بشرية {hs}", callback_data="prot_toggle_human")],
        [InlineKeyboardButton(f"💊 مراقبة الصحة {hm}", callback_data="prot_toggle_health")],
        [InlineKeyboardButton("⏱️ إعدادات التأخير", callback_data="prot_delay_settings")],
        [InlineKeyboardButton("📊 حالة معدل العمليات", callback_data="prot_rate_status")],
        [InlineKeyboardButton("🚨 سجل الطوارئ", callback_data="prot_emergency_log")],
        [InlineKeyboardButton("« رجوع", callback_data="adm_main")],
    ])


def _kb_backup() -> InlineKeyboardMarkup:
    ab = "✅" if is_auto_backup_enabled() else "❌"
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💾 إنشاء نسخة احتياطية", callback_data="backup_create")],
        [InlineKeyboardButton("📂 عرض النسخ", callback_data="backup_list")],
        [InlineKeyboardButton("📥 استعادة نسخة", callback_data="backup_restore")],
        [InlineKeyboardButton(f"🔄 نسخ تلقائي {ab}", callback_data="backup_toggle_auto")],
        [InlineKeyboardButton("« رجوع", callback_data="adm_main")],
    ])


def _kb_analytics() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 نظرة عامة", callback_data="analytics_overview")],
        [InlineKeyboardButton("📈 إحصائيات الحسابات", callback_data="analytics_accounts")],
        [InlineKeyboardButton("🏥 تقرير الصحة", callback_data="analytics_health")],
        [InlineKeyboardButton("📉 سجل النشاط", callback_data="analytics_activity")],
        [InlineKeyboardButton("📑 تصدير التقرير", callback_data="analytics_export")],
        [InlineKeyboardButton("« رجوع", callback_data="adm_main")],
    ])


def _kb_chat_mgmt() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🗄️ أرشفة جماعية", callback_data="chat_archive_all")],
        [InlineKeyboardButton("🗑️ حذف الرسائل القديمة", callback_data="chat_delete_old")],
        [InlineKeyboardButton("🔕 كتم جماعي", callback_data="chat_mute_all")],
        [InlineKeyboardButton("📤 تصدير المحادثات", callback_data="chat_export")],
        [InlineKeyboardButton("« رجوع", callback_data="adm_main")],
    ])


def _kb_templates() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ إنشاء قالب جديد", callback_data="tmpl_create")],
        [InlineKeyboardButton("📋 عرض القوالب", callback_data="tmpl_list")],
        [InlineKeyboardButton("🎯 تطبيق قالب", callback_data="tmpl_apply")],
        [InlineKeyboardButton("« رجوع", callback_data="adm_main")],
    ])


def _kb_tools() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔤 توليد يوزرنيمات", callback_data="tool_generate_usernames")],
        [InlineKeyboardButton("📊 إحصائيات اليوزرنيمات", callback_data="tool_username_stats")],
        [InlineKeyboardButton("🖼️ إحصائيات الصور", callback_data="tool_photo_stats")],
        [InlineKeyboardButton("« رجوع", callback_data="adm_main")],
    ])


def _kb_confirm(yes_data: str, no_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ تأكيد", callback_data=yes_data),
        InlineKeyboardButton("❌ إلغاء", callback_data=no_data),
    ]])


def _kb_back(target: str = "menu_main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("« رجوع", callback_data=target)]])


# ==============================================================================
# Message command handlers
# ==============================================================================

async def cmd_start(_, msg: Message) -> None:
    uid = msg.from_user.id

    if not is_any_admin(uid) and CAPTCHA_REQUIRED and uid not in captcha_cache:
        question, answer = make_captcha()
        captcha_cache[uid] = (answer, datetime.now())
        await msg.reply(f"🔐 **تحقق من أنك بشري:**\n\n{question}\n\nأرسل الإجابة:")
        return

    if not await access_check(msg):
        return

    db_upsert_user(uid, msg.from_user.username, msg.from_user.first_name)

    if is_any_admin(uid):
        em_status = "🔴 وضع الطوارئ مفعّل!" if _emergency_mode else ""
        await msg.reply(
            f"👋 **أهلاً بك في لوحة الإدارة**\n\n🤖 الإصدار v9.1.0\n{em_status}",
            reply_markup=_kb_admin_main(),
        )
    else:
        row = db_get_user(uid)
        await msg.reply(
            f"👋 **أهلاً بك يا {msg.from_user.first_name}!**\n\n"
            f"{rank_label(row)}\n"
            f"💰 رصيدك: **{db_get_points(uid)}** نقطة",
            reply_markup=_kb_user_main(uid),
        )


async def cmd_cancel(_, msg: Message) -> None:
    user_sessions.pop(msg.from_user.id, None)
    await msg.reply("❌ تم إلغاء العملية الحالية.")


async def cmd_addaccount(_, msg: Message) -> None:
    if not is_any_admin(msg.from_user.id):
        await msg.reply("🚫 غير مصرح لك.")
        return
    user_sessions[msg.from_user.id] = {"step": "phone"}
    await msg.reply("📱 **أدخل رقم الهاتف:**\n\nالصيغة: +201012345678")


async def handle_doc(client: Client, msg: Message) -> None:
    try:
        raw = await client.download_media(msg.document, in_memory=True)
        text = (
            bytes(raw).decode("utf-8")
            if isinstance(raw, (bytes, bytearray))
            else open(raw, encoding="utf-8").read()
        )
        data = json.loads(text)

        if not isinstance(data, dict) or not isinstance(data.get("accounts"), list):
            await msg.reply("❌ **صيغة JSON غير صحيحة.**\n\nيجب أن تحتوي على مفتاح `accounts` كقائمة.")
            return

        imported = failed = 0
        for entry in data["accounts"]:
            try:
                profile = entry.get("device_profile") or random.choice(DEVICE_PROFILES)
                if isinstance(profile, str):
                    profile = json.loads(profile)
                db_save_account(
                    phone=entry["phone"].strip(),
                    session_string=entry["session_string"].strip(),
                    added_by=msg.from_user.id,
                    device_profile=profile,
                    proxy=entry.get("proxy"),
                    api_id=entry.get("api_id"),
                    api_hash=entry.get("api_hash"),
                )
                imported += 1
            except (KeyError, AttributeError, json.JSONDecodeError) as exc:
                log.warning("Skipping malformed account entry: %s", exc)
                failed += 1

        await msg.reply(f"📥 **نتيجة الاستيراد**\n\n✅ نجح: {imported}\n❌ فشل: {failed}")
        db_add_audit_log(
            msg.from_user.id, "Import Accounts JSON", f"{imported} ok / {failed} failed"
        )

    except json.JSONDecodeError:
        await msg.reply("❌ **خطأ في صيغة JSON.** تأكد من صحة الملف.")
    except Exception as exc:
        log.error("Document handler error: %s", exc)
        await msg.reply(f"❌ **خطأ غير متوقع:** {str(exc)[:100]}")


async def handle_photo(client: Client, msg: Message) -> None:
    uid = msg.from_user.id
    if not is_any_admin(uid):
        return

    session = user_sessions.get(uid, {})
    if session.get("step") != "set_photo":
        return

    phone = session.get("target_phone", "")
    account = db_get_account(phone)
    if not account:
        await msg.reply("❌ الحساب غير موجود.")
        user_sessions.pop(uid, None)
        return

    tmp = None
    try:
        raw = await client.download_media(msg.photo, in_memory=True)
        photo_data = bytes(raw) if isinstance(raw, (bytes, bytearray)) else open(raw, "rb").read()

        async with session_lock(account["id"]):
            tmp = await _account_client(account, "set_photo")
            await tmp.set_profile_photo(photo=io.BytesIO(photo_data))

        await msg.reply(f"✅ تم تغيير صورة الحساب {phone} بنجاح.")
        db_add_audit_log(uid, "Change Profile Photo", phone)
        db_add_account_history(phone, "photo_change", None, "new_photo", uid)

    except Exception as exc:
        log.error("Set profile photo error: %s", exc)
        await msg.reply(f"❌ خطأ: {str(exc)[:80]}")
    finally:
        await disconnect(tmp)
        user_sessions.pop(uid, None)


# ==============================================================================
# Text router (multi-step wizards)
# ==============================================================================

async def text_router(_, msg: Message) -> None:
    if not await access_check(msg):
        return

    uid = msg.from_user.id

    if uid in captcha_cache:
        expected, _ts = captcha_cache[uid]
        try:
            if int(msg.text.strip()) == int(expected):
                del captcha_cache[uid]
                await msg.reply("✅ تحقق صحيح! مرحباً بك.")
                await cmd_start(_, msg)
            else:
                await msg.reply("❌ الإجابة خاطئة. حاول مجدداً.")
        except ValueError:
            await msg.reply("❌ أرسل رقم صحيح للإجابة.")
        return

    if CAPTCHA_REQUIRED and not is_any_admin(uid) and uid not in captcha_cache:
        await msg.reply("أرسل /start لبدء التحقق.")
        return

    if not (is_any_admin(uid) and uid in user_sessions):
        await msg.reply("أرسل /start للبدء.")
        return

    session = user_sessions[uid]
    step: str = session.get("step", "")

    # Add-account wizard
    if step == "phone":
        phone = msg.text.strip()
        session["phone"] = phone if phone.startswith("+") else f"+{phone}"
        session["step"] = "code"
        await msg.reply("📋 **أدخل رمز التحقق:**\n\nسيصل عبر SMS أو تطبيق تليجرام")
        return

    if step == "code":
        phone = session.get("phone", "").strip()
        code = msg.text.strip()

        if not phone or not code:
            await msg.reply("❌ خطأ في البيانات. ابدأ من جديد بـ /addaccount")
            user_sessions.pop(uid, None)
            return

        await msg.reply("⏳ جاري التحقق من الرمز...")
        device = random.choice(DEVICE_PROFILES)
        tmp = Client(
            f"add_{phone}",
            api_id=API_ID, api_hash=API_HASH, in_memory=True,
            device_model=device["device_model"],
            system_version=device["system_version"],
            app_version=device["app_version"],
            connect_timeout=PROXY_TIMEOUT_SECONDS,
        )
        try:
            await asyncio.wait_for(tmp.connect(), timeout=PROXY_TIMEOUT_SECONDS)

            if "phone_code_hash" not in session:
                sent = await tmp.send_code(phone)
                session["phone_code_hash"] = sent.phone_code_hash
                await msg.reply("📋 **الآن أدخل الرمز الذي وصلك:**")
                return

            try:
                await tmp.sign_in(phone, session["phone_code_hash"], code)
            except SessionPasswordNeeded:
                session["step"] = "2fa_password"
                session["device"] = device
                session["_client"] = tmp
                await msg.reply("🔐 **الحساب محمي بـ 2FA.** أرسل كلمة المرور:")
                return

            ss = await tmp.export_session_string()
            me = await tmp.get_me()
            db_save_account(phone, ss, uid, device, None, API_ID, API_HASH)
            await msg.reply(
                f"✅ **تم إضافة الحساب بنجاح!**\n☎️ {phone}\n👤 @{me.username or 'N/A'}"
            )
            db_add_audit_log(uid, "Add Account", phone)
            user_sessions.pop(uid, None)

        except (PhoneCodeInvalid, PhoneCodeExpired):
            await msg.reply("❌ رمز التحقق غير صحيح أو منتهي. ابدأ من جديد بـ /addaccount")
            user_sessions.pop(uid, None)
        except Exception as exc:
            log.error("Sign-in error: %s", exc)
            await msg.reply(f"❌ خطأ في التوثيق: {str(exc)[:80]}")
            user_sessions.pop(uid, None)
        finally:
            if user_sessions.get(uid, {}).get("step") != "2fa_password":
                await disconnect(tmp)
        return

    if step == "2fa_password":
        tmp = session.get("_client")
        phone = session.get("phone", "")
        device = session.get("device", random.choice(DEVICE_PROFILES))

        if tmp is None:
            await msg.reply("❌ انتهت الجلسة المؤقتة. ابدأ من جديد بـ /addaccount")
            user_sessions.pop(uid, None)
            return

        try:
            await tmp.check_password(msg.text.strip())
            ss = await tmp.export_session_string()
            me = await tmp.get_me()
            db_save_account(phone, ss, uid, device, None, API_ID, API_HASH)
            await msg.reply(
                f"✅ **تم إضافة الحساب بنجاح (2FA)!**\n☎️ {phone}\n👤 @{me.username or 'N/A'}"
            )
            db_add_audit_log(uid, "Add Account (2FA)", phone)
        except Exception as exc:
            log.error("2FA error: %s", exc)
            await msg.reply(f"❌ خطأ في كلمة المرور: {str(exc)[:50]}")
        finally:
            await disconnect(tmp)
            user_sessions.pop(uid, None)
        return

    # Cloner wizard
    if step == "cloner_source":
        session["cloner_source"] = msg.text.strip()
        session["step"] = "cloner_dest"
        await msg.reply("📡 أرسل معرّف القناة **الوجهة**:")
        return

    if step == "cloner_dest":
        source = session.get("cloner_source", "")
        dest = msg.text.strip()
        with db_connect() as conn:
            conn.execute(
                "UPDATE cloner_config SET source=?, destination=?, active=1 WHERE id=1",
                (source, dest),
            )
        await msg.reply(f"✅ تم إعداد النسخ:\nمن: {source}\nإلى: {dest}")
        user_sessions.pop(uid, None)
        return

    # Individual account wizards
    if step == "set_name":
        await _wizard_set_name(uid, msg, session)
        return

    if step == "set_username":
        await _wizard_set_username(uid, msg, session)
        return

    if step == "set_bio":
        await _wizard_set_bio(uid, msg, session)
        return

    if step == "leave_chat":
        await _wizard_leave_chat(uid, msg, session)
        return

    if step == "set_2fa_current":
        session["current_pass"] = msg.text.strip()
        session["step"] = "set_2fa_new"
        await msg.reply("🔐 الآن أرسل كلمة المرور **الجديدة**:")
        return

    if step == "set_2fa_new":
        await _wizard_set_2fa_new(uid, msg, session)
        return

    # Bulk wizards
    if step == "bulk_2fa_new":
        new_pass = msg.text.strip()
        await msg.reply("⏳ جاري تطبيق 2FA على كل الحسابات في الخلفية...")
        asyncio.create_task(
            _bulk_set_2fa_task(msg, new_pass, uid),
            name=f"bulk_2fa_{uid}",
        )
        user_sessions.pop(uid, None)
        return

    if step == "generate_usernames_count":
        await _wizard_generate_usernames(uid, msg, session)
        return

    if step == "delete_old_days":
        await _wizard_delete_old_messages(uid, msg, session)
        return

    # Template wizard
    if step == "tmpl_name":
        session["tmpl_name"] = msg.text.strip()
        session["step"] = "tmpl_first_name"
        await msg.reply("🏷️ أرسل الاسم الأول للقالب:")
        return

    if step == "tmpl_first_name":
        session["tmpl_first_name"] = msg.text.strip()
        session["step"] = "tmpl_last_name"
        await msg.reply("🏷️ أرسل الاسم الأخير (أو أرسل - لتركه فارغاً):")
        return

    if step == "tmpl_last_name":
        last = msg.text.strip()
        session["tmpl_last_name"] = "" if last == "-" else last
        session["step"] = "tmpl_bio"
        await msg.reply("📝 أرسل الوصف (أو أرسل - لتركه فارغاً):")
        return

    if step == "tmpl_bio":
        bio = msg.text.strip()
        session["tmpl_bio"] = "" if bio == "-" else bio
        
        tmpl_id = db_save_template(
            session["tmpl_name"],
            session["tmpl_first_name"],
            session["tmpl_last_name"],
            session["tmpl_bio"],
            "",
            uid
        )
        await msg.reply(f"✅ تم إنشاء القالب #{tmpl_id}: {session['tmpl_name']}")
        user_sessions.pop(uid, None)
        return

    # Auto-reply wizard
    if step == "auto_reply_trigger":
        session["trigger"] = msg.text.strip()
        session["step"] = "auto_reply_response"
        await msg.reply("💬 أرسل الرد المطلوب (أو اكتب AI لاستخدام الذكاء الاصطناعي):")
        return

    if step == "auto_reply_response":
        response = msg.text.strip()
        use_ai = response.upper() == "AI"
        
        rule_id = db_add_auto_reply(
            session.get("target_phone"),
            session["trigger"],
            "" if use_ai else response,
            session.get("is_regex", False),
            use_ai
        )
        await msg.reply(f"✅ تم إضافة قاعدة الرد التلقائي #{rule_id}")
        user_sessions.pop(uid, None)
        return

    # Sleep schedule wizard
    if step == "sleep_start":
        try:
            start = int(msg.text.strip())
            if not 0 <= start <= 23:
                raise ValueError
            session["sleep_start"] = start
            session["step"] = "sleep_end"
            await msg.reply("⏰ أرسل ساعة الانتهاء (0-23):")
        except ValueError:
            await msg.reply("❌ أرسل رقم بين 0 و 23")
        return

    if step == "sleep_end":
        try:
            end = int(msg.text.strip())
            if not 0 <= end <= 23:
                raise ValueError
            
            schedule_id = db_add_sleep_schedule(
                session.get("target_phone"),
                session["sleep_start"],
                end
            )
            await msg.reply(f"✅ تم إضافة جدول السكون #{schedule_id}")
            user_sessions.pop(uid, None)
        except ValueError:
            await msg.reply("❌ أرسل رقم بين 0 و 23")
        return

    # Admin wizards
    _steps: dict[str, Any] = {
        "broadcast_text": _step_broadcast,
        "ban_user_id": _step_ban,
        "unban_user_id": _step_unban,
        "vip_user_id": _step_vip,
        "points_user_id": _step_points_uid,
        "points_amount": _step_points_amount,
        "dm_user_id": _step_dm_uid,
        "dm_text": _step_dm_text,
    }
    handler = _steps.get(step)
    if handler:
        await handler(uid, msg, session)
        return

    await msg.reply("أرسل /start للبدء.")


# Wizard helpers

async def _wizard_set_name(uid: int, msg: Message, session: KV) -> None:
    phone = session.get("target_phone", "")
    parts = msg.text.strip().split(None, 1)
    first = parts[0] if parts else ""
    last = parts[1] if len(parts) > 1 else ""

    if not first:
        await msg.reply("❌ أرسل الاسم الأول على الأقل.")
        return

    account = db_get_account(phone)
    if not account:
        await msg.reply("❌ الحساب غير موجود.")
        user_sessions.pop(uid, None)
        return

    if not check_rate_limit(phone):
        await msg.reply("⚠️ تم تجاوز حد العمليات. انتظر قليلاً.")
        return

    tmp = None
    try:
        async with session_lock(account["id"]):
            tmp = await _account_client(account, "set_name")
            old_me = await tmp.get_me()
            old_name = f"{old_me.first_name or ''} {old_me.last_name or ''}".strip()
            
            await smart_delay()
            await tmp.update_profile(first_name=first, last_name=last)
            record_action(phone)
        
        new_name = f"{first} {last}".strip()
        await msg.reply(f"✅ تم تغيير الاسم إلى: **{new_name}**")
        db_add_audit_log(uid, "Change Name", f"{phone} → {new_name}")
        db_add_account_history(phone, "name_change", old_name, new_name, uid)
    except Exception as exc:
        if "flood" in str(exc).lower():
            trigger_emergency_mode("FloodWait on name change")
        await msg.reply(f"❌ خطأ: {str(exc)[:80]}")
    finally:
        await disconnect(tmp)
        user_sessions.pop(uid, None)


async def _wizard_set_username(uid: int, msg: Message, session: KV) -> None:
    phone = session.get("target_phone", "")
    username = msg.text.strip().lstrip("@")
    account = db_get_account(phone)
    if not account:
        await msg.reply("❌ الحساب غير موجود.")
        user_sessions.pop(uid, None)
        return

    if not check_rate_limit(phone):
        await msg.reply("⚠️ تم تجاوز حد العمليات. انتظر قليلاً.")
        return

    tmp = None
    try:
        async with session_lock(account["id"]):
            tmp = await _account_client(account, "set_username")
            old_me = await tmp.get_me()
            old_username = old_me.username or ""
            
            await smart_delay()
            await tmp.set_username(username if username != "." else "")
            record_action(phone)
        
        label = f"@{username}" if username and username != "." else "(تم الإزالة)"
        await msg.reply(f"✅ تم تغيير اليوزرنيم إلى: {label}")
        db_add_audit_log(uid, "Change Username", f"{phone} → {label}")
        db_add_account_history(phone, "username_change", old_username, username, uid)
    except UsernameOccupied:
        await msg.reply("❌ اليوزرنيم مستخدم بالفعل.")
    except UsernameInvalid:
        await msg.reply("❌ اليوزرنيم غير صالح.")
    except Exception as exc:
        await msg.reply(f"❌ خطأ: {str(exc)[:80]}")
    finally:
        await disconnect(tmp)
        user_sessions.pop(uid, None)


async def _wizard_set_bio(uid: int, msg: Message, session: KV) -> None:
    phone = session.get("target_phone", "")
    bio = msg.text.strip()
    account = db_get_account(phone)
    if not account:
        await msg.reply("❌ الحساب غير موجود.")
        user_sessions.pop(uid, None)
        return

    if not check_rate_limit(phone):
        await msg.reply("⚠️ تم تجاوز حد العمليات. انتظر قليلاً.")
        return

    tmp = None
    try:
        async with session_lock(account["id"]):
            tmp = await _account_client(account, "set_bio")
            await smart_delay()
            await tmp.update_profile(bio=bio)
            record_action(phone)
        await msg.reply("✅ تم تحديث الوصف.")
        db_add_audit_log(uid, "Change Bio", phone)
        db_add_account_history(phone, "bio_change", None, bio[:50], uid)
    except Exception as exc:
        await msg.reply(f"❌ خطأ: {str(exc)[:80]}")
    finally:
        await disconnect(tmp)
        user_sessions.pop(uid, None)


async def _wizard_leave_chat(uid: int, msg: Message, session: KV) -> None:
    phone = session.get("target_phone", "")
    chat_input = msg.text.strip()
    account = db_get_account(phone)
    if not account:
        await msg.reply("❌ الحساب غير موجود.")
        user_sessions.pop(uid, None)
        return

    if "t.me/" in chat_input:
        chat_id: str | int = chat_input.split("t.me/")[-1].split("/")[0].strip()
    elif chat_input.startswith("@"):
        chat_id = chat_input[1:]
    else:
        try:
            chat_id = int(chat_input)
        except ValueError:
            chat_id = chat_input

    tmp = None
    try:
        async with session_lock(account["id"]):
            tmp = await _account_client(account, "leave_chat")
            await smart_delay()
            await tmp.leave_chat(chat_id)
            record_action(phone)
        await msg.reply(f"✅ تمت مغادرة **{chat_input}** بنجاح.")
        db_add_audit_log(uid, "Leave Chat", f"{phone} → {chat_input}")
    except Exception as exc:
        await msg.reply(f"❌ خطأ: {str(exc)[:80]}")
    finally:
        await disconnect(tmp)
        user_sessions.pop(uid, None)


async def _wizard_set_2fa_new(uid: int, msg: Message, session: KV) -> None:
    phone = session.get("target_phone", "")
    current_pass = session.get("current_pass")
    new_pass = msg.text.strip()
    account = db_get_account(phone)

    if not account:
        await msg.reply("❌ الحساب غير موجود.")
        user_sessions.pop(uid, None)
        return

    tmp = None
    try:
        async with session_lock(account["id"]):
            tmp = await _account_client(account, "set_2fa")
            if current_pass:
                await tmp.change_cloud_password(current_pass, new_pass)
                await msg.reply(f"✅ تم تغيير كلمة مرور 2FA للحساب {phone}")
            else:
                await tmp.enable_cloud_password(new_pass, hint="")
                await msg.reply(f"✅ تم تفعيل 2FA للحساب {phone}")
        db_add_audit_log(uid, "Set/Change 2FA", phone)
        db_add_account_history(phone, "2fa_change", None, "updated", uid)
    except Exception as exc:
        await msg.reply(f"❌ خطأ: {str(exc)[:80]}")
    finally:
        await disconnect(tmp)
        user_sessions.pop(uid, None)


async def _wizard_generate_usernames(uid: int, msg: Message, session: KV) -> None:
    try:
        count = int(msg.text.strip())
        if count < 1 or count > 500:
            await msg.reply("❌ أدخل عدد بين 1 و 500")
            return
    except ValueError:
        await msg.reply("❌ أدخل رقم صحيح")
        return
    
    await msg.reply(f"⏳ جاري توليد {count} يوزرنيم...\nقد يستغرق هذا بعض الوقت.")
    user_sessions.pop(uid, None)
    
    asyncio.create_task(
        _generate_usernames_task(msg, count, uid),
        name=f"gen_usernames_{uid}",
    )


async def _wizard_delete_old_messages(uid: int, msg: Message, session: KV) -> None:
    try:
        days = int(msg.text.strip())
        if days < 1:
            await msg.reply("❌ أدخل عدد أيام صحيح")
            return
    except ValueError:
        await msg.reply("❌ أدخل رقم صحيح")
        return
    
    await msg.reply(f"⏳ جاري حذف الرسائل الأقدم من {days} يوم...")
    user_sessions.pop(uid, None)
    
    asyncio.create_task(
        _bulk_delete_old_messages_task(msg, days, uid),
        name=f"del_old_{uid}",
    )


# Admin wizard steps

async def _step_broadcast(uid: int, msg: Message, _: KV) -> None:
    await msg.reply("📢 جاري البث...")
    sent = 0
    for user in db_all_users():
        try:
            await bot.send_message(user["user_id"], msg.text)
            sent += 1
        except Exception:
            pass
    await msg.reply(f"✅ تم البث لـ {sent} مستخدم")
    user_sessions.pop(uid, None)


async def _step_ban(uid: int, msg: Message, _: KV) -> None:
    try:
        target = int(msg.text)
        db_set_ban(target, True)
        await msg.reply(f"🚫 تم حظر المستخدم {target}")
        db_add_audit_log(uid, "Ban User", str(target))
        user_sessions.pop(uid, None)
    except ValueError:
        await msg.reply("❌ أرسل ID رقمي صحيح")


async def _step_unban(uid: int, msg: Message, _: KV) -> None:
    try:
        target = int(msg.text)
        db_set_ban(target, False)
        await msg.reply(f"✅ تم رفع الحظر عن {target}")
        db_add_audit_log(uid, "Unban User", str(target))
        user_sessions.pop(uid, None)
    except ValueError:
        await msg.reply("❌ أرسل ID رقمي صحيح")


async def _step_vip(uid: int, msg: Message, _: KV) -> None:
    try:
        target = int(msg.text)
        db_set_vip(target, 5)
        await msg.reply(f"👑 تم منح VIP للمستخدم {target}")
        db_add_audit_log(uid, "Grant VIP", str(target))
        user_sessions.pop(uid, None)
    except ValueError:
        await msg.reply("❌ أرسل ID رقمي صحيح")


async def _step_points_uid(uid: int, msg: Message, session: KV) -> None:
    session["points_uid"] = msg.text.strip()
    session["step"] = "points_amount"
    await msg.reply("💰 أرسل المبلغ (رقم سالب للخصم):")


async def _step_points_amount(uid: int, msg: Message, session: KV) -> None:
    try:
        amount = int(msg.text)
        target = int(session["points_uid"])
        db_adjust_points(target, amount)
        await msg.reply(f"💰 تم تعديل رصيد {target} بمقدار {amount} نقطة")
        db_add_audit_log(uid, "Adjust Points", f"{target}: {amount}")
        user_sessions.pop(uid, None)
    except ValueError:
        await msg.reply("❌ أرسل رقم صحيح")


async def _step_dm_uid(uid: int, msg: Message, session: KV) -> None:
    session["dm_uid"] = msg.text.strip()
    session["step"] = "dm_text"
    await msg.reply("📝 أرسل نص الرسالة:")


async def _step_dm_text(uid: int, msg: Message, session: KV) -> None:
    try:
        target = int(session["dm_uid"])
        await bot.send_message(target, msg.text)
        await msg.reply(f"✅ تم إرسال الرسالة إلى {target}")
        db_add_audit_log(uid, "Send DM", str(target))
    except Exception as exc:
        await msg.reply(f"❌ خطأ: {str(exc)[:50]}")
    user_sessions.pop(uid, None)


# ==============================================================================
# Callback handlers - User menus
# ==============================================================================

async def cb_menu_main(_, q: CallbackQuery) -> None:
    uid = q.from_user.id
    await q.edit_message_text(
        f"👋 **القائمة الرئيسية**\n\n{rank_label(db_get_user(uid))}",
        reply_markup=_kb_user_main(uid),
    )


async def cb_menu_smm(_, q: CallbackQuery) -> None:
    await q.edit_message_text("⚡ **خدمات SMM**\n\nاختر الخدمة:", reply_markup=_kb_smm())


async def cb_menu_balance(_, q: CallbackQuery) -> None:
    uid = q.from_user.id
    await q.edit_message_text(
        f"💰 **رصيدك والنقاط**\n\n"
        f"💎 نقاطك: **{db_get_points(uid)}**\n"
        f"🎯 رتبتك: {rank_label(db_get_user(uid))}",
        reply_markup=_kb_back(),
    )


async def cb_menu_referral(_, q: CallbackQuery) -> None:
    await q.edit_message_text(
        f"🔗 **رابط الإحالة**\n\nhttps://t.me/YourBotUsername?start=ref{q.from_user.id}",
        reply_markup=_kb_back(),
    )


async def cb_menu_info(_, q: CallbackQuery) -> None:
    await q.edit_message_text(
        "ℹ️ **معلومات البوت**\n\n🤖 Telegram Multi-Account Bot v9.1.0\n\n"
        "✨ الميزات الجديدة:\n"
        "• نظام حماية متقدم\n"
        "• أتمتة ذكية\n"
        "• تحليلات شاملة\n"
        "• نسخ احتياطي مشفر",
        reply_markup=_kb_back(),
    )


async def cb_menu_vip_info(_, q: CallbackQuery) -> None:
    await q.edit_message_text(
        "👑 **ترقية VIP**\n\nتواصل مع الأدمن للترقية.",
        reply_markup=_kb_back(),
    )


async def cb_menu_sell_account(_, q: CallbackQuery) -> None:
    await q.edit_message_text(
        f"💰 **بيع حساب تليجرام**\n\n"
        f"قيمة الحساب: **{pts_sell()} نقطة**\n\n"
        "⚠️ تأكد أنك مالك الحساب قبل البيع.",
        reply_markup=_kb_confirm("sell_account_confirm", "menu_main"),
    )


async def cb_sell_account_confirm(_, q: CallbackQuery) -> None:
    uid = q.from_user.id
    with db_connect() as conn:
        row = conn.execute(
            "SELECT id, phone, session_string, device_profile, proxy, api_id, api_hash "
            "FROM accounts WHERE status='active' LIMIT 1"
        ).fetchone()

    if not row:
        await q.edit_message_text("❌ **لا توجد حسابات نشطة لبيعها.**")
        return

    tmp = None
    try:
        async with session_lock(row["id"]):
            tmp = await _account_client(row, "validate_sell")
            me = await tmp.get_me()
            db_add_points(uid, pts_sell())
            db_delete_account(row["phone"])
            background_clients.pop(row["phone"], None)

        await q.edit_message_text(
            f"✅ **تم البيع بنجاح!**\n\n"
            f"☎️ {me.phone_number or row['phone']}\n"
            f"💰 +{pts_sell()} نقطة"
        )
        db_add_audit_log(uid, "Sell Account", row["phone"])

    except asyncio.TimeoutError:
        await q.edit_message_text("⏱️ **انتهت مهلة الاتصال.** تحقق من البروكسي.")
    except Exception as exc:
        log.error("Sell account error: %s", exc)
        await q.edit_message_text("❌ **خطأ في التحقق.** الحساب قد يكون معطّلاً.")
    finally:
        await disconnect(tmp)


async def cb_act_start(_, q: CallbackQuery) -> None:
    action = q.data.split("_", 1)[1] if "_" in q.data else q.data
    await q.edit_message_text(
        f"⚡ **{action}**\n\nهذه الميزة قيد التطوير.",
        reply_markup=_kb_back("menu_smm"),
    )


# ==============================================================================
# Callback handlers - Admin panel
# ==============================================================================

async def cb_adm_main(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        await q.answer("🚫 غير مصرح", show_alert=True)
        return
    em_status = "\n🔴 **وضع الطوارئ مفعّل!**" if _emergency_mode else ""
    await q.edit_message_text(
        f"🛠️ **لوحة الإدارة**\n\nv9.1.0{em_status}",
        reply_markup=_kb_admin_main(),
    )


async def cb_adm_accounts(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    accounts = db_get_all_accounts()
    lines = ""
    for a in accounts:
        health = a.get("health_score", 100)
        icon = "🟢" if health >= 70 else "🟡" if health >= 40 else "🔴"
        lines += f"{icon} {a['phone']} | {a['status']} | {health}%\n"
    await q.edit_message_text(
        f"📱 **الحسابات المسجلة**\n\n{lines or 'لا توجد حسابات.'}"
        f"\n**المجموع: {len(accounts)}**",
        reply_markup=_kb_back("adm_main"),
    )


async def cb_adm_add_account(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    user_sessions[q.from_user.id] = {"step": "phone"}
    await q.edit_message_text("📱 **إضافة حساب جديد**\n\nأدخل رقم الهاتف:")


async def cb_adm_analytics(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    await q.edit_message_text(
        "📊 **لوحة التحليلات**\n\nاختر نوع التقرير:",
        reply_markup=_kb_analytics(),
    )


async def cb_analytics_overview(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    
    accounts = db_get_all_accounts()
    total = len(accounts)
    active = len([a for a in accounts if a["status"] == "active"])
    healthy = len([a for a in accounts if a.get("health_score", 100) >= 70])
    at_risk = len([a for a in accounts if a.get("ban_risk_level") in ("high", "critical")])
    
    em_status = "🔴 مفعّل" if _emergency_mode else "🟢 غير مفعّل"
    
    await q.edit_message_text(
        f"📊 **نظرة عامة**\n\n"
        f"📱 إجمالي الحسابات: {total}\n"
        f"✅ نشطة: {active}\n"
        f"💚 صحية (70%+): {healthy}\n"
        f"⚠️ معرضة للخطر: {at_risk}\n\n"
        f"🚨 وضع الطوارئ: {em_status}\n"
        f"🛡️ مكافحة الحظر: {'✅' if is_anti_ban_enabled() else '❌'}",
        reply_markup=_kb_back("adm_analytics"),
    )


async def cb_analytics_health(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    
    await q.answer("جاري فحص الصحة...", show_alert=False)
    results = await run_health_check_all()
    
    details_text = ""
    for d in results["details"][:10]:
        icon = "🟢" if d["score"] >= 70 else "🟡" if d["score"] >= 40 else "🔴"
        details_text += f"{icon} {d['phone']}: {d['score']}% ({d['risk']})\n"
    
    await q.edit_message_text(
        f"🏥 **تقرير الصحة**\n\n"
        f"💚 سليمة: {results['healthy']}\n"
        f"⚠️ تحذير: {results['warning']}\n"
        f"🔴 حرجة: {results['critical']}\n\n"
        f"**التفاصيل:**\n{details_text or 'لا توجد حسابات'}",
        reply_markup=_kb_back("adm_analytics"),
    )


async def cb_adm_health_check(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    await q.answer("جاري فحص الحسابات...", show_alert=False)
    
    results = await run_health_check_all()
    
    await q.edit_message_text(
        f"🔍 **نتائج فحص الصحة**\n\n"
        f"💚 سليمة: {results['healthy']}\n"
        f"⚠️ تحذير: {results['warning']}\n"
        f"🔴 حرجة: {results['critical']}",
        reply_markup=_kb_back("adm_main"),
    )


async def cb_adm_automation(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    await q.edit_message_text(
        "🤖 **الأتمتة الذكية**\n\nاختر نوع الأتمتة:",
        reply_markup=_kb_automation(),
    )


async def cb_auto_reply(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    
    rules = db_get_auto_replies()
    rules_text = ""
    for r in rules[:10]:
        ai_tag = "🤖" if r["use_ai"] else "📝"
        rules_text += f"{ai_tag} {r['trigger'][:20]}... → {r['response'][:20] or 'AI'}...\n"
    
    await q.edit_message_text(
        f"💬 **قواعد الرد التلقائي**\n\n{rules_text or 'لا توجد قواعد'}\n\n"
        "أرسل /add_reply لإضافة قاعدة جديدة",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ إضافة قاعدة", callback_data="auto_reply_add")],
            [InlineKeyboardButton("« رجوع", callback_data="adm_automation")],
        ]),
    )


async def cb_auto_reply_add(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    user_sessions[q.from_user.id] = {"step": "auto_reply_trigger"}
    await q.edit_message_text(
        "💬 **إضافة قاعدة رد تلقائي**\n\n"
        "أرسل الكلمة أو العبارة المُفعِّلة للرد:",
    )


async def cb_auto_sleep(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    
    schedules = db_get_sleep_schedules()
    schedules_text = ""
    for s in schedules[:10]:
        phone = s["phone"] or "الكل"
        schedules_text += f"😴 {phone}: {s['start_hour']}:00 - {s['end_hour']}:00\n"
    
    await q.edit_message_text(
        f"😴 **جداول السكون**\n\n{schedules_text or 'لا توجد جداول'}\n\n",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ إضافة جدول", callback_data="auto_sleep_add")],
            [InlineKeyboardButton("« رجوع", callback_data="adm_automation")],
        ]),
    )


async def cb_auto_sleep_add(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    user_sessions[q.from_user.id] = {"step": "sleep_start"}
    await q.edit_message_text(
        "😴 **إضافة جدول سكون**\n\n"
        "أرسل ساعة البداية (0-23):",
    )


async def cb_adm_chat_mgmt(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    await q.edit_message_text(
        "💬 **إدارة المحادثات**\n\nاختر العملية:",
        reply_markup=_kb_chat_mgmt(),
    )


async def cb_chat_delete_old(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    user_sessions[q.from_user.id] = {"step": "delete_old_days"}
    await q.edit_message_text(
        "🗑️ **حذف الرسائل القديمة**\n\n"
        "كم عدد الأيام؟ (سيتم حذف الرسائل الأقدم من هذا العدد)",
    )


async def cb_adm_protection(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    await q.edit_message_text(
        "🛡️ **نظام الحماية**\n\nإدارة إعدادات الحماية:",
        reply_markup=_kb_protection(),
    )


async def cb_prot_toggle_antiban(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    current = is_anti_ban_enabled()
    set_setting("anti_ban_enabled", "0" if current else "1")
    await q.answer(f"مكافحة الحظر: {'❌' if current else '✅'}")
    await cb_adm_protection(_, q)


async def cb_prot_toggle_human(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    current = is_human_sim_enabled()
    set_setting("human_simulation_enabled", "0" if current else "1")
    await q.answer(f"محاكاة بشرية: {'❌' if current else '✅'}")
    await cb_adm_protection(_, q)


async def cb_prot_toggle_health(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    current = is_health_monitoring()
    set_setting("health_monitoring_enabled", "0" if current else "1")
    await q.answer(f"مراقبة الصحة: {'❌' if current else '✅'}")
    await cb_adm_protection(_, q)


async def cb_prot_rate_status(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    
    status_text = ""
    for phone, actions in list(_action_counts.items())[:10]:
        count = len(actions)
        status_text += f"📱 {phone}: {count}/{MAX_ACTIONS_PER_HOUR} عملية/ساعة\n"
    
    await q.edit_message_text(
        f"📊 **حالة معدل العمليات**\n\n"
        f"الحد الأقصى: {MAX_ACTIONS_PER_HOUR} عملية/ساعة\n\n"
        f"{status_text or 'لا توجد عمليات مسجلة'}",
        reply_markup=_kb_back("adm_protection"),
    )


async def cb_adm_emergency(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    
    global _emergency_mode, _emergency_until
    
    if _emergency_mode:
        _emergency_mode = False
        _emergency_until = None
        await q.answer("✅ تم إلغاء وضع الطوارئ")
    else:
        trigger_emergency_mode("Manual activation")
        await q.answer("🚨 تم تفعيل وضع الطوارئ")
    
    await cb_adm_main(_, q)


async def cb_adm_backup(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    await q.edit_message_text(
        "💾 **النسخ الاحتياطي**\n\nإدارة النسخ الاحتياطية:",
        reply_markup=_kb_backup(),
    )


async def cb_backup_create(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    
    await q.answer("جاري إنشاء النسخة الاحتياطية...", show_alert=False)
    
    try:
        filename = await create_backup(encrypted=True)
        await q.edit_message_text(
            f"✅ **تم إنشاء النسخة الاحتياطية**\n\n"
            f"📁 الملف: `{filename}`\n"
            f"🔐 مشفرة: نعم",
            reply_markup=_kb_back("adm_backup"),
        )
    except Exception as e:
        await q.edit_message_text(
            f"❌ خطأ في إنشاء النسخة: {str(e)[:50]}",
            reply_markup=_kb_back("adm_backup"),
        )


async def cb_backup_list(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    
    backups = db_get_backups(10)
    backup_text = ""
    for b in backups:
        size_kb = b["size_bytes"] / 1024
        enc = "🔐" if b["encrypted"] else "📄"
        backup_text += f"{enc} {b['filename']} ({size_kb:.1f}KB)\n"
    
    await q.edit_message_text(
        f"📂 **النسخ الاحتياطية**\n\n{backup_text or 'لا توجد نسخ'}",
        reply_markup=_kb_back("adm_backup"),
    )


async def cb_backup_toggle_auto(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    current = is_auto_backup_enabled()
    set_setting("auto_backup_enabled", "0" if current else "1")
    await q.answer(f"نسخ تلقائي: {'❌' if current else '✅'}")
    await cb_adm_backup(_, q)


async def cb_adm_templates(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    await q.edit_message_text(
        "📋 **قوالب الملف الشخصي**\n\nإدارة القوالب المحفوظة:",
        reply_markup=_kb_templates(),
    )


async def cb_tmpl_create(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    user_sessions[q.from_user.id] = {"step": "tmpl_name"}
    await q.edit_message_text(
        "📋 **إنشاء قالب جديد**\n\nأرسل اسم القالب:",
    )


async def cb_tmpl_list(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    
    templates = db_get_templates()
    tmpl_text = ""
    for t in templates[:10]:
        tmpl_text += f"📋 #{t['id']} {t['name']}: {t['first_name']} {t['last_name']}\n"
    
    await q.edit_message_text(
        f"📋 **القوالب المحفوظة**\n\n{tmpl_text or 'لا توجد قوالب'}",
        reply_markup=_kb_back("adm_templates"),
    )


async def cb_adm_broadcast(_, q: CallbackQuery) -> None:
    if not is_primary_admin(q.from_user.id):
        return
    user_sessions[q.from_user.id] = {"step": "broadcast_text"}
    await q.edit_message_text("📢 **بث عام**\n\nأرسل نص الرسالة:")


async def cb_adm_dm(_, q: CallbackQuery) -> None:
    if not is_primary_admin(q.from_user.id):
        return
    user_sessions[q.from_user.id] = {"step": "dm_user_id"}
    await q.edit_message_text("✉️ **رسالة لمستخدم**\n\nأرسل ID المستخدم:")


async def cb_adm_ban(_, q: CallbackQuery) -> None:
    if not is_primary_admin(q.from_user.id):
        return
    user_sessions[q.from_user.id] = {"step": "ban_user_id"}
    await q.edit_message_text("🚫 **حظر مستخدم**\n\nأرسل ID المستخدم:")


async def cb_adm_unban(_, q: CallbackQuery) -> None:
    if not is_primary_admin(q.from_user.id):
        return
    user_sessions[q.from_user.id] = {"step": "unban_user_id"}
    await q.edit_message_text("✅ **رفع الحظر**\n\nأرسل ID المستخدم:")


async def cb_adm_grant_vip(_, q: CallbackQuery) -> None:
    if not is_primary_admin(q.from_user.id):
        return
    user_sessions[q.from_user.id] = {"step": "vip_user_id"}
    await q.edit_message_text("👑 **منح VIP**\n\nأرسل ID المستخدم:")


async def cb_adm_adjust_points(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    user_sessions[q.from_user.id] = {"step": "points_user_id"}
    await q.edit_message_text("📊 **ضبط رصيد النقاط**\n\nأرسل ID المستخدم:")


async def cb_adm_import_info(_, q: CallbackQuery) -> None:
    if not is_primary_admin(q.from_user.id):
        return
    await q.edit_message_text(
        "📥 **استيراد الجلسات**\n\n"
        "أرسل ملف JSON بالصيغة:\n"
        '`{"accounts": [{"phone": "+201012345678", "session_string": "..."}]}`'
    )


async def cb_adm_delegated(_, q: CallbackQuery) -> None:
    if not is_primary_admin(q.from_user.id):
        return
    admins = db_get_delegated_admins()
    lines = "".join(f"🔹 {a}\n" for a in admins)
    await q.edit_message_text(
        f"👥 **الأدمن المساعدون**\n\n{lines or 'لا يوجد أدمن مساعدون.'}\n"
        f"المجموع: {len(admins)}",
        reply_markup=_kb_back("adm_main"),
    )


async def cb_adm_cloner_panel(_, q: CallbackQuery) -> None:
    if not is_primary_admin(q.from_user.id):
        return
    with db_connect() as conn:
        cfg = conn.execute("SELECT * FROM cloner_config WHERE id=1").fetchone()
    src = cfg["source"] if cfg else "—"
    dst = cfg["destination"] if cfg else "—"
    state = "✅ مفعّل" if (cfg and cfg["active"]) else "❌ معطّل"
    await q.edit_message_text(
        f"📡 **نسخ القنوات**\n\nالحالة: {state}\nالمصدر: {src}\nالوجهة: {dst}",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⚙️ إعداد", callback_data="cloner_setup"),
                InlineKeyboardButton("🔄 تبديل التفعيل", callback_data="cloner_toggle"),
            ],
            [InlineKeyboardButton("« رجوع", callback_data="adm_main")],
        ]),
    )


async def cb_cloner_setup(_, q: CallbackQuery) -> None:
    if not is_primary_admin(q.from_user.id):
        return
    user_sessions[q.from_user.id] = {"step": "cloner_source"}
    await q.edit_message_text("📡 **إعداد النسخ**\n\nأرسل معرّف القناة المصدر:")


async def cb_cloner_toggle(_, q: CallbackQuery) -> None:
    if not is_primary_admin(q.from_user.id):
        return
    with db_connect() as conn:
        cfg = conn.execute("SELECT active FROM cloner_config WHERE id=1").fetchone()
        new = 0 if (cfg and cfg["active"]) else 1
        conn.execute("UPDATE cloner_config SET active=? WHERE id=1", (new,))
    await q.answer("✅ تم التفعيل" if new else "❌ تم الإيقاف")


async def cb_adm_tools(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    await q.edit_message_text(
        "🛠️ **أدوات التوليد**\n\nاختر أداة:",
        reply_markup=_kb_tools(),
    )


async def cb_toggle_forced(_, q: CallbackQuery) -> None:
    if not is_primary_admin(q.from_user.id):
        return
    new = "0" if is_forced_sub_enabled() else "1"
    set_setting("forced_sub_status", new)
    await q.answer("✅ مفعّل" if new == "1" else "❌ معطّل")


async def cb_toggle_public(_, q: CallbackQuery) -> None:
    if not is_primary_admin(q.from_user.id):
        return
    new = "0" if is_bot_public() else "1"
    set_setting("bot_status_public", new)
    await q.answer("عام ✅" if new == "1" else "خاص ❌")


async def cb_toggle_points(_, q: CallbackQuery) -> None:
    if not is_primary_admin(q.from_user.id):
        return
    new = "0" if is_points_enabled() else "1"
    set_setting("points_system_status", new)
    await q.answer("نقاط ✅" if new == "1" else "نقاط ❌")


async def cb_toggle_auto_terminate(_, q: CallbackQuery) -> None:
    if not is_primary_admin(q.from_user.id):
        return
    new = "0" if is_auto_terminate_enabled() else "1"
    set_setting("auto_terminate_feature", new)
    await q.answer("إنهاء تلقائي ✅" if new == "1" else "إنهاء تلقائي ❌")


async def cb_cancel_wizard(_, q: CallbackQuery) -> None:
    user_sessions.pop(q.from_user.id, None)
    await q.edit_message_text("❌ تم إلغاء العملية.")


async def cb_noop(_, q: CallbackQuery) -> None:
    await q.answer()


# ==============================================================================
# Callback handlers - Individual account control
# ==============================================================================

async def cb_adm_account_list(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return

    try:
        page = int(q.data.split(":")[-1])
    except (ValueError, IndexError):
        page = 0

    accounts = db_get_all_accounts()
    if not accounts:
        await q.edit_message_text(
            "❌ لا توجد حسابات مضافة.",
            reply_markup=_kb_back("adm_main"),
        )
        return

    total_pages = max(1, (len(accounts) + ACCOUNTS_PER_PAGE - 1) // ACCOUNTS_PER_PAGE)
    page = max(0, min(page, total_pages - 1))

    await q.edit_message_text(
        f"🎛️ **تحكم فردي بالحسابات**\n\n"
        f"اختر حساباً للتحكم فيه:\n"
        f"📦 {len(accounts)} حساب | صفحة {page + 1}/{total_pages}",
        reply_markup=_kb_account_list(accounts, page),
    )


async def cb_account_control(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return

    phone = _phone_from_data(q.data)
    account = db_get_account(phone)
    if not account:
        await q.answer("❌ الحساب غير موجود", show_alert=True)
        return

    health = account.get("health_score", 100)
    risk = account.get("ban_risk_level", "low")
    last_active = account.get("last_active", "غير معروف")
    
    risk_icon = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(risk, "⚪")

    await q.edit_message_text(
        f"🎛️ **لوحة التحكم بالحساب**\n\n"
        f"☎️ الرقم: `{phone}`\n"
        f"📊 الحالة: {account['status']}\n"
        f"💊 الصحة: {health}%\n"
        f"{risk_icon} مستوى الخطر: {risk}\n"
        f"⏰ آخر نشاط: {last_active}",
        reply_markup=_kb_account_control(phone),
    )


async def cb_acct_set_name(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    phone = _phone_from_data(q.data)
    await q.edit_message_text(
        f"🏷️ **تغيير الاسم**\n\nالحساب: `{phone}`\n\n"
        "اختر طريقة تغيير الاسم:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✍️ إدخال يدوي", callback_data=f"acct_set_name_manual:{phone}")],
            [InlineKeyboardButton("🤖 اسم ذكي (حسب الصورة)", callback_data=f"acct_set_name_smart:{phone}")],
            [InlineKeyboardButton("« رجوع", callback_data=f"account_control:{phone}")],
        ]),
    )


async def cb_acct_set_name_manual(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    phone = _phone_from_data(q.data)
    user_sessions[q.from_user.id] = {"step": "set_name", "target_phone": phone}
    await q.edit_message_text(
        f"🏷️ **تغيير الاسم يدوياً**\n\nالحساب: `{phone}`\n\n"
        "أرسل الاسم بالصيغة: `الاسم الأول الاسم الأخير`",
        reply_markup=_kb_back(f"account_control:{phone}"),
    )


async def cb_acct_set_name_smart(_, q: CallbackQuery) -> None:
    """Set name based on profile photo gender analysis."""
    if not is_any_admin(q.from_user.id):
        return
    phone = _phone_from_data(q.data)
    account = db_get_account(phone)
    if not account:
        await q.answer("❌ الحساب غير موجود", show_alert=True)
        return
    
    await q.edit_message_text(f"⏳ جاري تحليل صورة الحساب `{phone}`...")
    
    tmp = None
    try:
        tmp = await _account_client(account, "smart_name")
        
        # Get current info
        old_me = await tmp.get_me()
        old_name = f"{old_me.first_name or ''} {old_me.last_name or ''}".strip()
        
        # Generate smart name based on photo
        first, last = await generate_smart_name_for_photo(account, tmp)
        
        await smart_delay()
        await tmp.update_profile(first_name=first, last_name=last)
        record_action(phone)
        
        new_name = f"{first} {last}".strip()
        db_add_account_history(phone, "name_change_smart", old_name, new_name, q.from_user.id)
        db_add_audit_log(q.from_user.id, "Smart Name Change", f"{phone}: {old_name} → {new_name}")
        
        await q.edit_message_text(
            f"✅ **تم تغيير الاسم بنجاح**\n\n"
            f"📱 الحساب: `{phone}`\n"
            f"📝 الاسم القديم: {old_name}\n"
            f"✨ الاسم الجديد: {new_name}\n\n"
            f"🤖 تم التحديد بناءً على تحليل الصورة",
            reply_markup=_kb_back(f"account_control:{phone}"),
        )
    except Exception as exc:
        log.error("Smart name change error (%s): %s", phone, exc)
        await q.edit_message_text(
            f"❌ خطأ: {str(exc)[:60]}",
            reply_markup=_kb_back(f"account_control:{phone}"),
        )
    finally:
        await disconnect(tmp)


async def cb_acct_set_username(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    phone = _phone_from_data(q.data)
    user_sessions[q.from_user.id] = {"step": "set_username", "target_phone": phone}
    await q.edit_message_text(
        f"@ **تغيير اليوزرنيم**\n\nالحساب: `{phone}`\n\n"
        "أرسل اليوزرنيم الجديد بدون @ — أو أرسل نقطة `.` لحذفه.",
        reply_markup=_kb_back(f"account_control:{phone}"),
    )


async def cb_acct_set_bio(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    phone = _phone_from_data(q.data)
    user_sessions[q.from_user.id] = {"step": "set_bio", "target_phone": phone}
    await q.edit_message_text(
        f"📝 **تغيير الوصف**\n\nالحساب: `{phone}`\n\nأرسل الوصف الجديد:",
        reply_markup=_kb_back(f"account_control:{phone}"),
    )


async def cb_acct_set_photo(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    phone = _phone_from_data(q.data)
    await q.edit_message_text(
        f"🖼️ **تغيير الصورة**\n\nالحساب: `{phone}`\n\n"
        "اختر طريقة تغيير الصورة:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 رفع صورة", callback_data=f"acct_set_photo_upload:{phone}")],
            [InlineKeyboardButton("🤖 صورة ذكية (حسب الاسم)", callback_data=f"acct_set_photo_smart:{phone}")],
            [InlineKeyboardButton("« رجوع", callback_data=f"account_control:{phone}")],
        ]),
    )


async def cb_acct_set_photo_upload(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    phone = _phone_from_data(q.data)
    user_sessions[q.from_user.id] = {"step": "set_photo", "target_phone": phone}
    await q.edit_message_text(
        f"🖼️ **رفع صورة**\n\nالحساب: `{phone}`\n\nأرسل الصورة الجديدة الآن:",
        reply_markup=_kb_back(f"account_control:{phone}"),
    )


async def cb_acct_set_photo_smart(_, q: CallbackQuery) -> None:
    """Set photo based on account name gender analysis."""
    if not is_any_admin(q.from_user.id):
        return
    phone = _phone_from_data(q.data)
    account = db_get_account(phone)
    if not account:
        await q.answer("❌ الحساب غير موجود", show_alert=True)
        return
    
    await q.edit_message_text(f"⏳ جاري تحليل اسم الحساب `{phone}` واختيار صورة مناسبة...")
    
    tmp = None
    try:
        tmp = await _account_client(account, "smart_photo")
        
        # Get photo matching the account's name
        photo_url = await get_smart_photo_for_name(account, tmp)
        
        if not photo_url:
            await q.edit_message_text(
                "❌ لا توجد صور متاحة في المستودع",
                reply_markup=_kb_back(f"account_control:{phone}"),
            )
            return
        
        photo_data = await download_photo(photo_url)
        if not photo_data:
            await q.edit_message_text(
                "❌ فشل في تحميل الصورة",
                reply_markup=_kb_back(f"account_control:{phone}"),
            )
            return
        
        await smart_delay()
        await tmp.set_profile_photo(photo=io.BytesIO(photo_data))
        db_mark_photo_used(photo_url, phone)
        record_action(phone)
        
        db_add_account_history(phone, "photo_change_smart", None, "github_ai", q.from_user.id)
        db_add_audit_log(q.from_user.id, "Smart Photo Change", phone)
        
        await q.edit_message_text(
            f"✅ **تم تغيير الصورة بنجاح**\n\n"
            f"📱 الحساب: `{phone}`\n\n"
            f"🤖 تم اختيار الصورة بناءً على تحليل الاسم",
            reply_markup=_kb_back(f"account_control:{phone}"),
        )
    except Exception as exc:
        log.error("Smart photo change error (%s): %s", phone, exc)
        await q.edit_message_text(
            f"❌ خطأ: {str(exc)[:60]}",
            reply_markup=_kb_back(f"account_control:{phone}"),
        )
    finally:
        await disconnect(tmp)


async def cb_acct_leave_chat(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    phone = _phone_from_data(q.data)
    user_sessions[q.from_user.id] = {"step": "leave_chat", "target_phone": phone}
    await q.edit_message_text(
        f"🚪 **مغادرة قناة / جروب**\n\nالحساب: `{phone}`\n\n"
        "أرسل @يوزرنيم أو رابط t.me أو الـ ID:",
        reply_markup=_kb_back(f"account_control:{phone}"),
    )


async def cb_acct_stats(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    phone = _phone_from_data(q.data)
    stats = db_get_account_stats(phone, 7)
    
    stats_text = ""
    for s in stats:
        stats_text += f"📅 {s['stat_date']}: 📤{s['messages_sent']} 📥{s['messages_recv']}\n"
    
    await q.edit_message_text(
        f"📊 **إحصائيات الحساب**\n\n"
        f"📱 {phone}\n\n"
        f"{stats_text or 'لا توجد إحصائيات'}",
        reply_markup=_kb_back(f"account_control:{phone}"),
    )


async def cb_acct_history(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    phone = _phone_from_data(q.data)
    history = db_get_account_history(phone, 10)
    
    history_text = ""
    for h in history:
        history_text += f"• {h['action']}: {h['old_value'] or '-'} → {h['new_value'] or '-'}\n"
    
    await q.edit_message_text(
        f"📜 **سجل التغييرات**\n\n"
        f"📱 {phone}\n\n"
        f"{history_text or 'لا يوجد سجل'}",
        reply_markup=_kb_back(f"account_control:{phone}"),
    )


async def cb_acct_archive(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    phone = _phone_from_data(q.data)
    account = db_get_account(phone)
    if not account:
        await q.answer("❌ الحساب غير موجود", show_alert=True)
        return
    
    await q.edit_message_text(f"⏳ جاري أرشفة المحادثات للحساب `{phone}`...")
    
    tmp = None
    try:
        tmp = await _account_client(account, "archive")
        count = await archive_all_chats(tmp)
        await q.edit_message_text(
            f"✅ تم أرشفة {count} محادثة",
            reply_markup=_kb_back(f"account_control:{phone}"),
        )
    except Exception as e:
        await q.edit_message_text(
            f"❌ خطأ: {str(e)[:50]}",
            reply_markup=_kb_back(f"account_control:{phone}"),
        )
    finally:
        await disconnect(tmp)


async def cb_acct_mute_all(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    phone = _phone_from_data(q.data)
    account = db_get_account(phone)
    if not account:
        await q.answer("❌ الحساب غير موجود", show_alert=True)
        return
    
    await q.edit_message_text(f"⏳ جاري كتم الإشعارات للحساب `{phone}`...")
    
    tmp = None
    try:
        tmp = await _account_client(account, "mute")
        count = await mute_all_chats(tmp)
        await q.edit_message_text(
            f"✅ تم كتم {count} محادثة",
            reply_markup=_kb_back(f"account_control:{phone}"),
        )
    except Exception as e:
        await q.edit_message_text(
            f"❌ خطأ: {str(e)[:50]}",
            reply_markup=_kb_back(f"account_control:{phone}"),
        )
    finally:
        await disconnect(tmp)


async def cb_acct_del_photos(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    phone = _phone_from_data(q.data)
    account = db_get_account(phone)
    if not account:
        await q.answer("❌ الحساب غير موجود", show_alert=True)
        return
    
    await q.edit_message_text(f"⏳ جاري حذف الصور القديمة للحساب `{phone}`...")
    
    tmp = None
    try:
        tmp = await _account_client(account, "del_photos")
        count = await remove_old_profile_photos(tmp)
        await q.edit_message_text(
            f"✅ تم حذف {count} صورة قديمة",
            reply_markup=_kb_back(f"account_control:{phone}"),
        )
    except Exception as e:
        await q.edit_message_text(
            f"❌ خطأ: {str(e)[:50]}",
            reply_markup=_kb_back(f"account_control:{phone}"),
        )
    finally:
        await disconnect(tmp)


async def cb_acct_leave_channels(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    phone = _phone_from_data(q.data)
    await q.edit_message_text(
        f"📢 **مغادرة كل القنوات**\n\nالحساب: `{phone}`\n\n"
        "⚠️ سيتم مغادرة جميع القنوات.",
        reply_markup=_kb_confirm(
            f"acct_leave_channels_confirm:{phone}",
            f"account_control:{phone}",
        ),
    )


async def cb_acct_leave_channels_confirm(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    phone = _phone_from_data(q.data)
    account = db_get_account(phone)
    if not account:
        await q.answer("❌ الحساب غير موجود", show_alert=True)
        return
    await q.edit_message_text(f"⏳ جاري مغادرة كل القنوات للحساب `{phone}`...")
    asyncio.create_task(
        _leave_all_chats_task(q.message, account, ChatType.CHANNEL, q.from_user.id),
        name=f"leave_channels_{phone}",
    )


async def cb_acct_leave_groups(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    phone = _phone_from_data(q.data)
    await q.edit_message_text(
        f"👥 **مغادرة كل الجروبات**\n\nالحساب: `{phone}`\n\n"
        "⚠️ سيتم مغادرة جميع الجروبات.",
        reply_markup=_kb_confirm(
            f"acct_leave_groups_confirm:{phone}",
            f"account_control:{phone}",
        ),
    )


async def cb_acct_leave_groups_confirm(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    phone = _phone_from_data(q.data)
    account = db_get_account(phone)
    if not account:
        await q.answer("❌ الحساب غير موجود", show_alert=True)
        return
    await q.edit_message_text(f"⏳ جاري مغادرة كل الجروبات للحساب `{phone}`...")
    asyncio.create_task(
        _leave_all_chats_task(q.message, account, ChatType.GROUP, q.from_user.id),
        name=f"leave_groups_{phone}",
    )


async def cb_acct_set_2fa(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return

    phone = _phone_from_data(q.data)
    account = db_get_account(phone)
    if not account:
        await q.answer("❌ الحساب غير موجود", show_alert=True)
        return

    tmp = None
    try:
        tmp = await _account_client(account, "check_2fa")
        pwd_info = await tmp.invoke(raw_account.GetPassword())
        has_2fa = getattr(pwd_info, "has_password", False)
    except Exception as exc:
        await q.edit_message_text(
            f"❌ خطأ في الاتصال بالحساب: {str(exc)[:60]}",
            reply_markup=_kb_back(f"account_control:{phone}"),
        )
        return
    finally:
        await disconnect(tmp)

    uid = q.from_user.id
    if has_2fa:
        hint = getattr(pwd_info, "hint", "") or ""
        user_sessions[uid] = {"step": "set_2fa_current", "target_phone": phone}
        await q.edit_message_text(
            f"🔐 **تغيير التحقق بخطوتين**\n\nالحساب: `{phone}`\n"
            + (f"التلميح الحالي: _{hint}_\n\n" if hint else "\n")
            + "أرسل كلمة المرور **الحالية** أولاً:",
            reply_markup=_kb_back(f"account_control:{phone}"),
        )
    else:
        user_sessions[uid] = {
            "step": "set_2fa_new",
            "target_phone": phone,
            "current_pass": None,
        }
        await q.edit_message_text(
            f"🔐 **تفعيل التحقق بخطوتين**\n\nالحساب: `{phone}`\n\n"
            "أرسل كلمة المرور الجديدة:",
            reply_markup=_kb_back(f"account_control:{phone}"),
        )


# ==============================================================================
# Callback handlers - Bulk operations
# ==============================================================================

async def cb_adm_bulk_changes(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    await q.edit_message_text(
        "⚡ **التغيير الجماعي للحسابات**\n\n"
        "اختر العملية التي تريد تطبيقها على جميع الحسابات:",
        reply_markup=_kb_bulk_changes(),
    )


async def cb_bulk_random_names(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    await q.edit_message_text(
        "🏷️ **تغيير الأسماء عشوائياً**\n\n"
        "🤖 **الوضع الذكي (AI):**\n"
        "سيتم تحليل صورة كل حساب لتحديد الجنس واختيار اسم مناسب.\n"
        "• صورة ذكر ← اسم ذكر\n"
        "• صورة أنثى ← اسم أنثى\n\n"
        "اختر الوضع:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🤖 ذكي (تحليل الصور)", callback_data="bulk_random_names_smart")],
            [InlineKeyboardButton("🎲 عشوائي بالكامل", callback_data="bulk_random_names_random")],
            [InlineKeyboardButton("« رجوع", callback_data="adm_bulk_changes")],
        ]),
    )


async def cb_bulk_random_names_smart(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    global _used_names
    _used_names.clear()
    await q.edit_message_text("⏳ جاري تحليل الصور وتغيير الأسماء بالوضع الذكي...")
    asyncio.create_task(
        _bulk_random_names_task(q.message, q.from_user.id, smart_mode=True),
        name=f"bulk_names_smart_{q.from_user.id}",
    )


async def cb_bulk_random_names_random(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    global _used_names
    _used_names.clear()
    await q.edit_message_text("⏳ جاري تغيير الأسماء عشوائياً...")
    asyncio.create_task(
        _bulk_random_names_task(q.message, q.from_user.id, smart_mode=False),
        name=f"bulk_names_random_{q.from_user.id}",
    )


async def cb_bulk_usernames(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    total, available = db_get_username_count()
    await q.edit_message_text(
        f"@ **تغيير اليوزرنيمات الجماعي**\n\n"
        f"📊 المتاح: {available}/{total}\n\n"
        "هل تريد المتابعة؟",
        reply_markup=_kb_confirm("bulk_usernames_confirm", "adm_bulk_changes"),
    )


async def cb_bulk_usernames_confirm(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    await q.edit_message_text("⏳ جاري تغيير اليوزرنيمات...")
    asyncio.create_task(
        _bulk_usernames_task(q.message, q.from_user.id),
        name=f"bulk_usernames_{q.from_user.id}",
    )


async def cb_bulk_bios(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    has_key = GEMINI_API_KEY and "ضع" not in GEMINI_API_KEY
    api_status = "✅ مفعّل" if has_key else "❌ غير مفعّل"
    await q.edit_message_text(
        f"📝 **تغيير الأوصاف (AI)**\n\n"
        f"🤖 Gemini API: {api_status}\n\n"
        "هل تريد المتابعة؟",
        reply_markup=_kb_confirm("bulk_bios_confirm", "adm_bulk_changes"),
    )


async def cb_bulk_bios_confirm(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    await q.edit_message_text("⏳ جاري تغيير الأوصاف باستخدام AI...")
    asyncio.create_task(
        _bulk_bios_task(q.message, q.from_user.id),
        name=f"bulk_bios_{q.from_user.id}",
    )


async def cb_bulk_photos(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    has_repo = GITHUB_PHOTOS_REPO and "ضع" not in GITHUB_PHOTOS_REPO
    used_count = db_get_used_photos_count()
    await q.edit_message_text(
        f"🖼️ **تغيير الصور الجماعي**\n\n"
        f"📁 GitHub: {'✅' if has_repo else '❌'}\n"
        f"📊 مستخدمة: {used_count}\n\n"
        "🤖 **الوضع الذكي (AI):**\n"
        "سيتم تحليل اسم كل حساب لتحديد الجنس واختيار صورة مناسبة.\n"
        "• اسم ذكر ← صورة ذكر\n"
        "• اسم أنثى ← صورة أنثى\n\n"
        "اختر الوضع:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🤖 ذكي (تحليل الأسماء)", callback_data="bulk_photos_smart")],
            [InlineKeyboardButton("🎲 عشوائي بالكامل", callback_data="bulk_photos_random")],
            [InlineKeyboardButton("« رجوع", callback_data="adm_bulk_changes")],
        ]),
    )


async def cb_bulk_photos_smart(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    await q.edit_message_text("⏳ جاري تحليل الأسماء وتغيير الصور بالوضع الذكي...")
    asyncio.create_task(
        _bulk_photos_task(q.message, q.from_user.id, smart_mode=True),
        name=f"bulk_photos_smart_{q.from_user.id}",
    )


async def cb_bulk_photos_random(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    await q.edit_message_text("⏳ جاري تغيير الصور عشوائياً...")
    asyncio.create_task(
        _bulk_photos_task(q.message, q.from_user.id, smart_mode=False),
        name=f"bulk_photos_random_{q.from_user.id}",
    )


async def cb_bulk_set_2fa(_, q: CallbackQuery) -> None:
    if not is_primary_admin(q.from_user.id):
        return
    user_sessions[q.from_user.id] = {"step": "bulk_2fa_new"}
    await q.edit_message_text(
        "🔐 **تعيين 2FA لكل الحسابات**\n\n"
        "أرسل كلمة المرور الموحّدة:",
        reply_markup=_kb_back("adm_bulk_changes"),
    )


async def cb_bulk_leave_channels(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    await q.edit_message_text(
        "📢 **مغادرة كل القنوات — جماعي**\n\n"
        "⚠️ سيتم مغادرة جميع القنوات من كل الحسابات.",
        reply_markup=_kb_confirm("bulk_leave_channels_confirm", "adm_bulk_changes"),
    )


async def cb_bulk_leave_channels_confirm(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    await q.edit_message_text("⏳ جاري مغادرة القنوات...")
    asyncio.create_task(
        _bulk_leave_all_chats_task(q.message, ChatType.CHANNEL, q.from_user.id),
        name="bulk_leave_channels",
    )


async def cb_bulk_leave_groups(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    await q.edit_message_text(
        "👥 **مغادرة كل الجروبات — جماعي**\n\n"
        "⚠️ سيتم مغادرة جميع الجروبات من كل الحسابات.",
        reply_markup=_kb_confirm("bulk_leave_groups_confirm", "adm_bulk_changes"),
    )


async def cb_bulk_leave_groups_confirm(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    await q.edit_message_text("⏳ جاري مغادرة الجروبات...")
    asyncio.create_task(
        _bulk_leave_all_chats_task(q.message, ChatType.GROUP, q.from_user.id),
        name="bulk_leave_groups",
    )


async def cb_bulk_archive(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    await q.edit_message_text(
        "🗄️ **أرشفة جماعية**\n\n"
        "سيتم أرشفة كل المحادثات في جميع الحسابات.",
        reply_markup=_kb_confirm("bulk_archive_confirm", "adm_bulk_changes"),
    )


async def cb_bulk_archive_confirm(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    await q.edit_message_text("⏳ جاري الأرشفة...")
    asyncio.create_task(
        _bulk_archive_task(q.message, q.from_user.id),
        name="bulk_archive",
    )


async def cb_bulk_mute(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    await q.edit_message_text(
        "🔕 **كتم جماعي**\n\n"
        "سيتم كتم إشعارات كل المحادثات في جميع الحسابات.",
        reply_markup=_kb_confirm("bulk_mute_confirm", "adm_bulk_changes"),
    )


async def cb_bulk_mute_confirm(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    await q.edit_message_text("⏳ جاري الكتم...")
    asyncio.create_task(
        _bulk_mute_task(q.message, q.from_user.id),
        name="bulk_mute",
    )


async def cb_bulk_del_photos(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    await q.edit_message_text(
        "🗑️ **حذف الصور القديمة — جماعي**\n\n"
        "سيتم حذف كل صور البروفايل القديمة من جميع الحسابات.",
        reply_markup=_kb_confirm("bulk_del_photos_confirm", "adm_bulk_changes"),
    )


async def cb_bulk_del_photos_confirm(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    await q.edit_message_text("⏳ جاري حذف الصور القديمة...")
    asyncio.create_task(
        _bulk_del_photos_task(q.message, q.from_user.id),
        name="bulk_del_photos",
    )


# ==============================================================================
# Callback handlers - Tools
# ==============================================================================

async def cb_tool_generate_usernames(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    user_sessions[q.from_user.id] = {"step": "generate_usernames_count"}
    await q.edit_message_text(
        "🔤 **توليد يوزرنيمات**\n\n"
        "كم عدد اليوزرنيمات المطلوب توليدها؟\n"
        "(أرسل رقم بين 1 و 500)",
        reply_markup=_kb_back("adm_tools"),
    )


async def cb_tool_username_stats(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    total, available = db_get_username_count()
    await q.edit_message_text(
        f"📊 **إحصائيات اليوزرنيمات**\n\n"
        f"📦 الإجمالي: {total}\n"
        f"✅ المتاح: {available}\n"
        f"🔒 المستخدم: {total - available}",
        reply_markup=_kb_back("adm_tools"),
    )


async def cb_tool_photo_stats(_, q: CallbackQuery) -> None:
    if not is_any_admin(q.from_user.id):
        return
    used_count = db_get_used_photos_count()
    await q.edit_message_text(
        f"🖼️ **إحصائيات الصور**\n\n"
        f"📸 المستخدمة: {used_count}",
        reply_markup=_kb_back("adm_tools"),
    )


# ==============================================================================
# Background tasks
# ==============================================================================

async def _leave_all_chats_task(reply_msg: Message, account: Row, chat_type: ChatType, admin_id: int) -> None:
    phone = account["phone"]
    left = failed = 0
    tmp = None
    type_label = "القنوات" if chat_type == ChatType.CHANNEL else "الجروبات"

    try:
        tmp = await _account_client(account, f"leave_all_{chat_type.value}")

        async for dialog in tmp.get_dialogs():
            if is_in_sleep_mode(phone):
                break
            
            ct = dialog.chat.type
            should_leave = False
            if chat_type == ChatType.CHANNEL and ct == ChatType.CHANNEL:
                should_leave = True
            elif chat_type == ChatType.GROUP and ct in (ChatType.GROUP, ChatType.SUPERGROUP):
                should_leave = True

            if should_leave:
                if not check_rate_limit(phone):
                    await asyncio.sleep(60)
                    continue
                
                try:
                    await smart_delay()
                    await tmp.leave_chat(dialog.chat.id)
                    record_action(phone)
                    left += 1
                except FloodWait as exc:
                    await asyncio.sleep(exc.value)
                except Exception:
                    failed += 1

        await reply_msg.reply(
            f"✅ **تمت مغادرة {type_label}**\n\n"
            f"الحساب: `{phone}`\n"
            f"تمت المغادرة: {left}\n"
            f"فشل: {failed}"
        )
        db_add_audit_log(admin_id, f"Leave All {type_label}", f"{phone}: {left} ok / {failed} failed")

    except Exception as exc:
        log.error("Leave all chats error (%s): %s", phone, exc)
        await reply_msg.reply(f"❌ خطأ في الحساب `{phone}`: {str(exc)[:60]}")
    finally:
        await disconnect(tmp)


async def _bulk_set_2fa_task(reply_msg: Message, password: str, admin_id: int) -> None:
    accounts = db_get_all_accounts(active_only=True)
    success = failed = skipped = 0

    for account in accounts:
        phone = account["phone"]
        tmp = None
        try:
            tmp = await _account_client(account, "bulk_2fa")
            pwd_info = await tmp.invoke(raw_account.GetPassword())
            if getattr(pwd_info, "has_password", False):
                skipped += 1
            else:
                await tmp.enable_cloud_password(password, hint="")
                success += 1
                db_add_account_history(phone, "2fa_enabled", None, "bulk", admin_id)
        except Exception as exc:
            log.error("Bulk 2FA error (%s): %s", phone, exc)
            failed += 1
        finally:
            await disconnect(tmp)
            await asyncio.sleep(0.5)

    await reply_msg.reply(
        f"✅ **نتيجة تطبيق 2FA الجماعي**\n\n"
        f"تم التفعيل: {success}\n"
        f"لديه 2FA مسبقاً: {skipped}\n"
        f"فشل: {failed}"
    )
    db_add_audit_log(admin_id, "Bulk Set 2FA", f"{success} ok / {failed} failed / {skipped} skipped")


async def _bulk_leave_all_chats_task(reply_msg: Message, chat_type: ChatType, admin_id: int) -> None:
    accounts = db_get_all_accounts(active_only=True)
    total_left = 0
    total_fail = 0
    type_label = "القنوات" if chat_type == ChatType.CHANNEL else "الجروبات"

    for account in accounts:
        phone = account["phone"]
        tmp = None
        try:
            tmp = await _account_client(account, f"bulk_leave_{chat_type.value}")

            async for dialog in tmp.get_dialogs():
                ct = dialog.chat.type
                should_leave = False
                if chat_type == ChatType.CHANNEL and ct == ChatType.CHANNEL:
                    should_leave = True
                elif chat_type == ChatType.GROUP and ct in (ChatType.GROUP, ChatType.SUPERGROUP):
                    should_leave = True

                if should_leave:
                    try:
                        await smart_delay()
                        await tmp.leave_chat(dialog.chat.id)
                        total_left += 1
                    except FloodWait as exc:
                        await asyncio.sleep(exc.value)
                    except Exception:
                        total_fail += 1

        except Exception as exc:
            log.error("Bulk leave all chats error (%s): %s", phone, exc)
        finally:
            await disconnect(tmp)
            await asyncio.sleep(1)

    await reply_msg.reply(
        f"✅ **نتيجة مغادرة {type_label} الجماعية**\n\n"
        f"إجمالي ما تم مغادرته: {total_left}\n"
        f"فشل: {total_fail}"
    )
    db_add_audit_log(admin_id, f"Bulk Leave {type_label}", f"{total_left} left / {total_fail} failed")


async def _bulk_random_names_task(reply_msg: Message, admin_id: int, smart_mode: bool = True) -> None:
    """
    Change names for all accounts.
    If smart_mode=True, analyzes profile photo to determine appropriate gender for name.
    """
    accounts = db_get_all_accounts(active_only=True)
    success = failed = 0

    for account in accounts:
        phone = account["phone"]
        tmp = None
        try:
            if not check_rate_limit(phone):
                await asyncio.sleep(30)
            
            tmp = await _account_client(account, "bulk_names")
            
            old_me = await tmp.get_me()
            old_name = f"{old_me.first_name or ''} {old_me.last_name or ''}".strip()
            
            if smart_mode:
                # Use AI to detect photo gender and generate matching name
                first, last = await generate_smart_name_for_photo(account, tmp)
            else:
                first, last = generate_random_name("mixed")
            
            await smart_delay()
            await tmp.update_profile(first_name=first, last_name=last)
            record_action(phone)
            
            new_name = f"{first} {last}".strip()
            db_add_account_history(phone, "name_change", old_name, new_name, admin_id)
            success += 1
            log.info("Changed name for %s: %s -> %s", phone, old_name, new_name)
        except Exception as exc:
            log.error("Bulk name change error (%s): %s", phone, exc)
            failed += 1
        finally:
            await disconnect(tmp)
            await asyncio.sleep(0.5)

    await reply_msg.reply(
        f"✅ **نتيجة تغيير الأسماء العشوائي**\n\n"
        f"تم التغيير: {success}\n"
        f"فشل: {failed}"
    )
    db_add_audit_log(admin_id, "Bulk Random Names", f"{success} ok / {failed} failed")


async def _bulk_usernames_task(reply_msg: Message, admin_id: int) -> None:
    accounts = db_get_all_accounts(active_only=True)
    success = failed = no_username = 0

    for account in accounts:
        phone = account["phone"]
        tmp = None
        try:
            username = db_get_available_username()
            if not username:
                generated = await generate_available_usernames(1)
                username = generated[0] if generated else None
            
            if not username:
                no_username += 1
                continue

            tmp = await _account_client(account, "bulk_usernames")
            
            old_me = await tmp.get_me()
            old_username = old_me.username or ""
            
            await smart_delay()
            await tmp.set_username(username)
            db_mark_username_used(username)
            record_action(phone)
            
            db_add_account_history(phone, "username_change", old_username, username, admin_id)
            success += 1
        except (UsernameOccupied, UsernameInvalid, UsernameNotModified) as exc:
            log.warning("Username error (%s): %s", phone, exc)
            failed += 1
        except Exception as exc:
            log.error("Bulk username error (%s): %s", phone, exc)
            failed += 1
        finally:
            await disconnect(tmp)
            await asyncio.sleep(1)

    await reply_msg.reply(
        f"✅ **نتيجة تغيير اليوزرنيمات**\n\n"
        f"تم التغيير: {success}\n"
        f"فشل: {failed}\n"
        f"لا يوجد يوزرنيم متاح: {no_username}"
    )
    db_add_audit_log(admin_id, "Bulk Usernames", f"{success} ok / {failed} failed")


async def _bulk_bios_task(reply_msg: Message, admin_id: int) -> None:
    accounts = db_get_all_accounts(active_only=True)
    success = failed = 0

    for account in accounts:
        phone = account["phone"]
        tmp = None
        try:
            bio = await generate_bio_with_ai("arabic")
            tmp = await _account_client(account, "bulk_bios")
            
            await smart_delay()
            await tmp.update_profile(bio=bio)
            record_action(phone)
            
            db_add_account_history(phone, "bio_change", None, bio[:50], admin_id)
            success += 1
        except Exception as exc:
            log.error("Bulk bio error (%s): %s", phone, exc)
            failed += 1
        finally:
            await disconnect(tmp)
            await asyncio.sleep(1)

    await reply_msg.reply(
        f"✅ **نتيجة تغيير الأوصاف (AI)**\n\n"
        f"تم التغيير: {success}\n"
        f"فشل: {failed}"
    )
    db_add_audit_log(admin_id, "Bulk AI Bios", f"{success} ok / {failed} failed")


async def _bulk_photos_task(reply_msg: Message, admin_id: int, smart_mode: bool = True) -> None:
    """
    Change photos for all accounts.
    If smart_mode=True, selects photo based on account name gender.
    """
    accounts = db_get_all_accounts(active_only=True)
    success = failed = no_photo = 0

    for account in accounts:
        phone = account["phone"]
        tmp = None
        try:
            tmp = await _account_client(account, "bulk_photos")
            
            if smart_mode:
                # Get photo matching the account's name gender
                photo_url = await get_smart_photo_for_name(account, tmp)
            else:
                photo_url = await get_unused_photo()
            
            if not photo_url:
                no_photo += 1
                continue

            photo_data = await download_photo(photo_url)
            if not photo_data:
                failed += 1
                continue
            
            await smart_delay()
            await tmp.set_profile_photo(photo=io.BytesIO(photo_data))
            db_mark_photo_used(photo_url, phone)
            record_action(phone)
            
            db_add_account_history(phone, "photo_change", None, "github_smart", admin_id)
            success += 1
            log.info("Changed photo for %s (smart mode: %s)", phone, smart_mode)
        except Exception as exc:
            log.error("Bulk photo error (%s): %s", phone, exc)
            failed += 1
        finally:
            await disconnect(tmp)
            await asyncio.sleep(1)

    await reply_msg.reply(
        f"✅ **نتيجة تغيير الصور**\n\n"
        f"تم التغيير: {success}\n"
        f"فشل: {failed}\n"
        f"لا توجد صور متاحة: {no_photo}"
    )
    db_add_audit_log(admin_id, "Bulk Photos", f"{success} ok / {failed} failed")


async def _bulk_archive_task(reply_msg: Message, admin_id: int) -> None:
    accounts = db_get_all_accounts(active_only=True)
    total_archived = 0

    for account in accounts:
        phone = account["phone"]
        tmp = None
        try:
            tmp = await _account_client(account, "bulk_archive")
            count = await archive_all_chats(tmp)
            total_archived += count
        except Exception as exc:
            log.error("Bulk archive error (%s): %s", phone, exc)
        finally:
            await disconnect(tmp)
            await asyncio.sleep(1)

    await reply_msg.reply(
        f"✅ **نتيجة الأرشفة الجماعية**\n\n"
        f"إجمالي المحادثات المؤرشفة: {total_archived}"
    )
    db_add_audit_log(admin_id, "Bulk Archive", f"{total_archived} archived")


async def _bulk_mute_task(reply_msg: Message, admin_id: int) -> None:
    accounts = db_get_all_accounts(active_only=True)
    total_muted = 0

    for account in accounts:
        phone = account["phone"]
        tmp = None
        try:
            tmp = await _account_client(account, "bulk_mute")
            count = await mute_all_chats(tmp)
            total_muted += count
        except Exception as exc:
            log.error("Bulk mute error (%s): %s", phone, exc)
        finally:
            await disconnect(tmp)
            await asyncio.sleep(1)

    await reply_msg.reply(
        f"✅ **نتيجة الكتم الجماعي**\n\n"
        f"إجمالي المحادثات المكتومة: {total_muted}"
    )
    db_add_audit_log(admin_id, "Bulk Mute", f"{total_muted} muted")


async def _bulk_del_photos_task(reply_msg: Message, admin_id: int) -> None:
    accounts = db_get_all_accounts(active_only=True)
    total_deleted = 0

    for account in accounts:
        phone = account["phone"]
        tmp = None
        try:
            tmp = await _account_client(account, "bulk_del_photos")
            count = await remove_old_profile_photos(tmp)
            total_deleted += count
        except Exception as exc:
            log.error("Bulk del photos error (%s): %s", phone, exc)
        finally:
            await disconnect(tmp)
            await asyncio.sleep(1)

    await reply_msg.reply(
        f"✅ **نتيجة حذف الصور القديمة**\n\n"
        f"إجمالي الصور المحذوفة: {total_deleted}"
    )
    db_add_audit_log(admin_id, "Bulk Delete Photos", f"{total_deleted} deleted")


async def _bulk_delete_old_messages_task(reply_msg: Message, days: int, admin_id: int) -> None:
    accounts = db_get_all_accounts(active_only=True)
    total_deleted = 0

    for account in accounts:
        phone = account["phone"]
        tmp = None
        try:
            tmp = await _account_client(account, "bulk_del_msgs")
            count = await delete_old_messages(tmp, days)
            total_deleted += count
        except Exception as exc:
            log.error("Bulk del msgs error (%s): %s", phone, exc)
        finally:
            await disconnect(tmp)
            await asyncio.sleep(1)

    await reply_msg.reply(
        f"✅ **نتيجة حذف الرسائل القديمة**\n\n"
        f"إجمالي الرسائل المحذوفة: {total_deleted}"
    )
    db_add_audit_log(admin_id, "Bulk Delete Old Messages", f"{total_deleted} deleted")


async def _generate_usernames_task(reply_msg: Message, count: int, admin_id: int) -> None:
    try:
        usernames = await generate_available_usernames(count)
        await reply_msg.reply(
            f"✅ **تم توليد اليوزرنيمات**\n\n"
            f"المطلوب: {count}\n"
            f"تم توليده: {len(usernames)}\n\n"
            f"أمثلة: {', '.join(usernames[:5]) if usernames else 'لا يوجد'}"
        )
        db_add_audit_log(admin_id, "Generate Usernames", f"{len(usernames)} generated")
    except Exception as exc:
        log.error("Username generation error: %s", exc)
        await reply_msg.reply(f"❌ خطأ في توليد اليوزرنيمات: {str(exc)[:60]}")


# ==============================================================================
# Background loops
# ==============================================================================

async def _captcha_cleanup_task() -> None:
    while True:
        try:
            now = datetime.now()
            expired = [
                uid for uid, (_, ts) in captcha_cache.items()
                if (now - ts).total_seconds() > CAPTCHA_TTL_SECONDS
            ]
            for uid in expired:
                del captcha_cache[uid]
        except Exception as exc:
            log.error("Captcha cleanup error: %s", exc)
        await asyncio.sleep(60)


async def _auto_terminate_task() -> None:
    while True:
        try:
            if is_auto_terminate_enabled():
                for account in db_get_pending_terminate():
                    phone = account["phone"]
                    ss = account["session_string"]
                    vlock = validation_lock(ss)

                    async with vlock:
                        if _active_temp_clients.get(ss) is not None:
                            continue
                        tmp = None
                        try:
                            async with session_lock(account["id"]):
                                tmp = await _account_client(account, "auto_term")
                                _active_temp_clients[ss] = tmp
                                await tmp.terminate_other_sessions()
                                db_set_pending_terminate(phone, False)
                                log.info("Auto-terminated sessions for %s", phone)
                        except (RPCError, asyncio.TimeoutError) as exc:
                            if "FRESH_RESET_AUTHORISATION_FORBIDDEN" not in str(exc):
                                db_set_pending_terminate(phone, False)
                        except Exception as exc:
                            log.error("Auto-terminate error (%s): %s", phone, exc)
                        finally:
                            _active_temp_clients[ss] = None
                            await disconnect(tmp)
        except Exception as exc:
            log.error("Auto-terminate loop error: %s", exc)
        await asyncio.sleep(AUTO_TERMINATE_INTERVAL)


async def _health_monitor_task() -> None:
    """Periodic health monitoring for all accounts."""
    while True:
        try:
            if is_health_monitoring():
                accounts = db_get_all_accounts(active_only=True)
                critical_count = 0
                
                for account in accounts:
                    phone = account["phone"]
                    try:
                        score, risk = await check_account_health(account)
                        db_update_account_health(phone, score, risk)
                        
                        if risk == "critical":
                            critical_count += 1
                            # Alert admin
                            try:
                                await bot.send_message(
                                    ADMIN_ID,
                                    f"🚨 **تنبيه صحة الحساب**\n\n"
                                    f"📱 {phone}\n"
                                    f"💊 الصحة: {score}%\n"
                                    f"⚠️ الخطر: {risk}"
                                )
                            except Exception:
                                pass
                        
                    except Exception as e:
                        log.error("Health check error (%s): %s", phone, e)
                    
                    await asyncio.sleep(2)
                
                # Auto-trigger emergency if too many critical
                if critical_count >= 3 and setting("emergency_mode_auto") == "1":
                    trigger_emergency_mode(f"{critical_count} critical accounts detected")
                    try:
                        await bot.send_message(
                            ADMIN_ID,
                            f"🚨 **وضع الطوارئ التلقائي**\n\n"
                            f"تم تفعيله بسبب {critical_count} حسابات حرجة"
                        )
                    except Exception:
                        pass
                        
        except Exception as exc:
            log.error("Health monitor error: %s", exc)
        
        await asyncio.sleep(HEALTH_CHECK_INTERVAL_MINUTES * 60)


async def _auto_backup_task() -> None:
    """Periodic auto-backup."""
    while True:
        try:
            if is_auto_backup_enabled():
                filename = await create_backup(encrypted=True)
                log.info("Auto-backup created: %s", filename)
                
                try:
                    await bot.send_message(
                        ADMIN_ID,
                        f"💾 **نسخة احتياطية تلقائية**\n\n📁 {filename}"
                    )
                except Exception:
                    pass
                    
        except Exception as exc:
            log.error("Auto-backup error: %s", exc)
        
        await asyncio.sleep(AUTO_BACKUP_INTERVAL_HOURS * 3600)


async def _photo_rotation_task() -> None:
    """Rotate profile photos based on schedules."""
    while True:
        try:
            rotations = db_get_photo_rotations(active_only=True)
            
            for rotation in rotations:
                phone = rotation["phone"]
                photos = json.loads(rotation["photos"])
                interval = rotation["interval_hours"]
                current_idx = rotation["current_index"]
                last_rotated = rotation["last_rotated"]
                
                should_rotate = False
                if not last_rotated:
                    should_rotate = True
                else:
                    try:
                        last_dt = datetime.fromisoformat(last_rotated)
                        if (datetime.now() - last_dt).total_seconds() >= interval * 3600:
                            should_rotate = True
                    except:
                        should_rotate = True
                
                if should_rotate and photos:
                    account = db_get_account(phone)
                    if account:
                        tmp = None
                        try:
                            next_idx = (current_idx + 1) % len(photos)
                            photo_url = photos[next_idx]
                            
                            photo_data = await download_photo(photo_url)
                            if photo_data:
                                tmp = await _account_client(account, "photo_rotate")
                                await tmp.set_profile_photo(photo=io.BytesIO(photo_data))
                                db_update_photo_rotation(rotation["id"], next_idx)
                                log.info("Rotated photo for %s", phone)
                        except Exception as e:
                            log.error("Photo rotation error (%s): %s", phone, e)
                        finally:
                            await disconnect(tmp)
                
                await asyncio.sleep(1)
                
        except Exception as exc:
            log.error("Photo rotation task error: %s", exc)
        
        await asyncio.sleep(300)  # Check every 5 minutes


async def _cloner_task() -> None:
    running: dict[str, asyncio.Task] = {}

    async def _batch(source: str, dest: str, client: Client) -> None:
        try:
            last_id = db_get_cloner_checkpoint(source, dest)
            newest_seen = last_id

            async for m in client.get_chat_history(source, limit=20):
                if m.id <= last_id:
                    break
                newest_seen = max(newest_seen, m.id)

                try:
                    await client.forward_messages(dest, source, [m.id])
                except UserBannedInChannel:
                    log.warning("Banned in %s — stopping clone", dest)
                    return
                except FloodWait as exc:
                    log.warning("FloodWait %ss during clone", exc.value)
                    await asyncio.sleep(exc.value)
                except Exception as exc:
                    s = str(exc).lower()
                    if "protected" in s or "restricted" in s:
                        await _reupload(client, m, dest)
                    else:
                        log.debug("Clone forward error: %s", exc)

            if newest_seen > last_id:
                db_set_cloner_checkpoint(source, dest, newest_seen)

        except Exception as exc:
            log.error("Cloner batch error: %s", exc)

    while True:
        try:
            with db_connect() as conn:
                cfg = conn.execute("SELECT * FROM cloner_config WHERE id=1").fetchone()

            if cfg and cfg["active"] and cfg["source"] and cfg["destination"]:
                client = any_background_client()
                key = f"{cfg['source']}::{cfg['destination']}"
                if client and (key not in running or running[key].done()):
                    running[key] = asyncio.create_task(
                        _batch(cfg["source"], cfg["destination"], client)
                    )
        except Exception as exc:
            log.error("Cloner scheduler error: %s", exc)

        await asyncio.sleep(60)


async def _reupload(client: Client, msg: Message, dest: str) -> None:
    try:
        caption = msg.caption or msg.text or ""
        if msg.photo or msg.video or msg.document or msg.voice:
            raw = await client.download_media(msg, in_memory=True)
            data = bytes(raw) if isinstance(raw, (bytes, bytearray)) else raw
            buf = io.BytesIO(data) if isinstance(data, (bytes, bytearray)) else data

            if msg.photo:
                await client.send_photo(dest, buf, caption=caption)
            elif msg.video:
                await client.send_video(dest, buf, caption=caption)
            elif msg.document:
                await client.send_document(dest, buf, caption=caption)
            elif msg.voice:
                await client.send_voice(dest, buf)
        elif msg.text:
            await client.send_message(dest, msg.text)

        log.info("Re-uploaded message to %s", dest)
    except Exception as exc:
        log.error("Re-upload failed: %s", exc)


# ==============================================================================
# Session management
# ==============================================================================

async def load_all_sessions() -> None:
    accounts = db_get_all_accounts(active_only=True)

    async def _load(acc: Row) -> None:
        try:
            client = await _account_client(acc, "account")
            background_clients[acc["phone"]] = client
            log.info("Session loaded: %s", acc["phone"])
        except asyncio.TimeoutError:
            log.warning("Timeout loading session: %s", acc["phone"])
        except Exception as exc:
            log.error("Failed to load session %s: %s", acc["phone"], exc)

    await asyncio.gather(*(_load(acc) for acc in accounts), return_exceptions=True)


async def shutdown() -> None:
    log.info("Shutting down...")

    for task in (auto_terminate_task, cloner_task, health_monitor_task):
        if task and not task.done():
            task.cancel()

    if scheduler:
        scheduler.shutdown()

    for phone, client in background_clients.items():
        try:
            if client.is_connected:
                await client.disconnect()
        except Exception as exc:
            log.error("Disconnect error (%s): %s", phone, exc)

    if bot and bot.is_connected:
        await bot.stop()
        log.info("Bot stopped.")


# ==============================================================================
# Entrypoint
# ==============================================================================

async def main() -> None:
    global bot, scheduler, cloner_task, auto_terminate_task, health_monitor_task

    if not BOT_TOKEN or "ضع" in BOT_TOKEN:
        raise SystemExit("❌ ضع BOT_TOKEN الصحيح في قسم Configuration")
    if ADMIN_ID == 0:
        raise SystemExit("❌ ضع ADMIN_ID الصحيح في قسم Configuration")

    db_init()
    log.info("Starting bot v9.1.0 | Admin: %d", ADMIN_ID)

    bot = Client(
        "manager_bot",
        api_id=API_ID, api_hash=API_HASH,
        bot_token=BOT_TOKEN, in_memory=True,
    )

    # Message handlers
    bot.on_message(filters.command(["start", "help"]) & filters.private)(cmd_start)
    bot.on_message(filters.command("cancel") & filters.private)(cmd_cancel)
    bot.on_message(filters.command("addaccount") & filters.private)(cmd_addaccount)
    bot.on_message(
        filters.private & filters.document
        & filters.create(lambda _, __, m: is_any_admin(m.from_user.id))
    )(handle_doc)
    bot.on_message(
        filters.private & filters.photo
        & filters.create(lambda _, __, m: is_any_admin(m.from_user.id))
    )(handle_photo)
    bot.on_message(filters.private & filters.text)(text_router)

    # User menu callbacks
    bot.on_callback_query(filters.regex(r"^menu_main$"))(cb_menu_main)
    bot.on_callback_query(filters.regex(r"^menu_smm$"))(cb_menu_smm)
    bot.on_callback_query(filters.regex(r"^menu_balance$"))(cb_menu_balance)
    bot.on_callback_query(filters.regex(r"^menu_referral$"))(cb_menu_referral)
    bot.on_callback_query(filters.regex(r"^menu_info$"))(cb_menu_info)
    bot.on_callback_query(filters.regex(r"^menu_vip_info$"))(cb_menu_vip_info)
    bot.on_callback_query(filters.regex(r"^menu_sell_account$"))(cb_menu_sell_account)
    bot.on_callback_query(filters.regex(r"^sell_account_confirm$"))(cb_sell_account_confirm)
    bot.on_callback_query(filters.regex(r"^act_"))(cb_act_start)

    # Admin panel callbacks
    bot.on_callback_query(filters.regex(r"^adm_main$"))(cb_adm_main)
    bot.on_callback_query(filters.regex(r"^adm_accounts$"))(cb_adm_accounts)
    bot.on_callback_query(filters.regex(r"^adm_add_account$"))(cb_adm_add_account)
    bot.on_callback_query(filters.regex(r"^adm_analytics$"))(cb_adm_analytics)
    bot.on_callback_query(filters.regex(r"^analytics_overview$"))(cb_analytics_overview)
    bot.on_callback_query(filters.regex(r"^analytics_health$"))(cb_analytics_health)
    bot.on_callback_query(filters.regex(r"^adm_health_check$"))(cb_adm_health_check)
    bot.on_callback_query(filters.regex(r"^adm_automation$"))(cb_adm_automation)
    bot.on_callback_query(filters.regex(r"^auto_reply$"))(cb_auto_reply)
    bot.on_callback_query(filters.regex(r"^auto_reply_add$"))(cb_auto_reply_add)
    bot.on_callback_query(filters.regex(r"^auto_sleep$"))(cb_auto_sleep)
    bot.on_callback_query(filters.regex(r"^auto_sleep_add$"))(cb_auto_sleep_add)
    bot.on_callback_query(filters.regex(r"^adm_chat_mgmt$"))(cb_adm_chat_mgmt)
    bot.on_callback_query(filters.regex(r"^chat_delete_old$"))(cb_chat_delete_old)
    bot.on_callback_query(filters.regex(r"^adm_protection$"))(cb_adm_protection)
    bot.on_callback_query(filters.regex(r"^prot_toggle_antiban$"))(cb_prot_toggle_antiban)
    bot.on_callback_query(filters.regex(r"^prot_toggle_human$"))(cb_prot_toggle_human)
    bot.on_callback_query(filters.regex(r"^prot_toggle_health$"))(cb_prot_toggle_health)
    bot.on_callback_query(filters.regex(r"^prot_rate_status$"))(cb_prot_rate_status)
    bot.on_callback_query(filters.regex(r"^adm_emergency$"))(cb_adm_emergency)
    bot.on_callback_query(filters.regex(r"^adm_backup$"))(cb_adm_backup)
    bot.on_callback_query(filters.regex(r"^backup_create$"))(cb_backup_create)
    bot.on_callback_query(filters.regex(r"^backup_list$"))(cb_backup_list)
    bot.on_callback_query(filters.regex(r"^backup_toggle_auto$"))(cb_backup_toggle_auto)
    bot.on_callback_query(filters.regex(r"^adm_templates$"))(cb_adm_templates)
    bot.on_callback_query(filters.regex(r"^tmpl_create$"))(cb_tmpl_create)
    bot.on_callback_query(filters.regex(r"^tmpl_list$"))(cb_tmpl_list)
    bot.on_callback_query(filters.regex(r"^adm_broadcast$"))(cb_adm_broadcast)
    bot.on_callback_query(filters.regex(r"^adm_dm$"))(cb_adm_dm)
    bot.on_callback_query(filters.regex(r"^adm_ban$"))(cb_adm_ban)
    bot.on_callback_query(filters.regex(r"^adm_unban$"))(cb_adm_unban)
    bot.on_callback_query(filters.regex(r"^adm_grant_vip$"))(cb_adm_grant_vip)
    bot.on_callback_query(filters.regex(r"^adm_adjust_points$"))(cb_adm_adjust_points)
    bot.on_callback_query(filters.regex(r"^adm_import_info$"))(cb_adm_import_info)
    bot.on_callback_query(filters.regex(r"^adm_delegated$"))(cb_adm_delegated)
    bot.on_callback_query(filters.regex(r"^adm_cloner_panel$"))(cb_adm_cloner_panel)
    bot.on_callback_query(filters.regex(r"^cloner_setup$"))(cb_cloner_setup)
    bot.on_callback_query(filters.regex(r"^cloner_toggle$"))(cb_cloner_toggle)
    bot.on_callback_query(filters.regex(r"^adm_tools$"))(cb_adm_tools)
    bot.on_callback_query(filters.regex(r"^adm_toggle_forced$"))(cb_toggle_forced)
    bot.on_callback_query(filters.regex(r"^adm_toggle_public$"))(cb_toggle_public)
    bot.on_callback_query(filters.regex(r"^adm_toggle_points$"))(cb_toggle_points)
    bot.on_callback_query(filters.regex(r"^adm_toggle_auto_terminate$"))(cb_toggle_auto_terminate)

    # Individual account control callbacks
    bot.on_callback_query(filters.regex(r"^adm_account_list:\d+$"))(cb_adm_account_list)
    bot.on_callback_query(filters.regex(r"^account_control:.+$"))(cb_account_control)
    bot.on_callback_query(filters.regex(r"^acct_set_name:.+$"))(cb_acct_set_name)
    bot.on_callback_query(filters.regex(r"^acct_set_name_manual:.+$"))(cb_acct_set_name_manual)
    bot.on_callback_query(filters.regex(r"^acct_set_name_smart:.+$"))(cb_acct_set_name_smart)
    bot.on_callback_query(filters.regex(r"^acct_set_username:.+$"))(cb_acct_set_username)
    bot.on_callback_query(filters.regex(r"^acct_set_bio:.+$"))(cb_acct_set_bio)
    bot.on_callback_query(filters.regex(r"^acct_set_photo:.+$"))(cb_acct_set_photo)
    bot.on_callback_query(filters.regex(r"^acct_set_photo_upload:.+$"))(cb_acct_set_photo_upload)
    bot.on_callback_query(filters.regex(r"^acct_set_photo_smart:.+$"))(cb_acct_set_photo_smart)
    bot.on_callback_query(filters.regex(r"^acct_leave_chat:.+$"))(cb_acct_leave_chat)
    bot.on_callback_query(filters.regex(r"^acct_stats:.+$"))(cb_acct_stats)
    bot.on_callback_query(filters.regex(r"^acct_history:.+$"))(cb_acct_history)
    bot.on_callback_query(filters.regex(r"^acct_archive:.+$"))(cb_acct_archive)
    bot.on_callback_query(filters.regex(r"^acct_mute_all:.+$"))(cb_acct_mute_all)
    bot.on_callback_query(filters.regex(r"^acct_del_photos:.+$"))(cb_acct_del_photos)
    bot.on_callback_query(filters.regex(r"^acct_leave_channels:.+$"))(cb_acct_leave_channels)
    bot.on_callback_query(filters.regex(r"^acct_leave_channels_confirm:.+$"))(cb_acct_leave_channels_confirm)
    bot.on_callback_query(filters.regex(r"^acct_leave_groups:.+$"))(cb_acct_leave_groups)
    bot.on_callback_query(filters.regex(r"^acct_leave_groups_confirm:.+$"))(cb_acct_leave_groups_confirm)
    bot.on_callback_query(filters.regex(r"^acct_set_2fa:.+$"))(cb_acct_set_2fa)

    # Bulk operation callbacks
    bot.on_callback_query(filters.regex(r"^adm_bulk_changes$"))(cb_adm_bulk_changes)
    bot.on_callback_query(filters.regex(r"^bulk_random_names$"))(cb_bulk_random_names)
    bot.on_callback_query(filters.regex(r"^bulk_random_names_smart$"))(cb_bulk_random_names_smart)
    bot.on_callback_query(filters.regex(r"^bulk_random_names_random$"))(cb_bulk_random_names_random)
    bot.on_callback_query(filters.regex(r"^bulk_usernames$"))(cb_bulk_usernames)
    bot.on_callback_query(filters.regex(r"^bulk_usernames_confirm$"))(cb_bulk_usernames_confirm)
    bot.on_callback_query(filters.regex(r"^bulk_bios$"))(cb_bulk_bios)
    bot.on_callback_query(filters.regex(r"^bulk_bios_confirm$"))(cb_bulk_bios_confirm)
    bot.on_callback_query(filters.regex(r"^bulk_photos$"))(cb_bulk_photos)
    bot.on_callback_query(filters.regex(r"^bulk_photos_smart$"))(cb_bulk_photos_smart)
    bot.on_callback_query(filters.regex(r"^bulk_photos_random$"))(cb_bulk_photos_random)
    bot.on_callback_query(filters.regex(r"^bulk_set_2fa$"))(cb_bulk_set_2fa)
    bot.on_callback_query(filters.regex(r"^bulk_leave_channels$"))(cb_bulk_leave_channels)
    bot.on_callback_query(filters.regex(r"^bulk_leave_channels_confirm$"))(cb_bulk_leave_channels_confirm)
    bot.on_callback_query(filters.regex(r"^bulk_leave_groups$"))(cb_bulk_leave_groups)
    bot.on_callback_query(filters.regex(r"^bulk_leave_groups_confirm$"))(cb_bulk_leave_groups_confirm)
    bot.on_callback_query(filters.regex(r"^bulk_archive$"))(cb_bulk_archive)
    bot.on_callback_query(filters.regex(r"^bulk_archive_confirm$"))(cb_bulk_archive_confirm)
    bot.on_callback_query(filters.regex(r"^bulk_mute$"))(cb_bulk_mute)
    bot.on_callback_query(filters.regex(r"^bulk_mute_confirm$"))(cb_bulk_mute_confirm)
    bot.on_callback_query(filters.regex(r"^bulk_del_photos$"))(cb_bulk_del_photos)
    bot.on_callback_query(filters.regex(r"^bulk_del_photos_confirm$"))(cb_bulk_del_photos_confirm)

    # Tools callbacks
    bot.on_callback_query(filters.regex(r"^tool_generate_usernames$"))(cb_tool_generate_usernames)
    bot.on_callback_query(filters.regex(r"^tool_username_stats$"))(cb_tool_username_stats)
    bot.on_callback_query(filters.regex(r"^tool_photo_stats$"))(cb_tool_photo_stats)

    # Misc callbacks
    bot.on_callback_query(filters.regex(r"^cancel_wizard$"))(cb_cancel_wizard)
    bot.on_callback_query(filters.regex(r"^noop$"))(cb_noop)

    # Start bot
    await bot.start()
    me = await bot.get_me()
    log.info("Bot online: @%s (ID: %d)", me.username, me.id)

    # Start background tasks
    asyncio.create_task(load_all_sessions(), name="load_sessions")
    asyncio.create_task(_captcha_cleanup_task(), name="captcha_cleanup")
    auto_terminate_task = asyncio.create_task(_auto_terminate_task(), name="auto_terminate")
    cloner_task = asyncio.create_task(_cloner_task(), name="cloner")
    health_monitor_task = asyncio.create_task(_health_monitor_task(), name="health_monitor")
    asyncio.create_task(_auto_backup_task(), name="auto_backup")
    asyncio.create_task(_photo_rotation_task(), name="photo_rotation")

    log.info("All systems running — v9.1.0")

    loop = asyncio.get_event_loop()

    def _on_signal() -> None:
        log.info("Shutdown signal received.")
        asyncio.create_task(shutdown())

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _on_signal)
        except NotImplementedError:
            pass

    await idle()
    await shutdown()


if __name__ == "__main__":
    asyncio.run(main())
