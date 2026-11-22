# SmartHome AI – Smart Home Service Booking System

Final-year BCA minor project. Customers describe a problem at home, get a suggested service,
pick a verified provider in their city, see a price estimate and book a time slot.
Providers manage their jobs, and an admin verifies providers and watches the whole system.

Built with **Python Flask, MySQL, HTML/CSS/JS, Bootstrap 5 and scikit-learn**.

---

## 1. Setup on macOS

### 1.1 Install Python and MySQL (one-time)
Install Homebrew from https://brew.sh if you don't have it, then:

```bash
brew install python mysql
brew services start mysql
mysql_secure_installation      # set a root password and remember it
```

### 1.2 Create a virtual environment and install packages
```bash
cd ~/Desktop/SmartHome_AI
python3 -m venv venv
source venv/bin/activate        # run this every time you open a new terminal
pip install -r requirements.txt
```

### 1.3 Create your .env file
```bash
cp .env.example .env
python3 -c "import secrets; print(secrets.token_hex(32))"
```
Open `.env` and fill in:

| Key | What to put |
|---|---|
| `SECRET_KEY` | The random text generated above |
| `DB_PASSWORD` | Your MySQL root password (leave empty if root has none) |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | Login for the first admin (password min 8 characters) |
| `FLASK_DEBUG` | `1` on your laptop, `0` on a live server |

### 1.4 Create the database
```bash
mysql -u root -p < database/schema.sql
```
This creates `home_service_db` with 8 tables and the 8 service categories.
**Running it again wipes all data.**

### 1.5 Train the AI models
```bash
python3 train_models.py
```
Prints the evaluation results and saves both models in `ai_models/saved_models/`.

### 1.6 Add demo data (optional)
```bash
python3 seed_data.py        # demo customers, providers, bookings, reviews
```

### 1.7 Run the app
```bash
python3 app.py
```
Open http://127.0.0.1:5000. Visit http://127.0.0.1:5000/health to confirm the database connection.

### 1.8 How accounts are created

| Who | How |
|---|---|
| Customer | **Register** page on the website → choose *Customer* |
| Provider | **Register** page → choose *Provider* → waits as *pending* until the admin approves |
| First admin | **Automatic.** When the app starts and no admin exists, it creates one from `ADMIN_*` in `.env` |
| Extra admins | `python3 create_admin.py` on the server (optional) |

There is deliberately **no admin signup on the website**, so nobody can make themselves admin.
Once the first admin exists, the `ADMIN_*` values are ignored; change the password by
creating a new admin, or by updating the database.

## 2. Deploy online (Render + Aiven MySQL)

Render runs the Flask app; it has no MySQL, so the database lives on **Aiven** (free MySQL 8).

### 2.1 Create the database on Aiven
1. Sign up at https://aiven.io → **Create service** → **MySQL** → **Free plan**.
2. When it is running, open the service's **Overview** page and note **Host**, **Port**,
   **User** (`avnadmin`) and **Password**. Download the **CA certificate** (`ca.pem`).

### 2.2 Load tables and demo data from your laptop
Render's free plan has no terminal, so load the database from your own machine:
```bash
# tables (the CA file makes the connection secure)
mysql --host=<aiven-host> --port=<aiven-port> --user=avnadmin -p \
      --ssl-ca=ca.pem < database/schema.sql
```
Then temporarily point your local `.env` at Aiven (keep a copy of your local values) and run:
```bash
# in .env: DB_HOST, DB_PORT, DB_USER, DB_PASSWORD from Aiven, DB_SSL_CA=/full/path/to/ca.pem
python3 seed_data.py
```
Put your local values back in `.env` afterwards.

### 2.3 Put the code on GitHub
Push this folder to a GitHub repository. `.gitignore` already keeps `venv/` and `.env` out.
Make sure `ai_models/saved_models/*.joblib` **is** pushed (the server needs the trained models).

### 2.4 Create the web service on Render
1. Sign up at https://render.com with the same GitHub account.
2. **New → Blueprint** → choose your repository. Render reads `render.yaml`
   (build: `pip install -r requirements.txt`, start: `gunicorn app:app`, Python 3.10.14).
3. Fill in the values it asks for: `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` (from Aiven),
   `ADMIN_EMAIL`, `ADMIN_PASSWORD`. `SECRET_KEY` is generated automatically.
4. In the service → **Environment → Secret Files**, add a file named **`ca.pem`** and paste the
   Aiven CA certificate. It is mounted at `/etc/secrets/ca.pem` (already set as `DB_SSL_CA`).
5. Deploy. Open `https://<your-service>.onrender.com/health`. It should say `"database": "connected"`.
6. Log in at `/login` with `ADMIN_EMAIL` / `ADMIN_PASSWORD`. The admin is created on first start.

**Free-plan notes:** Render puts the app to sleep after ~15 minutes without visitors; the next
visit takes ~1 minute to wake it. Open the site a minute before a demo.

## 3. Sample logins (after `seed_data.py`)

All demo accounts use the password **`demo1234`**.

| Role | Email | Notes |
|---|---|---|
| Customer | aarav@demo.com | Mumbai, has bookings in every status |
| Customer | priya@demo.com | Mumbai |
| Customer | rohan@demo.com | Pune |
| Customer | neha@, karan@, sneha@, vikram@demo.com | Mumbai (booking history only) |
| Customer | ananya@, arjun@demo.com | Pune (booking history only) |
| Customer | riya@demo.com, aditya@demo.com (+18 more in `seed_indore.py`) | Indore |
| Provider | malwa@demo.com (Plumbing, Carpentry), powerline@demo.com (Electrical), chillzone@demo.com (AC), shinehome@demo.com (Cleaning), rangmahal@demo.com (Painting) | Indore, verified |
| Provider | arctic@demo.com | Indore, verified but **unavailable** (hidden) |
| Provider | nayisoch@demo.com, shivshakti@demo.com | Indore, **pending** verification |
| Provider | unverified@demo.com | Indore, **rejected** |
| Provider | ramesh@demo.com | Mumbai, Plumbing + Carpentry, 4.5★ |
| Provider | suresh@demo.com | Mumbai, cheapest plumber |
| Provider | volt@demo.com | Mumbai, Electrical + Appliance |
| Provider | coolair@demo.com | Mumbai, AC + Appliance |
| Provider | sparkle@demo.com | Mumbai, Home Cleaning |
| Provider | bugfree@demo.com | Mumbai, Pest Control |
| Provider | colorcraft@demo.com | Pune, Painting |
| Provider | punefix@demo.com | Pune, Plumbing + Electrical |
| Provider | pending@demo.com | **Pending** verification (hidden from customers) |
| Admin | `ADMIN_EMAIL` from `.env` | Password is `ADMIN_PASSWORD` in `.env` |

`seed_data.py` can be run again at any time; it deletes and recreates only the `@demo.com` accounts.
Besides the 11 hand-written bookings it adds 70 random past bookings in Mumbai/Pune, and a full
**Indore** data set from `seed_indore.py`: 20 customers, 25 providers (every service has 2–4
bookable providers), 400 past bookings with reviews that match each provider's quality, about
40 upcoming bookings for providers to act on, and sample AI suggestions. Everything uses a fixed
random seed (same data every run) and leans towards recent weeks so the demand chart shows a trend.

## 4. Architecture

```
Browser (Bootstrap pages)
   │  HTTP (forms with CSRF token)
   ▼
Flask app (app.py)  ── blueprints in routes/
   │     main · auth · customer · provider · admin · booking · ai
   │
   ├── services/      business rules (booking rules, cost estimate, notifications)
   ├── ai_models/     service classifier, sentiment analyzer, provider ranking
   ├── utils/         database helpers, login/role decorators, validators
   ▼
MySQL (home_service_db)   ←  mysql-connector connection pool, parameterized queries only
```

| Folder | What lives there |
|---|---|
| `routes/` | One file per area. Each function handles one URL. |
| `services/booking_service.py` | Which status changes are allowed, free slots, creating bookings |
| `services/cost_estimator.py` | `estimate(base_charge, is_urgent)`: plain arithmetic, **not AI** |
| `services/notification_service.py` | In-app notifications (navbar bell) |
| `ai_models/` | The AI features (see section 5) |
| `utils/database.py` | Pool + `fetch_one`, `fetch_all`, `execute` |
| `utils/decorators.py` | `@login_required`, `@role_required("admin")` |
| `utils/validators.py` | Email, phone, password, rating, charge, date and slot checks |
| `templates/` | Jinja2 pages; `base.html` holds the navbar, flash messages and footer |

**Security:** Werkzeug password hashing, CSRF on every POST form, role checks on every page,
every booking/review/service action checks that the record belongs to the logged-in user,
deactivated users are logged out on their next request.

## 5. Database tables (ER explanation)

```
users ─1───1─ providers ─1───*─ provider_services ─*───1─ services
  │               │                                          │
  │ (customer)    │                                          │
  └─1───*─ bookings ─*───1───────────────────────────────────┘
              │
              └─1───1─ reviews
users ─1───*─ notifications
users ─1───*─ ai_predictions ─*───1─ services
```

| Table | Stores | Key relationships |
|---|---|---|
| users | All accounts (customer, provider, admin) | `role` decides the dashboard |
| providers | Provider profile: experience, city, verification, rating | `user_id` → users (one-to-one) |
| services | The service categories | — |
| provider_services | Which services a provider offers, at what charge | provider ↔ service (many-to-many) |
| bookings | Bookings and their status | customer → users, provider → providers, service → services |
| reviews | One review per completed booking, with AI sentiment | `booking_id` UNIQUE |
| ai_predictions | Log of AI service suggestions | for admin stats |
| notifications | In-app notifications | user → users |

**Double booking protection:** `bookings.active_slot` is 1 while a booking is pending, accepted or
in progress, and NULL otherwise. A UNIQUE index on (provider, date, slot, active_slot) blocks two
active bookings for the same slot, while cancelled/rejected bookings free the slot.
The app checks first, and if two people click at the same moment, MySQL error 1062 is caught
and the user sees "slot just got booked".

**Booking statuses:** `pending → accepted / rejected`, `accepted → in_progress → completed`.
The customer can cancel while `pending` or `accepted`. Any other change is rejected on the server.

## 6. AI features

The AI is a small add-on; the booking website is the main project.

### 6.1 Service suggestion (machine learning)
- **Data:** `datasets/service_queries.csv`, 560 sentences (70 per service), including Indian-English phrasing.
- **Model:** `TfidfVectorizer(ngram_range=(1,2), stop_words='english')` + `LogisticRegression(max_iter=1000, C=10)`.
- **In the app:** shows the predicted service and confidence %. Below 40% confidence it says
  "Not sure — please pick a service" and lists all services. Every prediction is logged in `ai_predictions`.

### 6.2 Provider ranking (simple formula, not ML)
Only verified, available, active providers who offer the service in the customer's city are ranked.

```
score = 100 × (0.5 × rating/5  +  0.3 × min(experience,10)/10  +  0.2 × lowest_charge/this_charge)
```
Weights come from `Config.RANK_WEIGHTS`. Each provider gets 1–2 reasons such as
"Highly rated (4.5★)", "12 years experience" or "Lowest price".

### 6.3 Review sentiment (machine learning)
- **Data:** `datasets/reviews.csv`, 300 reviews (100 positive, 100 negative, 100 neutral).
- **Model:** same pipeline with **no stop-word removal**, so words like "not" are kept and "not good" stays negative.
- **In the app:** each new review gets a sentiment and confidence; the admin dashboard shows the counts.

### 6.4 Customers also booked (counting, no training)
On each service page: "Customers who booked Plumbing also booked …". For the chosen service it counts,
for every other service, how many **distinct customers** booked both (rejected/cancelled bookings ignored),
and shows the top 3. Code: `ai_models/related_services.py` (one SQL query).

### 6.5 Demand forecast for the admin (Linear Regression)
Admin → **Demand** page (`/admin/demand`), code in `ai_models/demand_forecast.py`:
- **Weekday heatmap:** bookings per service per weekday, darker cell = busier day.
- **Weekly trend:** bookings in each of the last 8 weeks, overall and per service.
- **Forecast:** scikit-learn `LinearRegression` fits a straight line to the 8 weekly counts
  (x = week number, y = bookings) and predicts week 9. The slope is shown as the trend
  (bookings gained or lost per week). Forecasts never go below 0.

> With only 8 points and synthetic seed data (which is deliberately skewed towards recent weeks),
> the forecast is a rough guide for a demo, not a reliable prediction.

### 6.6 Evaluation results (`python3 train_models.py`, 80/20 stratified split)

| Model | Test rows | Accuracy | Macro F1 |
|---|---|---|---|
| Service suggestion | 112 | 97.32% | 0.97 |
| Review sentiment | 60 | 100.00% | 1.00 |

`C=10` was chosen because with the default `C=1` the model was right but under-confident
(for example "kitchen tap leaking" scored only 39% for Plumbing, below the 40% threshold).
With `C=10` it scores 83%, while nonsense text such as "hello there friend" still scores only ~16%.

> **Honesty note:** both datasets are **synthetic**. They were generated from hand-written
> problem phrases and review sentences combined with templates, so the test sentences are very
> similar to the training sentences. The high scores above do **not** mean the models would be
> this accurate on real customer text. Real-world accuracy would need real, varied data.

If a model file is missing, the app does not crash: the suggestion page shows
"run `python3 train_models.py`" and reviews are saved without a sentiment.

## 7. Cost estimate (rule-based, not AI)
`estimate(base_charge, is_urgent)` returns the provider's charge, plus ₹150 if the booking is urgent,
and the total. The page always shows: *"Final price may change after the provider inspects the work."*

## 8. How to test

1. **Customer:** log in as `aarav@demo.com` → AI Suggest → type "water dripping from AC" →
   See providers → Book now → pick a date/slot → confirm → My Bookings → cancel a pending one.
2. **Provider:** log in as `ramesh@demo.com` → accept the request → Start Job → Mark Completed.
3. **Review:** back as the customer → My Bookings → Write review.
4. **Admin:** log in with `ADMIN_EMAIL` / `ADMIN_PASSWORD` from `.env` → approve "New Pro Pending" → add/edit/deactivate a service →
   deactivate a customer (they can no longer log in) → check AI stats on the dashboard →
   open **Demand** to see the heatmap and next-week forecast.
5. **Invalid inputs:** wrong phone, short password, past date, a slot already taken,
   a negative charge: each one shows an error message.

## Troubleshooting
- **`Access denied for user 'root'`**: the password in `.env` doesn't match your MySQL password.
- **`Can't connect to MySQL server`**: start MySQL with `brew services start mysql`.
- **`SECRET_KEY is missing`**: `.env` doesn't exist or `SECRET_KEY` is empty (step 1.3).
- **`Address already in use` on port 5000**: on macOS, AirPlay Receiver uses port 5000. Turn it off in
  System Settings → General → AirDrop & Handoff, or run `flask --app app run --port 5001`.
- **"AI model has not been trained yet"**: run `python3 train_models.py` and restart the app.
