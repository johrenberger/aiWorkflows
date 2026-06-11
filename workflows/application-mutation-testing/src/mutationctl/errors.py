class MutationCtlError(Exception):
    """Base error for mutationctl."""


class ConfigError(MutationCtlError):
    """Raised when workflow configuration is invalid."""


class RepoInputError(MutationCtlError):
    """Raised when repository input is invalid."""


class StateError(MutationCtlError):
    """Raised when workflow state cannot be persisted."""


class LedgerRenderError(MutationCtlError):
    """Raised when ledger rendering fails."""


class UnsafeOperationError(MutationCtlError):
    """Raised when a blocked operation is requested."""
