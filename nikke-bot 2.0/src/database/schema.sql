-- ============================================================
-- NIKKE 装备管理机器人 v2.1.1 数据库 Schema
-- SQLite 3.35+
-- ============================================================

-- ------------------------------------------------------------
-- Schema 版本管理
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS schema_version (
    version   INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

-- ------------------------------------------------------------
-- 用户表
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    qq_id       TEXT PRIMARY KEY,
    nickname    TEXT    NOT NULL DEFAULT '',
    preferences TEXT    NOT NULL DEFAULT '{"version":1}',
    created_at  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL
);

-- ------------------------------------------------------------
-- 角色表
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS characters (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT    NOT NULL UNIQUE,
    aliases      TEXT    NOT NULL DEFAULT '[]',
    rarity       TEXT,
    element      TEXT,
    weapon_type  TEXT,
    burst_level  TEXT,
    manufacturer TEXT
);

CREATE INDEX IF NOT EXISTS idx_characters_name ON characters(name);

-- ------------------------------------------------------------
-- 装备模板表
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS equipment_templates (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT    NOT NULL,
    type         TEXT    NOT NULL CHECK (type IN ('attack', 'defense', 'support')),
    slot         TEXT    NOT NULL CHECK (slot IN ('head', 'body', 'arm', 'leg')),
    manufacturer TEXT    NOT NULL CHECK (manufacturer IN ('elysion', 'missilis', 'tetra', 'pilgrim', 'abnormal')),
    rarity       TEXT,
    icon_name    TEXT,
    UNIQUE (manufacturer, type, slot)
);

-- ------------------------------------------------------------
-- 装备实例表
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS equipments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id        TEXT    NOT NULL,
    template_id     INTEGER NOT NULL,
    character_id    INTEGER,
    name            TEXT    NOT NULL,
    type            TEXT    NOT NULL CHECK (type IN ('attack', 'defense', 'support')),
    slot            TEXT    NOT NULL CHECK (slot IN ('head', 'body', 'arm', 'leg')),
    manufacturer    TEXT    NOT NULL CHECK (manufacturer IN ('elysion', 'missilis', 'tetra', 'pilgrim', 'abnormal')),
    level           INTEGER NOT NULL DEFAULT 0 CHECK (level >= 0 AND level <= 5),
    screenshot_path TEXT,
    scope           TEXT    NOT NULL DEFAULT 'private' CHECK (scope IN ('private', 'group', 'public')),
    group_id        TEXT,
    is_locked       INTEGER NOT NULL DEFAULT 0 CHECK (is_locked IN (0, 1)),
    score           REAL,
    is_bis          INTEGER CHECK (is_bis IN (0, 1)),
    created_at      TEXT    NOT NULL,
    updated_at      TEXT    NOT NULL,

    FOREIGN KEY (owner_id)    REFERENCES users(qq_id)               ON DELETE CASCADE,
    FOREIGN KEY (template_id) REFERENCES equipment_templates(id)    ON DELETE RESTRICT,
    FOREIGN KEY (character_id) REFERENCES characters(id)            ON DELETE SET NULL,
    CHECK ((scope = 'group' AND group_id IS NOT NULL) OR (scope != 'group' AND group_id IS NULL))
);

CREATE INDEX IF NOT EXISTS idx_equipments_owner        ON equipments(owner_id);
CREATE INDEX IF NOT EXISTS idx_equipments_character    ON equipments(character_id);
CREATE INDEX IF NOT EXISTS idx_equipments_template     ON equipments(template_id);
CREATE INDEX IF NOT EXISTS idx_equipments_type         ON equipments(type);
CREATE INDEX IF NOT EXISTS idx_equipments_filter       ON equipments(manufacturer, type, slot);
CREATE INDEX IF NOT EXISTS idx_equipments_scope_group  ON equipments(scope, group_id);
CREATE INDEX IF NOT EXISTS idx_equipments_score        ON equipments(score);
CREATE INDEX IF NOT EXISTS idx_equipments_is_bis       ON equipments(is_bis);
CREATE INDEX IF NOT EXISTS idx_equipments_is_locked    ON equipments(is_locked);

-- ------------------------------------------------------------
-- 词条表
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS affixes (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id         INTEGER NOT NULL,
    name                 TEXT    NOT NULL,
    value                REAL    NOT NULL CHECK (value >= 0),
    quality              TEXT    NOT NULL CHECK (quality IN ('blue', 'purple', 'gold')),
    tier                 INTEGER NOT NULL CHECK (tier >= 1 AND tier <= 15),
    raw_name             TEXT,
    sort_order           INTEGER NOT NULL DEFAULT 0 CHECK (sort_order IN (0, 1, 2, 3)),
    tier_config_version  TEXT,

    FOREIGN KEY (equipment_id) REFERENCES equipments(id) ON DELETE CASCADE,
    UNIQUE (equipment_id, sort_order)
);

CREATE INDEX IF NOT EXISTS idx_affixes_equipment ON affixes(equipment_id);
CREATE INDEX IF NOT EXISTS idx_affixes_name      ON affixes(name);
CREATE INDEX IF NOT EXISTS idx_affixes_tier      ON affixes(tier);
CREATE INDEX IF NOT EXISTS idx_affixes_quality   ON affixes(quality);

-- ------------------------------------------------------------
-- OCR 识别记录表
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ocr_records (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id                TEXT,
    image_path             TEXT    NOT NULL,
    ocr_engine             TEXT    NOT NULL,
    raw_text               TEXT    NOT NULL,
    confidence             REAL    CHECK (confidence >= 0.0 AND confidence <= 1.0),
    parser_result          TEXT,
    is_success             INTEGER NOT NULL DEFAULT 0 CHECK (is_success IN (0, 1)),
    is_confirmed           INTEGER NOT NULL DEFAULT 0 CHECK (is_confirmed IN (0, 1)),
    confirmed_equipment_id INTEGER,
    error_message          TEXT,
    processing_time_ms     INTEGER CHECK (processing_time_ms >= 0),
    created_at             TEXT    NOT NULL,

    FOREIGN KEY (user_id)                REFERENCES users(qq_id)        ON DELETE SET NULL,
    FOREIGN KEY (confirmed_equipment_id) REFERENCES equipments(id)     ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_ocr_user    ON ocr_records(user_id);
CREATE INDEX IF NOT EXISTS idx_ocr_created ON ocr_records(created_at);
CREATE INDEX IF NOT EXISTS idx_ocr_engine  ON ocr_records(ocr_engine);

-- ------------------------------------------------------------
-- 操作日志表
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS operation_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT,
    action      TEXT    NOT NULL CHECK (action != ''),
    target_type TEXT    NOT NULL,
    target_id   INTEGER,
    detail      TEXT,
    created_at  TEXT    NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users(qq_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_oplog_user    ON operation_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_oplog_action  ON operation_logs(action);
CREATE INDEX IF NOT EXISTS idx_oplog_target  ON operation_logs(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_oplog_created ON operation_logs(created_at);
