Shipora — Last Mile Logistics

A full-stack last-mile logistics platform for managing shipments, delivery agents, tracking, pricing, zones, notifications, and administrative operations through a unified web application.

Built with a React frontend, FastAPI backend, and MongoDB, Shipora provides role-based workflows for customers, delivery agents, and administrators.

🔗 This Repo: https://github.com/piyali-22/shipora

Table of Contents
The Problem
How It Works
Features
Tech Stack
Project Structure
Running It Yourself
API
Database Design
Authentication & Security
Limitations
Future Improvements
Built By
The Problem

Last-mile delivery involves more than simply moving a package from one location to another.

A logistics system needs to handle:

shipment creation
customer information
delivery agents
delivery zones
pricing
order assignment
shipment tracking
delivery attempts
notifications
administrative operations

Without a centralized system, these operations become difficult to coordinate and track.

Shipora brings these workflows together into a single full-stack platform.

The goal is to provide a structured logistics workflow where an order can move from:

Customer
   ↓
Shipment Creation
   ↓
Zone & Pricing
   ↓
Agent Assignment
   ↓
Delivery
   ↓
Tracking Events
   ↓
Completion / Delivery Attempt
How It Works
┌──────────────────────────────┐
│        React Frontend        │
│       Vite + JavaScript      │
└──────────────┬───────────────┘
               │
               │ REST API
               ▼
┌──────────────────────────────┐
│        FastAPI Backend       │
│                              │
│ Authentication               │
│ Role Authorization           │
│ Order Management             │
│ Pricing                      │
│ Agent Assignment             │
│ Tracking                     │
│ Notifications                │
└──────────────┬───────────────┘
               │
               │ Motor / Async MongoDB
               ▼
┌──────────────────────────────┐
│         MongoDB Atlas        │
│                              │
│ Users                        │
│ Orders                       │
│ Agents                       │
│ Zones                        │
│ Rate Cards                   │
│ Tracking Events              │
│ Notifications                │
│ Delivery Attempts            │
│ Audit Logs                   │
└──────────────────────────────┘
Shipment Flow
Create Shipment
       ↓
Generate Tracking ID
       ↓
Determine Delivery Zone
       ↓
Calculate Applicable Rate
       ↓
Assign Delivery Agent
       ↓
Update Shipment Status
       ↓
Create Tracking Events
       ↓
Delivery Attempt
       ↓
Delivered / Further Attempt
Features
📦 Shipment Management
Create new shipments
Generate unique tracking IDs
View order details
Manage shipment status
View customer orders
Track delivery progress
Record delivery attempts
📍 Shipment Tracking

Shipora maintains a tracking history for each order rather than storing only the current status.

Each tracking event can be associated with:

order
status
timestamp
tracking history

This allows a shipment's journey to be followed throughout its lifecycle.

🚚 Delivery Agent Management

Administrators can manage delivery agents and their operational information.

The system supports:

agent profiles
agent availability
agent assignment
current delivery zones
assigned orders
🗺️ Zone Management

Delivery zones are managed using pincode-based configuration.

Administrators can:

create zones
associate pincodes with zones
activate/deactivate zones
manage zone information
💰 Rate Card & Pricing

Shipora includes a configurable rate-card system.

Rates can be configured based on:

order type
pricing scope
active/inactive status
delivery zone configuration

This keeps pricing logic separate from the rest of the order workflow.

👤 Role-Based Authentication

Different users have different responsibilities within the platform.

Customer
   │
   ├── Create shipment
   ├── View orders
   └── Track shipment

Agent
   │
   ├── View assigned orders
   ├── Update delivery progress
   └── Manage delivery activity

Admin
   │
   ├── Manage orders
   ├── Manage agents
   ├── Manage zones
   ├── Manage rate cards
   └── Monitor operations
🔔 Notifications

The backend includes a notification service for managing user notifications and notification history.

Email configuration is also supported through environment variables.

📊 Admin Operations

The admin interface provides dedicated management pages for:

Orders
Agents
Zones
Rate Cards
Dashboard operations
Tech Stack
Layer	Technologies
Frontend	React, JavaScript, Vite
Styling	Tailwind CSS
Backend	Python, FastAPI
API Server	Uvicorn
Validation	Pydantic
Database	MongoDB Atlas
Database Driver	Motor
Authentication	JWT
Password Security	Password Hashing
Version Control	Git, GitHub
Project Structure
shipora/
│
├── backend/
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── deps.py
│   │   └── security.py
│   │
│   ├── models/
│   │   ├── agent.py
│   │   ├── delivery_attempt.py
│   │   ├── notification.py
│   │   ├── order.py
│   │   ├── rate_card.py
│   │   ├── tracking_event.py
│   │   ├── user.py
│   │   └── zone.py
│   │
│   ├── routes/
│   │   ├── agents.py
│   │   ├── auth.py
│   │   ├── notifications.py
│   │   ├── orders.py
│   │   ├── rate_card.py
│   │   └── zones.py
│   │
│   ├── schemas/
│   │   ├── agent.py
│   │   ├── auth.py
│   │   ├── notification.py
│   │   ├── order.py
│   │   ├── pricing.py
│   │   ├── rate_card.py
│   │   └── zone.py
│   │
│   ├── services/
│   │   ├── assignment_service.py
│   │   ├── delivery_service.py
│   │   ├── notification_service.py
│   │   ├── order_service.py
│   │   ├── pricing_engine.py
│   │   ├── tracking_service.py
│   │   └── zone_service.py
│   │
│   ├── tests/
│   ├── utils/
│   │   └── tracking_id.py
│   │
│   ├── server.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   │
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   ├── layouts/
│   │   ├── lib/
│   │   ├── pages/
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   │
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example
│
├── .gitignore
├── README.md
└── ...
Running It Yourself
1. Clone the repository
git clone https://github.com/piyali-22/shipora.git
cd shipora
2. Backend
cd backend

Create a virtual environment:

python -m venv venv

Activate it on Windows:

venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt
3. Configure MongoDB

Create:

backend/.env

using:

backend/.env.example

as the template.

Example:

MONGO_URI=your_mongodb_connection_string
MONGO_DB_NAME=shipora

JWT_SECRET=your_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

FRONTEND_ORIGIN=http://localhost:5173

SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=notifications@shipora.app

APP_ENV=development

Do not commit .env to GitHub.

4. Start the Backend

From the backend directory:

python -m uvicorn server:app --reload

The API will be available at:

http://127.0.0.1:8000

Health check:

http://127.0.0.1:8000/api/health

Interactive API documentation:

http://127.0.0.1:8000/docs
5. Start the Frontend

Open another terminal:

cd frontend

Install dependencies:

npm install

Start the development server:

npm run dev

The frontend will normally be available at:

http://localhost:5173
API

The backend is organized around REST endpoints for the main logistics workflows.

Authentication
/auth

Handles registration, login, and authentication-related operations.

Orders
/orders

Handles shipment and order operations.

Agents
/agents

Handles delivery-agent operations.

Zones
/zones

Handles delivery-zone management.

Rate Cards
/rate-card

Handles configurable pricing information.

Notifications
/notifications

Handles notification-related operations.

Database Design

MongoDB is organized into collections representing the main entities of the logistics system.

users
   │
   ├── orders
   │      │
   │      ├── tracking_events
   │      └── delivery_attempts
   │
   └── agents

zones
   │
   └── rate_cards

notifications
audit_logs

Indexes are created for frequently queried fields such as:

email
tracking ID
customer ID
assigned agent
order status
timestamps
zone
agent availability

This helps keep common queries efficient as the dataset grows.

Authentication & Security

Shipora uses JWT-based authentication for protected API access.

Security-related functionality includes:

JWT access tokens
Password hashing
Protected routes
Role-based authorization
Environment-based secrets
MongoDB credentials stored outside source control
Frontend protected routes

Sensitive configuration is excluded from Git using .gitignore.

Screenshots

Screenshots can be added here as the application UI evolves.

Example:

## Screenshots

### Customer Dashboard

![Customer Dashboard](screenshots/customer-dashboard.png)

### Admin Dashboard

![Admin Dashboard](screenshots/admin-dashboard.png)

### Shipment Tracking

![Shipment Tracking](screenshots/tracking.png)
What I Learned

Building Shipora involved working across the complete application stack rather than treating the frontend and backend as separate pieces.

Some of the main areas covered were:

Designing REST APIs with FastAPI
Structuring a backend using routes, schemas, models, and services
Async MongoDB operations using Motor
JWT authentication and authorization
Role-based application workflows
Database indexing
React component and page organization
Frontend API integration
Environment-based configuration
Git and GitHub workflow
Limitations
Email functionality requires SMTP configuration.
Local development requires a MongoDB connection.
Deployment configuration is not included yet.
Some operational workflows are represented through application logic rather than integration with real logistics providers.
Real-time GPS/driver location tracking is not currently implemented.
Future Improvements
📍 Real-time delivery-agent location tracking
🗺️ Route optimization for delivery agents
📱 Mobile application for delivery agents
🔔 Real-time push notifications
📊 Advanced logistics analytics
💳 Online payment integration
☁️ Production cloud deployment
🧪 Expanded automated test coverage
⚙️ CI/CD pipeline
📦 Integration with external shipping/carrier APIs
Built By
Piyali Khaitan

B.Tech CSE Student | Full-Stack Development & Software Engineering

GitHub: @piyali-22