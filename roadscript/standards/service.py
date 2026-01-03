"""Standards service that combines structured data with RAG retrieval."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from roadscript.ai.query_engine import QueryEngine, QueryResult
from roadscript.exceptions import StandardInterpolationRequiredError
from roadscript.standards.loader import StandardsLoader

LOG = logging.getLogger(__name__)

DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
VECTOR_ROOT = DATA_ROOT / "vector_index"


@dataclass
class StandardValue:
    """Resolved standards value with verification metadata."""

    value: Any
    units: Optional[str]
    source: str
    verified: bool
    verification: Dict[str, Any]
    citation: Optional[List[Dict[str, Any]]] = None


class StandardsService:
    """Resolve standards via structured tables with optional RAG verification."""

    def __init__(
        self,
        rag_enabled: Optional[bool] = None,
        strict: Optional[bool] = None,
        query_engine: Optional[QueryEngine] = None,
    ) -> None:
        self.loader = StandardsLoader()
        self.strict = strict if strict is not None else True
        self.rag_enabled = rag_enabled
        if self.rag_enabled is None:
            self.rag_enabled = os.getenv("ROADSCRIPT_RAG_ENABLED", "false").lower() == "true"
        self.query_engine = query_engine
        if self.rag_enabled and self.query_engine is None:
            if VECTOR_ROOT.exists():
                try:
                    self.query_engine = QueryEngine(VECTOR_ROOT)
                except ImportError as exc:
                    LOG.warning("RAG disabled: %s", exc)
                    self.rag_enabled = False
            else:
                LOG.warning("Vector index not found; disabling RAG.")
                self.rag_enabled = False

    def get_minimum_radius(self, design_speed: int) -> StandardValue:
        geom_standards = self.loader.get_geometry_standards()
        curve_standards = geom_standards["horizontal_curves"]["minimum_radius"]
        radius_table = curve_standards["design_speed_radius"]
        speed_key = str(design_speed)
        if speed_key not in radius_table:
            available = sorted(int(speed) for speed in radius_table.keys())
            raise StandardInterpolationRequiredError(
                f"Design speed {design_speed} mph not found in IDM minimum radius table. "
                f"Available speeds: {available}"
            )
        structured_value = radius_table[speed_key]
        units = curve_standards.get("units", "feet")

        return self._resolve_with_rag(
            query=(
                "INDOT design manual minimum horizontal curve radius "
                f"for design speed {design_speed} mph"
            ),
            structured_value=float(structured_value),
            units=units,
            design_speed=design_speed,
            value_count=1,
        )

    def get_vertical_curve_k(self, design_speed: int, curve_type: str) -> StandardValue:
        geom_standards = self.loader.get_geometry_standards()
        vert_curve = geom_standards["vertical_curves"]["minimum_length"]
        k_values = (
            vert_curve["crest_curves"]["K_values"]
            if curve_type == "crest"
            else vert_curve["sag_curves"]["K_values"]
        )
        speed_key = str(design_speed)
        if speed_key not in k_values:
            available = sorted(int(speed) for speed in k_values.keys())
            raise StandardInterpolationRequiredError(
                f"Design speed {design_speed} mph not found in IDM K-values. "
                f"Available speeds: {available}"
            )
        structured_value = k_values[speed_key]
        units = vert_curve.get("units", "feet")

        return self._resolve_with_rag(
            query=(
                "INDOT design manual vertical curve K-value "
                f"for {curve_type} curve at design speed {design_speed} mph"
            ),
            structured_value=float(structured_value),
            units=units,
            design_speed=design_speed,
            value_count=2,
            value_index=0 if curve_type == "crest" else 1,
        )

    def get_stopping_sight_distance(self, design_speed: int) -> StandardValue:
        geom_standards = self.loader.get_geometry_standards()
        ssd_table = geom_standards["vertical_curves"]["stopping_sight_distance"][
            "design_speed_ssd"
        ]
        speed_key = str(design_speed)
        if speed_key not in ssd_table:
            available = sorted(int(speed) for speed in ssd_table.keys())
            raise StandardInterpolationRequiredError(
                f"Design speed {design_speed} mph not found in IDM SSD table. "
                f"Available speeds: {available}"
            )
        structured_value = ssd_table[speed_key]
        units = geom_standards["vertical_curves"]["stopping_sight_distance"].get(
            "units", "feet"
        )

        return self._resolve_with_rag(
            query=(
                "INDOT design manual stopping sight distance "
                f"for design speed {design_speed} mph"
            ),
            structured_value=float(structured_value),
            units=units,
            design_speed=design_speed,
            value_count=1,
        )

    def get_clear_zone_width(
        self,
        design_speed: int,
        adt: int,
        slope_position: str,
        slope_category: str,
    ) -> StandardValue:
        clear_zone_standards = self.loader.get_clear_zone_standards()
        speed_based = clear_zone_standards.get("standards", {}).get("design_speed_based", {})
        speed_key = str(design_speed)
        if speed_key not in speed_based:
            available = sorted(int(speed) for speed in speed_based.keys())
            raise StandardInterpolationRequiredError(
                f"Design speed {design_speed} mph not found in IDM clear zone table. "
                f"Available speeds: {available}"
            )
        adt_category = self._get_adt_category(adt)
        speed_data = speed_based[speed_key]
        aadt_ranges = speed_data.get("aadt_ranges", {})
        aadt_data = aadt_ranges.get(adt_category, {})
        slope_key = "foreslopes" if slope_position == "foreslope" else "backslopes"
        slope_data = aadt_data.get(slope_key, {})
        structured_range = slope_data.get(slope_category)
        if structured_range is None:
            raise ValueError(
                "Clear zone width not found for IDM inputs: "
                f"design_speed={design_speed}, adt_category={adt_category}, "
                f"slope_position={slope_position}, slope_category={slope_category}"
            )

        units = clear_zone_standards.get("units", "feet")
        structured_min = float(structured_range.get("min"))
        structured_max = float(structured_range.get("max"))

        verification = {
            "structured_value": {"min": structured_min, "max": structured_max},
            "method": "structured",
        }
        citation = None

        if self.rag_enabled and self.query_engine:
            rag_result = self.query_engine.query_json(
                query=(
                    "INDOT clear zone width for design speed "
                    f"{design_speed} mph, ADT {adt}, "
                    f"{slope_position} {slope_category}"
                ),
                response_keys=["min_width", "max_width", "asterisk", "units"],
            )
            if rag_result and rag_result.raw:
                rag_value = rag_result.raw
                rag_min = _safe_float(rag_value.get("min_width"))
                rag_max = _safe_float(rag_value.get("max_width"))
                verification.update(
                    {
                        "rag_value": {"min": rag_min, "max": rag_max},
                        "method": rag_result.method,
                    }
                )
                citation = _build_citation(rag_result)
                if _matches_range(structured_min, structured_max, rag_min, rag_max):
                    return StandardValue(
                        value=structured_range,
                        units=units,
                        source="rag+structured",
                        verified=True,
                        verification=verification,
                        citation=citation,
                    )
                if not self.strict:
                    return StandardValue(
                        value={
                            "min": rag_min,
                            "max": rag_max,
                            "asterisk": bool(rag_value.get("asterisk", False)),
                        },
                        units=units,
                        source="rag_unverified",
                        verified=False,
                        verification=verification,
                        citation=citation,
                    )

        return StandardValue(
            value=structured_range,
            units=units,
            source="structured",
            verified=True,
            verification=verification,
            citation=citation,
        )

    def _resolve_with_rag(
        self,
        query: str,
        structured_value: float,
        units: Optional[str],
        design_speed: int,
        value_count: int,
        value_index: int = 0,
    ) -> StandardValue:
        verification = {"structured_value": structured_value, "method": "structured"}
        citation = None
        if self.rag_enabled and self.query_engine:
            rag_result = self.query_engine.query_speed_value(
                query=query,
                speed=design_speed,
                value_count=value_count,
            )
            if rag_result and rag_result.values and len(rag_result.values) > value_index:
                rag_value = rag_result.values[value_index]
                verification.update(
                    {"rag_value": rag_value, "method": rag_result.method}
                )
                citation = _build_citation(rag_result)
                if _matches_value(structured_value, rag_value):
                    return StandardValue(
                        value=structured_value,
                        units=units,
                        source="rag+structured",
                        verified=True,
                        verification=verification,
                        citation=citation,
                    )
                if not self.strict:
                    return StandardValue(
                        value=rag_value,
                        units=units,
                        source="rag_unverified",
                        verified=False,
                        verification=verification,
                        citation=citation,
                    )

        return StandardValue(
            value=structured_value,
            units=units,
            source="structured",
            verified=True,
            verification=verification,
            citation=citation,
        )

    @staticmethod
    def _get_adt_category(adt: int) -> str:
        if adt < 750:
            return "<750"
        if adt < 1500:
            return "750-1500"
        if adt <= 6000:
            return "1500-6000"
        return ">6000"


def _matches_value(structured_value: float, rag_value: float, tolerance: float = 0.5) -> bool:
    return abs(structured_value - rag_value) <= tolerance


def _matches_range(
    structured_min: float,
    structured_max: float,
    rag_min: Optional[float],
    rag_max: Optional[float],
    tolerance: float = 0.5,
) -> bool:
    if rag_min is None or rag_max is None:
        return False
    return (
        abs(structured_min - rag_min) <= tolerance
        and abs(structured_max - rag_max) <= tolerance
    )


def _safe_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_citation(rag_result: QueryResult) -> List[Dict[str, Any]]:
    citations = []
    for snippet in rag_result.snippets[:2]:
        citations.append(
            {
                "source": snippet.metadata.get("source"),
                "excerpt": snippet.text[:400],
            }
        )
    return citations
