"""
services/notification_service.py
Creates and reads in-app notifications (the bell icon in the navbar).
"""
from utils.database import execute, fetch_one, fetch_all


# Saves a notification for a user. `link` is the page it should open.
def notify(user_id, message, link=None, commit=True):
    execute(
        "INSERT INTO notifications (user_id, message, link) VALUES (%s, %s, %s)",
        (user_id, message[:255], link), commit=commit,
    )


# Returns how many unread notifications a user has.
def unread_count(user_id):
    row = fetch_one(
        "SELECT COUNT(*) AS total FROM notifications WHERE user_id = %s AND is_read = 0",
        (user_id,),
    )
    return row["total"]


# Returns the latest notifications of a user, newest first.
def get_notifications(user_id, limit=50):
    return fetch_all(
        "SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC, id DESC LIMIT %s",
        (user_id, limit),
    )


# Marks all notifications of a user as read.
def mark_all_read(user_id):
    execute("UPDATE notifications SET is_read = 1 WHERE user_id = %s AND is_read = 0", (user_id,))
