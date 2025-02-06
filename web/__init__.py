# web/__init__.py

from .web_utils import load_data, save_data, load_menu, load_advanced_menu
from .webapp import app

__all__ = ["load_data", "save_data", "load_menu", "load_advanced_menu", "app"]
