# SmartHome AI — Project Overview & Build Instructions

> Give this file to Claude Code at the start of every session.
> Tip: save it in the project folder as `CLAUDE.md` and Claude Code reads it automatically.

## 1. What this project is

**SmartHome AI** is a home service booking website, similar to Urban Company. Customers describe a problem at home, get a suggested service, pick a verified provider in their city, see an estimated price and book a time slot. Providers manage their jobs. An admin verifies providers and watches the whole system.

It is a **final-year BCA minor project**. The code must be simple, well-commented, beginner-friendly and fully working, not a static demo.

**Main focus:** the booking website. **AI is a small add-on.** Keep it light and don't over-engineer it.

## 2. Tech stack (strict)

| Layer | Use |
|---|---|
| Frontend | HTML5, CSS3, JavaScript, Bootstrap 5, Bootstrap Icons (via CDN) |
| Backend | Python 3, Flask 3 |
| Database | MySQL 8 (`mysql-connector-python`) |
| AI | scikit-learn, pandas, numpy, joblib |
| Other | Flask-WTF (CSRF only), python-dotenv, Werkzeug password hashing |

**Never use:** PHP, Laravel, Node.js backend, Firebase, Supabase, SQLAlchemy/ORM, NLTK.

Templates are Jinja2 (Flask's built-in templating).

**Target machine:** macOS, MySQL 8 installed via Homebrew, Python virtual environment in `venv/`.

## 3. User roles

Each role has its own dashboard and role-based access control.

**Customer**
- Register, log in, edit profile (name, phone, city, address).
- Browse and search services.
- Describe a problem and get a service suggestion.
- See ranked providers, compare them, see the cost estimate.
- Book a date and time slot.
- View booking status and history; cancel a booking while it is `pending` or `accepted`.
- Review only completed bookings.
- See notifications.

**Provider**
- Register as provider, which creates a `users` row plus a `providers` row with status `pending`.
- Edit profile: bio, experience, city, availability toggle.
- Add or remove the services they offer, with their own charge for each.
- View requests; accept or reject them.
- Move jobs from `accepted` to `in_progress` to `completed`.
- See their reviews, stats and history.

**Admin**
- Created **only** by `python3 create_admin.py`. There is no public admin signup.
- Dashboard stats: customers, providers (verified and pending), bookings by status.
- Approve or reject providers.
- Manage service categories: add, edit, activate/deactivate.
- Manage users: activate/deactivate.
- View all bookings and reviews.
- Simple AI stats: count of predictions per service, sentiment counts.

**Rules**
- Unverified or unavailable providers never appear in recommendations.
- Deactivated users cannot log in.

## 4. The three AI features (keep them LIGHT)

### 4.1 Service suggestion (ML)
- **Data:** `datasets/service_queries.csv` with columns `text,service`. About 60–80 realistic, varied example sentences per category for all 8 categories, including Indian-English phrasing.
- **Model:** scikit-learn `Pipeline(TfidfVectorizer(ngram_range=(1,2), lowercase=True, stop_words='english'), LogisticRegression(max_iter=1000))`. Do **not** use NLTK.
- **Training:** 80/20 stratified split. Print accuracy and `classification_report` (precision, recall, F1). Save to `ai_models/saved_models/service_model.joblib`.
- **In the app:** show the predicted service and confidence %. Log every prediction to `ai_predictions`.
- **Low confidence:** if confidence is below 40%, show "Not sure — please pick a service" with the full service list. Keep it simple.

### 4.2 Provider ranking (simple formula, NOT ML)
- **Candidates:** providers that are verified, have `is_available = 1`, an active user account, offer the required service, and have the same city as the customer (case-insensitive).
- **Score (0–100):**
  - rating 50%: `avg_rating / 5`
  - experience 30%: `min(experience_years, 10) / 10`
  - price 20%: `lowest charge among candidates / this provider's charge`
- **Weights:** read from `Config.RANK_WEIGHTS`.
- **Reasons:** show 1–2 plain-language reasons per provider, e.g. "Highly rated (4.6★)", "8 years experience", "Lowest price".
- **Code location:** `ai_models/provider_recommender.py`, as plain Python functions.

### 4.3 Review sentiment (ML)
- **Data:** `datasets/reviews.csv` with columns `text,sentiment`, where sentiment is `positive`, `negative` or `neutral`. About 100 realistic reviews per class.
- **Model:** the same pipeline type as 4.1. Do **not** remove negation words; use a custom stop-word list or none, so "not good" stays negative.
- **Training:** print evaluation results and save to `ai_models/saved_models/sentiment_model.joblib`.
- **In the app:** when a review is submitted, predict its sentiment and confidence and store both in `reviews`. The admin dashboard shows the counts.

### 4.4 One training script
`python3 train_models.py` trains both models, prints both evaluations and saves both files. If a model file is missing, the app must show a clear message instead of crashing.

**Honesty note for the README:** the datasets are synthetic, so test scores will look high. Say this plainly.

## 5. Cost estimate (rule-based, NOT AI)

`services/cost_estimator.py` has a single function, `estimate(base_charge, is_urgent)`.

- **Base charge:** the provider's charge from `provider_services`, or the service's `base_price` if no provider is chosen.
- **Urgent:** add `Config.URGENT_CHARGE` (₹150) if `is_urgent`.
- **Returns:** base, urgent charge and total.
- **UI:** show the breakdown and the disclaimer: "Final price may change after the provider inspects the work."
- **Labelling:** never call this AI.

## 6. Booking workflow

1. The customer describes the problem and gets a suggested service, or picks a service directly.
2. Ranked providers for that service in the customer's city are shown.
3. Optional: compare 2–3 providers side by side.
4. The customer selects a provider and sees the cost estimate.
5. The customer picks a date (today up to 30 days ahead) and one of the slots `09:00, 11:00, 13:00, 15:00, 17:00`. A same-day slot must be later than the current time. Booked slots for that provider and date are shown disabled.
6. The customer enters address and city (prefilled from profile), the problem description and the urgent checkbox.
7. On confirm:
   - validate on the server;
   - check for a conflict in the app;
   - insert the booking (the database unique index is the final guard; catch error 1062 and show "slot just got booked");
   - notify the provider.

**Statuses:** `pending → accepted / rejected`, `accepted → in_progress → completed`. The customer can move `pending` or `accepted` to `cancelled`.

- Every status change notifies the other party.
- Only the booking's own provider or customer can change it.
- Invalid transitions are rejected on the server.

**Reviews**
- Only for `completed` bookings that belong to the logged-in customer, one per booking.
- Rating 1–5 plus a comment.
- After saving, update the provider's `avg_rating` and `total_reviews`.

## 7. Database: `home_service_db`

Use this schema exactly (already tested on MySQL 8). Always use parameterized queries (`%s`). Never build SQL with f-strings.

```sql
-- =========================================================
-- SmartHome AI - Database Schema
-- Run with:  mysql -u root -p < database/schema.sql
-- WARNING: this drops and recreates home_service_db.
-- =========================================================

DROP DATABASE IF EXISTS home_service_db;
CREATE DATABASE home_service_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE home_service_db;

-- ---------------------------------------------------------
-- 1. users : one login table for customers, providers, admins
-- ---------------------------------------------------------
CREATE TABLE users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    email         VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone         VARCHAR(15),
    role          ENUM('customer', 'provider', 'admin') NOT NULL DEFAULT 'customer',
    city          VARCHAR(60),
    address       VARCHAR(255),
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_role (role)
);

-- ---------------------------------------------------------
-- 2. services : the home service categories
-- ---------------------------------------------------------
CREATE TABLE services (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(60) NOT NULL UNIQUE,
    description VARCHAR(255),
    icon        VARCHAR(50) NOT NULL DEFAULT 'bi-tools',   -- Bootstrap icon class
    base_price  DECIMAL(10,2) NOT NULL DEFAULT 0,          -- starting price in ₹
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------
-- 3. providers : extra profile details for provider users
-- ---------------------------------------------------------
CREATE TABLE providers (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    user_id             INT NOT NULL UNIQUE,
    bio                 VARCHAR(500),
    experience_years    INT NOT NULL DEFAULT 0,
    city                VARCHAR(60) NOT NULL,
    verification_status ENUM('pending', 'verified', 'rejected') NOT NULL DEFAULT 'pending',
    is_available        BOOLEAN NOT NULL DEFAULT TRUE,
    avg_rating          DECIMAL(3,2) NOT NULL DEFAULT 0,
    total_reviews       INT NOT NULL DEFAULT 0,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_providers_city_status (city, verification_status)
);

-- ---------------------------------------------------------
-- 4. provider_services : which services a provider offers + their price
-- ---------------------------------------------------------
CREATE TABLE provider_services (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    provider_id INT NOT NULL,
    service_id  INT NOT NULL,
    charge      DECIMAL(10,2) NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_provider_service (provider_id, service_id),
    FOREIGN KEY (provider_id) REFERENCES providers(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id)  REFERENCES services(id)  ON DELETE CASCADE
);

-- ---------------------------------------------------------
-- 5. bookings
-- ---------------------------------------------------------
CREATE TABLE bookings (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    customer_id         INT NOT NULL,
    provider_id         INT NOT NULL,
    service_id          INT NOT NULL,
    booking_date        DATE NOT NULL,
    time_slot           TIME NOT NULL,
    address             VARCHAR(255) NOT NULL,
    city                VARCHAR(60) NOT NULL,
    problem_description VARCHAR(1000),
    is_urgent           BOOLEAN NOT NULL DEFAULT FALSE,
    estimated_cost      DECIMAL(10,2) NOT NULL,
    status              ENUM('pending', 'accepted', 'rejected',
                             'in_progress', 'completed', 'cancelled')
                        NOT NULL DEFAULT 'pending',
    cancel_reason       VARCHAR(255),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Double-booking guard:
    -- is 1 while the booking holds the slot, NULL once rejected/cancelled/completed.
    -- MySQL allows many NULLs in a UNIQUE index, so freed slots can be rebooked,
    -- but two active bookings for the same provider + date + slot are blocked.
    active_slot TINYINT AS (
        CASE WHEN status IN ('pending', 'accepted', 'in_progress') THEN 1 ELSE NULL END
    ) STORED,
    UNIQUE KEY uq_provider_slot (provider_id, booking_date, time_slot, active_slot),

    FOREIGN KEY (customer_id) REFERENCES users(id)     ON DELETE CASCADE,
    FOREIGN KEY (provider_id) REFERENCES providers(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id)  REFERENCES services(id),
    INDEX idx_bookings_customer (customer_id),
    INDEX idx_bookings_status (status)
);

-- ---------------------------------------------------------
-- 6. reviews : one review per completed booking
-- ---------------------------------------------------------
CREATE TABLE reviews (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    booking_id           INT NOT NULL UNIQUE,
    customer_id          INT NOT NULL,
    provider_id          INT NOT NULL,
    rating               TINYINT NOT NULL,
    comment              VARCHAR(1000),
    sentiment            ENUM('positive', 'negative', 'neutral'),
    sentiment_confidence DECIMAL(5,2),
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_rating CHECK (rating BETWEEN 1 AND 5),
    FOREIGN KEY (booking_id)  REFERENCES bookings(id)  ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES users(id)     ON DELETE CASCADE,
    FOREIGN KEY (provider_id) REFERENCES providers(id) ON DELETE CASCADE,
    INDEX idx_reviews_sentiment (sentiment)
);

-- ---------------------------------------------------------
-- 7. ai_predictions : log of service suggestions (for admin stats)
-- ---------------------------------------------------------
CREATE TABLE ai_predictions (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    user_id              INT,
    input_text           VARCHAR(1000) NOT NULL,
    predicted_service_id INT,
    confidence           DECIMAL(5,2),
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)              REFERENCES users(id)    ON DELETE SET NULL,
    FOREIGN KEY (predicted_service_id) REFERENCES services(id) ON DELETE SET NULL
);

-- ---------------------------------------------------------
-- 8. notifications : in-app messages
-- ---------------------------------------------------------
CREATE TABLE notifications (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL,
    message    VARCHAR(255) NOT NULL,
    link       VARCHAR(255),
    is_read    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_notifications_user_read (user_id, is_read)
);

-- ---------------------------------------------------------
-- Sample service categories
-- ---------------------------------------------------------
INSERT INTO services (name, description, icon, base_price) VALUES
('Plumbing',                  'Leaking taps, blocked drains, pipe fitting and bathroom fixtures.', 'bi-droplet',           299),
('Electrical Repair',         'Wiring, switchboards, fans, lights and power issues.',             'bi-lightning-charge',  249),
('AC Repair and Maintenance', 'AC servicing, gas refill, cooling problems and installation.',     'bi-snow',              499),
('Home Cleaning',             'Deep cleaning, kitchen and bathroom cleaning, sofa cleaning.',     'bi-stars',             799),
('Appliance Repair',          'Washing machine, refrigerator, microwave and geyser repair.',     'bi-plug',              349),
('Painting',                  'Interior and exterior painting, wall touch-ups and waterproofing.','bi-palette',           1499),
('Carpentry',                 'Furniture repair, door and window fixing, new fittings.',         'bi-hammer',            299),
('Pest Control',              'Termite, cockroach, bed bug and general pest treatment.',         'bi-bug',               699);
```

**How the double-booking guard works:** `active_slot` is 1 only while a booking is pending, accepted or in progress, and NULL otherwise. MySQL allows multiple NULLs in a UNIQUE index, so cancelled or rejected bookings free the slot, while two active bookings for the same provider, date and slot fail with error 1062.

## 8. Folder structure

```
SmartHome_AI/
├── app.py                  # app factory, registers blueprints, CSRF, error pages
├── config.py               # settings; secrets from .env
├── create_admin.py         # CLI admin creation (only way to create admin)
├── seed_data.py            # demo customers, providers, bookings, reviews
├── train_models.py         # trains both ML models
├── requirements.txt
├── .env.example
├── .gitignore              # venv/, .env, __pycache__/
├── README.md
├── database/schema.sql
├── datasets/
│   ├── service_queries.csv
│   └── reviews.csv
├── ai_models/
│   ├── service_classifier.py     # load model + predict()
│   ├── provider_recommender.py   # ranking formula
│   ├── sentiment_analyzer.py     # load model + predict()
│   └── saved_models/
├── routes/
│   ├── auth.py  customer.py  provider.py  admin.py  booking.py  ai.py
├── services/
│   ├── cost_estimator.py
│   └── notification_service.py
├── utils/
│   ├── database.py      # pool + fetch_one / fetch_all / execute helpers
│   ├── decorators.py    # login_required, role_required
│   ├── validators.py    # server-side form validation helpers
│   └── helpers.py
├── templates/
│   ├── base.html  index.html  login.html  register.html  errors/
│   ├── customer/  provider/  admin/  bookings/
└── static/css/style.css  static/js/main.js  static/images/
```

## 9. Key implementation details

**`config.py`**
- `SECRET_KEY` and `DB_*` come from `.env`.
- `TIME_SLOTS = ["09:00","11:00","13:00","15:00","17:00"]`
- `URGENT_CHARGE = 150`
- `RANK_WEIGHTS = {"rating":0.5, "experience":0.3, "price":0.2}`
- `MODEL_DIR = ai_models/saved_models`

**`utils/database.py`**
- `mysql.connector.pooling.MySQLConnectionPool` (pool_size 5).
- One connection per request, stored in `flask.g` and returned in `teardown_appcontext`.
- Helpers: `fetch_one`, `fetch_all` (dict cursors), and `execute(sql, params, commit=True)`, which returns `lastrowid` and rolls back on error.

**`app.py`**
- `create_app()` raises a clear error if `SECRET_KEY` is missing.
- `/health` returns JSON with the database status.
- 403, 404 and 500 error pages use the dark theme.
- A context processor provides the unread notification count to the navbar.

**Auth**
- Werkzeug `generate_password_hash` / `check_password_hash`.
- Session stores `user_id`, `role` and `name`. Call `session.clear()` on login and logout.
- Login redirects to the dashboard for the user's role.

**Decorators**
- `@login_required` redirects to login.
- `@role_required('admin')` returns 403 for the wrong role.

**CSRF and validation**
- `CSRFProtect` is on for all POSTs. Every form includes `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`.
- Validate on the server:
  - email format;
  - password at least 8 characters;
  - phone is 10 digits;
  - required fields;
  - rating 1–5;
  - date range and slot in `TIME_SLOTS`;
  - charges are positive numbers.

**Messages and safety**
- Use `flash()` messages for all success and error feedback.
- Never trust IDs from forms. Always check that the record belongs to the logged-in user.

## 10. UI / design

- **Theme:** dark background (`#0f1412`-ish) with green/mint accents (`#2ecc71`, `#7dffc4`-ish).
- **Style:** modern font (e.g. Google Font "Poppins" or "Inter"), rounded cards, smooth hover effects, clean spacing. Same design language everywhere.
- **Layout:** Bootstrap 5 grid; responsive on mobile, tablet and desktop.
- **Shared page:** `base.html` contains the navbar (role-aware links plus a notification badge), flash messages and the footer.
- **Pages:**
  1. Home
  2. Login
  3. Register (customer/provider toggle)
  4. Customer dashboard
  5. Provider dashboard
  6. Admin dashboard
  7. Service listing with search
  8. Service details
  9. AI suggestion page
  10. Provider comparison
  11. Booking page
  12. Booking history
  13. Review page
  14. Profile page
  15. Provider verification (admin)
- **Admin charts (optional):** Chart.js via CDN.

## 11. Build phases (one at a time; test each before moving on)

1. **Setup:** folders, config, requirements, `.env.example`, `schema.sql`, `database.py`, `app.py` with `/health`, `create_admin.py`, README setup section.
2. **Frontend:** `base.html`, `style.css`, `main.js`, all page templates.
3. **Auth and roles:** register (customer/provider), login, logout, decorators, profile pages.
4. **Core booking:**
   - service listing and search;
   - provider services and profile;
   - admin verification and category management;
   - booking creation with slot checks;
   - status updates;
   - cancellation;
   - notifications.
5. **AI and estimate:** datasets, `train_models.py`, classifier, recommender, sentiment, cost estimator, AI pages, admin AI stats.
6. **Testing and docs:**
   - `seed_data.py`;
   - test every role end to end;
   - test invalid inputs;
   - test mobile layouts;
   - finish the README.

## 12. Rules for Claude while coding

- The developer is a **beginner**. Write complete files (no snippets, no pseudocode, no "TODO: implement").
- Add short comments explaining important functions.
- Keep table and column names exactly as in the schema.
- After each phase, run the app and test what was built. Fix errors before continuing.
- Never claim something works unless it was run and tested.
- Never hardcode passwords or secret keys. Never commit `.env`.
- Keep the AI simple. If something feels over-engineered, choose the simpler option.
- At the end of each phase, briefly list what was built and how to test it.

## 13. Final deliverables

1. Working source code.
2. `schema.sql`.
3. Datasets.
4. `train_models.py` and the saved models.
5. `requirements.txt` and `.env.example`.
6. `create_admin.py` and `seed_data.py`, with sample logins listed in the README.
7. README containing:
   - macOS setup steps;
   - architecture explanation;
   - table relationship (ER) explanation;
   - AI explanation with evaluation results and the honesty note about synthetic data.