# La Condesa - Tienda de Ropa

Aplicación web completa para la tienda de ropa "La Condesa" con catálogo público, carrito,
checkout con comprobante de pago y paneles de gestión para empleados y administradores.

## Características

- **Autenticación por roles**: administrador, empleado y cliente.
- **Catálogo y carrito**: filtros por categoría, talla y precio; carrito en sesión.
- **Pedidos**: checkout, comprobante de pago, confirmación, preparación, entrega y cancelación.
- **Inventario**: stock por talla, movimientos de entrada/salida y alertas de bajo stock.
- **Administración**: usuarios, productos, pedidos, inventario, perfiles de empleados y auditoría.
- **Reportes**: ventas, rentabilidad por producto y exportación CSV.
- **QR y comprobantes**: QR por pedido y comprobantes servidos solo a usuarios autorizados.

## Tecnologías

- **Backend**: Python 3.11+ (probado en 3.14) con Flask 3.x
- **Base de datos**: SQLite vía SQLAlchemy 2.0 / Flask-SQLAlchemy 3.x
- **Frontend**: Bootstrap 5, Jinja2, JavaScript vanilla
- **Autenticación**: Flask-Login + bcrypt
- **Formularios**: Flask-WTF con CSRF global
- **Email**: Flask-Mail
- **QR e imágenes**: qrcode + Pillow
- **Pruebas**: pytest

## Instalación

### Requisitos previos

- Python 3.11 o superior
- pip

### Pasos

1. **Clonar el repositorio**

   ```bash
   git clone https://github.com/yuikai789/La-Condesa-Clothing-Shop.git
   cd La-Condesa-Clothing-Shop
   ```

2. **Instalar dependencias**

   ```bash
   python -m pip install -r requirements.txt
   ```

3. **Configurar variables de entorno (opcional en desarrollo)**

   Copia `.env.example` a `.env` y ajusta los valores. En desarrollo se usa SQLite y un
   servidor de correo local en `localhost:1025`.

4. **Inicializar la base de datos**

   ```bash
   python init_db.py
   ```

   Esto crea las tablas, las categorías por defecto y la cuenta administradora.

5. **Ejecutar la aplicación**

   ```bash
   python app.py
   ```

   También puedes usar:

   ```bash
   flask --app app run
   ```

6. **Acceder**

   - Home: http://localhost:5000
   - Admin: http://localhost:5000/admin/dashboard
   - Empleado: http://localhost:5000/employee/dashboard
   - Cliente: http://localhost:5000/customer/dashboard

## Credenciales de administrador

Por defecto se crea:

- **Email**: `admin@lacondesa.com`
- **Password**: `Admin123!`

En producción define `ADMIN_EMAIL` y `ADMIN_PASSWORD` para evitar credenciales por defecto.

## Estructura del proyecto

```
La-Condesa-Clothing-Shop/
├── app.py                  # Fábrica de la aplicación Flask
├── config.py               # Configuración por entorno
├── extensions.py           # db, login_manager, migrate, mail, csrf
├── init_db.py              # Creación de tablas y datos iniciales
├── requirements.txt
├── models/                 # User, Product, Order, InventoryMovement, AuditLog, EmployeeProfile
├── routes/                 # public, auth, customer, employee, admin, order_actions
├── services/               # order, inventory, analytics, email, audit
├── utils/                  # decoradores, validadores, upload, QR, sesiones, fechas, paginación
├── templates/              # public, auth, customer, employee, admin, emails, errors, includes
├── static/                 # CSS, imágenes de productos, QR
├── tests/                  # Suite de pruebas de modelos, servicios, utilidades y rutas
└── instance/               # Base SQLite y comprobantes privados (no versionados)
```

## Configuración de email

Variables de entorno principales:

```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=tu-email@gmail.com
MAIL_PASSWORD=tu-password-de-app
MAIL_DEFAULT_SENDER=tu-email@gmail.com
```

Si el envío falla, el flujo del pedido continúa y el error se registra en `errors.txt`.

## Pruebas

```bash
python -m pytest tests
```

Para cobertura:

```bash
coverage run -m pytest tests
coverage report
```

## Producción

Variables obligatorias en el proveedor de hosting (por ejemplo Render):

- `SECRET_KEY` con un valor seguro.
- `FLASK_ENV=production`.
- Opcionalmente `DATABASE_URL`, `ADMIN_EMAIL` y `ADMIN_PASSWORD`.

Notas:

- En producción la aplicación exige que `SECRET_KEY` no sea el valor de desarrollo.
- Los comprobantes de pago se guardan en `instance/receipts/` y se sirven mediante una ruta
  autenticada, no como archivos estáticos públicos.
- En el plan gratuito de Render el disco SQLite es efímero: la base se recrea al reiniciar.
  Para persistencia usa PostgreSQL o un disco persistente.

## Licencia

Este proyecto es de código cerrado y propiedad de La Condesa.
