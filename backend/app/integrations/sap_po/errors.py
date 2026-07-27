class SapPoError(RuntimeError):
    """Base sanitized SAP PO integration error."""


class SapPoConfigurationError(SapPoError):
    """Required SAP PO configuration is missing or invalid."""


class SapPoConnectionError(SapPoError):
    """SAP PO could not be reached or returned an invalid response."""
