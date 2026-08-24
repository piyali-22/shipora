"""
Notification service.

Two responsibilities, deliberately kept separate:
  1. send_email() — a real SMTP-capable email sender. If SMTP_HOST
     isn't configured (the .env default), it does NOT pretend to send
     an email — it logs clearly that it's in dev-mode fallback and
     what would have been sent. This satisfies the spec's explicit
     rule: "Do not fake successful email delivery."
  2. create_in_app_notification() — writes a notification document
     that the frontend's notification center reads from directly,
     independent of whether email succeeded.

notify_status_change() is the single entry point tracking_service
calls after every status change — it composes the right message for
the status and fires both channels.
"""
import logging
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText

from motor.motor_asyncio import AsyncIOMotorDatabase

from core.config import get_settings

logger = logging.getLogger("shipora.notifications")

_STATUS_MESSAGES = {
    "CREATED": "Your shipment {tracking_id} has been placed and is being processed.",
    "ASSIGNED": "Your shipment {tracking_id} has been assigned to a delivery agent.",
    "PICKED_UP": "Your shipment {tracking_id} has been picked up.",
    "IN_TRANSIT": "Your shipment {tracking_id} is in transit.",
    "OUT_FOR_DELIVERY": "Your shipment {tracking_id} is out for delivery.",
    "DELIVERED": "Your shipment {tracking_id} has been delivered. Thank you for using Shipora!",
    "FAILED": "Delivery attempt for shipment {tracking_id} was unsuccessful.{reason_clause}",
    "RESCHEDULED": "Your shipment {tracking_id} has been rescheduled. We'll notify you once a new agent is assigned.",
}


def compose_status_message(status: str, tracking_id: str, note: str | None = None) -> str:
    template = _STATUS_MESSAGES.get(status, "Your shipment {tracking_id} status changed to " + status + ".")
    reason_clause = f" Reason: {note}" if status == "FAILED" and note else ""
    return template.format(tracking_id=tracking_id, reason_clause=reason_clause)


def send_email(*, to_email: str, subject: str, body: str) -> bool:
    """
    Sends a real email if SMTP is configured. Otherwise logs a clear
    dev-mode notice instead of silently no-op'ing or claiming success —
    the caller can tell from the return value whether it actually sent.
    """
    settings = get_settings()

    if not settings.smtp_host:
        logger.info(
            "[DEV MODE — no SMTP configured] Would send email to %s | Subject: %s | Body: %s",
            to_email, subject, body,
        )
        return False

    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from_email
        msg["To"] = to_email

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            server.starttls()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from_email, [to_email], msg.as_string())
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to send email to %s: %s", to_email, exc)
        return False


async def create_in_app_notification(
    db: AsyncIOMotorDatabase, *, recipient_id: str, title: str, message: str,
    order_id: str | None = None, tracking_id: str | None = None,
) -> dict:
    doc = {
        "recipient_id": recipient_id,
        "order_id": order_id,
        "tracking_id": tracking_id,
        "title": title,
        "message": message,
        "is_read": False,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.notifications.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def notify_status_change(
    db: AsyncIOMotorDatabase, *, order_doc: dict, status: str, note: str | None = None,
) -> None:
    """
    Fired once per status change, for the CUSTOMER on that order.
    Per the spec: 'Send a notification to the customer whenever order
    status changes.' Both channels are attempted; a failed email never
    blocks the in-app notification from being created.
    """
    customer = await db.users.find_one({"_id": _to_object_id(order_doc["customer_id"])})
    if not customer:
        logger.warning("Could not find customer %s to notify for order %s", order_doc["customer_id"], order_doc["tracking_id"])
        return

    message = compose_status_message(status, order_doc["tracking_id"], note)
    title = f"Shipment {order_doc['tracking_id']}: {status.replace('_', ' ').title()}"

    await create_in_app_notification(
        db, recipient_id=str(customer["_id"]), title=title, message=message,
        order_id=str(order_doc["_id"]), tracking_id=order_doc["tracking_id"],
    )

    send_email(to_email=customer["email"], subject=title, body=message)


def _to_object_id(value: str):
    from bson import ObjectId
    return ObjectId(value)
