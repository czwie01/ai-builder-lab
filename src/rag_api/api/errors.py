"""RFC 9457 problem-details error contract.

Every error the API emits — validation, guardrail, unexpected — shares
one shape and the application/problem+json content type, with the
request_id included as an extension member.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from rag_api.api.logging import request_id_var
from rag_api.domain.errors import GuardrailViolation

logger = logging.getLogger("rag_api.errors")

PROBLEM_CONTENT_TYPE = "application/problem+json"
GUARDRAIL_PROBLEM_TYPE = "urn:ai-builder-lab:guardrail-violation"
VALIDATION_PROBLEM_TYPE = "urn:ai-builder-lab:validation-error"


def problem_response(
    *,
    status_code: int,
    title: str,
    detail: str,
    type_: str = "about:blank",
    extra: dict[str, Any] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": type_,
        "title": title,
        "status": status_code,
        "detail": detail,
    }
    request_id = request_id_var.get()
    if request_id is not None:
        body["request_id"] = request_id
    if extra:
        body.update(extra)
    return JSONResponse(body, status_code=status_code, media_type=PROBLEM_CONTENT_TYPE)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def on_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return problem_response(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            title="Request validation failed",
            detail="One or more request fields are invalid.",
            type_=VALIDATION_PROBLEM_TYPE,
            extra={
                "errors": [
                    {
                        "loc": [str(part) for part in error.get("loc", ())],
                        "msg": error.get("msg", ""),
                        "type": error.get("type", ""),
                    }
                    for error in exc.errors()
                ]
            },
        )

    @app.exception_handler(GuardrailViolation)
    async def on_guardrail_violation(request: Request, exc: GuardrailViolation) -> JSONResponse:
        return problem_response(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            title="Question rejected by guardrail",
            detail=exc.reason,
            type_=GUARDRAIL_PROBLEM_TYPE,
        )

    @app.exception_handler(Exception)
    async def on_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled error")
        return problem_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            title="Internal server error",
            detail="An unexpected error occurred.",
        )
