"""
Pre-Resort Booking System
--------------------------
A single-file Streamlit + SQLite web application that lets guests browse
resort room types, submit a booking request with automatic price
calculation, and lets managers review every stored reservation.

Run with:
    streamlit run app.py
"""

import re
import sqlite3
from datetime import date, timedelta

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DB_FILE = "resort_bookings.db"

# Simple demo passcode for the manager dashboard. This is NOT secure and is
# only meant to keep the raw guest data behind one extra click during a demo.
# See README.md for notes on hardening this before any real-world use.
ADMIN_PASSCODE = "resort2026"

ROOM_TYPES = {
    "Deluxe Room": {
        "price": 120.0,
        "capacity": 2,
        "tagline": "Comfortable & bright",
        "description": (
            "A cozy, well-appointed room with a garden view, a plush queen "
            "bed, and a private balcony — perfect for couples or solo "
            "travelers who want comfort without the frills."
        ),
        "amenities": ["Garden view", "Queen bed", "Free Wi-Fi", "Mini fridge"],
        "accent": "#1B6B65",
    },
    "Oceanfront Suite": {
        "price": 250.0,
        "capacity": 4,
        "tagline": "Wake up to the waves",
        "description": (
            "A spacious suite with floor-to-ceiling windows facing the "
            "ocean, a separate sitting area, and a walk-out terrace — "
            "ideal for families or anyone who wants the sea close by."
        ),
        "amenities": ["Ocean view", "King bed + sofa bed", "Private terrace", "Rain shower"],
        "accent": "#0F3D3E",
    },
    "Luxury Villa": {
        "price": 480.0,
        "capacity": 6,
        "tagline": "The whole resort, to yourself",
        "description": (
            "A standalone villa with a private plunge pool, an outdoor "
            "dining pavilion, and dedicated butler service — the resort's "
            "most exclusive stay for groups and special occasions."
        ),
        "amenities": ["Private pool", "Butler service", "Outdoor pavilion", "3 bedrooms"],
        "accent": "#D4A017",
    },
}


# ---------------------------------------------------------------------------
# Database layer
# ---------------------------------------------------------------------------

def get_connection() -> sqlite3.Connection:
    """Open a fresh SQLite connection. Opening a new connection per call
    keeps this safe across Streamlit's script reruns/threads."""
    return sqlite3.connect(DB_FILE)


def init_db() -> None:
    """Create the bookings table if it doesn't already exist."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name       TEXT NOT NULL,
                email           TEXT NOT NULL,
                phone           TEXT NOT NULL,
                room_type       TEXT NOT NULL,
                check_in        TEXT NOT NULL,
                check_out       TEXT NOT NULL,
                guests          INTEGER NOT NULL,
                nights          INTEGER NOT NULL,
                price_per_night REAL NOT NULL,
                total_price     REAL NOT NULL,
                booked_on       TEXT NOT NULL
            )
            """
        )
        conn.commit()


def insert_booking(booking: dict) -> int:
    """Insert one booking row and return its new row id."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO bookings
                (full_name, email, phone, room_type, check_in, check_out,
                 guests, nights, price_per_night, total_price, booked_on)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                booking["full_name"],
                booking["email"],
                booking["phone"],
                booking["room_type"],
                booking["check_in"],
                booking["check_out"],
                booking["guests"],
                booking["nights"],
                booking["price_per_night"],
                booking["total_price"],
                booking["booked_on"],
            ),
        )
        conn.commit()
        return cursor.lastrowid


def fetch_all_bookings() -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query(
            "SELECT * FROM bookings ORDER BY id DESC", conn
        )


def delete_booking(booking_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
        conn.commit()


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_booking(name, email, phone, check_in, check_out, guests, capacity):
    """Return a list of human-readable error strings; empty list = valid."""
    errors = []

    if not name or not name.strip():
        errors.append("Full name is required.")

    if not email or not EMAIL_PATTERN.match(email.strip()):
        errors.append("Please enter a valid email address.")

    digits_only = re.sub(r"\D", "", phone or "")
    if len(digits_only) < 7:
        errors.append("Please enter a valid phone number.")

    if check_out <= check_in:
        errors.append("Check-out date must be after the check-in date.")

    if guests < 1:
        errors.append("Number of guests must be at least 1.")
    elif guests > capacity:
        errors.append(
            f"This room type sleeps up to {capacity} guest(s). "
            "Choose a larger room or reduce the guest count."
        )

    return errors


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------

def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Manrope:wght@400;500;600;700&display=swap');

        html, body, [class*="css"]  {
            font-family: 'Manrope', sans-serif;
        }

        h1, h2, h3, .hero-title {
            font-family: 'Fraunces', serif !important;
        }

        .hero-banner {
            background: linear-gradient(120deg, #0F3D3E 0%, #1B6B65 65%, #14514D 100%);
            padding: 2.4rem 2rem;
            border-radius: 14px;
            color: #F3E9D2;
            margin-bottom: 1.6rem;
        }
        .hero-title {
            font-size: 2.3rem;
            font-weight: 700;
            margin: 0 0 0.35rem 0;
            color: #F3E9D2;
        }
        .hero-subtitle {
            font-size: 1.02rem;
            opacity: 0.88;
            margin: 0;
        }

        .room-card {
            border: 1px solid #E7E0CC;
            border-radius: 12px;
            padding: 1.1rem 1.2rem 1.3rem 1.2rem;
            background: #FFFDF8;
            height: 100%;
        }
        .room-badge {
            display: inline-block;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            padding: 0.18rem 0.55rem;
            border-radius: 999px;
            color: #FFFDF8;
            margin-bottom: 0.6rem;
        }
        .room-name {
            font-family: 'Fraunces', serif;
            font-size: 1.28rem;
            font-weight: 600;
            margin: 0 0 0.1rem 0;
            color: #1C2321;
        }
        .room-tagline {
            font-size: 0.86rem;
            color: #6B6355;
            margin-bottom: 0.7rem;
        }
        .room-price {
            font-size: 1.6rem;
            font-weight: 700;
            color: #1C2321;
        }
        .room-price span {
            font-size: 0.82rem;
            font-weight: 500;
            color: #6B6355;
        }
        .room-desc {
            font-size: 0.88rem;
            color: #3B3730;
            margin: 0.55rem 0 0.7rem 0;
            line-height: 1.45;
        }
        .room-amenities {
            font-size: 0.8rem;
            color: #4A4638;
            margin: 0;
            padding-left: 1.1rem;
        }
        .room-amenities li {
            margin-bottom: 0.15rem;
        }

        .price-summary {
            background: #F3E9D2;
            border-radius: 10px;
            padding: 0.9rem 1.1rem;
            margin: 0.4rem 0 0.6rem 0;
            font-size: 0.95rem;
            color: #1C2321;
        }

        .section-label {
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #1B6B65;
            margin-bottom: 0.15rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def room_card_html(name: str, room: dict) -> str:
    amenities_html = "".join(f"<li>{item}</li>" for item in room["amenities"])
    return f"""
    <div class="room-card">
        <span class="room-badge" style="background:{room['accent']};">{name}</span>
        <div class="room-tagline">{room['tagline']}</div>
        <div class="room-price">${room['price']:.0f} <span>/ night</span></div>
        <p class="room-desc">{room['description']}</p>
        <ul class="room-amenities">{amenities_html}</ul>
    </div>
    """


# ---------------------------------------------------------------------------
# Page sections
# ---------------------------------------------------------------------------

def render_hero() -> None:
    st.markdown(
        """
        <div class="hero-banner">
            <div class="hero-title">Palm & Tide Resort</div>
            <p class="hero-subtitle">Reserve your room — Deluxe comfort, oceanfront views,
            or a private villa, all in one place.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_room_gallery() -> None:
    st.markdown('<div class="section-label">Room Types</div>', unsafe_allow_html=True)
    st.markdown("### Choose the stay that fits your trip")

    cols = st.columns(3)
    for col, (name, room) in zip(cols, ROOM_TYPES.items()):
        with col:
            st.markdown(room_card_html(name, room), unsafe_allow_html=True)
            st.write("")
            if st.button(f"Select {name}", key=f"select_{name}", use_container_width=True):
                st.session_state["preselected_room"] = name


def render_booking_form() -> None:
    st.write("")
    st.markdown('<div class="section-label">Reservation</div>', unsafe_allow_html=True)
    st.markdown("### Book your stay")

    room_names = list(ROOM_TYPES.keys())
    default_room = st.session_state.get("preselected_room", room_names[0])
    default_index = room_names.index(default_room) if default_room in room_names else 0

    # Room selector lives outside st.form so the price/capacity preview
    # below updates immediately as the guest changes their choice.
    selected_room = st.selectbox(
        "Room Selection", room_names, index=default_index, key="room_selection"
    )
    room_info = ROOM_TYPES[selected_room]

    st.caption(
        f"**${room_info['price']:.0f} / night** · sleeps up to "
        f"{room_info['capacity']} guest(s) · {room_info['tagline']}"
    )

    with st.form("booking_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full Name*", placeholder="Jordan Lee")
            email = st.text_input("Email*", placeholder="jordan@example.com")
            phone = st.text_input("Phone Number*", placeholder="+1 555 123 4567")
        with col2:
            check_in = st.date_input(
                "Check-In Date*", value=date.today(), min_value=date.today()
            )
            check_out = st.date_input(
                "Check-Out Date*", value=date.today() + timedelta(days=1),
                min_value=date.today() + timedelta(days=1),
            )
            guests = st.number_input(
                "Number of Guests*", min_value=1, max_value=room_info["capacity"],
                value=1, step=1,
            )

        # Live-ish price preview based on current widget values at last rerun.
        nights_preview = (check_out - check_in).days
        if nights_preview > 0:
            preview_total = nights_preview * room_info["price"]
            st.markdown(
                f"""
                <div class="price-summary">
                    {nights_preview} night(s) × ${room_info['price']:.0f}
                    = <strong>${preview_total:,.2f}</strong> estimated total
                </div>
                """,
                unsafe_allow_html=True,
            )

        submitted = st.form_submit_button("Confirm Booking", use_container_width=True)

    if submitted:
        errors = validate_booking(
            full_name, email, phone, check_in, check_out, guests, room_info["capacity"]
        )
        if errors:
            for err in errors:
                st.error(err)
            return

        nights = (check_out - check_in).days
        total_price = nights * room_info["price"]

        booking = {
            "full_name": full_name.strip(),
            "email": email.strip(),
            "phone": phone.strip(),
            "room_type": selected_room,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "guests": int(guests),
            "nights": nights,
            "price_per_night": room_info["price"],
            "total_price": total_price,
            "booked_on": date.today().isoformat(),
        }
        booking_id = insert_booking(booking)

        st.success(
            f"Booking confirmed! Reference **#{booking_id:04d}** — "
            f"{selected_room}, {nights} night(s), total **${total_price:,.2f}**."
        )
        st.balloons()
        st.session_state.pop("preselected_room", None)


def render_admin_view() -> None:
    st.write("")
    with st.expander("📊 Admin / Manager View — all bookings"):
        st.caption(
            "Demo-only access gate. This passcode is stored in plain text in "
            "the app source and is **not** suitable for production use."
        )
        passcode = st.text_input("Manager passcode", type="password", key="admin_pass")

        if not passcode:
            st.info("Enter the manager passcode to view stored reservations.")
            return
        if passcode != ADMIN_PASSCODE:
            st.error("Incorrect passcode.")
            return

        df = fetch_all_bookings()

        if df.empty:
            st.info("No bookings have been recorded yet.")
            return

        total_revenue = df["total_price"].sum()
        avg_nights = df["nights"].mean()

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Bookings", len(df))
        m2.metric("Total Revenue", f"${total_revenue:,.2f}")
        m3.metric("Avg. Stay Length", f"{avg_nights:.1f} nights")

        st.dataframe(df, use_container_width=True, hide_index=True)

        st.download_button(
            "Download bookings as CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="resort_bookings.csv",
            mime="text/csv",
        )

        st.write("")
        st.markdown("**Remove a booking**")
        options = {
            f"#{row.id:04d} — {row.full_name} ({row.room_type})": row.id
            for row in df.itertuples()
        }
        choice = st.selectbox("Select a booking to delete", list(options.keys()))
        if st.button("Delete selected booking", type="secondary"):
            delete_booking(options[choice])
            st.warning(f"Deleted booking {choice}.")
            st.rerun()


# ---------------------------------------------------------------------------
# App entry point
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(
        page_title="Palm & Tide Resort — Booking",
        page_icon="🌴",
        layout="wide",
    )
    init_db()
    inject_css()

    render_hero()
    render_room_gallery()
    st.divider()
    render_booking_form()
    st.divider()
    render_admin_view()

    st.write("")
    st.caption("Palm & Tide Resort · Pre-Resort Booking System demo")


if __name__ == "__main__":
    main()
