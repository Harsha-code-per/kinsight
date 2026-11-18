"""Signed synthetic laboratory events and atomic delivery bookkeeping."""

# ruff: noqa: B008

import hmac
import json
import re
import time
from typing import Annotated, Literal

from fastapi import Depends, HTTPException, Request
from pydantic import Field, TypeAdapter
from sqlalchemy.orm import Session

from services.consent import sharing
from services.consent.audit import append_event
from services.consent.policy import Actor, reference
from services.lifecycle import cfg, store

from .auth import Identity, secret
from .pilot_routes import SandboxIntake, Subject, record_intake
from .schemas import StrictModel

PATH = "/api/integrations/lab/events"
SIGNING_SECRET = "KINSIGHT_LAB_SIGNING_SECRET"
LAB = Actor("synthetic-lab", "lab")
MAX_BODY_SIZE = 16_384
WINDOW = 300


class StageEvent(StrictModel):
    kind: Literal["stage"]
    subject_id: Subject
    stage: Annotated[int, Field(ge=2, le=7)]


class ReportEvent(StrictModel):
    kind: Literal["report"]
    report: SandboxIntake


EVENT = TypeAdapter(Annotated[StageEvent | ReportEvent, Field(discriminator="kind")])


def signature(key: bytes, timestamp: str, delivery: str, body: bytes) -> str:
    return hmac.digest(key, f"POST {PATH}\n{timestamp}\n{delivery}\n".encode() + body, "sha256").hex()


def audit_rejection(db: Session, code: str) -> None:
    salt = secret("KINSIGHT_AUDIT_SALT")
    append_event(
        db,
        actor_ref=reference(LAB.id, salt),
        action="lab_delivery",
        resource_type="sandbox_report",
        resource_ref=reference(PATH, salt),
        decision="deny",
        reason_code=code,
    )
    db.commit()


def register(app, db_session, limit):
    @app.post(PATH)
    async def receive(request: Request, db: Session = Depends(db_session)):
        stamp = request.headers.get("x-lab-timestamp", "")
        delivery = request.headers.get("x-lab-delivery", "")
        supplied = request.headers.get("x-lab-signature", "")
        now = time.time()
        if (
            not re.fullmatch(r"[0-9]{1,12}", stamp)
            or abs(now - int(stamp)) > WINDOW
            or not re.fullmatch(r"[a-f0-9]{32}", delivery)
            or not re.fullmatch(r"[a-f0-9]{64}", supplied)
        ):
            raise HTTPException(401, "Lab authentication unavailable")
        raw = bytearray()
        async for chunk in request.stream():
            if len(raw) + len(chunk) > MAX_BODY_SIZE:
                raise HTTPException(413, "Lab event is too large")
            raw.extend(chunk)
        body = bytes(raw)
        if not hmac.compare_digest(signature(secret(SIGNING_SECRET), stamp, delivery, body), supplied):
            raise HTTPException(401, "Lab authentication unavailable")
        limit(db, Identity(LAB, LAB.id, 0))
        nonce = "signed-lab:" + delivery
        if db.get(store.LcTokenUse, nonce) is not None:
            audit_rejection(db, "lab_replayed")
            raise HTTPException(409, "Lab delivery already received")

        try:
            event = EVENT.validate_json(body)
            subject = event.subject_id if isinstance(event, StageEvent) else event.report.subject_id
            sample = store.lab_sample(db, subject, for_update=True)
            if isinstance(event, StageEvent):
                if event.stage != sample.stage + 1:
                    raise HTTPException(409, "Lab stage is out of sequence")
                next_stage = event.stage
            else:
                if sample.stage < 7:
                    raise HTTPException(409, "Sample has not finished processing")
                report = record_intake(db, event.report, LAB)
                next_stage = (
                    len(cfg()["lab_stages"]) if report.status in {"final", "amended", "corrected"} else sample.stage
                )
            if next_stage > sample.stage:
                sample.stage = next_stage
                times = json.loads(sample.times)
                times[str(next_stage)] = now
                sample.times = json.dumps(times)
                db.add(sample)
            # shortcut: keep delivery IDs for the sandbox lifetime, add expiry before sustained lab traffic.
            db.add(store.LcTokenUse(nonce=nonce))
            sharing.log_change(db, LAB, subject, "lab_delivery_applied", secret("KINSIGHT_AUDIT_SALT"))
            db.commit()
        except (ValueError, HTTPException):
            db.rollback()
            audit_rejection(db, "lab_event_rejected")
            raise
        return {"stage": sample.stage, "is_synthetic": True}
