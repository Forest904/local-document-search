"""Sessione console TXT; nessun algoritmo di indicizzazione nell'interfaccia."""
import argparse
import sys

from local_document_search.application.contracts import InvalidInput, SearchRequest
from local_document_search.application.errors import ApplicationError
from local_document_search.domain.queries import SearchField
from .composition import compose_cli


FIELDS = {"nome": SearchField.FILENAME, "contenuto": SearchField.CONTENT,
          "entrambi": SearchField.BOTH}
LABELS = {SearchField.FILENAME: "nome", SearchField.CONTENT: "contenuto"}


def parse_input(line: str) -> SearchRequest:
    parts = line.strip().split(maxsplit=1)
    if parts and parts[0] in FIELDS:
        return SearchRequest(parts[1] if len(parts) > 1 else "", FIELDS[parts[0]])
    return SearchRequest(line)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ricerca locale nei file TXT")
    parser.add_argument("directory", help="Directory TXT da indicizzare ricorsivamente")
    args = parser.parse_args(argv)
    try:
        app = compose_cli(args.directory)
        report = app.build.execute(app.root_directory)
        print(f"File scoperti: {report.discovered}; indicizzati: {report.indexed}; "
              f"esclusi: {report.excluded}; byte: {report.processed_bytes}; "
              f"tempo build: {report.elapsed:.6f} s")
        print("Query: nome/contenuto/entrambi, AND e frasi tra virgolette. EOF o Ctrl+C per uscire.")
        while True:
            try:
                line = input("query> ")
            except EOFError:
                return 0
            try:
                request = parse_input(line)
                response = app.search.execute(request)
                print(f"Risultati: {response.total_matches}")
                while True:
                    for result in response.results:
                        fields = ", ".join(LABELS[field] for field in sorted(result.matched_fields))
                        print(f"  {result.relative_path.value} [{fields}]")
                    offset = request.offset + len(response.results)
                    if offset >= response.total_matches:
                        break
                    request = SearchRequest(request.query, request.field, request.limit, offset)
                    response = app.search.execute(request)
            except InvalidInput as exc:
                print(f"Query non valida: {exc}", file=sys.stderr)
    except KeyboardInterrupt:
        print("\nSessione interrotta.", file=sys.stderr)
        return 130
    except InvalidInput as exc:
        print(f"Argomento non valido: {exc}", file=sys.stderr)
        return 2
    except ApplicationError as exc:
        print(f"Errore: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
