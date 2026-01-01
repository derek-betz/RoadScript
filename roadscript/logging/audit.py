"""
Audit Logger Module

Provides professional, structured logging for all calculations and validations.
Designed for legal defensibility and audit trail requirements.
"""

import logging
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import sys


class AuditLogger:
    """
    Professional audit logger for engineering calculations.
    
    Provides structured logging with timestamps, calculation context,
    and results for legal defensibility and Standard of Care compliance.
    """
    
    def __init__(self, name: str = "roadscript", log_file: Optional[str] = None):
        """
        Initialize the audit logger.
        
        Args:
            name: Logger name (default: "roadscript")
            log_file: Optional file path for log output
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Console handler with detailed format
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def log_calculation(
        self,
        calculation_type: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        standards_version: str,
        status: str = "SUCCESS"
    ) -> None:
        """
        Log a calculation with full audit trail.
        
        Args:
            calculation_type: Type of calculation (e.g., "buffer_strip", "clear_zone")
            inputs: Input parameters used in calculation
            outputs: Calculated results
            standards_version: Version of standards used
            status: Calculation status (SUCCESS, WARNING, ERROR)
        """
        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "calculation_type": calculation_type,
            "status": status,
            "standards_version": standards_version,
            "inputs": inputs,
            "outputs": outputs
        }
        
        log_message = f"AUDIT: {calculation_type} - {status}"
        log_detail = json.dumps(audit_entry, indent=2)
        
        if status == "SUCCESS":
            self.logger.info(f"{log_message}\n{log_detail}")
        elif status == "WARNING":
            self.logger.warning(f"{log_message}\n{log_detail}")
        else:
            self.logger.error(f"{log_message}\n{log_detail}")
    
    def log_validation(
        self,
        validation_type: str,
        inputs: Dict[str, Any],
        validation_results: Dict[str, Any],
        status: str = "PASS"
    ) -> None:
        """
        Log a validation check with results.
        
        Args:
            validation_type: Type of validation performed
            inputs: Inputs being validated
            validation_results: Results of validation checks
            status: Validation status (PASS, FAIL, WARNING)
        """
        validation_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "validation_type": validation_type,
            "status": status,
            "inputs": inputs,
            "results": validation_results
        }
        
        log_message = f"VALIDATION: {validation_type} - {status}"
        log_detail = json.dumps(validation_entry, indent=2)
        
        if status == "PASS":
            self.logger.info(f"{log_message}\n{log_detail}")
        elif status == "WARNING":
            self.logger.warning(f"{log_message}\n{log_detail}")
        else:
            self.logger.error(f"{log_message}\n{log_detail}")
    
    def log_standards_load(self, standards_version: str, metadata: Dict[str, Any]) -> None:
        """
        Log standards loading for audit trail.
        
        Args:
            standards_version: Version of standards loaded
            metadata: Standards metadata
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "STANDARDS_LOADED",
            "version": standards_version,
            "metadata": metadata
        }
        
        log_message = f"STANDARDS LOADED: Version {standards_version}"
        log_detail = json.dumps(entry, indent=2)
        self.logger.info(f"{log_message}\n{log_detail}")
    
    def log_error(self, error_type: str, error_message: str, context: Dict[str, Any]) -> None:
        """
        Log an error with context.
        
        Args:
            error_type: Type of error
            error_message: Error message
            context: Additional context
        """
        error_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error_type": error_type,
            "message": error_message,
            "context": context
        }
        
        log_message = f"ERROR: {error_type}"
        log_detail = json.dumps(error_entry, indent=2)
        self.logger.error(f"{log_message}\n{log_detail}")


# Global logger instance
_audit_logger = None


def get_audit_logger(log_file: Optional[str] = None) -> AuditLogger:
    """
    Get the global audit logger instance.
    
    Args:
        log_file: Optional file path for log output
        
    Returns:
        AuditLogger instance
    """
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(log_file=log_file)
    return _audit_logger
