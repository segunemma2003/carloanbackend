"""
Moderation endpoints.
Reports, moderation actions, and admin tools.
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.models.moderation import Report, ModerationLog, ReportType, ReportReason, ReportStatus, ModerationAction
from app.models.ad import Ad, AdStatus
from app.models.user import User
from app.models.chat import Dialog, Message
from app.schemas.common import PaginatedResponse, MessageOut
from app.api.deps import get_current_user, require_moderator, require_admin


router = APIRouter()


# ============ Reports ============

class ReportCreate:
    """Schema for creating a report."""

    def __init__(
        self,
        report_type: ReportType,
        target_id: int,
        reason: ReportReason,
        description: Optional[str] = None,
    ):
        self.report_type = report_type
        self.target_id = target_id
        self.reason = reason
        self.description = description


class ReportResponse:
    """Schema for report response."""

    def __init__(self, report: Report):
        self.id = report.id
        self.reporter_id = report.reporter_id
        self.report_type = report.report_type
        self.target_id = report.target_id
        self.reason = report.reason
        self.description = report.description
        self.status = report.status
        self.resolved_by = report.resolved_by
        self.resolved_at = report.resolved_at
        self.resolution_note = report.resolution_note
        self.created_at = report.created_at


@router.post("/reports/ad/{ad_id}", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def report_ad(
    ad_id: int,
    reason: ReportReason,
    description: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Report an ad.
    """
    # Check ad exists
    result = await db.execute(
        select(Ad).where(Ad.id == ad_id, Ad.deleted_at.is_(None))
    )
    ad = result.scalar_one_or_none()

    if not ad:
        raise NotFoundError("Ad not found", "ad", ad_id)

    # Create report
    report = Report(
        reporter_id=current_user.id,
        report_type=ReportType.AD,
        target_id=ad_id,
        reason=reason,
        description=description,
    )
    db.add(report)
    await db.commit()

    return MessageOut(message="Report submitted successfully")


@router.post("/reports/user/{user_id}", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def report_user(
    user_id: int,
    reason: ReportReason,
    description: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Report a user.
    """
    # Check user exists
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError("User not found", "user", user_id)

    if user_id == current_user.id:
        raise ValidationError("Cannot report yourself")

    # Create report
    report = Report(
        reporter_id=current_user.id,
        report_type=ReportType.USER,
        target_id=user_id,
        reason=reason,
        description=description,
    )
    db.add(report)
    await db.commit()

    return MessageOut(message="Report submitted successfully")


@router.post("/reports/message/{message_id}", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def report_message(
    message_id: int,
    reason: ReportReason,
    description: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Report a chat message.
    """
    # Check message exists and user is participant
    result = await db.execute(
        select(Message).where(Message.id == message_id)
    )
    message = result.scalar_one_or_none()

    if not message:
        raise NotFoundError("Message not found", "message", message_id)

    # Verify user is participant in dialog
    result = await db.execute(
        select(Dialog).where(Dialog.id == message.dialog_id)
    )
    dialog = result.scalar_one_or_none()

    if not dialog or not dialog.is_participant(current_user.id):
        raise NotFoundError("Message not found", "message", message_id)

    # Create report
    report = Report(
        reporter_id=current_user.id,
        report_type=ReportType.MESSAGE,
        target_id=message_id,
        reason=reason,
        description=description,
    )
    db.add(report)
    await db.commit()

    return MessageOut(message="Report submitted successfully")


# ============ Moderation (Moderators Only) ============

@router.get("/reports", response_model=dict)
async def list_reports(
    status_filter: Optional[ReportStatus] = None,
    report_type: Optional[ReportType] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    moderator: User = Depends(require_moderator),
):
    """
    List reports (moderator only).
    """
    query = select(Report)

    if status_filter:
        query = query.where(Report.status == status_filter)
    if report_type:
        query = query.where(Report.report_type == report_type)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Report.created_at.desc())

    result = await db.execute(query)
    reports = result.scalars().all()

    return {
        "items": [
            {
                "id": r.id,
                "reporter_id": r.reporter_id,
                "report_type": r.report_type.value,
                "target_id": r.target_id,
                "reason": r.reason.value,
                "description": r.description,
                "status": r.status.value,
                "created_at": r.created_at.isoformat(),
            }
            for r in reports
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/reports/{report_id}", response_model=dict)
async def get_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    moderator: User = Depends(require_moderator),
):
    """
    Get report details (moderator only).
    """
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise NotFoundError("Report not found", "report", report_id)

    return {
        "id": report.id,
        "reporter_id": report.reporter_id,
        "report_type": report.report_type.value,
        "target_id": report.target_id,
        "reason": report.reason.value,
        "description": report.description,
        "status": report.status.value,
        "resolved_by": report.resolved_by,
        "resolved_at": report.resolved_at.isoformat() if report.resolved_at else None,
        "resolution_note": report.resolution_note,
        "created_at": report.created_at.isoformat(),
    }


@router.post("/reports/{report_id}/resolve", response_model=MessageOut)
async def resolve_report(
    report_id: int,
    status_value: ReportStatus,
    note: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    moderator: User = Depends(require_moderator),
):
    """
    Resolve a report (moderator only).
    """
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise NotFoundError("Report not found", "report", report_id)

    if report.status not in [ReportStatus.PENDING, ReportStatus.REVIEWING]:
        raise ValidationError("Report already resolved")

    report.resolve(moderator.id, status_value, note)

    # Log moderation action
    log = ModerationLog(
        moderator_id=moderator.id,
        action=ModerationAction.APPROVE if status_value == ReportStatus.RESOLVED else ModerationAction.REJECT,
        target_type=report.report_type.value,
        target_id=report.target_id,
        reason=note,
        report_id=report_id,
    )
    db.add(log)

    await db.commit()

    return MessageOut(message="Report resolved successfully")


@router.post("/reports/{report_id}/take-action", response_model=MessageOut)
async def take_action_on_report(
    report_id: int,
    action: ModerationAction,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    moderator: User = Depends(require_moderator),
):
    """
    Take action on reported content (moderator only).
    """
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise NotFoundError("Report not found", "report", report_id)

    # Perform action based on report type
    if report.report_type == ReportType.AD:
        result = await db.execute(
            select(Ad).where(Ad.id == report.target_id)
        )
        ad = result.scalar_one_or_none()

        if ad:
            if action == ModerationAction.BLOCK_AD:
                ad.status = AdStatus.REJECTED
                ad.rejection_reason = reason
                ad.moderated_by = moderator.id
                ad.moderated_at = datetime.now(timezone.utc)
            elif action == ModerationAction.DELETE_AD:
                ad.soft_delete()

    elif report.report_type == ReportType.USER:
        result = await db.execute(
            select(User).where(User.id == report.target_id)
        )
        user = result.scalar_one_or_none()

        if user:
            if action == ModerationAction.BLOCK_USER:
                user.is_blocked = True
                user.blocked_reason = reason
                user.blocked_at = datetime.now(timezone.utc)
            elif action == ModerationAction.UNBLOCK_USER:
                user.is_blocked = False
                user.blocked_reason = None
                user.blocked_at = None
            elif action == ModerationAction.WARNING:
                # TODO: Implement warning system
                pass

    elif report.report_type == ReportType.MESSAGE:
        result = await db.execute(
            select(Message).where(Message.id == report.target_id)
        )
        message = result.scalar_one_or_none()

        if message and action == ModerationAction.DELETE_MESSAGE:
            message.is_deleted_by_sender = True
            message.is_deleted_by_recipient = True

    # Log action
    log = ModerationLog(
        moderator_id=moderator.id,
        action=action,
        target_type=report.report_type.value,
        target_id=report.target_id,
        reason=reason,
        report_id=report_id,
    )
    db.add(log)

    # Resolve report
    report.resolve(moderator.id, ReportStatus.RESOLVED, f"Action taken: {action.value}")

    await db.commit()

    return MessageOut(message=f"Action '{action.value}' performed successfully")


# ============ Moderation Logs ============

@router.get("/logs", response_model=dict)
async def list_moderation_logs(
    action: Optional[ModerationAction] = None,
    moderator_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    List moderation logs (admin only).
    """
    query = select(ModerationLog)

    if action:
        query = query.where(ModerationLog.action == action)
    if moderator_id:
        query = query.where(ModerationLog.moderator_id == moderator_id)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(ModerationLog.created_at.desc())

    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "items": [
            {
                "id": log.id,
                "moderator_id": log.moderator_id,
                "action": log.action.value,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "reason": log.reason,
                "report_id": log.report_id,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ============ Statistics ============

@router.get("/stats", response_model=dict)
async def get_moderation_stats(
    db: AsyncSession = Depends(get_db),
    moderator: User = Depends(require_moderator),
):
    """
    Get moderation statistics (moderator only).
    """
    # Pending reports
    pending_result = await db.execute(
        select(func.count()).select_from(
            select(Report).where(Report.status == ReportStatus.PENDING).subquery()
        )
    )
    pending_reports = pending_result.scalar() or 0

    # Pending ads
    pending_ads_result = await db.execute(
        select(func.count()).select_from(
            select(Ad).where(
                Ad.status == AdStatus.PENDING,
                Ad.deleted_at.is_(None),
            ).subquery()
        )
    )
    pending_ads = pending_ads_result.scalar() or 0

    # Reports by type
    reports_by_type = {}
    for report_type in ReportType:
        count_result = await db.execute(
            select(func.count()).select_from(
                select(Report).where(
                    Report.report_type == report_type,
                    Report.status == ReportStatus.PENDING,
                ).subquery()
            )
        )
        reports_by_type[report_type.value] = count_result.scalar() or 0

    # Reports by reason
    reports_by_reason = {}
    for reason in ReportReason:
        count_result = await db.execute(
            select(func.count()).select_from(
                select(Report).where(
                    Report.reason == reason,
                    Report.status == ReportStatus.PENDING,
                ).subquery()
            )
        )
        reports_by_reason[reason.value] = count_result.scalar() or 0

    return {
        "pending_reports": pending_reports,
        "pending_ads": pending_ads,
        "reports_by_type": reports_by_type,
        "reports_by_reason": reports_by_reason,
    }

