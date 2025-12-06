-- -------------------------------
-- SQL schema for ServeLoop (SQLite)
-- -------------------------------

-- Drop existing tables if they exist
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS participants;
DROP TABLE IF EXISTS proofs;
DROP TABLE IF EXISTS badges;
DROP TABLE IF EXISTS contact_messages;

-- -------------------------------
-- Users Table
-- -------------------------------
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    age INTEGER,
    gender TEXT,
    role TEXT CHECK(role IN ('organizer','volunteer')) NOT NULL DEFAULT 'volunteer',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------
-- Events Table
-- -------------------------------
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    date TEXT,
    location TEXT,
    media_url TEXT,
    organizer_id INTEGER,
    qr_token TEXT UNIQUE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organizer_id) REFERENCES users(id)
);

-- -------------------------------
-- Participants Table
-- -------------------------------
CREATE TABLE participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    event_id INTEGER NOT NULL,
    verified BOOLEAN DEFAULT 0,
    hours INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (event_id) REFERENCES events(id)
);

-- -------------------------------
-- Proofs Table
-- -------------------------------
CREATE TABLE proofs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant_id INTEGER NOT NULL,
    media_url TEXT,
    caption TEXT,
    verified BOOLEAN DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (participant_id) REFERENCES participants(id)
);

-- -------------------------------
-- Badges Table
-- -------------------------------
CREATE TABLE badges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    badge_name TEXT NOT NULL,
    badge_url TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- -------------------------------
-- Contact Messages Table
-- -------------------------------
CREATE TABLE contact_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    message TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
