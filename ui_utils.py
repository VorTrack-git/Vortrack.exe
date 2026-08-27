"""
ui_utils.py  (FACHADA)
Punto de compatibilidad: reexporta las utilidades de interfaz, que ahora viven
en módulos cohesivos por responsabilidad (SRP). El código existente puede seguir
usando `ui_utils.<algo>` sin cambios; el código nuevo puede importar del módulo
específico.

  - ui_tema      → COLORS, FONT_FAMILY (paleta y tipografía)
  - ui_imagenes  → load_image
  - ui_ventana   → maximize_window, set_window_icon
  - ui_dialogos  → scrollable_form, text_dialog, open_footer_link, bind_footer_link
  - ui_navbar    → build_app_navbar, build_app_footer
  - widgets      → FabricaWidgets (fábrica de widgets ctk/tk)
"""

from ui_tema import COLORS, FONT_FAMILY
from ui_imagenes import load_image
from ui_ventana import maximize_window, set_window_icon
from ui_dialogos import (
    scrollable_form,
    text_dialog,
    open_footer_link,
    bind_footer_link,
)
from ui_navbar import build_app_navbar, build_app_footer
from widgets import FabricaWidgets

__all__ = [
    "COLORS",
    "FONT_FAMILY",
    "load_image",
    "maximize_window",
    "set_window_icon",
    "scrollable_form",
    "text_dialog",
    "open_footer_link",
    "bind_footer_link",
    "build_app_navbar",
    "build_app_footer",
    "FabricaWidgets",
]
