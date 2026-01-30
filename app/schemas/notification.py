"""
Pydantic schemas for notifications.
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import ConfigDict
from app.schemas.common import BaseSchema, TimestampSchema
from app.models.notification import NotificationType


class NotificationResponse(TimestampSchema):
    id: int
    user_id: int
    type: NotificationType
    title: Optional[str]
    body: Optional[str]
    data: Optional[Any]
    is_read: bool
    is_archived: bool


class NotificationListResponse(BaseSchema):
    items: list[NotificationResponse]
    total: int


class NotificationPreferenceResponse(BaseSchema):
    id: int
    user_id: int
    email: bool
    sms: bool
    push: bool


class NotificationPreferenceUpdate(BaseSchema):
    email: Optional[bool]
    sms: Optional[bool]
    push: Optional[bool]


class NotificationMarkRead(BaseSchema):
    message_ids: list[int]
"""Pydantic schemas for Notification API."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: str
    title: Optional[str]
    body: Optional[str]
    data: Optional[str]
    is_read: bool
    is_archived: bool
    created_at: datetime

    class Config:
        orm_mode = True


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    page: int
    page_size: int


class NotificationPreferenceResponse(BaseModel):
    user_id: int
    email_new_message: bool
    email_moderation: bool
    sms_new_message: bool
    sms_moderation: bool

    class Config:
        orm_mode = True


class NotificationPreferenceUpdate(BaseModel):
    email_new_message: Optional[bool]
    email_moderation: Optional[bool]
    sms_new_message: Optional[bool]
    sms_moderation: Optional[bool]


class NotificationMarkRead(BaseModel):
    notification_ids: list[int]
"""Pydantic schemas for notifications."""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: str
    title: Optional[str]
    body: Optional[str]
    is_read: bool
    is_archived: bool
    created_at: datetime

    class Config:
        orm_mode = True


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    page: int
    page_size: int


class NotificationPreferenceResponse(BaseModel):
    id: int
    user_id: int
    email_new_message: bool
    email_moderation: bool
    sms_new_message: bool
    push_new_message: bool
    created_at: datetime

    class Config:
        orm_mode = True


class NotificationPreferenceUpdate(BaseModel):
    email_new_message: Optional[bool]
    email_moderation: Optional[bool]
    sms_new_message: Optional[bool]
    push_new_message: Optional[bool]


class NotificationMarkRead(BaseModel):
    notification_id: int
"""Pydantic schemas for notifications and preferences."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.common import BaseSchema


class NotificationResponse(BaseSchema):
    id: int
    user_id: int
    type: str
    title: Optional[str] = None
    body: Optional[str] = None
    payload: Optional[str] = None
    is_read: bool
    is_archived: bool
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    page: int
    page_size: int
    pages: int


class NotificationPreferenceResponse(BaseSchema):
    id: int
    user_id: int
    email_new_message: bool
    email_moderation: bool
    sms_new_message: bool
    push_new_message: bool
    created_at: datetime
    updated_at: datetime


class NotificationPreferenceUpdate(BaseModel):
    email_new_message: Optional[bool] = None
    email_moderation: Optional[bool] = None
    sms_new_message: Optional[bool] = None
    push_new_message: Optional[bool] = None


class NotificationMarkRead(BaseModel):
    ids: list[int]
"""Pydantic schemas for notifications API."""
from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: str
    title: Optional[str]
    body: Optional[str]
    payload: Optional[Any]
    is_read: bool
    is_archived: bool
    created_at: datetime

    class Config:
        orm_mode = True


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    page: int
    page_size: int


class NotificationPreferenceResponse(BaseModel):
    user_id: int
    email_new_message: bool
    email_system: bool
    sms_new_message: bool
    push_new_message: bool

    class Config:
        orm_mode = True


class NotificationPreferenceUpdate(BaseModel):
    email_new_message: Optional[bool]
    email_system: Optional[bool]
    sms_new_message: Optional[bool]
    push_new_message: Optional[bool]


class NotificationMarkRead(BaseModel):
    message_ids: list[int]
