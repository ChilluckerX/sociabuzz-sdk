"""
SociaBuzz Payment API — Entry Point
====================================

Run::

    python main.py                     # default :8000
    API_PORT=8004 python main.py       # custom port
"""

import uvicorn

from config import settings
from server import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
