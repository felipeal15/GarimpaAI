"""Launcher do frontend Streamlit do GarimpaAI.

Entry point registrado em pyproject.toml como `garimpaai-ui`.
"""
import sys
from pathlib import Path


def run():
    """Inicia o servidor Streamlit apontando para garimpaai/app.py."""
    try:
        from streamlit.web import cli as stcli
    except ImportError:
        print(
            "❌ Streamlit não está instalado.\n"
            "   Reinstale o pacote: pip install -e ."
        )
        sys.exit(1)

    app_path = Path(__file__).parent / "app.py"
    if not app_path.exists():
        print(f"❌ Arquivo da UI não encontrado: {app_path}")
        sys.exit(1)

    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        "--browser.gatherUsageStats=false",
    ]
    sys.exit(stcli.main())


if __name__ == "__main__":
    run()
