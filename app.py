import streamlit as st
import sqlite3
from datetime import datetime
import base64
import secrets
from PIL import Image, ImageDraw, ImageFont
import os
import io

# -------------------------------
# Quick local DB wiring
# -------------------------------
DB_PATH = "serveloop.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

# Create tables if they don't exist yet — simple, no-migrations approach
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    email TEXT PRIMARY KEY,
    password TEXT,
    name TEXT,
    age INTEGER,
    gender TEXT,
    bio TEXT DEFAULT '',
    total_hours INTEGER DEFAULT 0,
    is_organizer BOOLEAN DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    description TEXT,
    location TEXT,
    category TEXT,
    date TEXT,
    media_url TEXT,
    qr_token TEXT UNIQUE,
    host_email TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT,
    event_id INTEGER,
    checked_in BOOLEAN DEFAULT 0,
    hours INTEGER DEFAULT 0,
    joined_at TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS proofs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant_id INTEGER,
    media_url TEXT,
    caption TEXT,
    verified BOOLEAN DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# -------------------------------
# Minimal session-state defaults
# -------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "page" not in st.session_state:
    st.session_state.page = "Login"

# -------------------------------
# Small utility helpers
# -------------------------------
def upload_media_stub(file):
    """Return a data URL so images show in the UI.
    Replace with cloud upload in production."""
    if file is None:
        return ""
    data = file.read()
    b64 = base64.b64encode(data).decode()
    mime = file.type if hasattr(file, "type") else "image/jpeg"
    return f"data:{mime};base64,{b64}"

def generate_qr_token(length=16):
    """Tiny token generator for check-ins (keeps things simple)."""
    return secrets.token_urlsafe(length)[:length]

def safe_rerun():
    """Try to rerun the Streamlit script. Fall back to toggling a session flag if unavailable."""
    try:
        # preferred, available in modern Streamlit
        st.experimental_rerun()
    except Exception:
        # fallback (some Streamlit builds might not expose experimental_rerun)
        st.session_state["_needs_rerun"] = not st.session_state.get("_needs_rerun", False)

# -------------------------------
# New helper: certificate generator (returns bytes of PNG)
# -------------------------------
def generate_certificate_png(user_name: str, event_title: str, hours: int, verified_on: str) -> bytes:
    """Creates a simple certificate PNG in memory and returns bytes.
    Tries to load static/font.ttf for a nicer look; falls back to default font."""
    W, H = 1200, 800
    bg = (245, 245, 250)  # soft background
    title_color = (20, 20, 60)
    accent = (30, 115, 190)

    img = Image.new("RGB", (W, H), color=bg)
    draw = ImageDraw.Draw(img)

    # Fonts - try loading custom font from static/font.ttf
    font_path = os.path.join(os.path.dirname(__file__), "static", "font.ttf")
    try:
        if os.path.exists(font_path):
            font_title = ImageFont.truetype(font_path, 56)
            font_name = ImageFont.truetype(font_path, 44)
            font_body = ImageFont.truetype(font_path, 28)
        else:
            raise FileNotFoundError
    except Exception:
        # fallback to default fonts
        font_title = ImageFont.load_default()
        font_name = ImageFont.load_default()
        font_body = ImageFont.load_default()

    # Draw header bar
    draw.rectangle([(0, 0), (W, 110)], fill=accent)
    draw.text((40, 24), "ServeLoop Certificate", font=font_title, fill=(255,255,255))

    # Recipient
    draw.text((80, 180), "This certifies that", font=font_body, fill=title_color)
    draw.text((80, 230), f"{user_name}", font=font_name, fill=title_color)

    # Event & hours
    draw.text((80, 320), f"has participated in:", font=font_body, fill=title_color)
    draw.text((80, 360), f"{event_title}", font=font_name, fill=title_color)
    draw.text((80, 440), f"Hours awarded: {hours}", font=font_body, fill=title_color)

    # Verified on
    draw.text((80, 520), f"Verified on: {verified_on}", font=font_body, fill=title_color)

    # Signature / footer
    draw.line([(80, 640), (420, 640)], fill=title_color, width=2)
    draw.text((80, 650), "Organizer signature", font=font_body, fill=title_color)
    draw.text((W-380, H-80), "ServeLoop", font=font_body, fill=accent)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()

# -------------------------------
# Sidebar and page selection
# -------------------------------
BASE_DIR = os.path.dirname(__file__)
logo_path = os.path.join(BASE_DIR, "static", "logo.png")

# show logo if present (no width param for sidebar image to avoid compatibility issues)
if os.path.exists(logo_path):
    try:
        logo_img = Image.open(logo_path)
        st.sidebar.image(logo_img)  # simple display in sidebar
    except Exception:
        st.sidebar.write("Logo found but couldn't open it.")
else:
    st.sidebar.write("")  # keep sidebar tidy when logo missing

# show pages depending on whether the user is logged in and if they're an organizer
if st.session_state.logged_in:
    # attempt to read organizer flag defensively
    try:
        cursor.execute("SELECT is_organizer FROM users WHERE email=?", (st.session_state.user_email,))
        res = cursor.fetchone()
        is_org = bool(res[0]) if res and res[0] is not None else False
    except Exception:
        is_org = False

    pages = ["Home", "Discover", "My Events", "ServePass", "Profile", "Contact"]
    if is_org:
        pages.insert(1, "Create Event")
        pages.append("Verify")

    page = st.sidebar.radio("Navigate", pages)
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_email = None
        st.success("You have been logged out")
        safe_rerun()
else:
    page = st.sidebar.radio("Navigate", ["Login", "Register"])

# -------------------------------
# LOGIN
# -------------------------------
if page == "Login":
    st.title("🔐 Login to ServeLoop")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = cursor.fetchone()
        if user:
            st.session_state.logged_in = True
            st.session_state.user_email = email
            safe_rerun()
        else:
            st.error("Invalid email or password")

# -------------------------------
# REGISTER
# -------------------------------
elif page == "Register":
    st.title("📝 Register for ServeLoop")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    name = st.text_input("Full Name")
    age = st.number_input("Age", min_value=1, max_value=120, step=1)
    gender = st.selectbox("Gender", ["Male", "Female", "Prefer not to say"])
    register_as_org = st.checkbox("Register as Organizer")

    if st.button("Register"):
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        if cursor.fetchone():
            st.error("Email already exists. Try another.")
        else:
            is_org_flag = 1 if register_as_org else 0
            cursor.execute(
                "INSERT INTO users (email, password, name, age, gender, is_organizer) VALUES (?, ?, ?, ?, ?, ?)",
                (email, password, name, age, gender, is_org_flag)
            )
            conn.commit()
            st.session_state.logged_in = True
            st.session_state.user_email = email
            if register_as_org:
                st.success("Registered as Organizer successfully!")
            else:
                st.success("Registered as Volunteer successfully!")
            safe_rerun()

# -------------------------------
# HOME - upcoming events + leaderboard
# -------------------------------
elif page == "Home":
    st.title("🏠 ServeLoop - Discover Impact Events")
    st.subheader("Upcoming Events")
    cursor.execute("SELECT * FROM events ORDER BY date ASC LIMIT 10")
    events = cursor.fetchall()
    for e in events:
        st.markdown(f"**{e[1]}** — {e[5]}")
        if e[6]:  # media_url
            # modern Streamlit uses use_container_width
            try:
                st.image(e[6], use_container_width=True)
            except TypeError:
                # fallback for older versions
                st.image(e[6])
        if st.session_state.logged_in and st.button(f"Join {e[1]}", key=f"join_{e[0]}"):
            cursor.execute("SELECT * FROM participants WHERE user_email=? AND event_id=?", (st.session_state.user_email, e[0]))
            if cursor.fetchone():
                st.info("Already joined")
            else:
                cursor.execute("INSERT INTO participants (user_email, event_id) VALUES (?, ?)", (st.session_state.user_email, e[0]))
                conn.commit()
                st.success("Joined event! You can upload proof after attending.")

    st.markdown("---")
    st.subheader("Leaderboard — Top Contributors")
    # Fetch top contributors
    cursor.execute("SELECT name, email, COALESCE(total_hours,0) as hrs FROM users ORDER BY hrs DESC LIMIT 10")
    top_users = cursor.fetchall()
    if not top_users:
        st.info("No contributors yet — participate in events to appear on the leaderboard.")
    else:
        leaderboard = []
        for idx, u in enumerate(top_users, start=1):
            name, email, hrs = u
            if idx == 1:
                medal = "🥇"
            elif idx == 2:
                medal = "🥈"
            elif idx == 3:
                medal = "🥉"
            else:
                medal = f"{idx}."
            leaderboard.append({"rank": medal, "name": name or email, "hours": hrs})
        st.table(leaderboard)

# -------------------------------
# CREATE EVENT (organizer only)
# -------------------------------
elif page == "Create Event":
    if not st.session_state.logged_in:
        st.warning("Please login to request or create events.")
    else:
        # organizer request table (harmless if already created)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS organizer_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            message TEXT,
            requested_at TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending'
        )
        """)
        conn.commit()

        cursor.execute("SELECT is_organizer FROM users WHERE email=?", (st.session_state.user_email,))
        res = cursor.fetchone()
        is_org = bool(res[0]) if res and res[0] is not None else False

        if not is_org:
            st.title("📝 Create Event — Organizer Access Required")
            st.info("Only organizer accounts can create events. Request access below or ask an admin to grant it.")
            with st.expander("How to become an organizer"):
                st.markdown("""
                - Organizers can create/manage events and verify proofs.  
                - Admin approval is required for production apps.  
                - For this prototype: request access and an admin can approve.
                """)
            req_msg = st.text_area("Optional message to admin (why you should be an organizer)", max_chars=500)
            if st.button("Request Organizer Access"):
                cursor.execute("SELECT id FROM organizer_requests WHERE email=? AND status='pending'", (st.session_state.user_email,))
                if cursor.fetchone():
                    st.warning("You already have a pending organizer request.")
                else:
                    cursor.execute(
                        "INSERT INTO organizer_requests (email, message) VALUES (?, ?)",
                        (st.session_state.user_email, req_msg)
                    )
                    conn.commit()
                    st.success("Organizer request submitted.")
                    st.info("Admin can approve via SQL: `UPDATE users SET is_organizer=1 WHERE email=\"you@example.com\"`")
        else:
            st.title("📝 Create Event")
            title = st.text_input("Title")
            description = st.text_area("Description")
            category = st.selectbox("Category", ["Environment", "Health", "Education", "Community", "Other"])
            location = st.text_input("Location")
            date = st.date_input("Date")
            media = st.file_uploader("Poster / Image (optional)", type=["png", "jpg", "jpeg", "mp4"])

            if st.button("Create Event"):
                if not title:
                    st.error("Title is required.")
                else:
                    media_url = upload_media_stub(media) if media else ""
                    cursor.execute(
                        """INSERT INTO events (title, description, location, category, date, media_url, host_email)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (title, description, location, category, str(date), media_url, st.session_state.user_email)
                    )
                    conn.commit()
                    st.success("✅ Event created successfully!")
                    safe_rerun()

# -------------------------------
# DISCOVER
# -------------------------------
elif page == "Discover":
    st.title("🔍 Discover Events")
    search = st.text_input("Search by title or category")
    if search:
        cursor.execute("SELECT * FROM events WHERE title LIKE ? OR category LIKE ?", (f"%{search}%", f"%{search}%"))
    else:
        cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()
    for e in events:
        st.markdown(f"**{e[1]}** — {e[5]}")
        if e[6]:
            try:
                st.image(e[6], use_container_width=True)
            except TypeError:
                st.image(e[6])
        if st.session_state.logged_in and st.button(f"Join {e[1]}", key=f"discover_{e[0]}"):
            cursor.execute("SELECT * FROM participants WHERE user_email=? AND event_id=?", (st.session_state.user_email, e[0]))
            if cursor.fetchone():
                st.info("Already joined")
            else:
                cursor.execute("INSERT INTO participants (user_email, event_id) VALUES (?, ?)", (st.session_state.user_email, e[0]))
                conn.commit()
                st.success("Joined event! Upload proof after attending.")

# -------------------------------
# MY EVENTS — hosted & joined
# -------------------------------
if page == "My Events":
    if not st.session_state.logged_in:
        st.warning("Please login to see your events.")
    else:
        st.title("🎯 My Events & Proofs")
        user_email = st.session_state.user_email

        # organizer flag
        cursor.execute("SELECT is_organizer FROM users WHERE email=?", (user_email,))
        res = cursor.fetchone()
        is_org = bool(res[0]) if res else False

        # Hosted events for organizers
        if is_org:
            st.subheader("Hosted Events")
            cursor.execute("SELECT * FROM events WHERE host_email=?", (user_email,))
            hosted = cursor.fetchall()
            if hosted:
                for e in hosted:
                    st.markdown(f"**{e[1]}** — {e[5]}")  # title — date
                    st.write(e[2])  # description
                    col1, col2 = st.columns(2)
                    if col1.button(f"Terminate Event", key=f"terminate_{e[0]}"):
                        cursor.execute("DELETE FROM events WHERE id=?", (e[0],))
                        cursor.execute("DELETE FROM participants WHERE event_id=?", (e[0],))
                        cursor.execute("DELETE FROM proofs WHERE participant_id IN (SELECT id FROM participants WHERE event_id=?)", (e[0],))
                        conn.commit()
                        st.success(f"Event '{e[1]}' terminated successfully!")
                        safe_rerun()
            else:
                st.info("You have not hosted any events yet.")

        # Joined events for everyone
        st.subheader("Joined Events")
        cursor.execute("SELECT * FROM participants WHERE user_email=?", (user_email,))
        participants = cursor.fetchall()
        if participants:
            for p in participants:
                cursor.execute("SELECT * FROM events WHERE id=?", (p[2],))
                ev = cursor.fetchone()
                st.markdown(f"**{ev[1]}** — Checked in: {p[3]} — Hours: {p[4]}")
                col1, col2 = st.columns(2)

                if col1.button(f"Unregister", key=f"unreg_{p[0]}"):
                    cursor.execute("DELETE FROM participants WHERE id=?", (p[0],))
                    conn.commit()
                    st.success(f"You have unregistered from '{ev[1]}'")
                    safe_rerun()

                # Upload proof (if not already checked in)
                if not p[3]:
                    proof_file = col2.file_uploader(f"Upload Proof for '{ev[1]}'", type=["png","jpg","jpeg","mp4"], key=f"proof_{p[0]}")
                    caption = col2.text_input("Caption", max_chars=200, key=f"caption_{p[0]}")
                    if col2.button("Submit Proof", key=f"submit_proof_{p[0]}"):
                        if proof_file:
                            media_url = upload_media_stub(proof_file)
                            cursor.execute(
                                "INSERT INTO proofs (participant_id, media_url, caption) VALUES (?, ?, ?)",
                                (p[0], media_url, caption)
                            )
                            conn.commit()
                            st.success("Proof submitted! It will be verified by the organizer.")
                            safe_rerun()
        else:
            st.info("You have not joined any events yet.")

# -------------------------------
# SERVEPASS (gamified & exportable)
# -------------------------------
elif page == "ServePass":
    if not st.session_state.logged_in:
        st.warning("Login to see your ServePass")
    else:
        user_email = st.session_state.user_email

        try:
            cursor.execute("SELECT COALESCE(total_hours,0) FROM users WHERE email=?", (user_email,))
            total_hours = int(cursor.fetchone()[0] or 0)
        except Exception:
            total_hours = 0

        cursor.execute("""
            SELECT e.title, e.date, e.media_url, p.hours, p.joined_at, e.location, e.category, e.id
            FROM participants p
            JOIN events e ON p.event_id = e.id
            WHERE p.user_email = ? AND p.checked_in = 1
            ORDER BY p.joined_at DESC
        """, (user_email,))
        completed = cursor.fetchall()

        # --- Leaderboard rank for current user (new badge)
        cursor.execute("SELECT email FROM users ORDER BY COALESCE(total_hours,0) DESC")
        ordered = [r[0] for r in cursor.fetchall()]
        user_rank = None
        if user_email in ordered:
            user_rank = ordered.index(user_email) + 1

        st.title("🏅 Your ServePass")
        if user_rank:
            if user_rank == 1:
                rank_html = f"<span style='font-size:18px;padding:6px 10px;border-radius:8px;background:#FFD700;color:#000;font-weight:700'>Rank #{user_rank} 🥇</span>"
            elif user_rank == 2:
                rank_html = f"<span style='font-size:18px;padding:6px 10px;border-radius:8px;background:#C0C0C0;color:#000;font-weight:700'>Rank #{user_rank} 🥈</span>"
            elif user_rank == 3:
                rank_html = f"<span style='font-size:18px;padding:6px 10px;border-radius:8px;background:#cd7f32;color:#fff;font-weight:700'>Rank #{user_rank} 🥉</span>"
            else:
                rank_html = f"<span style='font-size:16px;padding:5px 8px;border-radius:6px;background:#eef3ff;color:#000'>Rank #{user_rank}</span>"
            st.markdown(rank_html, unsafe_allow_html=True)

        st.markdown("A snapshot of your verified volunteering history — achievements, milestones and event details.")

        m1, m2, m3 = st.columns(3)
        m1.metric("Completed Events", len(completed))
        m2.metric("Total Hours", f"{total_hours}")
        recent_date = completed[0][4].split(" ")[0] if completed else "—"
        m3.metric("Last Verified", recent_date)

        st.markdown("---")

        milestones = [(1, "Bronze Contributor", "🟫"), (20, "Silver Contributor", "🥈"),
                      (50, "Gold Contributor", "🥇"), (100, "Platinum Contributor", "🏆")]
        next_m = None
        for thresh, name, emoji in milestones:
            if total_hours < thresh:
                next_m = (thresh, name, emoji)
                break
        if not next_m:
            st.success(f"🎉 You are a top contributor — {total_hours} total hours! 🏆")
        else:
            thresh, name, emoji = next_m
            pct = min(100, int((total_hours / thresh) * 100)) if thresh else 0
            st.subheader("Achievements & Progress")
            st.markdown(f"**Current total:** {total_hours} hrs — Next milestone: **{name}** ({thresh} hrs) {emoji}")
            st.progress(pct)

        st.markdown("---")

        badge_html = ""
        if total_hours >= 100:
            badge_html = "<div style='padding:10px;background:#f7f0ff;border-radius:10px;display:inline-block'><h3 style='margin:0'>🏆 Platinum Contributor</h3><small>100+ hours</small></div>"
        elif total_hours >= 50:
            badge_html = "<div style='padding:10px;background:#fff8e6;border-radius:10px;display:inline-block'><h3 style='margin:0'>🥇 Gold Contributor</h3><small>50+ hours</small></div>"
        elif total_hours >= 20:
            badge_html = "<div style='padding:10px;background:#f0f6ff;border-radius:10px;display:inline-block'><h3 style='margin:0'>🥈 Silver Contributor</h3><small>20+ hours</small></div>"
        elif total_hours >= 1:
            badge_html = "<div style='padding:10px;background:#fff2ed;border-radius:10px;display:inline-block'><h3 style='margin:0'>🟫 Bronze Contributor</h3><small>1+ hour</small></div>"
        else:
            badge_html = "<div style='padding:10px;background:#f5f5f5;border-radius:10px;display:inline-block'><h3 style='margin:0'>No badges yet</h3><small>Start contributing!</small></div>"

        st.markdown(badge_html, unsafe_allow_html=True)
        st.markdown("---")

        # CSV export
        import io, csv
        csv_buffer = io.StringIO()
        csv_writer = csv.writer(csv_buffer)
        csv_writer.writerow(["Event Title", "Date", "Location", "Category", "Hours Awarded", "Verified On"])
        for row in completed:
            title, date, media_url, phours, joined_at, location, category, eid = row
            csv_writer.writerow([title or "", date or "", location or "", category or "", phours or 0, joined_at or ""])
        csv_data = csv_buffer.getvalue().encode("utf-8")
        st.download_button("📥 Download ServePass (CSV)", data=csv_data, file_name="servepass.csv", mime="text/csv")

        st.markdown("---")

        if not completed:
            st.info("You don't have any verified/completed events yet. Join events and submit proof to get verified hours!")
        else:
            for idx, row in enumerate(completed, start=1):
                title, date, media_url, phours, joined_at, location, category, eid = row
                phours = int(phours or 0)
                date_str = str(date) if date else (joined_at.split(" ")[0] if joined_at else "Date not set")

                with st.container():
                    left, right = st.columns([1, 3], gap="small")
                    with left:
                        if media_url:
                            try:
                                st.image(media_url, width=150)
                            except Exception:
                                st.markdown("<div style='width:150px;height:90px;background:#efefef;border-radius:8px;display:flex;align-items:center;justify-content:center;color:#888'>No preview</div>", unsafe_allow_html=True)
                        else:
                            st.markdown("<div style='width:150px;height:90px;background:#efefef;border-radius:8px;display:flex;align-items:center;justify-content:center;color:#888'>No preview</div>", unsafe_allow_html=True)

                    with right:
                        st.markdown(f"### {title or 'Untitled Event'}")
                        st.markdown(f"**Category:** {category or '—'}    •    **Location:** {location or '—'}")
                        st.markdown(f"**Date:** {date_str}")
                        st.markdown(f"**Hours awarded:** **{phours}**")
                        st.markdown(f"**Verified on:** {joined_at.split(' ')[0] if joined_at else '—'}")

                        if phours >= 8:
                            st.markdown("<span style='background:#FFD700;padding:6px 10px;border-radius:8px;color:#000;font-weight:700'>Major Contribution</span>", unsafe_allow_html=True)
                        elif phours >= 4:
                            st.markdown("<span style='background:#C0C0C0;padding:6px 10px;border-radius:8px;color:#000;font-weight:700'>Strong Contribution</span>", unsafe_allow_html=True)
                        elif phours > 0:
                            st.markdown("<span style='background:#CD7F32;padding:6px 10px;border-radius:8px;color:#fff;font-weight:700'>Contributed</span>", unsafe_allow_html=True)

                        # Certificate download button (generates PNG on demand)
                        cert_name = cursor.execute("SELECT name FROM users WHERE email=?", (user_email,)).fetchone()
                        user_name_display = cert_name[0] if cert_name and cert_name[0] else user_email
                        cert_bytes = generate_certificate_png(user_name_display, title or "Event", phours, (joined_at.split(" ")[0] if joined_at else str(datetime.now().date())))
                        st.download_button(f"🎓 Download Certificate", data=cert_bytes, file_name=f"certificate_{user_name_display.replace(' ','_')}_{eid}.png", mime="image/png")

                    st.markdown("")  # small spacer
                    st.markdown("***")  # divider between cards

# -------------------------------
# VERIFY - organizer awards hours
# -------------------------------
elif page == "Verify":
    if not st.session_state.logged_in:
        st.warning("Organizer login required")
    else:
        cursor.execute("PRAGMA table_info(users)")
        user_cols = [r[1] for r in cursor.fetchall()]
        if "is_organizer" in user_cols:
            cursor.execute("SELECT is_organizer FROM users WHERE email=?", (st.session_state.user_email,))
            r = cursor.fetchone()
            is_org = bool(r[0]) if r and r[0] is not None else False
        else:
            cursor.execute("SELECT role FROM users WHERE email=?", (st.session_state.user_email,))
            r = cursor.fetchone()
            is_org = (r and r[0] == "organizer")

        if not is_org:
            st.warning("Organizer login required")
            st.stop()

        st.title("✔️ Verification Panel")

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='proofs'")
        if not cursor.fetchone():
            st.info("No proofs table found. Nothing to verify.")
            st.stop()

        cursor.execute("PRAGMA table_info(participants)")
        pcol_meta = cursor.fetchall()
        pcol_names = [c[1] for c in pcol_meta]

        # Only fetch proofs for events hosted by this organizer
        cursor.execute("""
            SELECT p.id, p.participant_id, p.media_url, p.caption, p.verified, p.created_at
            FROM proofs p
            JOIN participants pa ON p.participant_id = pa.id
            JOIN events e ON pa.event_id = e.id
            WHERE p.verified = 0 AND e.host_email = ?
            ORDER BY p.created_at DESC
        """, (st.session_state.user_email,))
        proofs = cursor.fetchall()

        if not proofs:
            st.info("No unverified proofs for your events right now.")
            st.stop()

        for proof in proofs:
            proof_id, participant_id, media_url, caption, verified_flag, created_at = proof[:6]

            cursor.execute("SELECT * FROM participants WHERE id=?", (participant_id,))
            part = cursor.fetchone()
            if not part:
                st.warning(f"Proof {proof_id} links to a missing participant (id={participant_id}).")
                continue

            p_info = {}
            for idx, col_name in enumerate(pcol_names):
                p_info[col_name] = part[idx] if idx < len(part) else None

            ev_id = p_info.get("event_id")
            user_email_ref = p_info.get("user_email")
            user_id_ref = p_info.get("user_id")

            event_title = "Unknown Event"
            if ev_id:
                cursor.execute("SELECT title FROM events WHERE id=?", (ev_id,))
                ev_row = cursor.fetchone()
                if ev_row:
                    event_title = ev_row[0]

            user_display = "Unknown User"
            if user_email_ref:
                cursor.execute("SELECT name, email, COALESCE(total_hours,0) FROM users WHERE email=?", (user_email_ref,))
                u = cursor.fetchone()
                if u:
                    user_display = f"{u[0]} ({u[1]})"
                    user_total_hours = u[2]
                else:
                    user_display = user_email_ref
                    user_total_hours = 0
            elif user_id_ref:
                cursor.execute("SELECT name, email, COALESCE(total_hours,0) FROM users WHERE id=?", (user_id_ref,))
                u = cursor.fetchone()
                if u:
                    user_display = f"{u[0]} ({u[1]})"
                    user_total_hours = u[2]
                else:
                    user_total_hours = 0
            else:
                user_total_hours = 0

            st.markdown(f"**Event:** {event_title} — **Volunteer:** {user_display}")
            if caption:
                st.write(f"Caption: {caption}")
            if media_url:
                try:
                    st.image(media_url, use_container_width=True)
                except TypeError:
                    st.image(media_url)

            col1, col2 = st.columns([2, 1])
            with col1:
                award_hours = st.number_input("Hours to award", min_value=0, value=1, step=1, key=f"award_hours_{proof_id}")
            with col2:
                if st.button("Verify", key=f"verify_{proof_id}"):
                    cursor.execute("UPDATE proofs SET verified=1 WHERE id=?", (proof_id,))

                    if "checked_in" in pcol_names:
                        cursor.execute("UPDATE participants SET checked_in=1 WHERE id=?", (participant_id,))
                    if "hours" in pcol_names:
                        cursor.execute("UPDATE participants SET hours=? WHERE id=?", (int(award_hours), participant_id))

                    if user_email_ref:
                        cursor.execute("UPDATE users SET total_hours = COALESCE(total_hours,0) + ? WHERE email=?", (int(award_hours), user_email_ref))
                    elif user_id_ref:
                        cursor.execute("UPDATE users SET total_hours = COALESCE(total_hours,0) + ? WHERE id=?", (int(award_hours), user_id_ref))

                    conn.commit()
                    st.success(f"Verified — awarded {int(award_hours)} hour(s). ServePass updated.")
                    safe_rerun()

            if st.button("Reject", key=f"reject_{proof_id}"):
                cursor.execute("DELETE FROM proofs WHERE id=?", (proof_id,))
                conn.commit()
                st.info("Proof rejected and removed.")
                safe_rerun()

# -------------------------------
# PROFILE
# -------------------------------
elif page == "Profile":
    if not st.session_state.logged_in:
        st.warning("Please login to view your profile")
    else:
        st.title("👤 Your Profile")
        cursor.execute("SELECT name, email, age, gender, bio, total_hours FROM users WHERE email=?",
                       (st.session_state.user_email,))
        user = cursor.fetchone()
        if user:
            name, email, age, gender, bio, total_hours = user
            st.write(f"**Name:** {name}")
            st.write(f"**Email:** {email}")
            st.write(f"**Age:** {age}")
            st.write(f"**Gender:** {gender}")
            st.write(f"**Total Hours:** {total_hours}")

            new_bio = st.text_area("Edit Bio", bio)
            if st.button("Update Bio"):
                cursor.execute("UPDATE users SET bio=? WHERE email=?", (new_bio, st.session_state.user_email))
                conn.commit()
                st.success("✅ Bio updated successfully!")

            if st.button("Delete Account"):
                confirm = st.checkbox("Confirm account deletion")
                if confirm:
                    cursor.execute("DELETE FROM users WHERE email=?", (st.session_state.user_email,))
                    cursor.execute("DELETE FROM participants WHERE user_email=?", (st.session_state.user_email,))
                    conn.commit()
                    st.session_state.logged_in = False
                    st.session_state.user_email = None
                    st.success("Account deleted successfully")
                    safe_rerun()

# -------------------------------
# CONTACT
# -------------------------------
elif page == "Contact":
    st.title("📬 Contact Us")
    name = st.text_input("Your Name")
    email = st.text_input("Your Email")
    message = st.text_area("Message", max_chars=1000)

    # ensure contact_messages table exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contact_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        message TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()

    if st.button("Send Message"):
        if name and email and message:
            cursor.execute("INSERT INTO contact_messages (name, email, message) VALUES (?, ?, ?)", (name, email, message))
            conn.commit()
            st.success("✅ Your message has been submitted. We'll get back to you soon!")
        else:
            st.error("Please fill in all fields.")
