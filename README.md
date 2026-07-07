# La Condesa - Tienda de Ropa

Aplicación web completa para la tienda de ropa "La Condesa" con gestión de inventario, ventas, y e-commerce.

## Características

- **Sistema de Autenticación**: Tres roles de usuario (Administrador, Empleado, Cliente)
- **Catálogo de Productos**: browsing con filtros por categoría, talla y precio
- **Carrito de Compras**: Gestión completa de productos en el carrito
- **Gestión de Ventas**: Registro y seguimiento de pedidos
- **Panel de Administración**: Gestión completa de usuarios, productos e inventario
- **Reportes y Analytics**: Ventas diarias, productos más vendidos, stock bajo

## Tecnologías

- **Backend**: Python 3.9+ con Flask 2.3
- **Base de Datos**: SQLite 3.35+
- **ORM**: SQLAlchemy 2.0
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Autenticación**: Flask-Login
- **Migraciones**: Flask-Migrate
- **Email**: Flask-Mail
- **QR Codes**: qrcode
- **Imágenes**: Pillow

## Instalación

### Requisitos Previos

- Python 3.9 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar o descargar el proyecto**
   ```bash
   cd "c:\Users\Yuikai\Documents\Proyecto IV\la_condesa"
   ```

2. **Instalar dependencias**
   ```bash
   python -m pip install -r requirements.txt
   ```

3. **Inicializar la base de datos**
   ```bash
   python init_db.py
   ```
   
   Esto creará:
   - La base de datos SQLite `la_condesa.db`
   - 5 categorías por defecto (Mujeres, Hombres, Niños, Accesorios, Especiales)
   - Una cuenta de administrador

4. **Ejecutar la aplicación**
   ```bash
   flask run
   ```
   O directamente:
   ```bash
   python app.py
   ```

5. **Acceder a la aplicación**
   - **Homepage**: http://localhost:5000
   - **Admin**: http://localhost:5000/admin/dashboard
   - **Empleado**: http://localhost:5000/employee/dashboard
   - **Cliente**: http://localhost:5000/customer/dashboard

## Credenciales de Administrador

Por defecto, se crea la siguiente cuenta administrativa:

- **Email**: admin@lacondesa.com
- **Password**: Admin123!

⚠️ **Importante**: Cambia estas credenciales en producción.

## Estructura del Proyecto

```
la_condesa/
├── app.py                    # Aplicación Flask principal
├── config.py                 # Configuración del aplicación
├── requirements.txt          # Dependencias de Python
├── init_db.py               # Inicialización de base de datos
├── run.py                   # Script de inicio
│
├── models/                  # Modelos de base de datos
│   ├── __init__.py
│   ├── user.py             # Usuario y roles
│   ├── product.py          # Productos y categorías
│   ├── order.py            # Pedidos y items
│   └── movement.py         # Movimientos de inventario
│
├── routes/                  # Rutas y controladores
│   ├── __init__.py
│   ├── public.py           # Páginas públicas
│   ├── auth.py             # Autenticación
│   ├── customer.py         # Funcionalidades cliente
│   ├── employee.py         # Funcionalidades empleado
│   └── admin.py            # Funcionalidades admin
│
├── services/                # Lógica de negocio
│   ├── __init__.py
│   ├── email_service.py    # Envío de emails
│   ├── order_service.py    # Gestión de pedidos
│   ├── inventory_service.py # Gestión de inventario
│   └── analytics_service.py # Analytics y reportes
│
├── utils/                   # Utilidades
│   ├── __init__.py
│   ├── sessions.py         # Gestión de sesiones
│   ├── validators.py       # Validación de formularios
│   ├── upload.py           # Subida de imágenes
│   └── qr_generator.py     # Generación de QR
│
├── static/                  # Archivos estáticos
│   ├── css/
│   │   └── style.css       # Estilos personalizados
│   ├── images/             # Imágenes de productos
│   └── js/                 # JavaScript
│
└── templates/               # Plantillas HTML
    ├── base.html           # Plantilla base
    ├── public/             # Páginas públicas
    ├── auth/               # Páginas de autenticación
    ├── customer/           # Panel cliente
    ├── employee/           # Panel empleado
    └── admin/              # Panel administrador
```

## Configuración de Email

Para envío de emails en producción, configura las variables de entorno:

```bash
set MAIL_SERVER=smtp.gmail.com
set MAIL_PORT=587
set MAIL_USE_TLS=true
set MAIL_USERNAME=tu-email@gmail.com
set MAIL_PASSWORD=tu-password-de-app
set MAIL_DEFAULT_SENDER=tu-email@gmail.com
```

Para desarrollo, se usa un servidor de correo simulado en `localhost:1025`.

## Desarrollo

### Ejecutar tests
```bash
python -m pytest
```

### Ver cobertura
```bash
coverage run -m pytest
coverage report
```

## Producción

1. Usa `ProductionConfig` en lugar de `DevelopmentConfig`
2. Configura variables de entorno para producción
3. Ejecuta: `flask run --host=0.0.0.0 --port=80`

## Licencia

Este proyecto es de código cerrado y propiedad de La Condesa.
