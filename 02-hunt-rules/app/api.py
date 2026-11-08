"""HTTP-слой движка хантинга."""
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app import config, events, rules, service

router = APIRouter()


class RuleText(BaseModel):
    text: str


class EvaluateRequest(BaseModel):
    rule_ids: list[str] = Field(default_factory=list)


@router.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": config.SERVICE_NAME, "version": config.VERSION}


@router.get("/api/rules")
def list_rules() -> dict:
    return {"items": service.describe(), "sources": service.rule_sources()}


@router.post("/api/rules")
def create_rule(payload: RuleText) -> dict:
    return service.add_custom(payload.text)


@router.get("/api/events")
def list_events() -> dict:
    return {"count": service.event_count(), "items": list(events.load()[:30])}


@router.post("/api/evaluate")
def evaluate(payload: EvaluateRequest) -> dict:
    return service.run(tuple(payload.rule_ids))


@router.post("/api/replay")
def replay(payload: EvaluateRequest) -> dict:
    return service.replay(tuple(payload.rule_ids))


@router.get("/api/detections")
def detections() -> dict:
    return {"items": list(service.stored_detections())}


@router.post("/api/validate")
def validate(payload: RuleText) -> dict:
    return describe(rules.parse(payload.text, "validate"))


def describe(rule: rules.Rule) -> dict:
    return {"ok": True, "rule": rules.as_dict(rule)}
