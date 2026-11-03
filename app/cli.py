import sys
from pathlib import Path
from .core import Store, respond

def main():
    store = Store(Path(__file__).resolve().parents[1])
    command = sys.argv[1] if len(sys.argv) > 1 else "chat"
    if command == "evaluate":
        from tests.evaluation import run; raise SystemExit(run(store))
    if command == "ingest":
        from .postgres import reset_and_import
        print(reset_and_import(Path(__file__).resolve().parents[1]))
        return
    if command == "ingest-policy":
        from .postgres import ingest_policy
        print({"policy_chunks": ingest_policy(Path(__file__).resolve().parents[1])})
        return
    message = " ".join(sys.argv[2:] if command == "chat" else sys.argv[1:])
    print(respond(store, message))

if __name__ == "__main__": main()
