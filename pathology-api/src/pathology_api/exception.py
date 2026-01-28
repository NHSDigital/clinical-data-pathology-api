class ValidationError(Exception):
    """
    Custom exception for validation errors in FHIR resources.
    Note that any message here will be provided in the error response returned to users.
    """

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
