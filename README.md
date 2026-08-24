# SHIPORA — Smart Last-Mile Logistics Platform

> Status: **Phase 10 complete** — full backend (Phases 1-9) plus the frontend foundation: project scaffold, design system, auth pages, and role-based dashboard shells.
> Full customer/agent/admin dashboard build-out, analytics, and final docs/deployment remain.

> **Confirmed working end-to-end on Python 3.14** with the dependency versions pinned in `requirements.txt` and a real MongoDB Atlas free-tier cluster.

## What exists right now

```
shipora-last-mile/
├── backend/
│   ├── server.py             # FastAPI app entrypoint, health check, router mounting
│   ├── core/
│   │   ├── config.py         # env-based settings (pydantic-settings)
│   │   ├── database.py       # Motor (async MongoDB) connection + index setup
│   │   ├── security.py       # bcrypt hashing + JWT issue/verify helpers
│   │   └── deps.py           # get_current_user + require_role() route guards
│   ├── models/
│   │   └── user.py           # UserInDB — shared doc shape for customer/agent/admin
│   ├── schemas/
│   │   └── auth.py           # register/login/token request+response schemas
│   ├── routes/
│   │   └── auth.py           # /api/auth/register, /login, /me, /admin/create
│   ├── services/  utils/  tests/   # empty, filled in next phases
│   ├── requirements.txt
│   └── .env.example
├── .gitignore
└── README.md
```

## Auth endpoints (Phase 2)

| Method | Path                   | Who               | Notes |
|--------|------------------------|-------------------|-------|
| POST   | `/api/auth/register`   | public            | Customer self-registration only |
| POST   | `/api/auth/login`      | public            | Any role, returns JWT |
| GET    | `/api/auth/me`         | any logged-in user| Reads role/identity from bearer token |
| POST   | `/api/auth/admin/create` | admin only      | Admin provisions agent/admin/customer accounts |

- All three roles (`customer` / `agent` / `admin`) live in one `users` collection — role is just a field, not a separate table, since login/hashing/JWT logic is identical.
- There's **no public registration for agents or admins** — only an admin can create those, via `/api/auth/admin/create`. This matches "Admin can create orders on behalf of a customer" logic in spirit: admin provisions accounts.
- Passwords are bcrypt-hashed, never stored or returned in plaintext.
- JWTs embed `sub` (user id) and `role`, so route guards don't need a DB round-trip just to check role — though `get_current_user` still re-fetches the user to confirm the account still exists and is active.
- Login returns an identical error for "no such email" and "wrong password" — doesn't leak which emails are registered.

## Run it locally

1. **Get a MongoDB instance.** Easiest: a free [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register) cluster (takes ~5 min, gives you a `mongodb+srv://...` URI). Or run Mongo locally with Docker: `docker run -d -p 27017:27017 mongo`.

2. **Set up the backend:**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   ```
   Edit `.env` and paste your real `MONGO_URI`. Also change `JWT_SECRET` to any long random string.

3. **Run it:**
   ```bash
   uvicorn server:app --reload --port 8000
   ```

4. **Verify:** open `http://localhost:8000/api/health` — you should see:
   ```json
   {"service": "shipora-api", "status": "ok", "environment": "development", "database": "connected"}
   ```
   If `database` says `unreachable`, double check your `MONGO_URI` and that your IP is allow-listed in Atlas (Network Access → Add Current IP).

## Design notes for this phase

- **Settings are centralized** in `core/config.py` — nothing reads `os.environ` directly anywhere else in the app.
- **DB connection doesn't crash the app on startup** if Mongo is unreachable — it logs a clear error and stays up, since local dev often starts the API before the DB is ready. Requests that touch the DB will simply fail until it's reachable.
- **Indexes are created automatically** on startup (`ensure_indexes` in `database.py`) — tracking_id uniqueness, email uniqueness, zone pincode lookups, etc. This is where the schema's real constraints live, not just in Pydantic.
- **Security helpers are role-agnostic** — `core/security.py` only proves identity (password check, JWT issue/decode). Role-based access control is a routing concern, added in Phase 2.

## Zone + rate card endpoints (Phase 3)

| Method | Path | Who | Notes |
|--------|------|-----|-------|
| GET    | `/api/zones` | any logged-in user | List all zones |
| GET    | `/api/zones/resolve/{pincode}` | any logged-in user | Resolve a PIN to its zone — 422 if unmapped, never guesses |
| POST   | `/api/zones` | admin | Create a zone; rejects PINs already claimed by another active zone |
| PATCH  | `/api/zones/{id}` | admin | Edit name/description/active flag |
| POST   | `/api/zones/{id}/pincodes` | admin | Add PIN codes to a zone |
| DELETE | `/api/zones/{id}/pincodes` | admin | Remove PIN codes from a zone |
| DELETE | `/api/zones/{id}` | admin | Soft-delete (deactivate) — never hard-deletes, since orders may reference it historically |
| GET    | `/api/rates` | any logged-in user | List all rate cards, all versions |
| GET    | `/api/rates/active/{order_type}/{scope}` | any logged-in user | Get the current active card for e.g. B2C/INTRA_ZONE |
| POST   | `/api/rates` | admin | Create a new rate card version — auto-deactivates the prior active version for that (order_type, scope) combo |
| PATCH  | `/api/rates/{id}` | admin | Edit name/active flag only — **pricing fields are never editable in place** |

**Key design decisions:**
- Zone resolution lives in exactly one place (`services/zone_service.py`) so nothing else in the codebase ever pattern-matches on address strings.
- A PIN code can only belong to one *active* zone at a time — creating/editing PINs checks for clashes first.
- Rate cards are versioned, not edited. `POST /api/rates` for a combo that already has an active card creates version N+1 and flips the old one's `is_active` to false — the old version stays in the database untouched, satisfying "historical order prices must remain stable even if rate cards change later" once orders start snapshotting their charges in Phase 4.
- Zones are soft-deleted only (`is_active: false`), never removed from the database, for the same historical-integrity reason.

All of Phase 3 was verified end-to-end against an in-memory Mongo mock: zone CRUD, PIN validation/clash detection, PIN resolution (success + clear-error case), rate card versioning across two versions of the same combo, active-card lookup, and role restrictions blocking customers from every admin-only action.

## Pricing engine (Phase 4)

| Method | Path | Who | Notes |
|--------|------|-----|-------|
| POST | `/api/orders/quote` | any logged-in user | Full price breakdown — no order is created or persisted |

**`services/pricing_engine.py`** is the single source of truth for pricing — nothing else in the codebase computes a price. Calculation order, exactly matching the assignment spec:

1. Extract PIN from pickup/drop address text, resolve each to a zone via Phase 3's `zone_service` (422 if unmapped — never guesses)
2. Determine `INTRA_ZONE` (same zone) vs `INTER_ZONE` (different zones)
3. `volumetric_weight = (L × B × H) / 5000`
4. `chargeable_weight = max(actual_weight, volumetric_weight)`
5. Look up the active rate card for `(order_type, zone_type)` — 422 if none configured
6. `base_charge` covers `included_kg`; weight beyond that is `extra_kg × per_extra_kg_charge`
7. If COD: `cod_surcharge = cod_flat_charge + (subtotal × cod_percent_of_subtotal / 100)`
8. Returns every intermediate number, not just the total — so the frontend's price-preview panel can show a full itemized breakdown before the customer confirms

Example response:
```json
{
  "actual_weight": 1.2, "volumetric_weight": 1.8, "chargeable_weight": 1.8,
  "pickup_zone": {"id": "...", "name": "Delhi NCR", "code": "ZN-NCR"},
  "drop_zone": {"id": "...", "name": "Mumbai Metro", "code": "ZN-MUM"},
  "zone_type": "INTER_ZONE", "order_type": "B2C", "payment_type": "COD",
  "rate_card_id": "...", "rate_card_version": 1,
  "base_charge": 110.0, "extra_weight_charge": 17.6, "subtotal": 127.6,
  "cod_surcharge": 31.91, "total": 159.51
}
```

Verified against 7 test cases covering the exact matrix from the assignment's evaluation criteria: actual-weight-wins, volumetric-weight-wins, intra-zone, inter-zone, B2B, B2C, COD math, prepaid, unmapped-PIN rejection, missing-rate-card rejection, and address-with-no-PIN rejection — all pass with hand-verified numbers.

## Order creation + tracking (Phase 5)

| Method | Path | Who | Notes |
|--------|------|-----|-------|
| POST | `/api/orders/quote` | any logged-in user | Price preview only — nothing persisted |
| POST | `/api/orders` | customer | Creates + confirms a shipment for themselves |
| POST | `/api/orders/admin` | admin | Creates a shipment on behalf of an existing customer (by email) |
| GET  | `/api/orders` | any logged-in user | Customers see only their own orders; admins see all |
| GET  | `/api/orders/{id}` | owner or admin | Full order detail + complete tracking history |
| GET  | `/api/orders/track/{tracking_id}` | **public, no auth** | Tracking page lookup, per the assignment spec |

**Key design decisions:**
- **Tracking IDs** (`LM-XXXXXXX`) use a 31-character alphabet excluding `0/O/1/I/L` to avoid ambiguity, generated with a uniqueness check against the database before being assigned.
- **Prices are snapshotted, not recalculated.** `order_service.create_order()` calls the Phase 4 pricing engine once at creation time and stores every resulting number directly on the order document. A rate card can change completely afterward and it will never alter an existing order's `total_charge` — verified by a test that changes a rate card mid-test and re-fetches an old order to confirm its price didn't move.
- **The backend re-validates everything server-side** on order creation — it never trusts a price the frontend previously showed from `/quote`. The two calls happen to share the same pricing engine, but `/api/orders` doesn't accept a client-supplied price at all.
- **`services/tracking_service.py` is the only code path allowed to write to `tracking_events` or change `current_status`.** Every future phase that changes an order's status (assignment, delivery updates, admin overrides) goes through this one function, keeping the "append-only, never overwritten" guarantee real rather than just a convention.
- Order creation writes the first `CREATED` tracking event, correctly attributed to whichever actor made it (`customer` for self-service orders, `admin` for orders placed on a customer's behalf).

Verified with 12 end-to-end tests: order creation, tracking ID uniqueness, first tracking event correctness, public tracking lookup (success + 404), cross-customer access denial, correct list scoping for customers vs admins, admin-create-for-customer (success + unknown-email 404 + customer-blocked-from-endpoint), and — the important one — historical price stability across a rate card change.

## Agent assignment (Phase 6)

| Method | Path | Who | Notes |
|--------|------|-----|-------|
| POST  | `/api/agents` | admin | Create an agent profile for an existing agent-role user + zone |
| GET   | `/api/agents` | admin | List all agents with live load/availability |
| GET   | `/api/agents/me` | agent | Own profile |
| PATCH | `/api/agents/me/availability` | agent | Toggle own availability |
| PATCH | `/api/agents/{id}/zone` | admin | Reassign an agent's operating zone |
| GET   | `/api/agents/me/deliveries` | agent | Orders currently assigned to the logged-in agent |
| POST  | `/api/orders/{id}/assign` | admin | Manually assign a specific agent |
| POST  | `/api/orders/{id}/auto-assign` | admin | Auto-assign the nearest suitable available agent |

**`services/assignment_service.py`** implements both paths from the spec, converging on one `_assign()` function so manual and automatic assignment can never drift apart in behavior:

- **Auto-assignment algorithm:** filter to agents who are `is_active` + `is_available` + in the order's **pickup zone** (our proxy for "nearest," since there's no live GPS in this system — same-zone is the meaningful notion of proximity that actually exists here) → among those, pick the one with the fewest **active assignments** (load-balancing) → ties broken by whoever's been idle longest.
- **No suitable agent found** returns the exact error from the assignment spec's own example: `"No available delivery agents in the selected zone."`
- **Reassignment is handled correctly**, not just overwritten: assigning an order to a new agent automatically decrements the previous agent's load and increments the new one's — verified by a test that reassigns and checks both agents' counts.
- **Persisted in MongoDB, not just the UI** — `assigned_agent_id` is written to the order, an `ASSIGNED` tracking event is appended through the same `tracking_service` from Phase 5 (so it shows up correctly in the append-only history), and the agent's `active_assignment_count` is updated atomically alongside it.
- An order can only be assigned/reassigned while in `CREATED`, `ASSIGNED`, or `RESCHEDULED` status — attempting to assign a `DELIVERED` or `FAILED` order is rejected with a `409`.

Verified with 9 end-to-end tests: duplicate-profile rejection, correct auto-assignment target selection (correctly skipping an unavailable agent and a same-name agent in the wrong zone), the exact "no available agents" error message, tracking history ordering, manual override, role restriction (customer blocked), an agent viewing only their own deliveries, correct load transfer on reassignment, and 404 on a nonexistent agent.

## Tracking lifecycle + failed delivery (Phase 7)

| Method | Path | Who | Notes |
|--------|------|-----|-------|
| PATCH | `/api/orders/{id}/status` | agent (own order only) | Advance to the next valid status; FAILED requires `failure_reason` |
| POST  | `/api/orders/{id}/reschedule` | owner customer or admin | Reschedule a FAILED delivery — order must be in FAILED status |
| POST  | `/api/orders/{id}/override-status` | admin | Force-set any status, bypassing transition rules, fully audited |

**Valid transitions** (`services/tracking_service.py::VALID_TRANSITIONS`), enforced server-side, matching the spec exactly:
```
ASSIGNED → PICKED_UP → IN_TRANSIT → OUT_FOR_DELIVERY → DELIVERED
                                          ↓
                                       FAILED → RESCHEDULED → (re-assign) → ASSIGNED
```
Any other transition — skipping a step, going backwards, jumping straight to DELIVERED — is rejected with a `409` naming exactly which statuses are valid from the current one.

**Key design decisions:**
- **An agent can only update an order assigned to them** — checked by comparing the order's `assigned_agent_id` against the calling agent's own profile, not just trusting the frontend to only show their own orders. Per rule: *"Do not allow an agent to update arbitrary orders."*
- **`FAILED` requires a `failure_reason`** — enforced in the service layer (`422` if missing), and it's automatically folded into the tracking event's note if no separate note was given.
- **Reschedule starts a new delivery attempt without touching the old one.** `delivery_attempt` increments, a fresh `delivery_attempts` document is created, `assigned_agent_id` is cleared (forcing a real re-assign call, not an implicit re-use of the same agent), and a `RESCHEDULED` tracking event is appended — but every event from the failed attempt stays exactly where it was. Verified by a test that reschedules and then re-checks the full history is unchanged plus one new entry.
- **Reassignment after reschedule correctly tags the new attempt number** — the `ASSIGNED` event for attempt 2 is distinguishable from attempt 1's in the same history.
- **Admin override is unambiguous in the audit trail** — the tracking note is always prefixed `[ADMIN OVERRIDE]` and `actor_role` is `admin`, so it can never be confused with an organic agent-driven transition when reviewing history later.
- **Agent load/stats update on terminal outcomes** — `DELIVERED` and `FAILED` both decrement `active_assignment_count` and increment the relevant completed/failed counter, keeping Phase 6's auto-assignment load-balancing accurate going forward.

Verified with 15 end-to-end tests covering the exact matrix from the assignment's evaluation criteria: valid transition chain, invalid/backwards transition rejection, wrong-agent rejection, FAILED-without-reason rejection, full immutable history through a failure and a reschedule, cross-customer reschedule blocking, double-reschedule rejection, correct re-assignment attempt tagging, admin override (with correct audit attribution), and role restrictions on every new endpoint.

## Notifications (Phase 9)

| Method | Path | Who | Notes |
|--------|------|-----|-------|
| GET   | `/api/notifications` | any logged-in user | Own notifications, newest first |
| GET   | `/api/notifications/unread-count` | any logged-in user | For a nav badge |
| PATCH | `/api/notifications/{id}/read` | owner only | Mark one as read |
| PATCH | `/api/notifications/read-all` | any logged-in user | Mark all of the user's own as read |

**Automatic, not manually triggered per-endpoint.** `services/tracking_service.append_tracking_event()` — the single choke point every status change in this codebase already flows through (order creation, assignment, agent updates, reschedule, admin override) — calls `notify_status_change()` right after updating `current_status`. This means every phase built so far already generates notifications correctly with zero changes to their own code; adding a notification trigger to some future new status-changing feature only requires it to go through `tracking_service`, which it would have to anyway to satisfy the immutable-history rule.

**`services/notification_service.py`** has two independent channels:
- **In-app** (`create_in_app_notification`) — always written, this is what the frontend's notification center reads from.
- **Email** (`send_email`) — genuinely SMTP-capable (reads `SMTP_HOST`/`PORT`/`USER`/`PASSWORD`/`FROM_EMAIL` from `.env`), but when SMTP isn't configured (the default in `.env.example`, since most people won't have real SMTP credentials during development), it does **not** pretend to succeed — it logs a clear `[DEV MODE — no SMTP configured]` line with exactly what would have been sent, and returns `False` so any caller can tell email genuinely didn't go out. This directly satisfies the spec's rule: *"Do not fake successful email delivery."* Plugging in a real provider (Gmail SMTP, SendGrid, Resend, etc.) later is just filling in those four env vars — no code changes needed.
- A failed/misconfigured notification never breaks the underlying status update itself — it's wrapped so a notification error is logged, not raised, keeping the order operation's success independent of notification delivery.

Verified with 10 tests: dev-mode fallback correctly reports non-delivery rather than lying, message composition for each status (including the FAILED reason getting folded in), a full order lifecycle generating exactly one notification per status change (7 events → 7 notifications), unread-count accuracy, mark-read/mark-all-read, and cross-user notification access denial.

## Frontend (Phase 10 — foundation)

```
frontend/
├── src/
│   ├── lib/api.js              # single axios client every request goes through — attaches JWT, normalizes errors, handles 401s
│   ├── context/
│   │   ├── AuthContext.jsx     # login state, session re-validation on load, role-aware redirect helper
│   │   └── ToastContext.jsx    # success/error toast feedback
│   ├── components/
│   │   ├── ui/                 # Button, Input/Select/Textarea, Card/StatCard/Badge/StatusBadge, Empty/Loading/Error states
│   │   └── ProtectedRoute.jsx  # role-gated route wrapper
│   ├── layouts/
│   │   ├── AuthLayout.jsx      # split-screen login/register shell
│   │   └── DashboardShell.jsx  # sidebar + topbar shell, shared across all three roles
│   ├── pages/                  # LoginPage, RegisterPage, PublicTrackPage, + one dashboard placeholder per role
│   └── App.jsx                 # router, role-based redirects
```

### Setup

```bash
cd frontend
npm install
cp .env.example .env   # points VITE_API_BASE_URL at your local backend
npm run dev
```

### Design system

Visual direction is a deliberate departure from the earlier LASTMILE mockups — white/neutral canvas, deep navy-charcoal text (`#0F172A`), indigo brand accent (`#4F46E5`), Inter for UI text, **JetBrains Mono for all data — tracking IDs, prices, weights, timestamps** — which is the one signature choice threaded through the whole app: numbers and codes read as operational data, not decoration, echoing the "manifest" feel from the original shipment-form mockup without carrying over its brutalist styling. Full token set lives in `tailwind.config.js` (`canvas`, `ink`, `brand`, `success`/`warning`/`danger`).

Every component in `components/ui/` is built once and reused everywhere — no page has bespoke one-off styling. `npm run build` produces a clean production bundle with zero errors.

### What's built vs. what's next

**Built:** auth flow (login/register, both wired to real backend calls), role-based routing and redirects, public no-login tracking page with a full visual timeline, customer dashboard with live stat cards pulled from `GET /api/orders`, and placeholder shells for agent/admin dashboards with the correct nav structure per the spec.

**Not yet built:** the multi-step shipment creation flow with live price preview, order detail/tracking pages inside the authenticated app, the full agent delivery-card workflow, and the full admin operations console (orders table, zones, rate cards, analytics charts) — these are Phase 11 and 12.

## Next: Phase 11 — Customer flow + Phase 12 — Agent & Admin dashboards

The multi-step "New Shipment" form (pickup → drop → package → type/payment → live price preview → confirm) wired to `/api/orders/quote` and `/api/orders`, the order detail/tracking page, and notification center — followed by the agent delivery board (status action buttons calling `/api/orders/{id}/status`) and the full admin console (orders table with filters, zone/rate card management UIs, and analytics charts on real aggregated data).
