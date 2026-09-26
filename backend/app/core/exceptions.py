from fastapi import HTTPException, status


class DAMException(Exception):
    """Base exception for DAM application."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class AssetNotFoundError(DAMException):
    def __init__(self, asset_id: str):
        super().__init__(f"Asset not found: {asset_id}", "ASSET_NOT_FOUND")


class AssetProcessingError(DAMException):
    def __init__(self, asset_id: str, stage: str, reason: str):
        super().__init__(
            f"Processing failed for asset {asset_id} at stage {stage}: {reason}", "PROCESSING_ERROR"
        )
        self.asset_id = asset_id
        self.stage = stage
        self.reason = reason


class DuplicateAssetError(DAMException):
    def __init__(self, existing_asset_id: str, new_path: str):
        super().__init__(
            f"Duplicate asset detected. Existing: {existing_asset_id}, New path: {new_path}",
            "DUPLICATE_ASSET",
        )
        self.existing_asset_id = existing_asset_id
        self.new_path = new_path


class UnsupportedFileTypeError(DAMException):
    def __init__(self, file_path: str, mime_type: str):
        super().__init__(
            f"Unsupported file type: {mime_type} for {file_path}", "UNSUPPORTED_FILE_TYPE"
        )
        self.file_path = file_path
        self.mime_type = mime_type


class AIProviderError(DAMException):
    def __init__(self, provider: str, operation: str, reason: str):
        super().__init__(
            f"AI provider {provider} failed during {operation}: {reason}", "AI_PROVIDER_ERROR"
        )
        self.provider = provider
        self.operation = operation
        self.reason = reason


class VectorStoreError(DAMException):
    def __init__(self, operation: str, reason: str):
        super().__init__(f"Vector store {operation} failed: {reason}", "VECTOR_STORE_ERROR")
        self.operation = operation
        self.reason = reason


class DatabaseError(DAMException):
    def __init__(self, operation: str, reason: str):
        super().__init__(f"Database {operation} failed: {reason}", "DATABASE_ERROR")
        self.operation = operation
        self.reason = reason


class ConfigurationError(DAMException):
    def __init__(self, message: str):
        super().__init__(message, "CONFIGURATION_ERROR")


# HTTP Exception mappings
def to_http_exception(exc: DAMException) -> HTTPException:
    status_code_map = {
        "ASSET_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "PROCESSING_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "DUPLICATE_ASSET": status.HTTP_409_CONFLICT,
        "UNSUPPORTED_FILE_TYPE": status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        "AI_PROVIDER_ERROR": status.HTTP_503_SERVICE_UNAVAILABLE,
        "VECTOR_STORE_ERROR": status.HTTP_503_SERVICE_UNAVAILABLE,
        "DATABASE_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "CONFIGURATION_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    return HTTPException(
        status_code=status_code_map.get(exc.code, status.HTTP_500_INTERNAL_SERVER_ERROR),
        detail={"code": exc.code, "message": exc.message},
    )
