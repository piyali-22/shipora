"""
GET   /api/notifications              — logged-in user's own notifications, newest first
GET   /api/notifications/unread-count — count of unread notifications
PATCH /api/notifications/{id}/read    — mark a single notification as read
PATCH /api/notifications/read-all     — mark all of the user's notifications as read
"""
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, status

from core.database import get_db
from core.deps import get_current_user
from schemas.auth import UserPublic
from schemas.notification import NotificationPublic

router = APIRouter()


def _to_notification_public(doc: dict) -> NotificationPublic:
    return NotificationPublic(
        id=str(doc["_id"]),
        order_id=doc.get("order_id"),
        tracking_id=doc.get("tracking_id"),
        title=doc["title"],
        message=doc["message"],
        is_read=doc.get("is_read", False),
        created_at=doc["created_at"],
    )


@router.get("", response_model=list[NotificationPublic])
async def list_my_notifications(current_user: UserPublic = Depends(get_current_user)):
    db = get_db()
    docs = await db.notifications.find({"recipient_id": current_user.id}).sort("created_at", -1).to_list(length=200)
    return [_to_notification_public(d) for d in docs]


@router.get("/unread-count")
async def get_unread_count(current_user: UserPublic = Depends(get_current_user)):
    db = get_db()
    count = await db.notifications.count_documents({"recipient_id": current_user.id, "is_read": False})
    return {"unread_count": count}


@router.patch("/read-all")
async def mark_all_read(current_user: UserPublic = Depends(get_current_user)):
    db = get_db()
    result = await db.notifications.update_many(
        {"recipient_id": current_user.id, "is_read": False}, {"$set": {"is_read": True}}
    )
    return {"marked_read": result.modified_count}


@router.patch("/{notification_id}/read", response_model=NotificationPublic)
async def mark_notification_read(notification_id: str, current_user: UserPublic = Depends(get_current_user)):
    db = get_db()
    try:
        oid = ObjectId(notification_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid notification id.")

    doc = await db.notifications.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    if doc["recipient_id"] != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This notification doesn't belong to you.")

    result = await db.notifications.find_one_and_update(
        {"_id": oid}, {"$set": {"is_read": True}}, return_document=True
    )
    return _to_notification_public(result)
