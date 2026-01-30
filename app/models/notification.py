"""
Notification models: Notification and NotificationPreference
"""
import enum
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    Integer,
    String,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class NotificationType(str, enum.Enum):
    NEW_MESSAGE = "new_message"
    AD_APPROVED = "ad_approved"
    AD_REJECTED = "ad_rejected"
    MODERATION = "moderation"
    SYSTEM = "system"


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    body: Mapped[Optional[str]] = mapped_column(String(4000), nullable=True)
    data: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user = relationship("User")

    def mark_as_read(self) -> None:
        self.is_read = True

    def archive(self) -> None:
        self.is_archived = True


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    email: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sms: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    push: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user = relationship("User")
"""Notification models: Notification and NotificationPreference."""
from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class NotificationType(str, enum.Enum):
    NEW_MESSAGE = "new_message"
    AD_APPROVED = "ad_approved"
    AD_REJECTED = "ad_rejected"
    MODERATION = "moderation"
    SYSTEM = "system"


class Notification(Base, TimestampMixin):
    """User notification stored in DB."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string for extra payload
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user = relationship("User", backref="notifications")

    def mark_as_read(self) -> None:
        self.is_read = True

    def archive(self) -> None:
        self.is_archived = True


class NotificationPreference(Base):
    """User notification preferences."""

    __tablename__ = "notification_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)

    email_new_message: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_moderation: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sms_new_message: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sms_moderation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user = relationship("User", backref="notification_preferences")
"""Notification models: Notification and NotificationPreference."""
from datetime import datetime, timezone
import enum
from typing import Optional

from sqlalchemy import (
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class NotificationType(str, enum.Enum):
    NEW_MESSAGE = "new_message"
    AD_APPROVED = "ad_approved"
    AD_REJECTED = "ad_rejected"
    SYSTEM = "system"


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    meta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user = relationship("User", backref="notifications")

    def mark_as_read(self) -> None:
        self.is_read = True

    def archive(self) -> None:
        self.is_archived = True


class NotificationPreference(Base, TimestampMixin):
    __tablename__ = "notification_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    email_new_message: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_moderation: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sms_new_message: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    push_new_message: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user = relationship("User", backref="notification_preferences")
"""
Notification models: Notification and NotificationPreference.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class NotificationType(str, Enum):
    NEW_MESSAGE = "new_message"
    AD_APPROVED = "ad_approved"
    AD_REJECTED = "ad_rejected"
    GENERIC = "generic"


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user = relationship("User")

    def mark_as_read(self) -> None:
        self.is_read = True

    def archive(self) -> None:
        self.is_archived = True


class NotificationPreference(Base, TimestampMixin):
    __tablename__ = "notification_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    email_new_message: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_moderation: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sms_new_message: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    push_new_message: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user = relationship("User")
"""Notification models: Notification and NotificationPreference."""
import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class NotificationType(str, enum.Enum):
    NEW_MESSAGE = "new_message"
    AD_APPROVED = "ad_approved"
    AD_REJECTED = "ad_rejected"
    SYSTEM = "system"


class Notification(Base, TimestampMixin):
    """User notification record."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # optional JSON payload as string
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user = relationship("User", backref="notifications")

    def mark_as_read(self) -> None:
        self.is_read = True

    def archive(self) -> None:
        self.is_archived = True


class NotificationPreference(Base, TimestampMixin):
    """Stores per-user notification preferences."""

    __tablename__ = "notification_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    email_new_message: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_system: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sms_new_message: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    push_new_message: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user = relationship("User", backref="notification_preferences")
