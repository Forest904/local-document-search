"""Preferenze desktop indipendenti dagli snapshot e da Qt."""
from dataclasses import dataclass
from typing import Protocol

from .contracts import InvalidInput


@dataclass(frozen=True)
class DesktopPreferences:
    language: str = "it"
    theme: str = "light"

    def __post_init__(self):
        if self.language not in ("it", "en") or self.theme not in ("light", "dark"):
            raise InvalidInput("Preferenze non valide")


class PreferencesRepositoryPort(Protocol):
    def load_preferences(self) -> DesktopPreferences: ...

    def save_preferences(self, value: DesktopPreferences) -> None: ...


class GetDesktopPreferences:
    def __init__(self, repository: PreferencesRepositoryPort):
        self.repository = repository

    def execute(self):
        return self.repository.load_preferences()


class SaveDesktopPreferences:
    def __init__(self, repository: PreferencesRepositoryPort):
        self.repository = repository

    def execute(self, value: DesktopPreferences):
        if not isinstance(value, DesktopPreferences):
            raise InvalidInput("Preferenze non valide")
        self.repository.save_preferences(value)
        return value
