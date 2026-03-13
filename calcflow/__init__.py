"""CalcFlow - Interactive menu-driven CLI for VASP workflows."""

__version__ = "0.1.0"


class CalcFlowError(Exception):
    """Base exception for all CalcFlow errors."""


class PresetNotFoundError(CalcFlowError):
    """Raised when a named preset cannot be found."""


class CalculationError(CalcFlowError):
    """Raised when a VASP calculation fails."""


class JobSubmissionError(CalcFlowError):
    """Raised when job submission to the scheduler fails."""
