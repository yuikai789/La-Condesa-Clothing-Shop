# La Condesa - Tienda de Ropa

Aplicación web completa para la tienda de ropa "La Condesa" con catálogo público, carrito,
checkout con comprobante de pago y paneles de gestión para empleados y administradores.

## Características

- **Autenticación por roles**: administrador, empleado y cliente.
- **Verificación de correo y recuperación de contraseña** con tokens firmados y caducidad.
- **Rate limiting** en login, registro y recuperación de contraseña.
- **Catálogo y carrito**: filtros por categoría, talla y precio; carrito en sesión con TTL.
- **Pedidos**: checkout, comprobante de pago, confirmación, preparación, entrega y cancelación.
- **Inventario sin sobreventa**: reserva atómica de stock por talla al crear el pedido.
- **Inventario**: stock por talla, movimientos de entrada/salida y alertas de bajo stock.
- **Administración**: usuarios, productos, pedidos, inventario, perfiles de empleados y auditoría.
- **Reportes**: ventas, rentabilidad por producto y exportación CSV.
- **QR y comprobantes**: QR por pedido y comprobantes servidos solo a usuarios autorizados.

## Tecnologías

- **Backend**: Python 3.11+ (probado en 3.14) con Flask 3.x
- **Base de datos**: SQLite en desarrollo y PostgreSQL en producción (SQLAlchemy 2.0 / Flask-SQLAlchemy 3.x)
- **Frontend**: Bootstrap 5, Jinja2, JavaScript vanilla
- **Autenticación**: Flask-Login + bcrypt, tokens itsdangerous
- **Formularios**: Flask-WTF con CSRF global
- **Email**: Flask-Mail
- **Rate limiting**: Flask-Limiter
- **Almacenamiento de recibos**: local o S3-compatible (boto3)
- **QR e imágenes**: qrcode + Pillow
- **Pruebas**: pytest + coverage, con CI en GitHub Actions

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
├── extensions.py           # db, login_manager, migrate, mail, csrf, limiter
├── init_db.py              # Creación de tablas y datos iniciales
├── requirements.txt
├── models/                 # User, Product, Order, InventoryMovement, AuditLog, EmployeeProfile
├── routes/                 # public, auth, customer, employee, admin, order_actions
├── services/               # order, inventory, analytics, email, audit
├── utils/                  # decoradores, validadores, upload, storage, tokens, QR, sesiones, fechas
├── .github/workflows/      # CI: tests + cobertura mínima
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

Para cobertura (el umbral mínimo configurado es 85%, también validado en CI):

```bash
coverage run -m pytest tests
coverage report
```

## Configuración fiscal, carrito y seguridad

Variables principales (ver `.env.example` para la lista completa):

```bash
TAX_RATE=0.16                 # IVA configurable (Decimal)
CART_TTL_MINUTES=60           # vigencia del carrito en sesión
REQUIRE_EMAIL_VERIFICATION=false
EMAIL_VERIFICATION_MAX_AGE=86400
PASSWORD_RESET_MAX_AGE=3600
RATELIMIT_ENABLED=true
RATELIMIT_DEFAULT=200 per hour
RATELIMIT_STORAGE_URI=memory://
```

En producción se recomienda `REQUIRE_EMAIL_VERIFICATION=true`, un backend de rate limiting
compartido (por ejemplo Redis) y `SESSION_COOKIE_SECURE=true`.

## Producción

Variables obligatorias en el proveedor de hosting (por ejemplo Render):

- `SECRET_KEY` con un valor seguro.
- `FLASK_ENV=production`.
- `DATABASE_URL` apuntando a PostgreSQL gestionado.
- `ADMIN_EMAIL` y `ADMIN_PASSWORD`.
- `STORAGE_BACKEND=s3` y las variables `S3_*` para persistir los comprobantes en almacenamiento
  externo (S3, R2, MinIO, etc.).

Notas:

- En producción la aplicación exige que `SECRET_KEY` no sea el valor de desarrollo.
- Los comprobantes de pago se guardan en `instance/receipts/` (modo local) o en el bucket S3,
  y se sirven mediante una ruta autenticada, no como archivos estáticos públicos.
- En el plan gratuito de Render el disco SQLite es efímero: sin `DATABASE_URL` de PostgreSQL y
  `STORAGE_BACKEND=s3`, la base y los comprobantes se pierden en cada reinicio.
- La auditoría se escribe en una transacción independiente para no interferir con las operaciones
  de negocio. A esta escala el registro vive en la misma base de datos, por lo que un operador con
  acceso SQL directo podría alterarlo: no se considera evidencia inmutable.

## Licencia

Este proyecto es de código cerrado y propiedad de La Condesa.
