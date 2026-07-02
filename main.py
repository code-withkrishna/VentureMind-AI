from __future__ import annotations

from api_server import app


def main() -> None:
    from app import main as streamlit_main

    streamlit_main()


if __name__ == "__main__":
    main()
