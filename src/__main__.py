"""
Module execution entry point for RouterOS parser.

Allows running the parser with:
    python -m routeros_parser [args]
"""

if __name__ == "__main__":
    from .main import main
    main()