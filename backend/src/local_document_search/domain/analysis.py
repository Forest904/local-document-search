"""Analyzer deterministici condivisi da indicizzazione e query."""
from dataclasses import dataclass
import unicodedata
from .documents import require_nonnegative


@dataclass(frozen=True)
class Token:
    term: str
    position: int

    def __post_init__(self) -> None:
        if not self.term.strip():
            raise ValueError("Termine vuoto")
        require_nonnegative(self.position, "position")


def prepare_filename(filename: str) -> str:
    """Rimuove soltanto l'ultimo suffisso supportato dal nome sorgente."""
    stem, separator, suffix = filename.rpartition(".")
    return stem if separator and suffix.casefold() in {"txt", "md", "pdf"} else filename


def _tokens(text: str) -> tuple[Token, ...]:
    if text.isascii():
        folded = text.casefold()
        tokens = []
        current = []
        for char in folded:
            if "a" <= char <= "z" or "0" <= char <= "9":
                current.append(char)
            elif current:
                tokens.append(Token("".join(current), len(tokens)))
                current.clear()
        if current:
            tokens.append(Token("".join(current), len(tokens)))
        return tuple(tokens)
    text = unicodedata.normalize("NFC", unicodedata.normalize("NFC", text).casefold())
    terms = []
    current = []
    for char in text:
        category = unicodedata.category(char)[0]
        if category in {"L", "N"} or (category == "M" and current):
            current.append(char)
        elif current:
            terms.append("".join(current))
            current = []
    if current:
        terms.append("".join(current))
    return tuple(Token(term, position) for position, term in enumerate(terms))


class ContentAnalyzer:
    def analyze(self, text: str) -> tuple[Token, ...]:
        return _tokens(text)


class FilenameAnalyzer:
    def analyze(self, text: str) -> tuple[Token, ...]:
        # NFC rende equivalenti anche i confini CamelCase con accenti decomposti.
        text = unicodedata.normalize("NFC", text)
        units: list[str] = []
        for char in text:
            if unicodedata.category(char).startswith("M") and units:
                units[-1] += char
            else:
                units.append(char)
        split = []
        for i, unit in enumerate(units):
            char = unit[0]
            previous = units[i - 1][0] if i else ""
            following = units[i + 1][0] if i + 1 < len(units) else ""
            if previous and (
                (previous.islower() and char.isupper())
                or (previous.isupper() and char.isupper() and following.islower())
                or (previous.isalpha() and char.isnumeric())
                or (previous.isnumeric() and char.isalpha())
            ):
                split.append(" ")
            split.append(unit)
        return _tokens("".join(split))
