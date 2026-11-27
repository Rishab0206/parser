from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.logging import logger

class BSIException(Exception):
    def __init__(self, error_code: str, message: str, status_code: int = 400, details: dict = None):
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}

class PasswordRequiredException(BSIException):
    def __init__(self, message: str = "PDF is password protected. Please provide a password."):
        super().__init__(error_code="PASSWORD_REQUIRED", message=message, status_code=400)

class InvalidPasswordException(BSIException):
    def __init__(self, message: str = "Incorrect PDF password. Please enter the correct password and try again."):
        super().__init__(error_code="INCORRECT_PASSWORD", message=message, status_code=400)

class CorruptedPdfException(BSIException):
    def __init__(self, message: str = "Invalid or corrupted PDF file. Unable to open document."):
        super().__init__(error_code="INVALID_FILE", message=message, status_code=400)

class UnsupportedEncryptionException(BSIException):
    def __init__(self, message: str = "Unsupported PDF encryption method."):
        super().__init__(error_code="UNSUPPORTED_ENCRYPTION", message=message, status_code=400)

class NoTransactionsFoundException(BSIException):
    def __init__(self, message: str = "Statement could not be parsed. Please check the PDF password, file quality or statement format."):
        super().__init__(error_code="NO_TRANSACTIONS_FOUND", message=message, status_code=422)

class OcrExtractionFailedException(BSIException):
    def __init__(self, message: str = "Scanned PDF OCR extraction failed or returned no readable text."):
        super().__init__(error_code="OCR_FAILED", message=message, status_code=422)

class UnauthorizedException(BSIException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(error_code="UNAUTHORIZED", message=message, status_code=401)

class ForbiddenException(BSIException):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(error_code="FORBIDDEN", message=message, status_code=403)

async def bsi_exception_handler(request: Request, exc: BSIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict):
        error_code = detail.get("error_code", "REQUEST_ERROR")
        message = detail.get("message", "Request error")
        details = detail.get("details", {})
    else:
        error_code = "REQUEST_ERROR"
        message = str(detail)
        details = {"field": None, "page_no": None, "narration": None}

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": error_code,
            "message": message,
            "details": details
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first_err = errors[0] if errors else {}
    field = ".".join(str(l) for l in first_err.get("loc", []))
    msg = first_err.get("msg", "Validation error")
    return JSONResponse(
        status_code=422,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": f"Validation failed on {field}: {msg}",
            "details": {"field": field, "page_no": None, "narration": None, "errors": errors}
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred while processing the request.",
            "details": {"field": None, "page_no": None, "narration": None, "error_type": type(exc).__name__}
        }
    )

