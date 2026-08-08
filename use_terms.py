"""
use_terms.py
Diálogo de Términos de Uso de VorTrack (TRANSORE ISC).
"""
import ui_utils

TITULO = "Términos de Uso — VorTrack"
ENCABEZADO = "Términos de Uso"

TEXTO = """
Bienvenido a VorTrack, el sistema de gestión y seguimiento del proyecto TRANSORE ISC del Instituto San Carlos de La Salle. El uso de esta aplicación implica la aceptación de los siguientes términos.

1. Objeto y ámbito de uso
VorTrack es una herramienta de uso institucional y educativo, destinada a registrar y consultar la información del proceso de aprovechamiento de PET (recolección, transformación en filamento e impresión de material didáctico). Su uso está autorizado únicamente a los miembros del proyecto.

2. Cuentas y credenciales
El acceso se realiza mediante credenciales personales e intransferibles. El usuario es responsable de mantener la confidencialidad de su contraseña y de todas las actividades realizadas bajo su cuenta.

3. Uso adecuado
El usuario se compromete a:
• Registrar información veraz y completa.
• Utilizar la aplicación con fines relacionados con el proyecto.
• No alterar, dañar ni intentar acceder de forma no autorizada a los datos o al sistema.
• Cuidar los equipos institucionales en los que se ejecuta la aplicación.

4. Información registrada
Los datos ingresados forman parte del proyecto y podrán utilizarse para generar indicadores, reportes y estadísticas. El tratamiento de datos se rige por la Política de Privacidad de VorTrack.

5. Disponibilidad y garantía
La aplicación se ofrece "tal cual", con fines educativos. Se procura su correcto funcionamiento, pero no se garantiza que esté libre de errores. La institución y el desarrollador no serán responsables por pérdidas derivadas de un uso indebido.

6. Propiedad
VorTrack fue desarrollado por Miguel Ruiz Ramírez para el proyecto TRANSORE ISC del Instituto San Carlos de La Salle.

7. Soporte y contacto
Para dudas, reportes o sugerencias, escriba al correo de soporte: vortrack.soporte@gmail.com

Nota: Este documento es una versión preliminar (borrador) para el contexto del proyecto y podrá ajustarse a los términos definitivos de la institución.
"""


def abrir_terminos(parent_root):
    """Abre la ventana modal con los términos de uso."""
    return ui_utils.text_dialog(parent_root, TITULO, ENCABEZADO, TEXTO)
