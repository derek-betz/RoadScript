"""FastAPI service for RoadScript calculations and knowledge ingestion."""

from __future__ import annotations

import logging
import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from roadscript.agent_hub import fetch_knowledge, register_agent
from roadscript.core.clear_zones import ClearZoneCalculator
from roadscript.core.geometry import GeometryCalculator
from roadscript.knowledge_store import add_item, query_items
from roadscript.standards.loader import StandardsLoader

load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI(title="RoadScript API", version="1.0.0")


class ClearZoneRequest(BaseModel):
    design_speed: int = Field(..., ge=20, le=80)
    adt: int = Field(..., ge=0)
    slope_position: str
    slope_category: str


class GeometryRadiusRequest(BaseModel):
    design_speed: int = Field(..., ge=20, le=80)


class VerticalCurveRequest(BaseModel):
    design_speed: int = Field(..., ge=20, le=80)
    grade_difference: float = Field(..., gt=0)
    curve_type: str = Field(..., pattern="^(crest|sag)$")


class KnowledgeItem(BaseModel):
    source: str
    topic: str
    payload: dict[str, Any]
    tags: list[str] = Field(default_factory=list)


@app.on_event("startup")
def on_startup() -> None:
    register_agent()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/agent/info")
def agent_info() -> dict[str, Any]:
    return {
        "name": os.getenv("AGENT_NAME", "RoadScript"),
        "capabilities": ["standards", "calculations", "knowledge"],
    }


@app.get("/standards/metadata")
def standards_metadata() -> dict[str, Any]:
    loader = StandardsLoader()
    return loader.get_metadata()


@app.post("/calc/clear-zone")
def calculate_clear_zone(payload: ClearZoneRequest) -> dict[str, Any]:
    calculator = ClearZoneCalculator()
    try:
        return calculator.calculate(
            design_speed=payload.design_speed,
            adt=payload.adt,
            slope_position=payload.slope_position,
            slope_category=payload.slope_category,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/calc/geometry/minimum-radius")
def calculate_minimum_radius(payload: GeometryRadiusRequest) -> dict[str, Any]:
    calculator = GeometryCalculator()
    try:
        return calculator.calculate_minimum_radius(design_speed=payload.design_speed)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/calc/geometry/vertical-curve")
def calculate_vertical_curve(payload: VerticalCurveRequest) -> dict[str, Any]:
    calculator = GeometryCalculator()
    try:
        return calculator.calculate_vertical_curve_length(
            design_speed=payload.design_speed,
            grade_difference=payload.grade_difference,
            curve_type=payload.curve_type,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/knowledge/query")
def knowledge_query(
    source: str | None = None,
    topic: str | None = None,
    tag: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    return query_items(source=source, topic=topic, tag=tag, limit=limit)


@app.post("/knowledge/ingest")
def knowledge_ingest(payload: KnowledgeItem) -> dict[str, Any]:
    item_id = add_item(
        {
            "source": payload.source,
            "topic": payload.topic,
            "payload": payload.payload,
            "tags": payload.tags,
        }
    )
    return {"id": item_id}


@app.get("/agent/knowledge/query")
def agent_query(
    source: str | None = None,
    topic: str | None = None,
    tag: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    return fetch_knowledge(source=source, topic=topic, tag=tag, limit=limit)


def start_server() -> None:
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "9001"))
    uvicorn.run("roadscript.api.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    start_server()
