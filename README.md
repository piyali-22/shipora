# Shipora — Last Mile Logistics

A full-stack last-mile logistics platform for managing shipments, delivery agents, tracking, pricing, zones, notifications, and administrative operations through a unified web application.

Built with a **React frontend, FastAPI backend, and MongoDB**, Shipora provides role-based workflows for customers, delivery agents, and administrators.

🔗 **Repository:** https://github.com/piyali-22/shipora

---

## Table of Contents

- [The Problem](#the-problem)
- [How It Works](#how-it-works)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Running It Yourself](#running-it-yourself)
- [Database Design](#database-design)
- [Authentication & Security](#authentication--security)
- [API Overview](#api-overview)
- [Application Roles](#application-roles)
- [Future Improvements](#future-improvements)
- [Current Status](#current-status)
- [Built By](#built-by)

---

## The Problem

Last-mile delivery involves coordinating customers, shipments, delivery agents, delivery zones, pricing, tracking, and notifications across multiple operational workflows.

Without a centralized system, managing these processes can become difficult to track and maintain.

**Shipora closes that gap:** customers can create and track shipments, agents can manage assigned deliveries, and administrators can manage orders, zones, agents, and pricing through a unified platform.

The project focuses on bringing the major components of a last-mile logistics workflow into a single full-stack application.

---

## How It Works

```text
Customer / Agent / Admin
          |
          v
   +------------------+
   |  React Frontend  |
   |      (Vite)      |
   +--------+---------+
            |
            | REST API
            v
   +------------------+
   | FastAPI Backend  |
   |                  |
   | Routes           |
   | Services         |
   | Authentication   |
   | Validation       |
   +--------+---------+
            |
            v
   +------------------+
   |     MongoDB      |
   |                  |
   | Users            |
   | Orders           |
   | Agents           |
   | Zones            |
   | Rate Cards       |
   | Tracking Events  |
   | Notifications    |
   +------------------+
```

### Shipment Workflow

```text
Customer creates shipment
          ↓
Pricing is calculated
          ↓
Tracking ID is generated
          ↓
Order is stored in MongoDB
          ↓
Delivery agent is assigned
          ↓
Order moves through delivery statuses
          ↓
Tracking events are recorded
          ↓
Shipment is delivered
```

---

## Features

### 👤 Authentication & Authorization

- User registration and login
- JWT-based authentication
- Protected application routes
- Role-based workflows
- Customer, Agent, and Admin access
- Secure password handling

### 📦 Shipment & Order Management

- Create new shipments
- Generate unique tracking IDs
- View customer orders
- View detailed order information
- Manage order statuses
- Assign delivery agents
- Record delivery attempts
- Track shipment progress

### 🚴 Delivery Agent Management

- Agent dashboard
- View assigned deliveries
- Agent profile management
- Agent availability tracking
- Zone assignment
- Delivery tracking

### 📍 Delivery Zone Management

Administrators can manage delivery zones and their associated pincodes.

- Create and manage zones
- Activate or deactivate zones
- Manage zone pincodes
- Associate agents with zones

### 💰 Pricing & Rate Cards

Shipora includes a centralized rate-card system for managing delivery pricing.

- Create rate cards
- Manage active and inactive rates
- Configure pricing based on order type
- Configure pricing based on scope
- Apply pricing rules to shipments

### 📍 Shipment Tracking

Each shipment can have a history of tracking events.

- Unique tracking IDs
- Order status updates
- Tracking event history
- Timestamped events
- Public shipment tracking

### 🔔 Notifications

The platform supports notifications for important delivery events.

- Recipient-based notifications
- Notification history
- Timestamped notifications
- Notification management

### 🛡️ Admin Operations

Administrators can manage the major logistics operations from dedicated dashboards.

- Order management
- Agent management
- Zone management
- Rate card management
- Shipment monitoring

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React |
| Build Tool | Vite |
| Backend | Python, FastAPI |
| API Server | Uvicorn |
| Database | MongoDB |
| Database Driver | Motor |
| Validation | Pydantic |
| Authentication | JWT |
| Styling | CSS / Tailwind CSS |
| Package Management | npm / pip |
| Version Control | Git & GitHub |

---

## Project Structure

```text
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
│   ├── .env.example
│   ├── requirements.txt
│   └── server.py
│
├── frontend/
│   │
│   ├── public/
│   │
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
│   ├── .env.example
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js
│   └── tailwind.config.js
│
├── .gitignore
├── README.md
└── ...
```

---

## Running It Yourself

### 1. Clone the Repository

```bash
git clone https://github.com/piyali-22/shipora.git
cd shipora
```

### 2. Backend

Move into the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file using `.env.example` as a reference.

Start the backend:

```bash
python -m uvicorn server:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/api/health
```

### 3. Frontend

Open another terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Vite will display the local frontend URL in the terminal.

---

## Database Design

Shipora uses MongoDB for storing application data.

### Main Collections

| Collection | Purpose |
|---|---|
| `users` | Customer, agent, and administrator accounts |
| `orders` | Shipment and order information |
| `agents` | Delivery agent information |
| `zones` | Delivery zones and pincodes |
| `rate_cards` | Delivery pricing configuration |
| `tracking_events` | Shipment tracking history |
| `delivery_attempts` | Delivery attempt records |
| `notifications` | User notifications |
| `audit_logs` | Operational audit information |

Indexes are created for frequently queried fields such as:

- Email
- Tracking ID
- Customer ID
- Agent ID
- Order status
- Creation timestamp
- Zone
- Notification recipient

---

## Authentication & Security

Shipora uses JWT-based authentication for protected API endpoints.

The authentication flow is:

```text
User Login
    ↓
Credentials Validated
    ↓
JWT Token Generated
    ↓
Token Sent With Protected Requests
    ↓
Backend Validates Token
    ↓
Authorized Resource Returned
```

Sensitive configuration is stored using environment variables.

The actual `.env` file is excluded from Git using `.gitignore`.

Example configuration:

```env
MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/
MONGO_DB_NAME=shipora

JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

FRONTEND_ORIGIN=http://localhost:5173

SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=notifications@shipora.app

APP_ENV=development
```

> **Never commit real database credentials, JWT secrets, or other sensitive environment variables to GitHub.**

---

## API Overview

The backend is organized into modular API routes.

| Route | Purpose |
|---|---|
| `/auth` | Registration and authentication |
| `/orders` | Shipment and order operations |
| `/agents` | Delivery agent operations |
| `/zones` | Delivery zone management |
| `/rate-card` | Pricing and rate card management |
| `/notifications` | Notification operations |
| `/api/health` | Application and database health check |

The API can also be explored through FastAPI's interactive Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

---

## Application Roles

### Customer

Customers can:

- Register and log in
- Create shipments
- View orders
- Track shipments
- View order details
- Receive notifications
- Manage their profile

### Delivery Agent

Agents can:

- Log in to the platform
- View assigned deliveries
- Track orders
- Manage delivery information
- Manage their profile
- Manage availability

### Administrator

Administrators can:

- View and manage orders
- Manage delivery agents
- Manage zones
- Manage rate cards
- Monitor logistics operations

---

## Future Improvements

Some possible improvements for future versions include:

- 📍 Real-time GPS delivery tracking
- 🗺️ Route optimization
- 🤖 Automated delivery-agent assignment
- 📊 Advanced logistics analytics
- 📱 SMS and email notification integration
- 💳 Payment gateway integration
- 🧪 Expanded automated test coverage
- 🔄 CI/CD pipeline
- ☁️ Production deployment
- 📈 Advanced operational reporting

---

## Current Status

**Development**

The core full-stack architecture is implemented with:

- React frontend
- FastAPI backend
- MongoDB database
- JWT authentication
- Role-based workflows
- Shipment management
- Delivery-agent management
- Tracking
- Pricing
- Zones
- Notifications
- Administrative dashboards

---

## Built By

**Piyali Khaitan**

B.Tech Computer Science & Engineering

GitHub: https://github.com/piyali-22/shipora

---

## License

This project is developed for educational and development purposes.