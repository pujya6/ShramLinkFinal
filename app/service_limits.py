"""Database-backed counters. No raw text, audio, API keys or prompts are logged."""

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError

from app.models import ServiceBudget, ServiceMetric, db


def ensure_row(model, key):
    if db.session.get(model, key) is None:
        db.session.add(model(key=key, count=0))
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


def consume(key, limit):
    ensure_row(ServiceBudget, key)
    result = db.session.execute(
        update(ServiceBudget)
        .where(ServiceBudget.key == key, ServiceBudget.count < limit)
        .values(count=ServiceBudget.count + 1)
    )
    db.session.commit()
    return result.rowcount == 1


def metric(key, amount=1):
    ensure_row(ServiceMetric, key)
    db.session.execute(
        update(ServiceMetric)
        .where(ServiceMetric.key == key)
        .values(count=ServiceMetric.count + amount)
    )
    db.session.commit()
