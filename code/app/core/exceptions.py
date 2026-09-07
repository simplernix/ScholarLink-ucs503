class DomainError(Exception):
    """Base class for business-rule errors raised from the service layer."""


class EmailAlreadyRegisteredError(DomainError):
    pass


class InvalidCredentialsError(DomainError):
    pass


class InactiveUserError(DomainError):
    pass


class InvalidTokenError(DomainError):
    pass


class UserNotFoundError(DomainError):
    pass


class PermissionDeniedError(DomainError):
    pass


class PaperNotFoundError(DomainError):
    pass


class PaperFileMissingError(DomainError):
    pass
