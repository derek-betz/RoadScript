"""
Validation Audit Logger

Writes validation results to a persistent audit log.
"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from roadscript.validators.base import ValidationResult

DEFAULT_LOG_FILE = "roadscript_audit.log"


def log_validation_result(
    result: "ValidationResult",
    revision_tag: str,
    log_file: str = DEFAULT_LOG_FILE
) -> None:
    """
    Log IDM 43-4.0 validation results with revision tags for audit traceability.

    Args:
        result: ValidationResult containing IDM reference and K-values
        revision_tag: Standards revision tag (for example, IDM_2024_v1)
        log_file: Path to the audit log file
    """
    entry: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "revision_tag": revision_tag,
        "validation_result": {
            "status": result.status,
            "message": result.message,
            "idm_reference": result.idm_reference,
            "actual_k": result.actual_k,
            "required_k": result.required_k,
        },
    }

    with open(log_file, "a", encoding="utf-8") as audit_file:
        audit_file.write(json.dumps(entry, ensure_ascii=True) + "\n")
