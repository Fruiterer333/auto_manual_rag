class AutoManualRAGError(Exception):
    """Base exception for Auto Manual RAG Assistant."""


class NotImplementedRAGFeatureError(AutoManualRAGError):
    """Raised when a planned RAG feature has not been implemented yet."""
