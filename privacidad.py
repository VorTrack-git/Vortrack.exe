"""
privacidad.py
Diálogo de Política de Privacidad de VorTrack (TRANSORE ISC).
"""
import ui_utils

TITULO = "Privacidad — VorTrack"
ENCABEZADO = "Política de Privacidad"

TEXTO = """
VorTrack es una aplicación de escritorio desarrollada para el proyecto TRANSORE ISC del Instituto San Carlos de La Salle, orientada a la gestión y trazabilidad del aprovechamiento de residuos de PET para la fabricación de material didáctico.

1. Información que se registra
La aplicación almacena únicamente la información necesaria para la gestión del proyecto:
• Datos de responsables y estudiantes participantes (nombre y rol).
• Jornadas de recolección: fecha, aportante, cantidad y peso de PET.
• Producción de filamento: peso ingresado, peso salido, desperdicio y metros producidos.
• Impresiones y material didáctico fabricado.
• Observaciones asociadas a cada registro.

2. Almacenamiento local
Los datos se guardan de forma local en los equipos de cómputo de la institución destinados al proyecto. VorTrack no transmite información a servidores externos ni a terceros a través de Internet.

3. Finalidad del tratamiento
La información se utiliza exclusivamente para fortalecer la trazabilidad de los procesos, generar indicadores y reportes, y apoyar la toma de decisiones dentro del proyecto educativo.

4. Datos de menores de edad
Cuando se registren datos de estudiantes menores de edad, su tratamiento se realiza bajo la responsabilidad de la institución educativa y con el consentimiento de los acudientes, conforme a la normativa aplicable de protección de datos.

5. Acceso y seguridad
El acceso a la aplicación está protegido por credenciales personales. Cada usuario es responsable del uso de sus credenciales y de la información que registra.

6. Contacto
Para consultas o solicitudes relacionadas con el tratamiento de datos, escriba al correo de soporte: vortrack.soporte@gmail.com

Nota: Este documento es una versión preliminar (borrador) para el contexto del proyecto y podrá ajustarse a las políticas definitivas de la institución.
"""


def abrir_privacidad(parent_root):
    """Abre la ventana modal con la política de privacidad."""
    return ui_utils.text_dialog(parent_root, TITULO, ENCABEZADO, TEXTO)
