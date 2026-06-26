"""Structured logging configuration."""
import logging
import sys
from datetime import datetime
from typing import Any, Dict

import structlog
from .config import settings


def configure_logging() -> None:
    """Configure structured logging for the application."""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer() if not settings.DEBUG else structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a logger instance."""
    return structlog.get_logger(name)


class BedrockCallLogger:
    """Logger specifically for AWS Bedrock API calls."""
    
    def __init__(self):
        self.logger = get_logger("bedrock")
    
    def log_request(
        self,
        agent_name: str,
        model_id: str,
        request_payload: Dict[str, Any],
        review_id: str = None
    ) -> Dict[str, Any]:
        """Log a Bedrock request and return metadata for tracking."""
        metadata = {
            "agent_name": agent_name,
            "model_id": model_id,
            "review_id": review_id,
            "timestamp": datetime.utcnow().isoformat(),
            "request_size": len(str(request_payload))
        }
        self.logger.info(
            "bedrock_request_started",
            **metadata
        )
        return metadata
    
    def log_response(
        self,
        metadata: Dict[str, Any],
        response_payload: Dict[str, Any],
        input_tokens: int,
        output_tokens: int,
        latency_ms: int,
        success: bool = True,
        error: str = None
    ) -> None:
        """Log a Bedrock response."""
        log_data = {
            **metadata,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "latency_ms": latency_ms,
            "success": success,
            "response_size": len(str(response_payload))
        }
        
        if error:
            log_data["error"] = error
            self.logger.error("bedrock_request_failed", **log_data)
        else:
            self.logger.info("bedrock_request_completed", **log_data)


bedrock_logger = BedrockCallLogger()
