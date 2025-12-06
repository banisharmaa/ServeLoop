# serveloop/database/models.py
"""
SQLAlchemy models for ServeLoop + small DB helpers.

Usage:
    from database.models import init_db, get_session, seed_demo_data
    init_db()
    db = get_session()
    seed_demo_data(db)

This file is intentionally dependency-light so it works in Streamlit quick demos
and hackathon environments. Move to a package-style layout later if needed.
"""

import os
from datetime import datetime, date, time
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Text,
    ForeignKey,
    Boolean,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.exc import IntegrityError

# DB URL can be supplied via environment; default to a local sqlite file
DB_URL = os.getenv("SERVELOOP_DB", "sqlite:///serveloop.db")

# Create engine with check_same_thread False for SQLite + Streamlit
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


# -------------------------
# Models
# -------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)
    bio = Column(Text, default="")
    total_hours = Column(Integer, default=0)
    is_organizer = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    participations = relationship("Participant", back_populates="user", cascade="all, delete-orphan")
    hosted_events = relationship("Event", back_populates="host", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User id={self.id} email={self.email} name={self.name}>"


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    location = Column(String, nullable=True)
    category = Column(String, nullable=True)
    date = Column(DateTime, nullable=True)
    media_url = Column(String, nullable=True)
    qr_token = Column(String, unique=True, nullable=True)
    host_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    participants = relationship("Participant", back_populates="event", cascade="all, delete-orphan")
    host = relationship("User", back_populates="hosted_events")

    def __repr__(self):
        return f"<Event id={self.id} title={self.title}>"


class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_id = Column(Integer, ForeignKey("events.id"))
    checked_in = Column(Boolean, default=False)
    hours = Column(Integer, default=0)
    joined_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="participations")
    event = relationship("Event", back_populates="participants")
    proofs = relationship("Proof", back_populates="participant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Participant id={self.id} user_id={self.user_id} event_id={self.event_id}>"


class Proof(Base):
    __tablename__ = "proofs"

    id = Column(Integer, primary_key=True)
    participant_id = Column(Integer, ForeignKey("participants.id"))
    media_url = Column(String, nullable=True)
    caption = Column(Text, default="")
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    participant = relationship("Participant", back_populates="proofs")

    def __repr__(self):
        return f"<Proof id={self.id} participant_id={self.participant_id} verified={self.verified}>"


# -------------------------
# DB helpers
# -------------------------
def init_db():
    """Create database tables."""
    Base.metadata.create_all(engine)


def get_session():
    """Return a new SQLAlchemy session (caller must close it)."""
    return SessionLocal()


# -------------------------
# Demo seed data
# -------------------------
def seed_demo_data(db=None, replace_existing=False):
    """
    Quickly populate the DB with demo users and events for hackathon demo.

    Args:
        db: optional SQLAlchemy session. If None, a session is created and closed.
        replace_existing: if True, attempt to drop and recreate tables (simple).
    """
    created_session = False
    if db is None:
        db = get_session()
        created_session = True

    if replace_existing:
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)

    # check if users already present
    existing = db.query(User).first()
    if existing:
        # do not double-seed unless explicitly requested with replace_existing
        if not replace_existing:
            print("DB already has data — skipping seed (set replace_existing=True to force).")
            if created_session:
                db.close()
            return

    # Create demo users
    alice = User(email="alice@example.com", name="Alice", bio="Volunteer and community leader", is_organizer=True)
    bob = User(email="bob@example.com", name="Bob", bio="Student volunteer")
    carol = User(email="carol@example.com", name="Carol", bio="Environment activist")

    db.add_all([alice, bob, carol])
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # reload existing users
        alice = db.query(User).filter_by(email="alice@example.com").first()
        bob = db.query(User).filter_by(email="bob@example.com").first()
        carol = db.query(User).filter_by(email="carol@example.com").first()

    # Create demo events
    from secrets import token_urlsafe

    ev1 = Event(
        title="Beach Cleanup Drive",
        description="Community beach cleanup with local volunteers. Bring gloves and reusable water bottle.",
        location="Marina Beach",
        category="Environment",
        date=datetime.combine(date.today(), time(hour=9)),
        media_url="",
        qr_token=token_urlsafe(12),
        host_id=alice.id,
    )

    ev2 = Event(
        title="Free Health Checkup Camp",
        description="Basic health screening for elderly residents. Blood pressure, sugar checks, and counselling.",
        location="Community Hall, Block A",
        category="Health",
        date=datetime.combine(date.today(), time(hour=10)),
        media_url="",
        qr_token=token_urlsafe(12),
        host_id=alice.id,
    )

    db.add_all([ev1, ev2])
    db.commit()

    # Let Bob join event 1
    part_bob = Participant(user_id=bob.id, event_id=ev1.id, checked_in=False, hours=0)
    db.add(part_bob)
    db.commit()

    # Add a sample proof (unverified)
    proof = Proof(participant_id=part_bob.id, media_url="", caption="Photo of collected plastic bags", verified=False)
    db.add(proof)
    db.commit()

    print("Seeded demo data: users, events, participant, and proof.")

    if created_session:
        db.close()


# -------------------------
# Run standalone for quick dev
# -------------------------
if __name__ == "__main__":
    print("Initializing DB and seeding demo data (for local dev).")
    init_db()
    s = get_session()
    seed_demo_data(s, replace_existing=False)
    s.close()
