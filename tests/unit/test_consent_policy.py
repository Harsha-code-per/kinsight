import time

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from services.consent.audit import verify_chain
from services.consent.models import AuditEvent, Base, Consent
from services.consent.policy import Actor, ResourceRef, decide

SALT = b"synthetic-test-audit-salt-32-bytes!"


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def test_default_deny_and_every_decision_audited(db):
    actor = Actor("synthetic-a", "person")
    for resource, fields, expected in [
        (ResourceRef("unknown", "x", actor.id), {"status"}, False),
        (ResourceRef("result", "x", actor.id), {"status"}, True),
        (ResourceRef("result", "x", "other"), {"status"}, False),
    ]:
        assert (
            decide(actor, resource, "own_care", fields, session=db, audit_salt=SALT).allowed
            is expected
        )
    assert len(db.scalars(select(AuditEvent)).all()) == 3


def test_scope_purpose_expiry_owner_first_and_revocation(db):
    grant = Consent(
        grantor_id="a",
        grantee_id="b",
        resource_type="result",
        resource_id="r",
        scope="condition_findings",
        fields=["status"],
        condition_ids=["COND_001"],
        purpose="family_notification",
        expires_at=time.time() + 60,
        text_shown_hash="a" * 64,
    )
    db.add(grant)
    db.flush()
    actor = Actor("b", "relative")
    resource = ResourceRef("result", "r", "a", "COND_001", True)

    def check(purpose="family_notification"):
        return decide(
            actor, resource, purpose, {"status", "panel_version"}, session=db, audit_salt=SALT
        )

    assert check().allowed_fields == {"status"}
    assert not check("employment").allowed
    assert not check("own_care").allowed
    grant.revoked_at = time.time()
    assert not check().allowed
    grant.revoked_at = None
    grant.expires_at = time.time() - 1
    assert not check().allowed


@settings(max_examples=40, deadline=None)
@example(
    requested={"status", "panel_version"}, granted={"status"}, matching_condition=True,
    active=True, unknown_field=False, role="counsellor", grant_matches_actor=True,
    owner_viewed=True, assigned=True,
)
@given(
    requested=st.sets(st.sampled_from(["status", "panel_version", "condition_id"])),
    granted=st.sets(st.sampled_from(["status", "panel_version"])),
    matching_condition=st.booleans(),
    active=st.booleans(),
    unknown_field=st.booleans(),
    role=st.sampled_from(["relative", "partner", "counsellor", "analyst"]),
    grant_matches_actor=st.booleans(),
    owner_viewed=st.booleans(),
    assigned=st.booleans(),
)
def test_family_projection_and_revocation(
    requested, granted, matching_condition, active, unknown_field, role, grant_matches_actor, owner_viewed, assigned,
):
    engine = create_engine("sqlite://")
    purpose = "counselling" if role == "counsellor" else "family_notification"
    try:
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            consent = Consent(
                grantor_id="a",
                grantee_id="b" if grant_matches_actor else "unrelated",
                resource_type="result",
                resource_id="r",
                scope="condition_findings",
                fields=sorted(granted),
                condition_ids=["COND_001"],
                purpose=purpose,
                expires_at=time.time() + (60 if active else -1),
                text_shown_hash="a" * 64,
            )
            session.add(consent)
            session.flush()
            actor = Actor("b", role)
            resource = ResourceRef(
                "result", "r", "a", "COND_001" if matching_condition else "COND_002",
                owner_viewed=owner_viewed, assigned_to="b" if assigned else None,
                assignment_expires_at=time.time() + 60, assignment_reason="case-review",
            )
            fields = requested | {"private"} if unknown_field else requested
            decision = decide(actor, resource, purpose, fields, session=session, audit_salt=SALT)
            permitted = set()
            if (
                active and matching_condition and not unknown_field and grant_matches_actor and owner_viewed
                and (role in {"relative", "partner"} or (role == "counsellor" and assigned))
            ):
                permitted = requested & granted
            assert decision.allowed_fields == permitted
            assert decision.allowed is bool(permitted)
            consent.revoked_at = time.time()
            session.flush()
            revoked = decide(actor, resource, purpose, fields, session=session, audit_salt=SALT)
            assert not revoked.allowed and not revoked.allowed_fields
            assert len(session.scalars(select(AuditEvent)).all()) == 2
            assert verify_chain(session)
    finally:
        engine.dispose()
