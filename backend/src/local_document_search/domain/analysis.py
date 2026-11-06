"""Token posizionali; analyzer previsti in M2."""
from dataclasses import dataclass
from .documents import require_nonnegative


@dataclass(frozen=True)
class Token:
    term: str
    position: int

    def __post_init__(self) -> None:
        if not self.term.strip():
            raise ValueError("Termine vuoto")
        require_nonnegative(self.position, "position")
