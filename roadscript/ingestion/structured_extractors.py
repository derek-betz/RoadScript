"""Structured extraction helpers for INDOT tables."""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import re
from typing import Dict, List, Optional

LOG = logging.getLogger(__name__)

EXPECTED_SPEEDS = [30, 40, 45, 50, 60, 70, 80]


@dataclass
class ExtractionResult:
    """Container for structured extraction output."""

    geometry: Dict[str, object]
    clear_zones: Dict[str, object]
    metadata: Dict[str, object]


def _find_candidate_lines(text: str, keywords: List[str], window: int = 80) -> List[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    lowered = [line.lower() for line in lines]
    for idx, line in enumerate(lowered):
        if any(keyword in line for keyword in keywords):
            start = max(0, idx - 3)
            end = min(len(lines), idx + window)
            return lines[start:end]
    return lines


def _extract_table_lines(
    text: str,
    header_keywords: List[str],
    stop_keywords: List[str],
) -> List[str]:
    lines = text.splitlines()
    collecting = False
    collected: List[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if collecting:
                continue
            continue
        lowered = stripped.lower()
        if not collecting:
            if any(keyword in lowered for keyword in header_keywords):
                collecting = True
            continue
        if stop_keywords and any(keyword in lowered for keyword in stop_keywords):
            break
        collected.append(stripped)
    return collected


def _parse_speed_table(
    lines: List[str],
    value_count: int,
    speed_set: Optional[List[int]] = None,
) -> Dict[str, List[float]]:
    results: Dict[str, List[float]] = {}
    speeds = speed_set or EXPECTED_SPEEDS
    for line in lines:
        tokens = re.findall(r"\d+(?:\.\d+)?", line)
        if not tokens:
            continue
        speed = int(float(tokens[0]))
        if speed not in speeds:
            continue
        if str(speed) in results:
            continue
        if len(tokens) < value_count + 1:
            continue
        values = [float(value) for value in tokens[1:value_count + 1]]
        results[str(speed)] = values
    return results


def _extract_ssd_from_design_tables(text: str) -> Dict[str, int]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    candidate_values: Dict[int, List[int]] = defaultdict(list)
    for idx, line in enumerate(lines):
        if "stopping sight distance" not in line.lower():
            continue
        speeds = _find_design_speeds(lines, idx)
        if not speeds:
            continue
        values = _find_ssd_values(lines, idx, len(speeds))
        if not values or len(speeds) < 3 or len(values) != len(speeds):
            continue
        for speed, value in zip(speeds, values):
            candidate_values[speed].append(value)

    resolved: Dict[str, int] = {}
    for speed, values in candidate_values.items():
        counts = Counter(values)
        most_common = counts.most_common()
        max_count = most_common[0][1]
        candidates = [value for value, count in most_common if count == max_count]
        chosen = max(candidates)
        if len(counts) > 1:
            LOG.warning(
                "SSD values for %s mph=%s; choosing %s",
                speed,
                dict(counts),
                chosen,
            )
        resolved[str(speed)] = chosen
    return resolved


def _find_design_speeds(lines: List[str], ssd_index: int) -> List[int]:
    for back in range(1, 15):
        index = ssd_index - back
        if index < 0:
            break
        candidate = lines[index]
        if "design speed" in candidate.lower():
            speeds = _parse_speed_tokens(candidate)
            if speeds:
                return speeds
            speeds = _collect_speeds(lines[index + 1:ssd_index])
            return speeds
    return []


def _parse_speed_tokens(line: str) -> List[int]:
    mph_matches = re.findall(r"\b(\d{2,3})\s*mph\b", line, re.IGNORECASE)
    tokens = mph_matches
    if not tokens and ("design speed" in line.lower() or "mph" in line.lower()):
        tokens = re.findall(r"\b(\d{2,3})\b", line)
    if not tokens:
        stripped = line.strip()
        if stripped.isdigit():
            tokens = [stripped]
    speeds = []
    for token in tokens:
        speed = int(token)
        if 20 <= speed <= 80:
            speeds.append(speed)
    return speeds


def _find_ssd_values(lines: List[str], ssd_index: int, speed_count: int) -> List[int]:
    collected: List[int] = []
    for forward in range(1, 15):
        index = ssd_index + forward
        if index >= len(lines):
            break
        candidate = lines[index]
        lowered = candidate.lower()
        if "stopping sight distance" in lowered:
            continue
        if "42-1" in lowered or "manual" in lowered or "section" in lowered:
            continue
        if any(
            keyword in lowered
            for keyword in (
                "decision sight distance",
                "passing sight distance",
                "minimum radius",
                "superelevation",
                "horizontal sight distance",
                "vertical curvature",
                "k-value",
                "maximum grade",
                "minimum grade",
                "intersection sight distance",
            )
        ):
            break
        values = _parse_ssd_values(candidate)
        if values:
            collected.extend(values)
            if len(collected) >= speed_count:
                return collected[:speed_count]
    return collected[:speed_count]


def _collect_speeds(lines: List[str]) -> List[int]:
    speeds: List[int] = []
    for line in lines:
        speeds.extend(_parse_speed_tokens(line))
    return speeds


def _parse_ssd_values(line: str) -> List[int]:
    values: List[int] = []
    for token in re.findall(r"\d+(?:\.\d+)?", line):
        value = float(token)
        if value < 80:
            continue
        values.append(int(value))
    return values


def extract_geometry_standards(text: str) -> Dict[str, object]:
    """Extract geometry tables (radius, K-values, SSD) from text."""
    geometry: Dict[str, object] = {}

    radius_lines = _extract_table_lines(
        text,
        header_keywords=["minimum radius", "horizontal curve"],
        stop_keywords=["k value", "k values", "stopping sight distance"],
    )
    radius_rows = _parse_speed_table(radius_lines, value_count=1)
    if radius_rows:
        geometry.setdefault("horizontal_curves", {}).setdefault("minimum_radius", {})[
            "design_speed_radius"
        ] = {speed: int(values[0]) for speed, values in radius_rows.items()}
    else:
        LOG.warning("No minimum radius rows extracted.")

    k_lines = _extract_table_lines(
        text,
        header_keywords=["k value", "k values"],
        stop_keywords=["stopping sight distance"],
    )
    k_rows = _parse_speed_table(k_lines, value_count=2)
    if k_rows:
        crest = {speed: int(values[0]) for speed, values in k_rows.items()}
        sag = {speed: int(values[1]) for speed, values in k_rows.items()}
        geometry.setdefault("vertical_curves", {}).setdefault("minimum_length", {})[
            "crest_curves"
        ] = {"K_values": crest}
        geometry.setdefault("vertical_curves", {}).setdefault("minimum_length", {})[
            "sag_curves"
        ] = {"K_values": sag}
    else:
        LOG.warning("No K-value rows extracted.")

    ssd_table = _extract_ssd_from_design_tables(text)
    if not ssd_table:
        ssd_lines = _extract_table_lines(
            text,
            header_keywords=["stopping sight distance", "ssd"],
            stop_keywords=[],
        )
        ssd_rows = _parse_speed_table(ssd_lines, value_count=1)
        ssd_table = {speed: int(values[0]) for speed, values in ssd_rows.items()}
    if ssd_table:
        geometry.setdefault("vertical_curves", {}).setdefault(
            "stopping_sight_distance", {}
        )["design_speed_ssd"] = ssd_table
    else:
        LOG.warning("No SSD rows extracted.")

    return geometry


def extract_clear_zone_standards(text: str) -> Dict[str, object]:
    """Extract clear zone table data when the PDF text is flattened."""
    clear_zones: Dict[str, object] = {}
    pattern = re.compile(
        r"(?P<speed>\d{2})\s+(?P<adt><\d+|\d+-\d+|>\d+)\s+"
        r"(?P<slope_position>foreslope|backslope)\s+"
        r"(?P<slope_category>[A-Za-z0-9_]+)\s+"
        r"(?P<min>\d+)\s+(?P<max>\d+)",
        re.IGNORECASE,
    )
    entries = []
    for line in text.splitlines():
        match = pattern.search(line)
        if not match:
            continue
        entry = match.groupdict()
        entry["min"] = int(entry["min"])
        entry["max"] = int(entry["max"])
        entries.append(entry)

    if not entries:
        LOG.warning("No clear zone rows extracted.")
        return clear_zones

    for entry in entries:
        speed_key = entry["speed"]
        adt_key = entry["adt"]
        slope_position = entry["slope_position"].lower()
        slope_key = "foreslopes" if slope_position == "foreslope" else "backslopes"
        slope_category = entry["slope_category"]

        speed_bucket = clear_zones.setdefault("standards", {}).setdefault(
            "design_speed_based", {}
        ).setdefault(speed_key, {})
        aadt_bucket = speed_bucket.setdefault("aadt_ranges", {}).setdefault(adt_key, {})
        slope_bucket = aadt_bucket.setdefault(slope_key, {})
        slope_bucket[slope_category] = {
            "min": entry["min"],
            "max": entry["max"],
            "asterisk": False,
        }

    return clear_zones


def merge_structured_standards(
    base: Dict[str, object],
    extraction: ExtractionResult,
) -> Dict[str, object]:
    """Overlay extracted tables onto a base standards structure."""
    merged = deepcopy(base)
    geometry = extraction.geometry
    clear_zones = extraction.clear_zones

    if geometry:
        merged_geometry = merged.setdefault("geometry", {})
        _deep_update(merged_geometry, geometry)

    if clear_zones:
        merged_clear_zones = merged.setdefault("clear_zones", {})
        _deep_update(merged_clear_zones, clear_zones)

    metadata = merged.setdefault("metadata", {})
    metadata["ingested_at"] = datetime.now(timezone.utc).isoformat()
    if extraction.metadata:
        metadata.update(extraction.metadata)

    return merged


def _deep_update(target: Dict[str, object], updates: Dict[str, object]) -> None:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_update(target[key], value)
        else:
            target[key] = value
