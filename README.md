# Palm & Tide Resort — Pre-Resort Booking System

A single-file Streamlit web app for browsing resort room types and
submitting a booking request. Every reservation is saved to a local
SQLite database, and a passcode-gated Admin/Manager view lets staff
review all stored bookings.

## Features

- **Room gallery** — three room types (Deluxe Room, Oceanfront Suite,
  Luxury Villa) shown as cards with nightly rate, capacity, description,
  and amenities. A "Select" button on each card pre-fills the booking
  form below.
- **Booking form** — Full Name, Email, Phone Number, Room Selection,
  Check-In Date, Check-Out Date, and Number of Guests, with input
  validation (valid email format, phone length, check-out after
  check-in, guest count within the room's capacity).
- **Automatic price calculation** — nights are computed from the two
  dates and multiplied by the selected room's nightly rate; a live
  estimate is shown before you submit.
- **SQLite persistence** — every confirmed booking is written to
  `resort_bookings.db` in the project folder, created automatically on
  first run.
- **Admin/Manager view** — an expandable, passcode-protected section
  showing total bookings, total revenue, average stay length, a full
  data table, a CSV export button, and the ability to delete a booking.

## Project structure

```
.
├── app.py              # the entire application (UI + database logic)
├── requirements.txt    # Python dependencies
└── README.md
```

Running the app also creates `resort_bookings.db` (SQLite) in the same
folder the first time it starts — this file is the database and will
persist between runs.

## Requirements

- Python 3.9+
- pip

## Setup

1. **Clone or download** this folder to your machine.

2. **(Recommended) create a virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

## Running the app

From the project folder, run:

```bash
streamlit run app.py
```

Streamlit will start a local server and print a URL — typically:

```
Local URL: http://localhost:8501
```

Your browser should open automatically; if not, open that URL manually.

## Using the app

1. Browse the three room cards at the top of the page. Click **Select**
   under a room to pre-fill it in the form below (optional — you can
   also just pick a room directly from the dropdown).
2. Fill in the booking form: name, email, phone, check-in/check-out
   dates, and number of guests. The estimated total updates as you
   change the dates.
3. Click **Confirm Booking**. On success you'll see a confirmation
   message with a booking reference number, and the reservation is
   saved to the database.
4. To review bookings, open the **📊 Admin / Manager View** section at
   the bottom of the page and enter the manager passcode:

   ```
   resort2026
   ```

   From there you can see summary metrics, the full bookings table,
   export everything to CSV, or delete a specific booking.

## Customizing

- **Room types, rates, descriptions, and capacity** — edit the
  `ROOM_TYPES` dictionary near the top of `app.py`.
- **Admin passcode** — edit the `ADMIN_PASSCODE` constant near the top
  of `app.py`.
- **Database file location/name** — edit the `DB_FILE` consant.

## Troubleshooting

- **`streamlit: command not found`** — make sure your virtual
  environment is activated and `pip install -r requirements.txt`
  completed without errors.
- **Port already in use** — run `streamlit run app.py --server.port 8502`
  (or any free port).
- **Database looks empty after restarting** — confirm you're running
  `streamlit run app.py` from the same folder each time; `resort_bookings.db`
  is created relative to the current working directory.
