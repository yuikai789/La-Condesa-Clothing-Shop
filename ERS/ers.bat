import os
import subprocess
import sys

# Ensure python-docx is installed
try:
    import docx
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-docx"])
    import docx

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def create_ers_document():
    doc = Document()
    
    # Page setup
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Palette Colors
    PRIMARY_COLOR = RGBColor(27, 54, 93)     # #1B365D Deep Navy
    SECONDARY_COLOR = RGBColor(44, 82, 130)  # #2C5282 Slate Blue
    TEXT_COLOR = RGBColor(45, 55, 72)        # #2D3748 Charcoal
    PRIMARY_HEX = "1B365D"
    ZEBRA_HEX = "F7FAFC"
    BORDER_HEX = "E2E8F0"

    # Set Default Font Style
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Arial'
    font.size = Pt(11)
    font.color.rgb = TEXT_COLOR
    style.paragraph_format.line_spacing = 1.15
    style.paragraph_format.space_after = Pt(6)

    # Helper function for adding headings
    def add_custom_heading(text, level):
        heading = doc.add_heading(text, level=level)
        heading.paragraph_format.space_before = Pt(12)
        heading.paragraph_format.space_after = Pt(4)
        heading.paragraph_format.keep_with_next = True
        run = heading.runs[0]
        run.font.name = 'Arial'
        if level == 1:
            run.font.size = Pt(18)
            run.font.color.rgb = PRIMARY_COLOR
            run.bold = True
        elif level == 2:
            run.font.size = Pt(14)
            run.font.color.rgb = SECONDARY_COLOR
            run.bold = True
        else:
            run.font.size = Pt(12)
            run.font.color.rgb = TEXT_COLOR
            run.bold = True
            run.italic = True
        return heading

    def set_cell_background(cell, color_hex):
        shading_xml = f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>'
        cell._tc.get_or_add_tcPr().append(parse_xml(shading_xml))

    def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
        tcPr = cell._tc.get_or_add_tcPr()
        tcMar = OxmlElement('w:tcMar')
        for margin_name, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
            m = OxmlElement(f'w:{margin_name}')
            m.set(qn('w:w'), str(val))
            m.set(qn('w:type'), 'dxa')
            tcMar.append(m)
        tcPr.append(tcMar)

    def set_table_borders(table, color=BORDER_HEX, sz="4", val="single"):
        tblPr = table._tbl.tblPr
        tblBorders = OxmlElement('w:tblBorders')
        for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
            border = OxmlElement(f'w:{border_name}')
            border.set(qn('w:val'), val)
            border.set(qn('w:sz'), sz)
            border.set(qn('w:space'), '0')
            border.set(qn('w:color'), color)
            tblBorders.append(border)
        tblPr.append(tblBorders)

    def add_styled_table(headers, rows):
        table = doc.add_table(rows=1, cols=len(headers))
        table.autofit = True
        set_table_borders(table)
        
        # Header formatting
        hdr_cells = table.rows[0].cells
        for i, header_text in enumerate(headers):
            hdr_cells[i].text = header_text
            set_cell_background(hdr_cells[i], PRIMARY_HEX)
            set_cell_margins(hdr_cells[i], top=120, bottom=120, left=150, right=150)
            p = hdr_cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.runs[0].font.bold = True
            p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
            p.runs[0].font.size = Pt(10)
            
        # Rows formatting
        for r_idx, row_data in enumerate(rows):
            row_cells = table.add_row().cells
            is_zebra = (r_idx % 2 == 1)
            for c_idx, cell_value in enumerate(row_data):
                row_cells[c_idx].text = str(cell_value)
                set_cell_margins(row_cells[c_idx], top=100, bottom=100, left=150, right=150)
                if is_zebra:
                    set_cell_background(row_cells[c_idx], ZEBRA_HEX)
                if len(row_cells[c_idx].paragraphs) > 0:
                    p = row_cells[c_idx].paragraphs[0]
                    p.runs[0].font.size = Pt(9.5)
        doc.add_paragraph() # spacing after table

    # --- COVER / TITLE ---
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.paragraph_format.space_before = Pt(50)
    title_p.paragraph_format.space_after = Pt(12)
    run_title = title_p.add_run("Especificación de Requisitos de Software (ERS)")
    run_title.font.size = Pt(24)
    run_title.bold = True
    run_title.font.color.rgb = PRIMARY_COLOR

    subtitle_p = doc.add_paragraph()
    subtitle_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle_p.paragraph_format.space_after = Pt(100)
    run_sub = subtitle_p.add_run("Sistema Web de Gestión Comercial y Control de Inventario — La Condesa")
    run_sub.font.size = Pt(14)
    run_sub.font.color.rgb = SECONDARY_COLOR

    doc.add_page_break()

    # --- ÍNDICE ---
    add_custom_heading("Índice", level=1)
    indice_text = [
        "1. Introducción",
        "   - 1.1 Propósito",
        "   - 1.2 Ámbito del Sistema",
        "   - 1.3 Definiciones, Acrónimos y Abreviaturas",
        "   - 1.4 Referencias",
        "   - 1.5 Visión General del Documento",
        "2. Descripción General",
        "   - 2.1 Perspectiva del Producto",
        "   - 2.2 Funciones del Producto",
        "   - 2.3 Características de los Usuarios",
        "   - 2.4 Restricciones",
        "   - 2.5 Suposiciones y Dependencias",
        "   - 2.6 Requisitos Futuros",
        "3. Requisitos Específicos",
        "   - 3.1 Interfaces Externas",
        "   - 3.2 Funciones",
        "   - 3.3 Requisitos de Rendimiento",
        "   - 3.4 Restricciones de Diseño",
        "   - 3.5 Atributos del Sistema",
        "   - 3.6 Otros Requisitos",
        "4. Apéndices"
    ]
    for line in indice_text:
        p = doc.add_paragraph(line)
        p.paragraph_format.space_after = Pt(2)
    doc.add_page_break()

    # --- SECCIÓN 1 ---
    add_custom_heading("1. Introducción", level=1)
    doc.add_paragraph("En esta sección se proporciona una introducción a todo el documento de Especificación de Requisitos Software (ERS). Consta de varias subsecciones: propósito, ámbito del sistema, definiciones, referencias y visión general del documento.")

    add_custom_heading("1.1 Propósito", level=2)
    doc.add_paragraph("El propósito de este documento es especificar los requisitos de software de la plataforma web diseñada para la gestión de los procesos administrativos, comerciales y de control de inventario del establecimiento comercial \"La Condesa\", ubicado en la Avenida Miranda de la ciudad de Maturín, estado Monagas.")
    doc.add_paragraph("Las especificaciones están dirigidas a los involucrados en el proyecto:")
    doc.add_paragraph("• Desarrolladores: Para implementar el sistema según lo especificado.\n"
                      "• Directivos del negocio: Para confirmar que los requisitos cubren las necesidades reales de la tienda.\n"
                      "• Asesores académicos: Para supervisar el cumplimiento del Proyecto Socio-Tecnológico.\n"
                      "• Equipo de pruebas: Para planificar las verificaciones de cada requisito.", style='List Bullet')
    doc.add_paragraph("Este documento sigue las directrices del estándar IEEE Std. 830-1998 para la especificación de requisitos de software, garantizando que cada requisito sea correcto, no ambiguo, completo, consistente, clasificado, verificable, modificable y trazable.")

    add_custom_heading("1.2 Ámbito del Sistema", level=2)
    doc.add_paragraph("Nombre del sistema: La Condesa — Plataforma Web de Gestión Comercial")
    doc.add_paragraph("Descripción general: El sistema es una aplicación web integral, con arquitectura responsive, orientada a la digitalización y optimización de los procesos administrativos, de facturación, control de inventario y habilitación de un canal de ventas en línea para el establecimiento comercial \"La Condesa\".")
    
    doc.add_paragraph("Lo que el sistema hará:").runs[0].bold = True
    haras = [
        "Gestión de usuarios con tres roles (Administrador, Empleado, Cliente) mediante autenticación segura.",
        "Catálogo público de productos con filtros por categoría, talla, precio y búsqueda por palabra clave.",
        "Carrito de compras y proceso de apartado en línea para clientes registrados.",
        "Gestión completa de pedidos con flujo de estados (pendiente → pagado → preparando → listo → entregado).",
        "Control de inventario con registro de movimientos (compras, devoluciones, pérdidas, correcciones, ventas).",
        "Generación de reportes financieros y de ventas con exportación a CSV.",
        "Sistema de auditoría que registra todas las acciones realizadas por los usuarios administrativos y de empleado.",
        "Envío de correos electrónicos de notificación (confirmación de pedido, pedido listo, pedido entregado).",
        "Generación de códigos QR para la identificación de pedidos listos para recoger.",
        "Subida de comprobantes de pago por parte de los clientes."
    ]
    for h in haras:
        doc.add_paragraph(h, style='List Bullet')

    doc.add_paragraph("Lo que el sistema NO hará:").runs[0].bold = True
    noharas = [
        "No gestionará envíos a domicilio (el modelo de negocio es de retiro en tienda).",
        "No será una aplicación móvil nativa; será accesible exclusivamente a través de navegadores web.",
        "No integrará pasarelas de pago en línea directas (el pago se realiza por transferencia o presencialmente).",
        "No reemplazará un sistema punto de venta (POS) físico existente.",
        "No gestionará contabilidad general ni generará declaraciones fiscales.",
        "No manejará programación de turnos ni nómina de empleados."
    ]
    for nh in noharas:
        doc.add_paragraph(nh, style='List Bullet')

    doc.add_paragraph("Beneficios esperados:").runs[0].bold = True
    beneficios = [
        "Ahorro en tiempo administrativo estimado en $780 USD anuales.",
        "Reducción de pérdidas por descontrol de inventario estimada en $350 USD anuales.",
        "Incremento estimado de ventas por canal web de $1,200 USD anuales.",
        "ROI proyectado: 149,43%.",
        "Período de recuperación de inversión: aproximadamente 4,81 meses."
    ]
    for b in beneficios:
        doc.add_paragraph(b, style='List Bullet')

    add_custom_heading("1.3 Definiciones, Acrónimos y Abreviaturas", level=2)
    def_headers = ["Término", "Definición"]
    def_rows = [
        ["ERS", "Especificación de Requisitos de Software"],
        ["IEEE", "Institute of Electrical and Electronics Engineers"],
        ["CRUD", "Create, Read, Update, Delete — Operaciones básicas de mantenimiento de datos"],
        ["ORM", "Object-Relational Mapping — Mapeo objeto-relacional"],
        ["CSRF", "Cross-Site Request Forgery — Falsificación de solicitudes entre sitios"],
        ["Flask", "Microframework web para Python"],
        ["SQLAlchemy", "ORM para Python que facilita la interacción con bases de datos"],
        ["SQLite", "Sistema de base de datos relacional ligero, embebido"],
        ["Bootstrap", "Framework de diseño web front-end"],
        ["bcrypt", "Algoritmo de hash de contraseñas con sal"],
        ["QR", "Quick Response — Código de respuesta rápida"],
        ["CSV", "Comma-Separated Values — Valores separados por comas"],
        ["HTTPS", "Hypertext Transfer Protocol Secure — Protocolo de transferencia segura"],
        ["SMTP", "Simple Mail Transfer Protocol — Protocolo de transferencia de correo"],
        ["SSL", "Secure Sockets Layer — Capa de enchufes seguros"],
        ["CDN", "Content Delivery Network — Red de distribución de contenido"],
        ["CU", "Caso de Uso"],
        ["PST", "Proyecto Socio-Tecnológico"],
        ["KLOC", "Thousand Lines of Code — Miles de líneas de código"],
        ["COCOMO", "Constructive Cost Model"],
        ["ROI", "Return on Investment — Retorno de inversión"],
        ["API", "Application Programming Interface — Interfaz de programación de aplicaciones"],
        ["MVC", "Model-View-Controller — Modelo-Vista-Controlador"],
        ["URL", "Uniform Resource Locator — Localizador uniforme de recursos"],
        ["HTML", "HyperText Markup Language — Lenguaje de marcado de hipertexto"],
        ["CSS", "Cascading Style Sheets — Hojas de estilo en cascada"],
        ["JS", "JavaScript — Lenguaje de programación para la web"],
        ["PaaS", "Platform as a Service — Plataforma como servicio"]
    ]
    add_styled_table(def_headers, def_rows)

    add_custom_heading("1.4 Referencias", level=2)
    ref_headers = ["ID", "Documento", "Descripción"]
    ref_rows = [
        ["[R1]", "IEEE Std. 830-1998", "Recommended Practice for Software Requirements Specifications"],
        ["[R2]", "PST IV Informe", "Proyecto Socio-Tecnológico: Desarrollo Web, bajo Estándares de Calidad, de los Procesos Administrativos para La Condesa"],
        ["[R3]", "Flask Documentation", "https://flask.palletsprojects.com/ — Documentación oficial del framework Flask"],
        ["[R4]", "SQLAlchemy Documentation", "https://docs.sqlalchemy.org/ — Documentación oficial de SQLAlchemy"],
        ["[R5]", "Bootstrap 5 Documentation", "https://getbootstrap.com/ — Documentación del framework Bootstrap"],
        ["[R6]", "Flask-Login Documentation", "https://flask-login.readthedocs.io/ — Gestión de sesiones de usuario"],
        ["[R7]", "Flask-Mail Documentation", "https://pythonhosted.org/Flask-Mail/ — Envío de correos electrónicos"],
        ["[R8]", "Python Documentation", "https://docs.python.org/3/ — Documentación oficial de Python"]
    ]
    add_styled_table(ref_headers, ref_rows)

    add_custom_heading("1.5 Visión General del Documento", level=2)
    vision_points = [
        "Sección 1 — Introducción: Presenta el propósito, ámbito, definiciones y referencias del documento.",
        "Sección 2 — Descripción General: Describe el contexto del producto, sus funciones generales, las características de los usuarios, restricciones, suposiciones y requisitos futuros.",
        "Sección 3 — Requisitos Específicos: Contiene los requisitos detallados del sistema, organizados en interfaces externas, funciones (por tipo de usuario), requisitos de rendimiento, restricciones de diseño, atributos del sistema y otros requisitos.",
        "Sección 4 — Apéndices: Incluye el glosario completo, la tabla consolidada de casos de uso y el diagrama de clases resumido."
    ]
    for vp in vision_points:
        doc.add_paragraph(vp, style='List Bullet')

    # --- SECCIÓN 2 ---
    add_custom_heading("2. Descripción General", level=1)
    doc.add_paragraph("En esta sección se describen todos aquellos factores que afectan al producto y a sus requisitos. No se describen los requisitos, sino su contexto. Esto permitirá definir con detalle los requisitos en la sección 3, haciendo que sean más fáciles de entender.")

    add_custom_heading("2.1 Perspectiva del Producto", level=2)
    doc.add_paragraph("El sistema \"La Condesa — Plataforma Web de Gestión Comercial\" es un producto independiente diseñado para el establecimiento homónimo. No forma parte de otro sistema ni requiere integración con software externo existente.")
    doc.add_paragraph("El sistema se despliega como una aplicación web accesible a través de navegadores, desde un servidor en la nube. Su arquitectura se compone de las siguientes capas:")

    # Architecture block
    arch_diagram = (
        "┌─────────────────────────────────────────┐\n"
        "│           CAPA DE PRESENTACIÓN          │\n"
        "│  HTML5 · CSS3 · JavaScript · Bootstrap  │\n"
        "├─────────────────────────────────────────┤\n"
        "│           CAPA DE APLICACIÓN            │\n"
        "│  Python 3.9+ · Flask 2.3 · Blueprints   │\n"
        "├─────────────────────────────────────────┤\n"
        "│           CAPA DE NEGOCIO               │\n"
        "│  Services (Order, Inventory, Analytics, │\n"
        "│  Email, Audit) · Utils (Validators,     │\n"
        "│  Upload, QR Generator, Pagination)      │\n"
        "├─────────────────────────────────────────┤\n"
        "│           CAPA DE DATOS                 │\n"
        "│  SQLAlchemy 2.0 ORM · SQLite 3.35+      │\n"
        "├─────────────────────────────────────────┤\n"
        "│        INFRAESTRUCTURA                  │\n"
        "│  Render (PaaS) · Cloudflare (DNS/SSL)   │\n"
        "└─────────────────────────────────────────┘"
    )
    p_arch = doc.add_paragraph()
    p_arch.paragraph_format.left_indent = Inches(0.5)
    run_arch = p_arch.add_run(arch_diagram)
    run_arch.font.name = 'Courier New'
    run_arch.font.size = Pt(9.5)

    doc.add_paragraph("Relación con el entorno: El sistema opera como la plataforma digital central del negocio. Los clientes acceden al catálogo público y realizan apartados en línea, mientras que el personal interno (administrador y empleados) gestiona las operaciones diarias desde el panel de administración.")

    add_custom_heading("2.2 Funciones del Producto", level=2)
    doc.add_paragraph("El sistema agrupa su funcionalidad en cinco áreas principales:")

    funcs = {
        "2.2.1 Autenticación y Gestión de Usuarios": [
            "Registro de nuevos clientes con validación de datos.",
            "Inicio de sesión seguro con cifrado de contraseñas (bcrypt).",
            "Gestión de tres roles: Administrador, Empleado y Cliente.",
            "Control de acceso basado en roles mediante decoradores.",
            "Gestión de sesiones con tiempo de expiración configurable."
        ],
        "2.2.2 Catálogo Público y Comercio Electrónico": [
            "Página principal con productos destacados.",
            "Catálogo de productos con filtros por categoría, talla y rango de precios.",
            "Vista detallada de productos con imágenes, descripciones, tallas y colores disponibles.",
            "Búsqueda de productos por palabra clave.",
            "Carrito de compras con gestión de cantidades.",
            "Proceso de checkout con selección de punto de recogida.",
            "Subida de comprobantes de pago por parte del cliente."
        ],
        "2.2.3 Gestión de Inventario": [
            "Registro de productos con specifications (tallas, colores, stock por talla).",
            "Registro de movimientos de inventario (compra, devolución, pérdida, corrección, venta).",
            "Alertas de stock bajo (umbral configurable: 5 unidades).",
            "Descontado automático del inventario al confirmar la entrega de un pedido.",
            "Consulta de historial de movimientos de inventario."
        ],
        "2.2.4 Administración de Pedidos y Apartados": [
            "Flujo completo de estados del pedido: pendiente de pago → pagado → preparando → listo para recoger → entregado.",
            "Confirmación de pago por parte de administrador o empleado.",
            "Generación de código QR para pedidos listos para recogida.",
            "Envío de correos electrónicos en cada etapa del pedido.",
            "Cancelación de pedidos con liberación automática de inventario."
        ],
        "2.2.5 Reportes y Análisis": [
            "Dashboard con métricas en tiempo real (ventas totales, pedidos, promedio).",
            "Reporte de ventas diarias con gráficos.",
            "Productos más vendidos en un período determinado.",
            "Reporte financiero con ingresos, impuestos, descuentos y ganancia por producto.",
            "Desglose de estados de pedidos.",
            "Exportación de reportes a formato CSV.",
            "Logs de auditoría con seguimiento de todas las acciones administrativas."
        ]
    }
    for f_title, f_list in funcs.items():
        add_custom_heading(f_title, level=3)
        for item in f_list:
            doc.add_paragraph(item, style='List Bullet')

    add_custom_heading("2.3 Características de los Usuarios", level=2)
    user_chars = {
        "2.3.1 Administrador": [
            "Descripción: Gerente o propietario del establecimiento comercial \"La Condesa\".",
            "Nivel educativo: Profesional o técnico con experiencia en gestión comercial.",
            "Experiencia técnica: Uso básico de computadora, navegadores web y herramientas ofimáticas.",
            "Tareas principales: Supervisión general del negocio, gestión de empleados, aprobación de pagos, revisión de reportes y auditoría.",
            "Frecuencia de uso: Diaria, durante el horario laboral (9:00 am - 4:00 pm)."
        ],
        "2.3.2 Empleado": [
            "Descripción: Personal que labora en el establecimiento y atiende a los clientes.",
            "Nivel educativo: Estudiantes universitarios o personas con educación media.",
            "Experiencia técnica: Uso básico de dispositivos electrónicos y aplicaciones web.",
            "Tareas principales: Registro de ventas, atención de apartados presenciales, consulta de inventario.",
            "Frecuencia de uso: Diaria, durante turnos de trabajo."
        ],
        "2.3.3 Cliente": [
            "Descripción: Usuarios finales que visitan el catálogo en línea y realizan apartados de productos.",
            "Nivel educativo: variable, desde educación básica hasta profesional.",
            "Experiencia técnica: Básica, navegación web estándar.",
            "Tareas principales: Explorar catálogo, agregar productos al carrito, realizar apartados, subir comprobantes de pago.",
            "Frecuencia de uso: Variable, según necesidad de compra."
        ]
    }
    for u_title, u_list in user_chars.items():
        add_custom_heading(u_title, level=3)
        for item in u_list:
            doc.add_paragraph(item, style='List Bullet')

    add_custom_heading("2.4 Restricciones", level=2)
    restricciones = {
        "2.4.1 Restricciones Tecnológicas": [
            "El sistema se desarrolla utilizando Python 3.9+ con el microframework Flask 2.3.",
            "La base de datos es SQLite 3.35+ (no se utilizará un servidor de bases de datos independiente).",
            "El frontend se construye con HTML5, CSS3, JavaScript y Bootstrap 5, sin frameworks JavaScript adicionales."
        ],
        "2.4.2 Restricciones de Hardware": [
            "El servidor de hosting en Render dispone de recursos limitados en el plan Starter.",
            "El equipo de cómputo del establecimiento tiene especificaciones mínimas (procesador doble núcleo, 1 GB RAM)."
        ],
        "2.4.3 Restricciones Organizacionales": [
            "El sistema es de uso exclusivo del establecimiento \"La Condesa\".",
            "No se contempla integración con sistemas externos de terceros.",
            "El modelo de negocio es de retiro en tienda, sin envíos a domicilio."
        ],
        "2.4.4 Restricciones de Seguridad": [
            "Las contraseñas se almacenan cifradas con bcrypt (12 rounds).",
            "Se implementan tokens CSRF en todos los formularios.",
            "Las sesiones expiran tras 30 minutos de inactividad.",
            "Las cookies de sesión son HttpOnly.",
            "Se utilizan decoradores de control de acceso por rol."
        ],
        "2.4.5 Restricciones de Formato": [
            "Las imágenes de productos deben estar en formato PNG, JPG, JPEG, GIF o WebP.",
            "El tamaño máximo de archivos subidos es de 5 MB.",
            "Los reportes se exportan exclusivamente en formato CSV."
        ]
    }
    for r_title, r_list in restricciones.items():
        add_custom_heading(r_title, level=3)
        for item in r_list:
            doc.add_paragraph(item, style='List Bullet')

    add_custom_heading("2.5 Suposiciones y Dependencias", level=2)
    add_custom_heading("2.5.1 Suposiciones", level=3)
    sups = [
        "El establecimiento \"La Condesa\" contará con una conexión a internet estable y continua para el funcionamiento del sistema.",
        "Los usuarios finales (clientes) contarán con dispositivos equipados con navegadores web actualizados (Chrome, Firefox, Edge o equivalentes).",
        "El personal del establecimiento recibirá capacitación básica para el uso del sistema.",
        "El volumen de transacciones diarias será acorde al de una tienda local (decenas de pedidos como máximo).",
        "El hosting en Render mantendrá un nivel de disponibilidad del 99.9%."
    ]
    for s in sups:
        doc.add_paragraph(s, style='List Bullet')

    add_custom_heading("2.5.2 Dependencias", level=3)
    deps = [
        "El correcto funcionamiento del sistema depende de la disponibilidad del servicio de hosting en Render.",
        "El envío de correos electrónicos depende de la configuración del servidor SMTP.",
        "La generación de códigos QR depende de la librería qrcode para Python.",
        "El procesamiento de imágenes depende de la librería Pillow para Python."
    ]
    for d in deps:
        doc.add_paragraph(d, style='List Bullet')

    add_custom_heading("2.6 Requisitos Futuros", level=2)
    req_futs = [
        "Pasarela de pago en línea: Integración con procesadores de pago (PayPal, pagos móviles) para permitir transacciones directas desde la plataforma.",
        "Gestión de promociones y descuentos: Sistema de cupones y ofertas por temporada.",
        "Sistema de valoraciones: Permite a los clientes calificar y comentar productos.",
        "Soporte para múltiples sucursales: Gestión de inventario y ventas en diferentes ubicaciones.",
        "Aplicación móvil: Versión optimizada para dispositivos móviles."
    ]
    for rf in req_futs:
        doc.add_paragraph(rf, style='List Bullet')

    # --- SECCIÓN 3 ---
    add_custom_heading("3. Requisitos Específicos", level=1)
    doc.add_paragraph("Esta sección contiene los requisitos detallados del sistema, organizados por interfaces, funciones, rendimiento y restricciones. Cada requisito describe comportamientos externos del sistema, perceptibles por los usuarios y operadores.")
    doc.add_paragraph("Los requisitos se organizan por tipo de usuario, dado que el sistema presenta tres roles diferenciados con necesidades funcionales distintas.")

    add_custom_heading("3.1 Interfaces Externas", level=2)
    add_custom_heading("3.1.1 Interfaz de Usuario", level=3)
    doc.add_paragraph("Páginas Públicas (no requieren autenticación):")
    add_styled_table(["Página", "URL", "Descripción"], [
        ["Página Principal", "/", "Muestra productos destacados y categorías disponibles"],
        ["Catálogo", "/catalog", "Listado de productos con filtros por categoría, talla y precio"],
        ["Detalle de Producto", "/product/<id>", "Ficha completa del producto con imágenes, tallas, colores y precio"],
        ["Acerca de", "/about", "Información sobre el establecimiento"],
        ["Contacto", "/contact", "Formulario de contacto"]
    ])

    doc.add_paragraph("Paneles de Usuario (requieren autenticación):")
    add_styled_table(["Panel", "URL Base", "Rol"], [
        ["Dashboard Admin", "/admin/dashboard", "Administrador"],
        ["Gestión de Usuarios", "/admin/users", "Administrador"],
        ["Gestión de Productos", "/admin/products", "Administrador"],
        ["Gestión de Pedidos", "/admin/orders", "Administrador"],
        ["Inventario", "/admin/inventory", "Administrador"],
        ["Analytics", "/admin/analytics", "Administrador"],
        ["Reportes Financieros", "/admin/financial-reports", "Administrador"],
        ["Logs de Auditoría", "/admin/audit-logs", "Administrador"],
        ["Gestión de Empleados", "/admin/employees", "Administrador"],
        ["Dashboard Empleado", "/employee/dashboard", "Empleado"],
        ["Pedidos Empleado", "/employee/orders", "Empleado"],
        ["Ventas Empleado", "/employee/sales", "Empleado"],
        ["Dashboard Cliente", "/customer/dashboard", "Cliente"],
        ["Carrito", "/customer/cart", "Cliente"],
        ["Checkout", "/customer/checkout", "Cliente"],
        ["Mis Pedidos", "/customer/orders", "Cliente"],
        ["Detalle de Pedido", "/customer/orders/<id>", "Cliente"]
    ])

    doc.add_paragraph("Elementos comunes de la interfaz:").runs[0].bold = True
    elems = [
        "Barra de navegación superior con enlaces a secciones según el rol del usuario.",
        "Indicador del carrito de compras con contador de productos (visible para clientes autenticados).",
        "Sistema de mensajes flash para notificaciones de éxito, error, advertencia e información.",
        "Formularios con validación en cliente y servidor.",
        "Paginación para listados de datos.",
        "Tablas responsivas con ordenamiento y filtrado."
    ]
    for el in elems:
        doc.add_paragraph(el, style='List Bullet')

    add_custom_heading("3.1.2 Interfaces de Software", level=3)
    add_styled_table(["Componente", "Versión", "Propósito"], [
        ["Python", "3.9+", "Lenguaje de programación del backend"],
        ["Flask", "2.3.3", "Microframework web"],
        ["SQLAlchemy", "2.0.21", "ORM para interacción con la base de datos"],
        ["Flask-Login", "0.6.3", "Gestión de sesiones y autenticación de usuarios"],
        ["Flask-WTF", "1.2.1", "Protección CSRF y gestión de formularios"],
        ["Flask-Migrate", "4.0.5", "Migraciones de base de datos"],
        ["Flask-Mail", "0.9.1", "Envío de correos electrónicos"],
        ["Werkzeug", "2.3.7", "Utilidades WSGI"],
        ["Jinja2", "3.1.2", "Motor de plantillas"],
        ["bcrypt", "4.1.0", "Cifrado de contraseñas"],
        ["Pillow", "10.0.1", "Procesamiento de imágenes"],
        ["qrcode", "7.4.2", "Generación de códigos QR"],
        ["SQLite", "3.35+", "Sistema de base de datos relacional"],
        ["Bootstrap", "5.x", "Framework de diseño front-end"]
    ])

    add_custom_heading("3.1.3 Interfaces de Hardware", level=3)
    doc.add_paragraph("Servidor (producción):")
    add_styled_table(["Recurso", "Especificación"], [
        ["Proveedor", "Render (plan Starter)"],
        ["Tipo", "PaaS (Platform as a Service)"],
        ["Almacenamiento", "Incluido en el plan"],
        ["Memoria", "Limitada por el plan"],
        ["Acceso", "HTTPS vía Cloudflare"]
    ])
    doc.add_paragraph("Cliente (requisitos mínimos):")
    add_styled_table(["Recurso", "Especificación"], [
        ["Procesador", "Doble núcleo o superior"],
        ["Memoria RAM", "1 GB mínimo"],
        ["Almacenamiento", "Espacio suficiente para SO y navegador"],
        ["Pantalla", "Resolución mínima de 1024×768"],
        ["Conexión", "Internet activa (banda ancha recomendada)"],
        ["Navegador", "Chrome, Firefox, Edge u otro compatible"]
    ])

    add_custom_heading("3.1.4 Interfaces de Comunicaciones", level=3)
    add_styled_table(["Protocolo", "Uso", "Configuración"], [
        ["HTTPS", "Acceso seguro a la aplicación", "Certificado SSL vía Cloudflare"],
        ["SMTP", "Envío de correos electrónicos", "Puerto 587 (TLS) en producción; localhost:1025 en desarrollo"],
        ["HTTP/1.1", "Comunicación interna con el servidor", "Flask development server / WSGI en producción"]
    ])

    add_custom_heading("3.2 Funciones", level=2)
    doc.add_paragraph("Esta sección especifica todas las acciones que el sistema deberá llevar a cabo. Los requisitos se organizan por tipo de usuario, dado que el sistema presenta tres roles diferenciados con necesidades funcionales distintas.")

    # USE CASES BUILDER DATA
    use_cases_data = [
        # --- ADMIN ---
        {
            "section": "3.2.1 Funciones del Administrador",
            "id": "CU1", "name": "Autenticar Usuario (Administrador)",
            "meta": [
                ["ID", "CU1"], ["Nombre", "Autenticar usuario"], ["Actores", "Administrador"],
                ["Descripción", "Permite al Administrador ingresar al sistema de manera segura validando sus credenciales de acceso. Una vez verificado, se le otorga el acceso a las funciones administrativas del sistema."],
                ["Casos de uso relacionados", "CU2 (Visualizar dashboard)"], ["Entradas", "Correo electrónico y contraseña"],
                ["Salidas", "Sesión activa, token de autenticación y redirección al panel principal"],
                ["Precondición", "El Administrador debe estar previamente registrado en el sistema y contar con un rol administrativo activo en la base de datos."],
                ["Postcondición", "El sistema inicia la sesión del Administrador de forma segura y permite el acceso al Dashboard de gestión."]
            ],
            "typical": [
                ["1", "El Administrador accede a la interfaz de inicio de sesión del sistema.", "El sistema muestra los campos de entrada de credenciales (Correo y Contraseña)."],
                ["2", "El Administrador introduce sus credenciales correspondientes.", "—"],
                ["3", "El Administrador hace clic en el botón para iniciar sesión.", "El sistema recibe los datos de ingreso de forma segura."],
                ["4", "—", "El sistema cifra y valida las credenciales introducidas contra la base de datos."],
                ["5", "—", "El sistema verifica que el usuario cuente con el rol asignado de \"Administrador\"."],
                ["6", "—", "El sistema genera la sesión activa, otorga los permisos necesarios y redirige al Administrador al Dashboard (CU2)."]
            ],
            "exceptional": [
                ["3", "El Administrador intenta enviar el formulario dejando campos en blanco.", "El sistema interrumpe el proceso, resalta visualmente los campos obligatorios vacíos y muestra un mensaje de advertencia: \"Por favor, complete todos los campos obligatorios.\""],
                ["4", "El usuario o la contraseña no coinciden con los registros de la base de datos.", "El sistema deniega el acceso, limpia el campo de la contraseña y muestra un mensaje genérico de alerta: \"Correo o contraseña incorrectos.\" El sistema mantiene al usuario en la pantalla de login."]
            ]
        },
        {
            "section": None,
            "id": "CU2", "name": "Visualizar Dashboard (Administrador)",
            "meta": [
                ["ID", "CU2"], ["Nombre", "Visualizar dashboard"], ["Actores", "Administrador"],
                ["Descripción", "Permite al Administrador visualizar un panel de control centralizado con resúmenes estadísticos, indicadores clave del estado del negocio y un menú con accesos directos a las diferentes funcionalidades del sistema."],
                ["Casos de uso relacionados", "CU1, CU3, CU4, CU5, CU6, CU7, CU8, CU12"],
                ["Entradas", "Petición de carga de la página (redirección automática tras login o clic en el menú de navegación)."],
                ["Salidas", "Interfaz gráfica del Dashboard con contadores de métricas en tiempo real, alertas del sistema y menús de navegación."],
                ["Precondición", "El Administrador debe haber iniciado sesión exitosamente en el sistema y mantener una sesión activa y válida."],
                ["Postcondición", "El sistema despliega correctamente la información del panel de control, quedando en espera de que el Administrador seleccione alguna opción administrativa."]
            ],
            "typical": [
                ["1", "El Administrador es redirigido automáticamente tras autenticarse (o hace clic en \"Dashboard\").", "El sistema recibe la solicitud de acceso al panel de control."],
                ["2", "—", "El sistema verifica de forma interna que la sesión del usuario sea válida y corresponda a un Administrador."],
                ["3", "—", "El sistema realiza consultas simultáneas a la base de datos para extraer los datos de resumen (total de usuarios, productos, pedidos recientes, resumen de ventas de 30 días)."],
                ["4", "—", "El sistema procesa los datos obtenidos y renderiza la interfaz gráfica con los indicadores actualizados."],
                ["5", "El Administrador visualiza el estado general del negocio en las tarjetas informativas y gráficos en pantalla.", "El sistema permanece activo y listo para responder a las interacciones del menú lateral."]
            ],
            "exceptional": [
                ["2", "El Administrador intenta ingresar escribiendo la URL directamente sin haberse autenticado o tras inactividad prolongada.", "El sistema detecta que no hay una sesión activa, bloquea la carga de la página y redirige al usuario a la pantalla de login con el mensaje: \"Por favor inicia sesión para acceder a esta página.\""],
                ["3", "El servidor de la base de datos no responde o la consulta de métricas falla.", "El sistema renderiza la estructura base del Dashboard, pero despliega un mensaje controlado: \"Error al cargar indicadores. Por favor, actualice la página o intente más tarde.\""]
            ]
        },
        {
            "section": None,
            "id": "CU3", "name": "Administrar Empleados",
            "meta": [
                ["ID", "CU3"], ["Nombre", "Administrar empleados"], ["Actores", "Administrador"],
                ["Descripción", "Permite al Administrador gestionar de forma integral el personal del establecimiento, contemplando el registro de nuevos trabajadores, la consulta de sus datos, la modificación de sus perfiles o cargos, y la baja o inactivación en el sistema."],
                ["Casos de uso relacionados", "CU2 (Visualizar dashboard)"],
                ["Entradas", "Datos del empleado (nombre, correo electrónico, contraseña, teléfono, cargo) y selección de acciones (registrar, editar, eliminar)."],
                ["Salidas", "Lista de empleados actualizada en pantalla, modificaciones guardadas en la base de datos y mensajes de confirmación."],
                ["Precondición", "El Administrador debe tener una sesión activa y válida (CU1) y haber ingresado a la interfaz de gestión desde el Dashboard (CU2)."],
                ["Postcondición", "El sistema actualiza la información en la base de datos a través del ORM y refresca la interfaz visual con los datos modificados del personal."]
            ],
            "typical": [
                ["1", "El Administrador selecciona la opción \"Administrar empleados\" en el menú de navegación del Dashboard.", "El sistema consulta a la base de datos y despliega la interfaz de gestión con la lista de empleados registrados y sus opciones operativas (Agregar, Editar, Eliminar)."],
                ["2", "El Administrador hace clic en el botón para registrar un nuevo empleado.", "El sistema despliega un formulario limpio con los campos requeridos para el perfil del trabajador."],
                ["3", "El Administrador introduce los datos obligatorios del empleado y hace clic en el botón \"Guardar\".", "El sistema recibe los datos de entrada y valida internamente que cumplan con los formatos correctos."],
                ["4", "—", "El sistema realiza una consulta de verificación para asegurar que el correo electrónico no exista previamente."],
                ["5", "—", "El sistema almacena de forma segura el nuevo registro del empleado en la base de datos con rol \"employee\"."],
                ["6", "—", "El sistema refresca la lista del personal en pantalla y muestra un mensaje de éxito: \"Usuario creado exitosamente\"."]
            ],
            "exceptional": [
                ["3", "El Administrador intenta procesar el formulario omitiendo datos requeridos.", "El sistema detiene el registro, resalta visualmente las casillas vacías y muestra una notificación: \"Por favor, complete todos los campos obligatorios.\""],
                ["4", "El correo electrónico del nuevo empleado ya se encuentra registrado.", "El sistema cancela el almacenamiento y muestra una alerta: \"El correo ya está registrado\"."],
                ["3", "El Administrador introduce un formato de correo electrónico incorrecto o una contraseña débil.", "El sistema bloquea el envío del formulario y despliega un mensaje de advertencia: \"Formato de datos incorrecto. La contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula y un número.\""]
            ]
        },
        {
            "section": None,
            "id": "CU4", "name": "Administrar Apartados (Pedidos)",
            "meta": [
                ["ID", "CU4"], ["Nombre", "Administrar apartados"], ["Actores", "Administrador"],
                ["Descripción", "Permite al Administrador supervisar y actualizar el estado de los pedidos, controlando pagos, preparación y entrega."],
                ["Casos de uso relacionados", "CU2 (Visualizar dashboard)"],
                ["Entradas", "Criterios de búsqueda (código de pedido, nombre del cliente), selección de nuevo estado del pedido (pagado, preparando, listo, entregado, cancelado)."],
                ["Salidas", "Listado interactivo de pedidos en pantalla, alertas visuales sobre pedidos con pago pendiente y confirmación del cambio de estatus."],
                ["Precondición", "El Administrador debe tener una sesión activa y válida (CU1) y encontrarse en el panel central de administración (CU2)."],
                ["Postcondición", "El sistema modifica el estado del pedido en la base de datos y, al marcar como entregado, descuenta automáticamente las unidades del inventario."]
            ],
            "typical": [
                ["1", "El Administrador hace clic en la opción \"Administrar pedidos\" desde el menú del Dashboard.", "El sistema consulta la base de datos y despliega el panel de gestión con todos los pedidos ordenados por fecha de creación."],
                ["2", "El Administrador selecciona un pedido en estado \"Pendiente de pago\" para gestionarlo.", "El sistema abre una vista detallada mostrando los artículos del pedido, el monto total, los datos del cliente y el estado actual."],
                ["3", "El Administrador revisa el comprobante de pago subido por el cliente y cambia el estado a \"Pagado\".", "El sistema procesa la solicitud de cambio de estatus."],
                ["4", "El Administrador guarda las modificaciones realizadas.", "El sistema actualiza el registro en la base de datos y muestra un mensaje de éxito: \"Pago confirmado exitosamente\"."]
            ],
            "exceptional": [
                ["3", "El cliente aún no ha subido su comprobante de pago.", "El sistema deniega la operación y muestra: \"El cliente aún no ha subido su comprobante de pago\"."],
                ["3", "El estado actual del pedido no permite la transición solicitada.", "El sistema muestra: \"No se puede realizar esta acción. Transición de estado inválida.\""]
            ]
        },
        {
            "section": None,
            "id": "CU5", "name": "Generar Reportes",
            "meta": [
                ["ID", "CU5"], ["Nombre", "Generar reportes"], ["Actores", "Administrador"],
                ["Descripción", "Permite al Administrador generar informes de productos, inventario, ventas y finanzas de la tienda."],
                ["Casos de uso relacionados", "CU2 (Visualizar dashboard)"],
                ["Entradas", "Selección del tipo de reporte (analytics, financiero, mensual, por producto, por estado), parámetros de filtrado (rango de fechas, 7/15/30/90/365 días)."],
                ["Salidas", "Despliegue de datos estructurados, tablas estadísticas en pantalla y opción de exportar el documento en formato CSV."],
                ["Precondición", "El Administrador debe mantener una sesión activa en la plataforma (CU1) and haber ingresado a la sección de reportes desde el panel de control (CU2)."],
                ["Postcondición", "El sistema compila y presenta los datos analíticos solicitados de manera exclusiva para lectura, sin alterar los registros existentes."]
            ],
            "typical": [
                ["1", "El Administrador selecciona la opción \"Reportes Financieros\" en el menú de navegación del Dashboard.", "El sistema despliega la interfaz de reportes mostrando los diferentes módulos disponibles (Resumen, Ventas Mensuales, Ganancia por Producto, Estado de Pedidos)."],
                ["2", "El Administrador selecciona el período de análisis (7, 15, 30, 90 o 365 días).", "El sistema ajusta los campos de filtrado según el período seleccionado."],
                ["3", "El Administrador hace clic en \"Generar Reporte\" o navega a la pestaña del reporte deseado.", "El sistema procesa los parámetros de consulta y ejecuta las consultas a la base de datos mediante el ORM."],
                ["4", "—", "El sistema estructura la información recopilada y la renderiza en pantalla mediante tablas organizadas y resúmenes estadísticos."],
                ["5", "El Administrador presiona el botón \"Exportar\" para guardar el documento.", "El sistema genera un archivo CSV con la información del reporte y habilita su descarga inmediata."]
            ],
            "exceptional": [
                ["3", "No existen movimientos ni datos que cumplan con los filtros seleccionados.", "El sistema despliega una notificación controlada: \"No se encontraron registros para los criterios seleccionados en este periodo.\""],
                ["5", "Ocurre un problema técnico al generar el archivo de exportación.", "El sistema mantiene el reporte visible en la pantalla y emite un mensaje de alerta: \"No se pudo procesar la descarga del archivo en este momento. Por favor, intente exportar de nuevo.\""]
            ]
        },
        {
            "section": None,
            "id": "CU6", "name": "Administrar Clientes",
            "meta": [
                ["ID", "CU6"], ["Nombre", "Administrar clientes"], ["Actores", "Administrador"],
                ["Descripción", "Permite al Administrador gestionar y supervisar la base de datos de los clientes registrados en la plataforma, incluyendo la visualización de sus datos, la modificación de información y el control de su estado (activo/inactivo)."],
                ["Casos de uso relacionados", "CU2 (Visualizar dashboard)"],
                ["Entradas", "Criterios de búsqueda (nombre o correo del cliente), datos de edición (teléfono, estado de la cuenta)."],
                ["Salidas", "Listado general de clientes en pantalla, visualización detallada y mensajes de confirmación tras modificaciones."],
                ["Precondición", "El Administrador debe estar debidamente autenticado (CU1) y dentro de la interfaz del panel de control (CU2)."],
                ["Postcondición", "Cualquier cambio en el registro o estatus del cliente se almacena de forma permanente en la base de datos."]
            ],
            "typical": [
                ["1", "El Administrador hace clic en la opción \"Administrar usuarios\" del menú del Dashboard.", "El sistema consulta la base de datos y despliega el listado con todos los usuarios registrados, mostrando campos clave como Nombre, Correo, Rol y Estado."],
                ["2", "El Administrador selecciona un cliente y presiona \"Editar\".", "El sistema abre un formulario con la información actual del cliente precargada."],
                ["3", "El Administrador modifica los datos necesarios y hace clic en \"Guardar cambios\".", "El sistema recibe los datos y verifica que los formatos sean correctos."],
                ["4", "—", "El sistema procesa la actualización mediante el ORM y muestra el mensaje: \"Usuario actualizado exitosamente\"."]
            ],
            "exceptional": [
                ["2", "No se encuentra el cliente buscado.", "El sistema muestra: \"No se encontraron usuarios que coincidan con la búsqueda.\""],
                ["3", "Se introduce un correo con formato inválido.", "El sistema resalta el campo con error y muestra: \"Por favor, introduzca un formato de contacto válido.\""]
            ]
        },
        {
            "section": None,
            "id": "CU7", "name": "Auditar Transacciones",
            "meta": [
                ["ID", "CU7"], ["Nombre", "Auditar transacciones"], ["Actores", "Administrador"],
                ["Descripción", "Permite al Administrador revisar el historial de acciones del sistema (creaciones, modificaciones, eliminaciones, pagos, movimientos de inventario)."],
                ["Casos de uso relacionados", "CU2 (Visualizar dashboard)"],
                ["Entradas", "Parámetros de filtrado (tipo de entidad: usuario, producto, orden, inventario, perfil de empleado; tipo de acción: crear, actualizar, eliminar, confirmar pago, movimiento de inventario)."],
                ["Salidas", "Despliegue en pantalla de la bitácora detallada de acciones con metadatos (usuario responsable, fecha, dirección IP, valores anteriores y nuevos)."],
                ["Precondición", "El Administrador debe mantener una sesión activa (CU1) y acceder al módulo desde el menú del panel de control (CU2)."],
                ["Postcondición", "El sistema expone los registros de auditoría de manera exclusiva para lectura, asegurando la inmutabilidad de los datos."]
            ],
            "typical": [
                ["1", "El Administrador selecciona \"Logs de Auditoría\" en el menú del Dashboard.", "El sistema consulta el repositorio de auditoría y despliega los movimientos más recientes."],
                ["2", "El Administrador define filtros específicos (tipo de entidad, tipo de acción).", "El sistema ajusta los parámetros de búsqueda y habilita los filtros."],
                ["3", "El sistema procesa los filtros y extrae los registros correspondientes desde la base de datos.", "El sistema organiza cronológicamente la información y renderiza el listado detallado en pantalla."],
                ["4", "El Administrador hace clic sobre un registro en particular para inspeccionar su desglose.", "El sistema muestra datos complementarios (usuario responsable, valores anteriores y nuevos, dirección IP)."]
            ],
            "exceptional": [
                ["3", "No existen registros que correspondan a los filtros seleccionados.", "El sistema muestra: \"No se encontraron registros para los criterios seleccionados.\""]
            ]
        },
        {
            "section": None,
            "id": "CU8", "name": "Administrar Catálogo",
            "meta": [
                ["ID", "CU8"], ["Nombre", "Administrar catálogo"], ["Actores", "Administrador"],
                ["Descripción", "Permite al Administrador gestionar de forma global los productos expuestos en el catálogo de ventas en línea, sirviendo como la interfaz centralizada desde la cual se supervisa la oferta comercial y se accede a las opciones de registro, modificación y eliminación de artículos."],
                ["Casos de uso relacionados", "CU2, CU9, CU10, CU11"],
                ["Entradas", "Selección de la opción de catálogo, términos de búsqueda/filtrado."],
                ["Salidas", "Despliegue de productos del catálogo con descripciones, precios y estatus; accesos a sub-formularios de gestión."],
                ["Precondición", "El Administrador debe poseer una sesión activa (CU1) y encontrarse dentro de la interfaz del Dashboard (CU2)."],
                ["Postcondición", "El sistema presenta la lista actualizada de los productos en exhibición pública y queda a la espera de una acción específica."]
            ],
            "typical": [
                ["1", "El Administrador hace clic en \"Productos\" en el menú de navegación.", "El sistema consulta la base de datos y recupera todos los productos registrados."],
                ["2", "—", "El sistema renderiza la interfaz gráfica del catálogo administrativo, listando los productos con sus datos principales y habilitando los botones de acción (Agregar, Editar, Eliminar)."],
                ["3", "El Administrador introduce el nombre de un producto o selecciona una categoría en los filtros.", "El sistema procesa los filtros y actualiza la lista en pantalla de manera inmediata."],
                ["4", "El Administrador selecciona una opción operativa (agregar, editar o eliminar).", "El sistema redirige el flujo al caso de uso específico seleccionado (CU9, CU10 o CU11)."]
            ],
            "exceptional": [
                ["1", "No se pueden extraer los registros de productos.", "El sistema muestra: \"Error al cargar el catálogo. Por favor, intente de nuevo.\""],
                ["3", "Ningún producto coincide con los criterios de búsqueda.", "El sistema muestra: \"No se encontraron productos que coincidan con los parámetros de búsqueda.\""]
            ]
        },
        {
            "section": None,
            "id": "CU9", "name": "Registrar Producto en Catálogo",
            "meta": [
                ["ID", "CU9"], ["Nombre", "Registrar producto en catálogo en venta"], ["Actores", "Administrador"],
                ["Descripción", "Permite al Administrador publicar un artículo en la sección comercial pública de la plataforma, asignándole un precio, descripción, categoría, tallas, colores e imágenes para que esté disponible para los clientes en línea."],
                ["Casos de uso relacionados", "CU8 (Administrar catálogo)"],
                ["Entradas", "Nombre, descripción, precio base, categoría, tallas con stock, colores, imagen del producto."],
                ["Salidas", "Producto registrado en el catálogo, confirmación en pantalla y habilitación en la vista pública de clientes."],
                ["Precondición", "El Administrador debe tener una sesión válida (CU1) y encontrarse en el módulo de catálogo (CU8)."],
                ["Postcondición", "El sistema almacena la información del producto en la base de datos, incluyendo sus tallas, colores e imagen principal."]
            ],
            "typical": [
                ["1", "El Administrador hace clic en \"Agregar\" dentro del módulo de catálogo (CU8).", "El sistema despliega el formulario de registro con los campos requeridos."],
                ["2", "El Administrador rellena los campos: nombre, descripción, precio, categoría, tallas con stock, colores.", "El sistema recibe las entradas de texto."],
                ["3", "El Administrador carga la imagen del producto y hace clic en \"Guardar\".", "El sistema valida que todos los campos requeridos estén correctos."],
                ["4", "—", "El sistema procesa la inserción del producto, sus tallas, colores y almacena la imagen en static/images/."],
                ["5", "—", "El sistema redirige al Administrador a la vista del catálogo (CU8) y muestra: \"Producto creado exitosamente\"."]
            ],
            "exceptional": [
                ["3", "El Administrador intenta guardar sin precio o categoría.", "El sistema muestra: \"Por favor, complete todos los campos obligatorios.\""],
                ["3", "La imagen subida no es de formato permitido o excede 5 MB.", "El sistema muestra: \"Formato de archivo no válido. Solo se admiten imágenes PNG, JPG, JPEG, GIF o WebP menores a 5MB.\""]
            ]
        },
        {
            "section": None,
            "id": "CU10", "name": "Editar Producto en Catálogo",
            "meta": [
                ["ID", "CU10"], ["Nombre", "Editar producto en catálogo en venta"], ["Actores", "Administrador"],
                ["Descripción", "Permite al Administrador modificar los datos comerciales de un artículo previamente publicado en el catálogo (precio, descripción, categoría, imagen)."],
                ["Casos de uso relacionados", "CU8 (Administrar catálogo)"],
                ["Entradas", "Selección del artículo y nuevos datos modificados."],
                ["Salidas", "Registro actualizado, notificación de éxito y refrescamiento en la interfaz de clientes."],
                ["Precondición", "El Administrador debe mantener una sesión activa (CU1), estar en el módulo de catálogo (CU8) y el artículo debe estar listado."],
                ["Postcondición", "El sistema guarda las modificaciones de manera persistentemente, actualizando la vista pública."]
            ],
            "typical": [
                ["1", "El Administrador localiza el artículo y hace clic en \"Editar\".", "El sistema consulta los datos del artículo y despliega el formulario con la información precargada."],
                ["2", "El Administrador modifica los campos que desea actualizar.", "El sistema registra las entradas en tiempo real."],
                ["3", "El Administrador hace clic en \"Guardar cambios\".", "El sistema valida que los datos cumplan con las reglas de negocio."],
                ["4", "—", "El sistema procesa la actualización en la base de datos."],
                ["5", "—", "El sistema cierra el formulario y muestra: \"Producto actualizado exitosamente\"."]
            ],
            "exceptional": [
                ["2", "El Administrador introduce un precio menor o igual a cero.", "El sistema muestra: \"Por favor, introduzca un precio válido mayor a cero.\""],
                ["2", "La imagen subida supera los 5 MB o no es de formato válido.", "El sistema muestra: \"Formato de archivo no válido. Solo se admiten imágenes PNG, JPG, JPEG, GIF o WebP menores a 5MB.\""]
            ]
        },
        {
            "section": None,
            "id": "CU11", "name": "Eliminar Producto del Catálogo",
            "meta": [
                ["ID", "CU11"], ["Nombre", "Eliminar producto en catálogo en venta"], ["Actores", "Administrador"],
                ["Descripción", "Permite al Administrador retirar un artículo de la tienda en línea, haciendo que deje de ser visible para el público general."],
                ["Casos de uso relacionados", "CU8 (Administrar catálogo)"],
                ["Entradas", "Selección del artículo y confirmación de la eliminación."],
                ["Salidas", "Registro actualizado (producto desactivado), notificación de éxito."],
                ["Precondición", "El Administrador debe tener una sesión activa (CU1), estar en el módulo de catálogo (CU8) y el artículo debe estar publicado."],
                ["Postcondición", "El sistema actualiza el estado del producto a inactivo en la base de datos, inhabilitándolo en la vista pública sin alterar registros históricos."]
            ],
            "typical": [
                ["1", "El Administrador localiza la prenda en el catálogo (CU8).", "El sistema mantiene el listado con sus opciones operativas."],
                ["2", "El Administrador hace clic en \"Eliminar\" del artículo.", "El sistema despliega un cuadro de diálogo de confirmación: \"¿Está seguro de que desea eliminar este producto?\""],
                ["3", "El Administrador hace clic en \"Confirmar\".", "El sistema procesa la solicitud."],
                ["4", "—", "El sistema ejecuta la baja lógica del producto (cambia estado a inactivo)."],
                ["5", "—", "El sistema cierra el diálogo y muestra: \"Producto eliminado exitosamente\"."]
            ],
            "exceptional": [
                ["3", "El Administrador decide cancelar la eliminación.", "El sistema cierra el diálogo sin realizar modificaciones."]
            ]
        },
        {
            "section": None,
            "id": "CU12", "name": "Administrar Inventario",
            "meta": [
                ["ID", "CU12"], ["Nombre", "Administrar inventario"], ["Actores", "Administrador"],
                ["Descripción", "Permite al Administrador gestionar y supervisar las existencias físicas de mercancía, controlando las entradas, salidas y niveles de stock actualizados en tiempo real."],
                ["Casos de uso relacionados", "CU2, CU13, CU14, CU15"],
                ["Entradas", "Selección de inventario en el menú, parámetros de filtrado."],
                ["Salidas", "Listado general del stock con cantidades, costos y alertas de stock bajo; acceso a opciones de modificación."],
                ["Precondición", "El Administrador debe mantener una sesión activa (CU1) y haber ingresado al inventario desde el Dashboard (CU2)."],
                ["Postcondición", "El sistema expone el estado actual del inventario y queda a la espera de una acción operativa."]
            ],
            "typical": [
                ["1", "El Administrador selecciona \"Inventario\" en el menú del Dashboard.", "El sistema consulta la base de datos y recupera los datos de existencias de todos los productos."],
                ["2", "—", "El sistema renderiza la interfaz de inventario, listando artículos con stock actual, alertas de stock bajo y botones de acción."],
                ["3", "El Administrador introduce el nombre de un producto en la barra de búsqueda.", "El sistema filtra el listado en tiempo real."],
                ["4", "El Administrador escoge una acción (registrar, editar, eliminar o registrar movimiento).", "El sistema redirige al caso de uso correspondiente (CU13, CU14, CU15 o formulario de movimiento)."]
            ],
            "exceptional": [
                ["1", "No se pueden recuperar los registros de stock.", "El sistema muestra: \"Error al cargar el inventario. Intente nuevamente.\""],
                ["3", "Ningún producto coincide con la búsqueda.", "El sistema muestra: \"No se encontraron productos que coincidan con los parámetros especificados.\""]
            ]
        },
        {
            "section": None,
            "id": "CU13", "name": "Registrar Producto (Inventario)",
            "meta": [
                ["ID", "CU13"], ["Nombre", "Registrar producto"], ["Actores", "Administrador"],
                ["Descripción", "Permite al Administrador ingresar una nueva prenda al inventario general, definiendo sus características, precio y existencias iniciales."],
                ["Casos de uso relacionados", "CU12 (Administrar inventario)"],
                ["Entradas", "Nombre, descripción, precio base, categoría, tallas con stock, colores."],
                ["Salidas", "Registro del artículo creado, actualización del listado y mensaje de confirmación."],
                ["Precondición", "El Administrador debe tener una sesión iniciada (CU1) y estar en el módulo de inventario (CU12)."],
                ["Postcondición", "El sistema almacena el producto en la base de datos, quedando disponible para publicación en catálogo."]
            ],
            "typical": [
                ["1", "El Administrador hace clic en \"Agregar\" dentro del panel de inventario (CU12).", "El sistema despliega un formulario en blanco con los campos requeridos."],
                ["2", "El Administrador rellena los campos con los datos de la prenda.", "El sistema recibe los datos introducidos."],
                ["3", "El Administrador hace clic en \"Guardar producto\".", "El sistema valida internamente que todos los campos requeridos estén llenos y que los formatos numéricos sean válidos."],
                ["4", "—", "El sistema procesa la inserción en la base de datos mediante el ORM."],
                ["5", "—", "El sistema cierra el formulario, actualiza el listado y muestra: \"Producto creado exitosamente\"."]
            ],
            "exceptional": [
                ["3", "Se intenta registrar un producto con un nombre duplicado.", "El sistema muestra: \"Ya existe un producto con ese nombre.\""],
                ["3", "Se deja el stock inicial en blanco o se ingresa un precio negativo.", "El sistema muestra: \"Por favor, complete todos los campos obligatorios con valores válidos.\""]
            ]
        },
        {
            "section": None,
            "id": "CU14", "name": "Editar Producto (Inventario)",
            "meta": [
                ["ID", "CU14"], ["Nombre", "Editar producto"], ["Actores", "Administrador"],
                ["Descripción", "Permite al Administrador modificar las especificaciones y niveles de existencias de una prenda registrada en el inventario."],
                ["Casos de uso relacionados", "CU12 (Administrar inventario)"],
                ["Entradas", "Selección del artículo y datos actualizados."],
                ["Salidas", "Registro actualizado, listado refrescado y mensaje de confirmación."],
                ["Precondición", "El Administrador debe mantener una sesión activa (CU1), estar en el módulo de inventario (CU12) y el artículo debe existir."],
                ["Postcondición", "El sistema almacena las modificaciones en la base de datos."]
            ],
            "typical": [
                ["1", "El Administrador busca el artículo y hace clic en \"Editar\".", "El sistema despliega el formulario con los datos precargados."],
                ["2", "El Administrador modifica los campos requeridos.", "El sistema registra las entradas de datos."],
                ["3", "El Administrador hace clic en \"Guardar cambios\".", "El sistema verifica que no existan campos obligatorios vacíos."],
                ["4", "—", "El sistema procesa la actualización en la base de datos."],
                ["5", "—", "El sistema cierra el formulario y muestra: \"Producto actualizado exitosamente\"."]
            ],
            "exceptional": [
                ["3", "Se deja el campo de precio o stock vacío o con valor negativo.", "El sistema muestra: \"Por favor, verifique los campos numéricos. Los valores deben ser mayores o iguales a cero.\""]
            ]
        },
        {
            "section": None,
            "id": "CU15", "name": "Eliminar Producto (Inventario)",
            "meta": [
                ["ID", "CU15"], ["Nombre", "Eliminar producto"], ["Actores", "Administrador"],
                ["Descripción", "Permite al Administrador dar de baja un artículo del inventario interno general."],
                ["Casos de uso relacionados", "CU12 (Administrar inventario)"],
                ["Entradas", "Selección del producto y confirmación de la acción."],
                ["Salidas", "Registro actualizado (baja lógica), listado refrescado y mensaje de confirmación."],
                ["Precondición", "El Administrador debe mantener una sesión activa (CU1), estar en el inventario (CU12) y el artículo debe existir."],
                ["Postcondición", "El sistema aplica la baja lógica del producto, preservando el histórico."]
            ],
            "typical": [
                ["1", "El Administrador ubica la prenda en el inventario (CU12).", "El sistema mantiene el listado con opciones operativas."],
                ["2", "El Administrador hace clic en \"Eliminar\".", "El sistema muestra un cuadro de confirmación: \"¿Está seguro de que desea eliminar este producto?\""],
                ["3", "El Administrador hace clic en \"Confirmar\".", "El sistema procesa la solicitud."],
                ["4", "—", "El sistema ejecuta la baja lógica en la base de datos (estado = inactivo)."],
                ["5", "—", "El sistema cierra el diálogo y muestra: \"Producto eliminado exitosamente\"."]
            ],
            "exceptional": [
                ["3", "El Administrador cancela la operación.", "El sistema cierra el diálogo sin modificar datos."]
            ]
        },
        # --- EMPLEADO ---
        {
            "section": "3.2.2 Funciones del Empleado",
            "id": "CU16", "name": "Autenticar Usuario (Empleado)",
            "meta": [
                ["ID", "CU16"], ["Nombre", "Autenticar usuario"], ["Actores", "Empleado"],
                ["Descripción", "Permite al empleado ingresar al sistema validando sus credenciales de acceso para iniciar una sesión segura y acceder a las funciones de su rol."],
                ["Casos de uso relacionados", "CU17 (Visualizar dashboard). Depende de: CU3 (Administrar empleados)."],
                ["Entradas", "Correo electrónico y contraseña."], ["Salidas", "Sesión activa, redirección al Dashboard del Empleado o mensaje de error."],
                ["Precondición", "El empleado debe estar previamente registrado en el sistema por un Administrador (CU3) y poseer un estado activo."],
                ["Postcondición", "El sistema inicia la sesión del empleado y le permite el acceso al panel de funciones autorizadas."]
            ],
            "typical": [
                ["1", "El Empleado accede al apartado de inicio de sesión.", "El sistema renderiza el formulario solicitando correo y contraseña."],
                ["2", "El Empleado ingresa sus credenciales y hace clic en \"Iniciar Sesión\".", "El sistema recibe los datos y realiza la consulta en la base de datos."],
                ["3", "—", "El sistema valida que el correo y la contraseña coincidan, que el rol sea \"employee\" y que la cuenta esté activa."],
                ["4", "—", "El sistema inicializa la sesión, asigna los permisos del rol y redirige al Dashboard del Empleado (CU17)."]
            ],
            "exceptional": [
                ["3", "Las credenciales no coinciden con ningún registro.", "El sistema deniega el acceso y muestra: \"Correo o contraseña incorrectos\"."],
                ["3", "Las credenciales corresponden a un rol distinto.", "El sistema muestra: \"Su cuenta no tiene acceso a esta sección.\"."],
                ["3", "La cuenta del empleado está marcada como inactiva.", "El sistema muestra: \"Usuario inactivo. Contacte al Administrador.\""]
            ]
        },
        {
            "section": None,
            "id": "CU17", "name": "Visualizar Dashboard (Empleado)",
            "meta": [
                ["ID", "CU17"], ["Nombre", "Visualizar dashboard"], ["Actores", "Empleado"],
                ["Descripción", "Muestra al empleado un panel con pedidos recientes, pagos pendientes, alertas de stock bajo y ventas de la semana."],
                ["Casos de uso relacionados", "CU16 (Autenticar usuario)"], ["Entradas", "Sesión activa del empleado."],
                ["Salidas", "Dashboard con métricas operativas y accesos directos a los módulos autorizados."],
                ["Precondición", "El empleado debe haber iniciado sesión (CU16)."], ["Postcondición", "Se muestra el panel de control del empleado."]
            ],
            "typical": [
                ["1", "El Empleado es redirigido al dashboard tras autenticarse.", "El sistema valida la sesión y ejecuta consultas para obtener pedidos recientes, pagos pendientes, stock bajo y ventas de 7 días."],
                ["2", "—", "El sistema renderiza el Dashboard con las métricas cargadas."],
                ["3", "El Empleado visualiza la información.", "—"]
            ],
            "exceptional": [
                ["1", "La sesión ha expirado.", "El sistema redirige al login: \"Sesión expirada. Inicie sesión nuevamente.\""]
            ]
        },
        {
            "section": None,
            "id": "CU18", "name": "Consultar Catálogo de Productos (Empleado)",
            "meta": [
                ["ID", "CU18"], ["Nombre", "Consultar catálogo de productos"], ["Actores", "Empleado"],
                ["Descripción", "Permite al empleado ver el listado de productos con precios, stock y especificaciones en modo solo lectura."],
                ["Casos de uso relacionados", "CU17 (Dashboard)"], ["Entradas", "Parámetros opcionales de búsqueda (nombre, categoría, precio)."],
                ["Salidas", "Catálogo con imagen, nombre, categoría, precio y stock."],
                ["Precondición", "Sesión activa del empleado (CU16)."], ["Postcondición", "Se muestra la información actualizada de productos."]
            ],
            "typical": [
                ["1", "El Empleado selecciona \"Catálogo de Productos\" desde su panel.", "El sistema renderiza el catálogo paginado."],
                ["2", "El Empleado aplica filtros de búsqueda.", "El sistema ejecuta la consulta filtrada y refresca los resultados."],
                ["3", "El Empleado selecciona un producto.", "El sistema muestra la ficha técnica completa."]
            ],
            "exceptional": [
                ["2", "Ningún producto coincide con la búsqueda.", "El sistema muestra: \"No se encontraron productos.\""]
            ]
        },
        {
            "section": None,
            "id": "CU19", "name": "Registrar Venta",
            "meta": [
                ["ID", "CU19"], ["Nombre", "Registrar venta"], ["Actores", "Empleado"],
                ["Descripción", "Permite al Empleado registrar una venta directa realizada en el establecimiento físico, seleccionando productos, calculando el total y descontando automáticamente del inventario."],
                ["Casos de uso relacionados", "CU18, CU21, CU23"],
                ["Entradas", "Productos seleccionados, cantidades, datos del cliente (opcional), método de pago."],
                ["Salidas", "Registro de venta almacenado, stock actualizado, monto total calculado y confirmación en pantalla."],
                ["Precondición", "El Empleado debe tener sesión activa (CU16) y estar en el módulo de ventas (CU17). Los productos deben tener stock disponible."],
                ["Postcondición", "El sistema almacena la venta y descuenta las unidades del inventario."]
            ],
            "typical": [
                ["1", "El Empleado selecciona \"Registrar venta\" desde el Dashboard.", "El sistema despliega la interfaz de venta con un buscador de productos."],
                ["2", "El Empleado busca y selecciona los productos con la cantidad deseada.", "El sistema verifica la disponibilidad en stock y agrega los ítems al detalle, calculando el subtotal."],
                ["3", "El Empleado indica el método de pago y opcionalmente asocia al cliente.", "El sistema calcula el monto total incluyendo impuestos (16%)."],
                ["4", "El Empleado hace clic en \"Confirmar venta\".", "El sistema valida los datos y procesa la transacción."],
                ["5", "—", "El sistema registra la venta en la base de datos y descuenta las unidades del inventario."],
                ["6", "—", "El sistema muestra un mensaje de confirmación y habilita la opción de generar factura (CU21)."]
            ],
            "exceptional": [
                ["2", "La cantidad solicitada supera el stock disponible.", "El sistema rechaza la adición y muestra: \"Cantidad solicitada supera el stock disponible.\""],
                ["4", "No hay productos en el detalle de venta.", "El sistema bloquea la operación y muestra: \"Debe agregar al menos un producto para registrar la venta.\""]
            ]
        },
        {
            "section": None,
            "id": "CU20", "name": "Registrar Apartado de Producto (Presencial)",
            "meta": [
                ["ID", "CU20"], ["Nombre", "Registrar apartado de producto"], ["Actores", "Empleado"],
                ["Descripción", "Permite al Empleado registrar presencialmente la reserva de productos solicitados por un cliente que visita la tienda, estableciendo un abono y un plazo límite de retiro."],
                ["Casos de uso relacionados", "CU18, CU22, CU4"],
                ["Entradas", "Productos a apartar, cantidades, datos del cliente, monto de abono, fecha límite de retiro."],
                ["Salidas", "Apartado registrado, stock reservado, comprobante generado y confirmación."],
                ["Precondición", "El Empleado debe contar con sesión activa (CU16) y los productos deben tener stock disponible."],
                ["Postcondición", "El sistema almacena el apartado, reserva las unidades y refleja el registro en el módulo de administración (CU4)."]
            ],
            "typical": [
                ["1", "El Empleado selecciona \"Registrar apartado\".", "El sistema despliega el formulario con buscador de productos."],
                ["2", "El Empleado selecciona los productos y cantidades deseadas.", "El sistema reserva temporalmente el stock y calcula el monto total."],
                ["3", "El Empleado ingresa los datos del cliente y el monto de abono.", "El sistema valida que el abono sea adecuado."],
                ["4", "El Empleado establece la fecha límite de retiro y confirma.", "El sistema procesa la solicitud."],
                ["5", "—", "El sistema almacena el apartado, marca el stock como reservado y genera el comprobante."],
                ["6", "—", "El sistema muestra: \"Apartado registrado con éxito.\""]
            ],
            "exceptional": [
                ["3", "El abono es inferior al mínimo requerido.", "El sistema muestra: \"El abono ingresado no cumple con el mínimo permitido.\""],
                ["4", "La fecha límite es anterior a la fecha actual.", "El sistema muestra: \"La fecha límite debe ser posterior a la fecha actual.\""]
            ]
        },
        {
            "section": None,
            "id": "CU21", "name": "Registrar Factura de Compra",
            "meta": [
                ["ID", "CU21"], ["Nombre", "Registrar factura de compra"], ["Actores", "Empleado"],
                ["Descripción", "Permite al Empleado generar el comprobante correspondiente a una venta ya registrada, detallando productos, montos e impuestos."],
                ["Casos de uso relacionados", "CU19 (Registrar venta)"], ["Entradas", "Identificador de la venta, datos fiscales del cliente (opcional)."],
                ["Salidas", "Factura generada (visualización e impresión/descarga), registro vinculado a la venta."],
                ["Precondición", "El Empleado debe tener sesión activa (CU16) y debe existir una venta confirmada (CU19)."],
                ["Postcondición", "El sistema almacena la factura vinculada a la venta, disponible para auditoría."]
            ],
            "typical": [
                ["1", "El Empleado, tras confirmar una venta, hace clic en \"Generar factura\".", "El sistema recupera los datos de la venta."],
                ["2", "—", "El sistema despliega un formulario con los datos precargados y solicita datos fiscales adicionales."],
                ["3", "El Empleado completa los datos y hace clic en \"Emitir factura\".", "El sistema valida los campos obligatorios."],
                ["4", "—", "El sistema genera el documento de factura con numeración correlativa y lo asocia a la venta."],
                ["5", "—", "El sistema muestra la factura en pantalla y habilita las opciones de imprimir o descargar."]
            ],
            "exceptional": [
                ["1", "La venta ya tiene factura emitida.", "El sistema muestra: \"Esta venta ya cuenta con una factura registrada.\""],
                ["3", "Campos obligatorios vacíos.", "El sistema muestra: \"Por favor, complete los datos obligatorios para emitir la factura.\""]
            ]
        },
        {
            "section": None,
            "id": "CU22", "name": "Gestionar Clientes (Empleado)",
            "meta": [
                ["ID", "CU22"], ["Nombre", "Gestionar clientes"], ["Actores", "Empleado"],
                ["Descripción", "Permite al Empleado consultar, registrar y actualizar datos básicos de los clientes que realizan compras o apartados presencialmente."],
                ["Casos de uso relacionados", "CU19, CU20"], ["Entradas", "Criterios de búsqueda (nombre), datos del cliente a registrar o editar."],
                ["Salidas", "Listado de clientes, confirmación de registro o actualización."],
                ["Precondición", "El Empleado debe contar con sesión activa (CU16) y acceso al módulo desde el Dashboard (CU17)."],
                ["Postcondición", "Los datos nuevos o modificados se almacenan de forma permanente en la base de datos."]
            ],
            "typical": [
                ["1", "El Empleado selecciona \"Gestionar clientes\".", "El sistema despliega el listado de clientes registrados."],
                ["2", "El Empleado busca un cliente por nombre.", "El sistema filtra el listado en tiempo real."],
                ["3", "Si el cliente no existe, el Empleado hace clic en \"Registrar nuevo\" e ingresa los datos.", "El sistema valida el formato de los campos."],
                ["4", "El Empleado guarda la información.", "El sistema procesa el registro mediante el ORM."],
                ["5", "—", "El sistema actualiza el listado y muestra: \"Usuario creado exitosamente\"."]
            ],
            "exceptional": [
                ["2", "La búsqueda no arroja coincidencias.", "El sistema muestra: \"No se encontraron clientes\" y habilita la opción de registrar uno nuevo."],
                ["3", "El correo ya está registrado.", "El sistema rechaza el registro y muestra: \"El correo ya está registrado.\""]
            ]
        },
        {
            "section": None,
            "id": "CU23", "name": "Consultar Inventario (Empleado)",
            "meta": [
                ["ID", "CU23"], ["Nombre", "Consultar inventario"], ["Actores", "Empleado"],
                ["Descripción", "Permite al empleado verificar stock de productos en modo solo lectura."],
                ["Casos de uso relacionados", "CU17, CU19, CU20"], ["Entradas", "Criterios de búsqueda (nombre, categoría)."],
                ["Salidas", "Listado de productos con cantidad disponible."],
                ["Precondición", "Sesión activa del empleado (CU16)."], ["Postcondición", "Se muestra el stock actual en solo lectura."]
            ],
            "typical": [
                ["1", "El Empleado selecciona \"Consultar inventario\".", "El sistema muestra el listado de productos con stock actual."],
                ["2", "El Empleado busca un producto específico.", "El sistema filtra y muestra los resultados."]
            ],
            "exceptional": [
                ["1", "Error de conexión.", "El sistema muestra: \"Error al cargar el inventario. Intente nuevamente.\""],
                ["2", "Sin resultados.", "El sistema muestra: \"No se encontraron productos.\""]
            ]
        },
        # --- CLIENTE ---
        {
            "section": "3.2.3 Funciones del Cliente",
            "id": "CU24", "name": "Registrarse",
            "meta": [
                ["ID", "CU24"], ["Nombre", "Registrarse"], ["Actores", "Cliente"],
                ["Descripción", "Permite a un usuario nuevo crear una cuenta proporcionando sus datos personales y de contacto."],
                ["Casos de uso relacionados", "CU26 (Autenticar usuario)"],
                ["Entradas", "Nombre, correo electrónico, teléfono, contraseña y confirmación de contraseña."],
                ["Salidas", "Cuenta creada, mensaje de confirmación y redirección al login."],
                ["Precondición", "El usuario no debe tener una cuenta previa con el mismo correo."],
                ["Postcondición", "El sistema almacena el nuevo cliente con la contraseña cifrada."]
            ],
            "typical": [
                ["1", "El usuario hace clic en \"Registrarse\" desde la vista de login.", "El sistema despliega el formulario de registro."],
                ["2", "El usuario completa los campos requeridos.", "El sistema valida el formato de cada campo en tiempo real."],
                ["3", "El usuario confirma la contraseña y hace clic en \"Crear cuenta\".", "El sistema verifica que las contraseñas coincidan y que el correo no exista."],
                ["4", "—", "El sistema cifra la contraseña y almacena el registro."],
                ["5", "—", "Muestra \"Cuenta creada con éxito\" y redirige al login (CU26)."]
            ],
            "exceptional": [
                ["3", "El correo ya está registrado.", "El sistema muestra: \"Ya existe una cuenta asociada a este correo.\""],
                ["3", "Las contraseñas no coinciden.", "El sistema muestra: \"Las contraseñas no coinciden.\""],
                ["2", "Campos vacíos o contraseña débil.", "El sistema muestra: \"Complete todos los campos. La contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula y un número.\""]
            ]
        },
        {
            "section": None,
            "id": "CU26", "name": "Autenticar Usuario (Cliente)",
            "meta": [
                ["ID", "CU26"], ["Nombre", "Autenticar usuario"], ["Actores", "Cliente"],
                ["Descripción", "Permite al Cliente ingresar de manera segura al sistema validando sus credenciales previamente registradas."],
                ["Casos de uso relacionados", "CU24, CU27, CU32"], ["Entradas", "Correo electrónico y contraseña."],
                ["Salidas", "Sesión activa y redirección al catálogo o perfil del Cliente."],
                ["Precondición", "El Cliente debe estar previamente registrado (CU24) y contar con una cuenta activa."],
                ["Postcondición", "El sistema inicia la sesión y habilita el acceso a funcionalidades exclusivas de clientes."]
            ],
            "typical": [
                ["1", "El Cliente introduce sus credenciales en el formulario de login y hace clic en \"Ingresar\".", "El sistema recibe los datos de forma segura."],
                ["2", "—", "El sistema cifra y valida las credenciales contra la base de datos."],
                ["3", "—", "El sistema verifica que la cuenta esté activa y corresponda al rol \"Cliente\"."],
                ["4", "—", "El sistema genera la sesión, otorga permisos y redirige al Cliente al catálogo (CU32)."]
            ],
            "exceptional": [
                ["2", "Correo o contraseña incorrectos.", "El sistema deniega el acceso y muestra: \"Correo o contraseña incorrectos.\""],
                ["3", "La cuenta está inactiva.", "El sistema muestra: \"Su cuenta se encuentra inactiva. Póngase en contacto con la tienda.\""]
            ]
        },
        {
            "section": None,
            "id": "CU27", "name": "Ver Detalles de Perfil",
            "meta": [
                ["ID", "CU27"], ["Nombre", "Ver detalles de perfil"], ["Actores", "Cliente"],
                ["Descripción", "Muestra los datos personales del cliente y accesos a \"Mis Pedidos\" y \"Configurar Perfil\"."],
                ["Casos de uso relacionados", "CU26, CU28, CU30, CU31"], ["Entradas", "Solicitud de acceso al perfil."],
                ["Salidas", "Vista con datos del cliente y accesos directos."], ["Precondición", "Sesión activa del cliente (CU26)."],
                ["Postcondición", "Se muestra la información del perfil."]
            ],
            "typical": [
                ["1", "El Cliente hace clic en su ícono de perfil.", "El sistema verifica la sesión y consulta los datos del cliente en la base de datos."],
                ["2", "—", "El sistema renderiza la vista de perfil con nombre, correo, teléfono y accesos."],
                ["3", "El Cliente selecciona una opción.", "—"]
            ],
            "exceptional": [
                ["1", "La sesión ha expirado.", "El sistema redirige al login: \"Sesión expirada. Inicie sesión nuevamente.\""]
            ]
        },
        {
            "section": None,
            "id": "CU28", "name": "Carrito de Apartados",
            "meta": [
                ["ID", "CU28"], ["Nombre", "Carrito de apartados"], ["Actores", "Cliente"],
                ["Descripción", "Permite al Cliente visualizar los productos que ha añadido temporalmente con la intención de apartarlos, mostrando detalle, cantidad y monto total estimado."],
                ["Casos de uso relacionados", "CU27, CU29, CU35"], ["Entradas", "Solicitud de acceso al carrito."],
                ["Salidas", "Listado de productos con cantidades, subtotal y opción de proceder al apartado."],
                ["Precondición", "El Cliente debe haber iniciado sesión (CU26) y haber agregado al menos un producto al carrito."],
                ["Postcondición", "El sistema muestra el estado actual del carrito."]
            ],
            "typical": [
                ["1", "El Cliente hace clic en el ícono del carrito de apartados.", "El sistema consulta los productos agregados en la sesión actual."],
                ["2", "—", "El sistema despliega el listado de artículos con imagen, cantidad, precio unitario y subtotal."],
                ["3", "—", "El sistema calcula y muestra el monto total del carrito."],
                ["4", "El Cliente revisa el contenido y hace clic en \"Continuar con el apartado\".", "El sistema redirige al CU35 (Realizar apartado)."]
            ],
            "exceptional": [
                ["1", "El carrito está vacío.", "El sistema muestra: \"Su carrito de apartados está vacío. Explore nuestro catálogo para agregar productos.\" con enlace al catálogo (CU32)."],
                ["2", "Algunos productos ya no tienen stock disponible.", "El sistema marca el artículo y muestra: \"El producto seleccionado ya no se encuentra disponible.\""]
            ]
        },
        {
            "section": None,
            "id": "CU29", "name": "Gestionar Carrito",
            "meta": [
                ["ID", "CU29"], ["Nombre", "Gestionar carrito"], ["Actores", "Cliente"],
                ["Descripción", "Permite al Cliente modificar el contenido de su carrito, ajustando cantidades o eliminando artículos antes de finalizar el apartado."],
                ["Casos de uso relacionados", "CU28"], ["Entradas", "Selección de producto, nueva cantidad o confirmación de eliminación."],
                ["Salidas", "Carrito actualizado con nuevo monto total."],
                ["Precondición", "El Cliente debe tener sesión activa (CU26) y al menos un producto en el carrito (CU28)."],
                ["Postcondición", "El sistema actualiza el estado del carrito en la sesión del Cliente."]
            ],
            "typical": [
                ["1", "El Cliente ajusta la cantidad de un producto mediante controles de incremento/decremento.", "El sistema valida que la nueva cantidad no supere el stock disponible."],
                ["2", "—", "El sistema recalcula el subtotal del artículo y el monto total del carrito."],
                ["3", "El Cliente hace clic en \"Eliminar\" sobre un artículo.", "El sistema remueve el producto del carrito."],
                ["4", "—", "El sistema actualiza la interfaz en tiempo real y refleja el nuevo total."]
            ],
            "exceptional": [
                ["1", "La cantidad excede el stock disponible.", "El sistema muestra: \"La cantidad máxima disponible para este producto es [X] unidades.\""],
                ["3", "El Cliente elimina el último producto del carrito.", "El sistema vacía el carrito y muestra: \"Su carrito de apartados está vacío.\""]
            ]
        },
        {
            "section": None,
            "id": "CU30", "name": "Consultar Historial",
            "meta": [
                ["ID", "CU30"], ["Nombre", "Consultar historial"], ["Actores", "Cliente"],
                ["Descripción", "Muestra el listado cronológico de pedidos anteriores del cliente con su estado."],
                ["Casos de uso relacionados", "CU27 (Ver perfil)"], ["Entradas", "Criterios opcionales de filtrado (fechas, estado)."],
                ["Salidas", "Listado de pedidos con fecha, productos, monto y estado."], ["Precondición", "Sesión activa del cliente (CU26)."],
                ["Postcondición", "Se muestra el historial en solo lectura."]
            ],
            "typical": [
                ["1", "El Cliente selecciona \"Mis Pedidos\" desde su perfil.", "El sistema recupera los pedidos asociados a su cuenta."],
                ["2", "—", "El sistema renderiza el listado ordenado cronológicamente."],
                ["3", "El Cliente aplica un filtro.", "El sistema actualiza los resultados."]
            ],
            "exceptional": [
                ["1", "Sin pedidos previos.", "El sistema muestra: \"Aún no tiene historial de compras.\""],
                ["3", "Sin resultados.", "El sistema muestra: \"No se encontraron registros.\""]
            ]
        },
        {
            "section": None,
            "id": "CU31", "name": "Configurar Perfil",
            "meta": [
                ["ID", "CU31"], ["Nombre", "Configurar perfil"], ["Actores", "Cliente"],
                ["Descripción", "Permite al cliente actualizar su información personal y contraseña."],
                ["Casos de uso relacionados", "CU27 (Ver perfil)"], ["Entradas", "Datos a modificar (nombre, teléfono, correo, contraseña)."],
                ["Salidas", "Perfil actualizado y confirmación."], ["Precondición", "Sesión activa del cliente (CU26)."],
                ["Postcondición", "Los datos se guardan de forma persistente."]
            ],
            "typical": [
                ["1", "El Cliente selecciona \"Configurar perfil\".", "El sistema muestra el formulario con los datos actuales precargados."],
                ["2", "El Cliente modifica los campos.", "El sistema valida los formatos en tiempo real."],
                ["3", "Si cambia contraseña, introduce la actual y la nueva.", "El sistema verifica que la contraseña actual sea correcta."],
                ["4", "El Cliente hace clic en \"Guardar cambios\".", "El sistema actualiza el registro en la base de datos y muestra: \"Perfil actualizado con éxito.\""]
            ],
            "exceptional": [
                ["3", "Contraseña actual incorrecta.", "El sistema muestra: \"La contraseña actual es incorrecta.\""],
                ["2", "Formato inválido.", "El sistema muestra: \"Introduzca un formato de contacto válido.\""]
            ]
        },
        {
            "section": None,
            "id": "CU32", "name": "Consultar Catálogo",
            "meta": [
                ["ID", "CU32"], ["Nombre", "Consultar catálogo"], ["Actores", "Cliente"],
                ["Descripción", "Permite al Cliente, registrado o no, visualizar el listado público de productos disponibles para la venta en línea."],
                ["Casos de uso relacionados", "CU26, CU33, CU34"], ["Entradas", "Selección de categoría o navegación libre por el catálogo."],
                ["Salidas", "Listado de productos con imagen, nombre y precio."], ["Precondición", "El Cliente debe encontrarse en la plataforma web pública; no se requiere sesión activa."],
                ["Postcondición", "El sistema despliega la información pública y actualizada del catálogo."]
            ],
            "typical": [
                ["1", "El Cliente accede a la sección \"Catálogo\" desde la página principal.", "El sistema consulta la base de datos y recupera los productos publicados."],
                ["2", "—", "El sistema renderiza el catálogo público de forma paginada, con imágenes, nombres y precios."],
                ["3", "El Cliente selecciona una categoría específica (ej. \"Mujeres\", \"Hombres\").", "El sistema filtra el listado dinámicamente."],
                ["4", "El Cliente hace clic sobre un producto de su interés.", "El sistema redirige al CU33 (Ver detalles de producto)."]
            ],
            "exceptional": [
                ["1", "Error al cargar los productos del servidor.", "El sistema muestra: \"Error al cargar el catálogo. Intente nuevamente.\""],
                ["3", "Ninguna categoría contiene productos disponibles.", "El sistema muestra: \"No hay productos disponibles en esta categoría por el momento.\""]
            ]
        },
        {
            "section": None,
            "id": "CU33", "name": "Ver Detalles de Producto",
            "meta": [
                ["ID", "CU33"], ["Nombre", "Ver detalles de producto"], ["Actores", "Cliente"],
                ["Descripción", "Permite al Cliente visualizar la ficha ampliada de un producto específico, incluyendo descripción, precio, tallas y colores disponibles."],
                ["Casos de uso relacionados", "CU32, CU28"], ["Entradas", "Selección del producto desde el catálogo (CU32) o desde resultados de búsqueda (CU34)."],
                ["Salidas", "Vista detallada del producto con toda su información y el botón para agregar al carrito."],
                ["Precondición", "El producto debe encontrarse publicado y activo en el catálogo."], ["Postcondición", "El sistema despliega la información completa del producto."]
            ],
            "typical": [
                ["1", "El Cliente hace clic sobre un producto desde el catálogo (CU32).", "El sistema consulta el detalle completo del artículo."],
                ["2", "—", "El sistema renderiza la ficha del producto con descripción, precio, imágenes, tallas y colores disponibles."],
                ["3", "El Cliente selecciona la talla y color de su preferencia y define la cantidad.", "—"],
                ["4", "El Cliente hace clic en \"Agregar al carrito\".", "El sistema añade el producto al carrito de apartados (CU28) y muestra la confirmación."]
            ],
            "exceptional": [
                ["1", "El producto ya no está disponible o fue retirado.", "El sistema muestra: \"Este producto ya no se encuentra disponible.\""],
                ["4", "La cantidad supera el stock disponible.", "El sistema rechaza la acción y muestra: \"La cantidad solicitada supera las unidades disponibles.\""]
            ]
        },
        {
            "section": None,
            "id": "CU34", "name": "Buscar Productos",
            "meta": [
                ["ID", "CU34"], ["Nombre", "Buscar productos"], ["Actores", "Cliente"],
                ["Descripción", "Permite al Cliente localizar productos específicos dentro del catálogo mediante palabras clave y filtros opcionales."],
                ["Casos de uso relacionados", "CU32"], ["Entradas", "Término de búsqueda (texto libre) y filtros opcionales (categoría, rango de precio, talla)."],
                ["Salidas", "Listado de productos que coinciden con los criterios de búsqueda."], ["Precondición", "El Cliente debe encontrarse en la sección del catálogo (CU32)."],
                ["Postcondición", "El sistema despliega los resultados sin alterar el estado de los registros."]
            ],
            "typical": [
                ["1", "El Cliente introduce una palabra clave en la barra de búsqueda y presiona \"Buscar\".", "El sistema procesa el término ingresado."],
                ["2", "—", "El sistema consulta la base de datos aplicando coincidencias sobre nombre y descripción."],
                ["3", "El Cliente aplica filtros adicionales (categoría, rango de precio).", "El sistema refina los resultados dinámicamente."],
                ["4", "—", "El sistema renderiza el listado de productos coincidentes en pantalla."]
            ],
            "exceptional": [
                ["2", "Ningún producto coincide con la búsqueda.", "El sistema muestra: \"No se encontraron productos que coincidan con su búsqueda.\""],
                ["1", "El campo de búsqueda está vacío.", "El sistema muestra: \"Por favor, introduzca un término de búsqueda.\""]
            ]
        },
        {
            "section": None,
            "id": "CU35", "name": "Realizar Apartado",
            "meta": [
                ["ID", "CU35"], ["Nombre", "Realizar apartado"], ["Actores", "Cliente"],
                ["Descripción", "Permite al Cliente formalizar la reserva de los productos contenidos en su carrito, generando una solicitud de apartado con un plazo límite de retiro."],
                ["Casos de uso relacionados", "CU28, CU36"], ["Entradas", "Confirmación de los productos del carrito, punto de retiro (si aplica), aceptación de términos."],
                ["Salidas", "Solicitud de apartado registrada, código de apartado generado y redirección al proceso de pago (CU36)."],
                ["Precondición", "El Cliente debe haber iniciado sesión (CU26) y contar con al menos un producto en el carrito (CU28)."],
                ["Postcondición", "El sistema almacena el apartado, reserva las unidades del inventario y establece el plazo de retiro."]
            ],
            "typical": [
                ["1", "El Cliente, desde el carrito (CU28), hace clic en \"Realizar apartado\".", "El sistema muestra un resumen final con productos, cantidades y monto total."],
                ["2", "El Cliente confirma los datos y acepta los términos y condiciones.", "El sistema valida la disponibilidad de stock en tiempo real."],
                ["3", "El Cliente hace clic en \"Confirmar apartado\".", "El sistema procesa la solicitud mediante el ORM."],
                ["4", "—", "El sistema genera un código único de apartado, establece el plazo límite y reserva el stock."],
                ["5", "—", "El sistema redirige al Cliente al proceso de pago (CU36) y muestra: \"Apartado generado con éxito.\""]
            ],
            "exceptional": [
                ["2", "Alguno de los productos perdió disponibilidad.", "El sistema detiene el proceso y muestra: \"Uno de los productos ya no se encuentra disponible. Por favor, actualice su carrito.\""],
                ["3", "Error de conexión con el servidor.", "El sistema mantiene el carrito intacto y muestra: \"No se pudo procesar el apartado. Intente nuevamente.\""]
            ]
        },
        {
            "section": None,
            "id": "CU36", "name": "Pagar Apartado",
            "meta": [
                ["ID", "CU36"], ["Nombre", "Pagar apartado"], ["Actores", "Cliente"],
                ["Descripción", "Permite al Cliente realizar el pago correspondiente a un apartado previamente generado, a través de los métodos de pago habilitados."],
                ["Casos de uso relacionados", "CU35 (Realizar apartado)"], ["Entradas", "Selección del método de pago, datos de la transacción (comprobante de transferencia), monto a cancelar."],
                ["Salidas", "Confirmación de pago registrada, actualización del estado del apartado y comprobante digital."],
                ["Precondición", "El Cliente debe contar con un apartado previamente generado y vigente (CU35)."],
                ["Postcondición", "El sistema actualiza el estado del apartado, quedando disponible para validación por el Administrador (CU4)."]
            ],
            "typical": [
                ["1", "El Cliente, tras generar el apartado (CU35), es redirigido a la vista de pago.", "El sistema despliega los métodos de pago disponibles."],
                ["2", "El Cliente selecciona el método de pago e introduce los datos o adjunta el comprobante.", "El sistema recibe la información de forma segura."],
                ["3", "El Cliente hace clic en \"Confirmar pago\".", "El sistema valida el formato y la completitud de los datos."],
                ["4", "—", "El sistema registra el pago asociado al apartado y actualiza su estado."],
                ["5", "—", "El sistema muestra el comprobante de pago y el mensaje: \"Pago registrado con éxito.\""]
            ],
            "exceptional": [
                ["3", "No se adjunta el comprobante requerido.", "El sistema muestra: \"Por favor, adjunte el comprobante de pago para continuar.\""],
                ["4", "El plazo del apartado ha vencido.", "El sistema rechaza el pago, libera el stock y muestra: \"El plazo de este apartado ha vencido. Por favor, realice un nuevo apartado.\""]
            ]
        }
    ]

    for cu in use_cases_data:
        if cu["section"]:
            add_custom_heading(cu["section"], level=2)
        add_custom_heading(f"{cu['id']} — {cu['name']}", level=3)
        
        # Meta table
        add_styled_table(["Campo", "Descripción"], cu["meta"])
        
        # Flows
        doc.add_paragraph("Flujo típico:").runs[0].bold = True
        add_styled_table(["Paso", "Acción del Actor", "Respuesta del Sistema"], cu["typical"])
        
        if cu["exceptional"]:
            doc.add_paragraph("Flujo excepcional:").runs[0].bold = True
            add_styled_table(["Paso (Origen)", "Excepción", "Respuesta del Sistema"], cu["exceptional"])

    # --- PERFORMANCE ---
    add_custom_heading("3.3 Requisitos de Rendimiento", level=2)
    perf = {
        "3.3.1 Tiempos de Respuesta": [
            "Páginas principales: carga en menos de 3 segundos con conexión estable.",
            "Búsquedas y filtrados: resultados en menos de 2 segundos.",
            "Exportaciones CSV: generación en menos de 5 segundos."
        ],
        "3.3.2 Capacidad de Usuarios": [
            "El sistema debe soportar al menos 20 usuarios simultáneos. Se espera un uso típico de 1 Administrador, 2-3 Empleados y 10-15 Clientes en horario pico."
        ],
        "3.3.3 Almacenamiento": [
            "SQLite debe manejar al menos 10,000 productos y 50,000 pedidos.",
            "Imágenes y comprobantes: máximo 5 MB por archivo, almacenados en static/."
        ],
        "3.3.4 Sesiones": [
            "Expiración por inactividad: 30 minutos.",
            "Cookies: HttpOnly, SameSite=Lax, Secure en producción."
        ],
        "3.3.5 Errores": [
            "Errores HTTP (404, 403, 500) renderizan páginas amigables.",
            "Errores de base de datos y correo se registran en logs internos."
        ]
    }
    for p_title, p_list in perf.items():
        add_custom_heading(p_title, level=3)
        for item in p_list:
            doc.add_paragraph(item, style='List Bullet')

    # --- DESIGN ---
    add_custom_heading("3.4 Restricciones de Diseño", level=2)
    design = {
        "3.4.1 Restricciones de Arquitectura": [
            "El sistema utiliza el patrón Model-View-Controller (MVC) organizado en Blueprints de Flask.",
            "La capa de persistencia utiliza SQLAlchemy ORM con el motor de base de datos SQLite.",
            "El frontend se construye exclusivamente con HTML5, CSS3, JavaScript y Bootstrap 5, sin frameworks JavaScript adicionales (React, Vue, Angular)."
        ],
        "3.4.2 Restricciones de Lenguaje": [
            "El lenguaje de programación del backend es Python 3.9 o superior.",
            "Las plantillas HTML utilizan el motor Jinja2.",
            "Los estilos se definen en un archivo CSS personalizado (style.css) complementando Bootstrap."
        ],
        "3.4.3 Restricciones de Seguridad": [
            "Las contraseñas se cifran con bcrypt utilizando 12 rounds de salt.",
            "Se implementa protección CSRF en todos los formularios mediante Flask-WTF.",
            "Los decoradores de control de acceso (@admin_required, @employee_required) restringen las funciones por rol.",
            "La validación de entradas se realiza tanto en el cliente (HTML5) como en el servidor (validators.py)."
        ],
        "3.4.4 Restricciones de Despliegue": [
            "El sistema se despliega en Render (plan Starter) como plataforma PaaS.",
            "El dominio se registra en Cloudflare Registrar con DNS y SSL gestionados por Cloudflare.",
            "En desarrollo, el servidor de correo opera en localhost:1025 (sin envío real de emails)."
        ]
    }
    for d_title, d_list in design.items():
        add_custom_heading(d_title, level=3)
        for item in d_list:
            doc.add_paragraph(item, style='List Bullet')

    # --- ATTRIBUTES ---
    add_custom_heading("3.5 Atributos del Sistema", level=2)
    attrs = {
        "3.5.1 Seguridad": [
            "Autenticación: Login con correo y contraseña cifrada con bcrypt.",
            "Autorización: Tres roles (Administrador, Empleado, Cliente) controlados con decoradores.",
            "Protección CSRF en formularios mediante Flask-WTF.",
            "Cookies: HttpOnly, SameSite=Lax, Secure en producción.",
            "Validación de entradas en cliente y servidor.",
            "Auditoría: Logs de cada acción administrativa con usuario, timestamp, IP y valores anteriores/nuevos."
        ],
        "3.5.2 Fiabilidad": [
            "Manejo de excepciones: Operaciones críticas con bloques try-except y mensajes controlados.",
            "Transacciones ORM: Uso de flush y commit para consistencia.",
            "Validación de estados: El flujo de pedidos valida transiciones para evitar inconsistencias.",
            "Integridad referencial: Claves foráneas y restricciones únicas en SQLAlchemy."
        ],
        "3.5.3 Disponibilidad": [
            "Operación continua (24/7) sin interrupciones programadas.",
            "Dependencia del hosting Render (SLA 99.9%).",
            "Modo degradado: En error de base de datos, se muestra la estructura base con mensajes de error."
        ],
        "3.5.4 Mantenibilidad": [
            "Código modular en Blueprints (public, auth, customer, employee, admin).",
            "Separación de capas: Models, Routes, Services, Utils.",
            "Documentación: README.md con instalación, estructura y credenciales por defecto.",
            "Estándares: PEP 8 para Python, indentación consistente."
        ],
        "3.5.5 Portabilidad": [
            "Diseño responsive con Bootstrap 5 (escritorio, tablet, teléfono).",
            "Navegadores compatibles: Chrome, Firefox, Edge y basados en WebKit.",
            "Backend Python multiplataforma (Windows, Linux, macOS).",
            "Requisitos del cliente: Procesador doble núcleo, 1 GB RAM, navegador actualizado."
        ]
    }
    for a_title, a_list in attrs.items():
        add_custom_heading(a_title, level=3)
        for item in a_list:
            doc.add_paragraph(item, style='List Bullet')

    # --- OTHERS ---
    add_custom_heading("3.6 Otros Requisitos", level=2)
    others = {
        "3.6.1 Localización": [
            "Estados del sistema en español mediante filtros Jinja2:",
            "  - status_es: pending_payment → \"Pendiente de pago\", paid → \"Pagado\", etc.",
            "  - role_es: administrator → \"Administrador\", employee → \"Empleado\", customer → \"Cliente\".",
            "  - payment_status_es: pending → \"Pendiente\", verified → \"Verificado\", cancelled → \"Cancelado\"."
        ],
        "3.6.2 Códigos QR": [
            "Se generan para cada pedido que llega a \"listo para recoger\".",
            "Almacenados en static/images/qrcodes/ con el número de orden.",
            "Librería: qrcode con corrección de errores nivel L."
        ],
        "3.6.3 Imágenes": [
            "Almacenadas en static/images/ con nombre basado en ID del producto y UUID.",
            "Formatos soportados: PNG, JPG, JPEG, GIF, WebP.",
            "Imagen principal: is_primary = True en la base de datos."
        ],
        "3.6.4 Exportación": [
            "Formato: CSV (Comma-Separated Values).",
            "Reportes exportables: resumen de ventas, ventas diarias, productos más vendidos, resumen financiero, ventas mensuales, ganancia por producto, desglose por estado."
        ],
        "3.6.5 Correo Electrónico": [
            "Notificaciones enviadas en:",
            "  - Confirmación de pedido al crear un nuevo apartado.",
            "  - Pedido listo al marcar como \"ready_for_pickup\".",
            "  - Pedido entregado al marcar como \"entregado\".",
            "En desarrollo: servidor SMTP local (localhost:1025)."
        ]
    }
    for o_title, o_list in others.items():
        add_custom_heading(o_title, level=3)
        for item in o_list:
            doc.add_paragraph(item)

    # --- APÉNDICES ---
    add_custom_heading("4. Apéndices", level=1)
    
    add_custom_heading("Apéndice A — Glosario Completo", level=2)
    glosario_headers = ["", "Término", "Definición"]
    glosario_rows = [
        ["1", "Apartado", "Reserva de productos por parte de un cliente con un plazo de pago y retiro definido"],
        ["2", "bcrypt", "Algoritmo de hash de contraseñas que utiliza sal para prevenir ataques de fuerza bruta"],
        ["3", "Blueprint", "Módulo de Flask que permite organizar rutas y funciones relacionadas"],
        ["4", "Carrito", "Estructura de datos temporal que almacena los productos seleccionados por un cliente antes de formalizar un apartado"],
        ["5", "Catálogo", "Conjunto de productos disponibles para la venta pública en la plataforma web"],
        ["6", "COCOMO II", "Modelo de estimación de costos de desarrollo de software (Constructive Cost Model II)"],
        ["7", "CRUD", "Operaciones básicas de mantenimiento de datos: Create (Crear), Read (Leer), Update (Actualizar), Delete (Eliminar)"],
        ["8", "CSV", "Formato de archivo de texto plano que utiliza comas para separar valores (Comma-Separated Values)"],
        ["9", "CSRF", "Tipo de ataque web que fuerza a un usuario autenticado a ejecutar acciones no deseadas (Cross-Site Request Forgery)"],
        ["10", "Dashboard", "Panel de control principal que muestra métricas y accesos directos a las funcionalidades del sistema"],
        ["11", "ERS", "Especificación de Requisitos de Software, documento que describe los requisitos de un sistema"],
        ["12", "Flask", "Microframework web ligero para Python, utilizado como base del backend del sistema"],
        ["13", "HTTP-only", "Atributo de cookie que impide su acceso mediante JavaScript, previniendo ataques XSS"],
        ["14", "IEEE 830", "Estándar del Instituto de Ingenieros Eléctricos y Electrónicos para la especificación de requisitos de software"],
        ["15", "Inventario", "Conjunto de productos almacenados en el establecimiento, con control de stock por talla"],
        ["16", "ORM", "Object-Relational Mapping, técnica de mapeo entre objetos Python y tablas de base de datos"],
        ["18", "Movimiento de inventario", "Registro de entrada o salida de mercancía (compra, devolución, pérdida, corrección, venta)"],
        ["19", "PaaS", "Platform as a Service, modelo de computación en la nube donde el proveedor gestiona la infraestructura"],
        ["20", "Pillow", "Librería de Python para el procesamiento de imágenes"],
        ["21", "QR Code", "Código de respuesta rápida que almacena información legible por dispositivos móviles"],
        ["22", "Render", "Proveedor de hosting en la nube (PaaS) utilizado para el despliegue del sistema"],
        ["23", "SQLAlchemy", "ORM para Python que facilita la interacción con bases de datos relacionales"],
        ["24", "SQLite", "Sistema de base de datos relacional ligero, embebido, que no requiere servidor dedicado"],
        ["25", "Stock", "Cantidad disponible de un producto en el inventario, especificada por talla"],
        ["26", "Token", "Elemento de seguridad generado durante la autenticación para validar la sesión del usuario"],
        ["27", "UML", "Unified Modeling Language, lenguaje de modelado unificado para diagramas de software"]
    ]
    add_styled_table(glosario_headers, glosario_rows)

    add_custom_heading("Apéndice B — Tabla Consolidada de Casos de Uso", level=2)
    cu_headers = ["Código", "Caso de Uso", "Actor Principal", "Descripción Breve"]
    cu_rows = [
        ["CU1", "Autenticar usuario", "Administrador", "Inicio de sesión seguro del administrador"],
        ["CU2", "Visualizar dashboard", "Administrador", "Panel de control con métricas y accesos"],
        ["CU3", "Administrar empleados", "Administrador", "CRUD de perfiles de empleados"],
        ["CU4", "Administrar apartados", "Administrador", "Gestión de pedidos y reservas"],
        ["CU5", "Generar reportes", "Administrador", "Informes financieros y de ventas"],
        ["CU6", "Administrar clientes", "Administrador", "Gestión de la base de datos de clientes"],
        ["CU7", "Auditar transacciones", "Administrador", "Revisión de logs de auditoría"],
        ["CU8", "Administrar catálogo", "Administrador", "Gestión global del catálogo de venta"],
        ["CU9", "Registrar producto en catálogo", "Administrador", "Alta de producto en venta pública"],
        ["CU10", "Editar producto en catálogo", "Administrador", "Modificación de datos comerciales"],
        ["CU11", "Eliminar producto del catálogo", "Administrador", "Retiro de producto de venta pública"],
        ["CU12", "Administrar inventario", "Administrador", "Control de stock y movimientos"],
        ["CU13", "Registrar producto", "Administrador", "Alta de producto en inventario interno"],
        ["CU14", "Editar producto", "Administrador", "Modificación de datos de inventario"],
        ["CU15", "Eliminar producto", "Administrador", "Baja de producto del inventario"],
        ["CU16", "Autenticar usuario", "Empleado", "Inicio de sesión seguro del empleado"],
        ["CU17", "Visualizar dashboard", "Empleado", "Panel de control operativo"],
        ["CU18", "Consultar catálogo", "Empleado", "Visualización de productos (solo lectura)"],
        ["CU19", "Registrar venta", "Empleado", "Registro de venta directa en tienda"],
        ["CU20", "Registrar apartado presencial", "Empleado", "Reserva de productos para cliente presencial"],
        ["CU21", "Registrar factura", "Empleado", "Generación de comprobante de venta"],
        ["CU22", "Gestionar clientes", "Empleado", ""] # As requested by cutoff
    ]
    add_styled_table(cu_headers, cu_rows)

    filename = "Especificacion_Requisitos_Software_La_Condesa.docx"
    doc.save(filename)
    return filename

output_file = create_ers_document()
print(f"File created successfully: {output_file}")