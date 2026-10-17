# PROJECT_REVIEW.md — Revisión técnica completa

> Referencia técnica del proyecto **La Condesa Clothing Shop**. Este documento reúne el mapa
> del proyecto, el flujo de datos y **todos los hallazgos de la revisión de código**, para que
> sea posible entender y auditar el proyecto sin abrir archivo por archivo.
>
> Revisión realizada el 17/10/2026 sobre el commit `19e9248` (master).
> Las referencias son `archivo:línea` verificadas contra el código real.

---

## 1. Vista general

Aplicación web Flask para la tienda de ropa "La Condesa": catálogo público, carrito,
checkout con comprobante de pago, y paneles de gestión para empleados y administradores.

| Componente | Tecnología |
|---|---|
| Backend | Python + Flask (Blueprints por rol) |
| Base de datos | SQLite (`instance/la_condesa.db`) vía SQLAlchemy 2.0 |
| ORM / migraciones | Flask-SQLAlchemy 3.x + Flask-Migrate |
| Sesiones / auth | Flask-Login (cookies de sesión firmadas por `SECRET_KEY`) |
| Frontend | Bootstrap 5, Jinja2, JavaScript vanilla |
| Formularios / CSRF | Flask-WTF + CSRFProtect global |
| Email | Flask-Mail (SMTP en `localhost:1025` en desarrollo) |
| QR / imágenes | `qrcode` + Pillow |
| Hash de contraseñas | bcrypt (rounds=12) |

**Roles**: `administrator`, `employee`, `customer` (columna `User.role`, `models/user.py:13`).

> ⚠️ **Nota de entorno**: `requirements.txt` estaba desactualizado (pines de 2023 que no
> instalan en Python 3.14). Fue actualizado junto con los arreglos de despliegue; el entorno
> real usa Python 3.14 + Flask 3.x.

---

## 2. Mapa del proyecto (estructura real)

```
La-Condesa-Clothing-Shop/
├── app.py                  # create_app(): extensiones, blueprints, filtros Jinja, errores
├── config.py               # Config / DevelopmentConfig / ProductionConfig (env vars)
├── extensions.py           # Instancias globales: db, login_manager, migrate, mail, csrf
├── init_db.py              # Init manual: create_all + categorías + admin por defecto
├── requirements.txt        # Dependencias (actualizadas para Python 3.14 / Flask 3)
├── open_server.bat         # Abre la app con `python app.py`
├── .env.example            # Ejemplo de variables de entorno
│
├── models/                 # Modelos SQLAlchemy
│   ├── user.py             # User (roles, bcrypt) y Category
│   ├── product.py          # Product, ProductSize (stock por talla)
│   ├── order.py            # Order + OrderItem (estados y transiciones)
│   ├── movement.py         # InventoryMovement (entradas/salidas de stock)
│   ├── employee.py         # EmployeeProfile (perfil extendido de empleados)
│   └── audit.py            # AuditLog (acciones administrativas)
│
├── routes/                 # Blueprints
│   ├── public.py           # Sin auth: home, catálogo, producto, about, contact
│   ├── auth.py             # login / register / logout
│   ├── customer.py         # dashboard, carrito, checkout, pedidos, subir comprobante
│   ├── employee.py         # dashboard, pedidos (flujo de preparación), ventas
│   └── admin.py            # users, products, orders, inventory, analytics, audit, HR
│
├── services/               # Lógica de negocio
│   ├── order_service.py    # create_order, confirm_payment, mark_as_ready/delivered
│   ├── inventory_service.py# update_stock (check_availability es código muerto)
│   ├── analytics_service.py# Reportes, CSV export
│   ├── email_service.py    # Emails transaccionales (confirmación/listo/entregado)
│   └── audit_service.py    # Registro en AuditLog (commit propio)
│
├── utils/
│   ├── decorators.py       # @admin_required, @employee_required (NO existe customer_required)
│   ├── validators.py       # validate_registration / product / order (parciales)
│   ├── upload.py           # Subida/borrado de imágenes y recibos
│   ├── qr_generator.py     # QR por número de pedido
│   ├── sessions.py         # "Actividad" de sesión (maymente cosmética)
│   └── pagination.py       # Paginación de listados
│
├── templates/              # Jinja2: base, public/, auth/, customer/, employee/,
│                           # admin/, emails/, errors/, includes/
└── static/                 # css/style.css, images/ (productos), receipts/, qrcodes/
```

**Inconsistencias con el README.md original** (sección 8): el README menciona un `run.py`
que no existe, omite `decorators.py`, `pagination.py`, `audit_service.py`, `employee.py`,
`audit.py`, y las carpetas `emails/`, `errors/`, `includes/`, y usa una ruta de proyecto
antigua (`la_condesa`).

---

## 3. Mapa de rutas y control de acceso

### public.py — 5 rutas (sin auth)
| Ruta | Método | Línea |
|---|---|---|
| `/` (home) | GET | public.py:8 |
| `/about` | GET | public.py:17 |
| `/contact` | GET | public.py:22 |
| `/catalog` | GET | public.py:27 |
| `/product/<id>` | GET | public.py:63 |

### auth.py — 3 rutas
| Ruta | Método | Auth | Línea |
|---|---|---|---|
| `/auth/login` | GET/POST | — | auth.py:22 |
| `/auth/register` | GET/POST | — | auth.py:49 |
| `/auth/logout` | **GET** | login_required | auth.py:88 |

> Logout por GET permite logout-CSRF (baja severidad).

### customer.py — 6 rutas (⚠️ solo `@login_required`, sin restricción de rol)
| Ruta | Método | Auth | Línea |
|---|---|---|---|
| `/customer/dashboard` | GET | login_required | customer.py:77-78 |
| `/customer/cart` | GET/POST | login_required | customer.py:84-85 |
| `/customer/checkout` | GET/POST | login_required | customer.py:178-179 |
| `/customer/orders` | GET | login_required | customer.py:226-227 |
| `/customer/orders/<id>` | GET | login_required | customer.py:233-234 |
| `/customer/orders/<id>/upload-receipt` | POST | login_required | customer.py:245-246 |

> No existe `customer_required` (utils/decorators.py solo define admin/employee).
> Un administrador o empleado puede usar el checkout de cliente.

### employee.py — 8 rutas (todas `@login_required` + `@employee_required`) ✅
| Ruta | Método | Línea |
|---|---|---|
| `/employee/dashboard` | GET | employee.py:14-16 |
| `/employee/orders` | GET | employee.py:43-45 |
| `/employee/orders/<id>/confirm-payment` | POST | employee.py:57-59 |
| `/employee/orders/<id>/prepare` | POST | employee.py:86-88 |
| `/employee/orders/<id>/ready` | POST | employee.py:110-112 |
| `/employee/orders/<id>/deliver` | POST | employee.py:135-137 |
| `/employee/sales` | GET | employee.py:160-162 |

### admin.py — 23 rutas (todas `@login_required` + `@admin_required`) ✅
| Ruta | Método | Línea |
|---|---|---|
| `/admin/dashboard` | GET | admin.py:33-35 |
| `/admin/users` | GET / POST | admin.py:53-55 / 62-64 |
| `/admin/users/<id>` (update) | POST | admin.py:101-103 |
| `/admin/users/<id>/delete` | POST | admin.py:126-128 |
| `/admin/products` | GET / POST | admin.py:148-150 / 158-160 |
| `/admin/products/<id>` (update) | POST | admin.py:243-245 |
| `/admin/products/<id>/delete` | POST | admin.py:295-297 |
| `/admin/orders` | GET | admin.py:309-311 |
| `/admin/orders/<id>/confirm-payment` | POST | admin.py:321-323 |
| `/admin/orders/<id>/prepare` | POST | admin.py:346-348 |
| `/admin/orders/<id>/ready` | POST | admin.py:366-368 |
| `/admin/orders/<id>/deliver` | POST | admin.py:387-389 |
| `/admin/inventory` | GET | admin.py:408-410 |
| `/admin/inventory/movements` | POST | admin.py:423-425 |
| `/admin/analytics` | GET | admin.py:464-466 |
| `/admin/analytics/export` | GET | admin.py:480-482 |
| `/admin/employees` | GET | admin.py:502-504 |
| `/admin/employees/<id>/profile` | POST | admin.py:523-524 |
| `/admin/audit-logs` | GET | admin.py:572 |
| `/admin/financial-reports` | GET | admin.py:590 |
| `/admin/financial-reports/export` | GET | admin.py:616 |

**Veredicto de control de acceso**: admin y employee completamente protegidos y con rol.
Customer sin rol. Logout por GET.

---

## 4. Flujo principal de datos

### 4.1 Carrito → pedido

```
1. Cliente agrega al carrito            customer.py:96-135  (carrito en la COOKIE de sesión)
2. Checkout (elige punto de retiro)     customer.py:178    (validate_order: solo pickup_location)
3. order_service.create_order           order_service.py:10-50
     a. Valida solo pickup_location     order_service.py:11-14
     b. Crea Order + OrderItems         (precios tomados de la cookie del cliente)
     c. Calcula total + IVA 16%         order_service.py:37-39
     d. commit()                        order_service.py:41   ← el pedido YA quedó guardado
     e. send_order_confirmation()       order_service.py:43   ← si falla → 500 (bug, ver §5.1)
4. Éxito → se limpia el carrito         customer.py:218
```

### 4.2 Ciclo de vida del pedido

```
pending_payment ──(sube comprobante)──► pago verificado por empleado/admin
      │                                 confirm_payment → status 'paid'   order_service.py:64-81
      ▼
   'paid' ──prepare──► 'preparing' ──ready──► 'ready_for_pickup' (genera QR) ──deliver──► 'delivered'
                                                                        mark_as_delivered:
                                                                        descuenta stock  order_service.py:104-130
```

El stock **solo se descuenta al entregar**, con `max(0, stock - qty)` que oculta oversells
silenciosamente (ver §5.2). El estado `cancelled` existe en `valid_transitions`
(models/order.py:58-63) pero **no** en `Order.STATUSES` (models/order.py:8), por lo que la
cancelación siempre falla (ver §5.9).

### 4.3 Emails, QR y recibos

- **Emails** (Flask-Mail): confirmación al crear pedido, "listo para recoger" al marcar
  listo, "entregado" (código muerto — nunca se llama). Envío en `email_service.py:18-34`.
- **QR**: se genera al marcar "listo" (`qr_generator.py`, nombre de archivo con timestamp
  en segundos → colisión si dos pedidos se marcan en el mismo segundo). Se sirve desde
  `static/images/qrcodes/` (ignorado en git, pero **público sin auth**).
- **Recibos de pago**: el cliente sube un comprobante (`utils/upload.py:19`) a
  `static/receipts/` con nombre `receipt_<order_id>_<8hex>.png` — servidos **sin
  autenticación** y enumerables (ver §5.3).

### 4.4 Sesiones

- Cookie de sesión firmada por `SECRET_KEY`; carrito completo (con precios) vive ahí.
- `utils/sessions.py` escribe `last_activity/ip/user_agent` pero nada los valida;
  `cleanup_expired_sessions` nunca se llama.
- Expiración: 30 min (`config.py:12`).

---

## 5. Hallazgos

### 🔴 Críticos

#### 5.1 El email roto revienta el checkout (bug confirmado en producción del proyecto)
- `services/email_service.py:81` crea el singleton `email_service = EmailService()` **sin app**;
  `init_app` (línea 15) **no se llama en ninguna parte** del código.
- Cuando el SMTP (`localhost:1025`) no está disponible, la excepción entra al `except` y evalúa
  `self.app` (email_service.py:29) → `AttributeError` → HTTP 500. El traceback exacto está
  commiteado en `errors.txt`.
- **Impacto**: el pedido ya hizo `commit()` (order_service.py:41) antes del email, así que el
  cliente ve un 500 pero el pedido existe y el carrito **no se limpia** (customer.py:218
  inalcanzable) → al reintentar se crean **pedidos duplicados**. Mismo patrón en
  `mark_as_ready` (order_service.py:96): el estado y QR ya se guardaron, el 500 hace que
  parezca fallo y el reintento choque con la validación de transición.
- **Arreglo aplicado**: `email_service.init_app(app)` en `create_app()`, uso de
  `current_app` con guardia de contexto, y try/except en `order_service` para que un fallo
  de email **nunca** interrumpa el flujo del pedido.

#### 5.2 Inventario: sin validación de stock al pedir, oversell silencioso
- `create_order` nunca verifica disponibilidad. `inventory_service.check_availability`
  (inventory_service.py:56) existe pero **nunca se llama** (código muerto).
- El stock solo baja al entregar, con `max(0, ...)` (order_service.py:127) que enmascara
  cualquier oversell; el movimiento de inventario registra la cantidad pedida, no el cambio real.
- Cantidades y precios no se validan en el servidor: `validators.validate_order`
  (validators.py:76-87) solo revisa `pickup_location`/`payment_reference`.
  `customer.py:96,99,142` hace `int()` sin límites → cantidad negativa pasa el check
  (`stock < -5` es falso) y produce totales negativos (order_service.py:35-39).
- Actualizaciones de stock son read-modify-write sin lock (inventory_service.py:18-22,
  order_service.py:124-127) → pérdidas de update con concurrencia.

#### 5.3 Recibos de pago públicos (y dos commiteados al repo)
- Los recibos se escriben en `static/receipts/` (upload.py:19) y Flask los sirve sin auth.
- `static/receipts/receipt_1_e44221ec.png` y `receipt_3.jpg` estaban **trackeados en git**
  → quitar del índice e ignorar la carpeta (ver Paso 5 del plan de despliegue).
- Nombre predecible (`receipt_<order_id>_<8 hex>`) → enumerables.

#### 5.4 Precios confiados en la cookie del cliente
- El carrito con `unit_price` vive en la cookie de sesión firmada; `create_order` confía en
  `item['unit_price']` (order_service.py:32) sin releer precios de la BD.
- Con la `SECRET_KEY` por defecto `'dev-secret-key-change-in-production'` (config.py:5,
  commiteada) cualquiera puede firmar cookies falsas → manipulación de precios.
  En producción Render usa env var `SECRET_KEY` (mitad del problema); falta el re-lectura
  de precios en servidor (mejora futura recomendada).

### 🟡 Medianos

#### 5.5 `admin.update_user` sin validación (admin.py:101-123)
- No usa `validate_registration` ni chequea email duplicado → `IntegrityError` = 500
  (`User.email` es unique, user.py:13).
- `role = request.form.get('role', ...)` (admin.py:112) salta el whitelist que solo existe
  en `User.__init__` (user.py:22-25) → cualquier string de rol queda persistido.

#### 5.6 Rutas de customer sin restricción de rol
- Solo `@login_required` (ver §3). No existe `customer_required` en utils/decorators.py.

#### 5.7 Conversiones `int()`/`float()` sin manejo → 500
- `customer.py:96,99,142`; `admin.py:194,204,255-261,430`. Entrada no numérica = excepción.

#### 5.8 `utils/upload.py` débil
- `secure_filename` importado y no usado (upload.py:3); solo se valida extensión (upload.py:8-10).
- `delete_image` (upload.py:46-56) une un path controlado por la BD al filesystem sin
  normalización → path traversal si `image_path` se manipula.
- `config.ALLOWED_EXTENSIONS` (config.py:24, sin webp) nunca se usa e inconsistente con upload.py:6.

#### 5.9 `cancelled` inalcanzable (models/order.py:8 vs 58-63)
- `Order.STATUSES` omite `'cancelled'` pero `valid_transitions` lo incluye →
  `update_status('cancelled')` siempre retorna False. Los pedidos no se pueden cancelar.

#### 5.10 Borrados con huérfanos
- `admin.delete_user` (126-144) y `delete_product` (295-306): `Order.user_id` y
  `OrderItem.product_id` no tienen cascade y SQLite no enforcea FKs → pedidos/items
  huérfanos; las plantillas luego renderizan vacío (`order.customer.name` en orders.html:49).

#### 5.11 Sesiones: login no rota la sesión
- `auth.login` no limpia la sesión al autenticar (fijación de sesión); combinado con la
  SECRET_KEY default es más grave. `SESSION_COOKIE_SECURE = False` en dev (config.py:10),
  True en producción (config.py:42).

#### 5.12 QR: colisión por timestamp de segundo (qr_generator.py:11-12) y sin manejo de
error en `mark_as_ready` (order_service.py:91) → 500 si falla qrcode/Pillow.

### 🟢 Bajos / deuda técnica

- **APIs legadas**: `User.query.get()` (~18 sitios: app.py:39, customer.py:35,101,146,
  admin.py:325,350,370,391,454, employee.py:61,90,114,139, order_service.py:53,65,84,105)
  → usar `db.session.get(User, id)`. `datetime.utcnow()` deprecado (16+ sitios en models/,
  services/, utils/, routes/).
- **bcrypt truncación**: sin longitud máxima en `validators.py:16-24`; bcrypt corta a
  72 bytes. `set_password` ignora `BCRYPT_LOG_ROUNDS` (hardcodea 12, user.py:28).
- **`audit_service.log` hace su propio commit** (audit_service.py:28) → el log puede
  confirmarse aunque la acción descrita no (o viceversa).
- **CSV injection** en `analytics_service.export_to_csv` (241-253): nombres de producto sin
  escapar → fórmulas al abrir en Excel. `export_type` de query param va a `Content-Disposition`
  sin sanitizar (admin.py:496,639).
- **Producto inactivo visible**: `public.product_detail` usa `get_or_404` sin filtrar
  `is_active` (public.py:65); el catálogo sí filtra.
- **`Order.discount`** siempre 0 (nunca se setea); `InventoryMovement.TYPES` no se valida
  (admin.py:444 infiere signo del tipo → typo cambia el signo del movimiento); sin CHECK
  `stock >= 0`.
- **Código muerto**: `inventory_service.check_availability`, `sessions.cleanup_expired_sessions`,
  `upload.get_image_url`, `customer.get_cart_item_count`, `Order.can_be_delivered/is_overdue/
  calculate_totals`, `EmailService.send_order_delivered`, `audit_service.get_logs*`,
  `config.ALLOWED_EXTENSIONS`.
- `static/js/` existe pero está vacía.
- `User.is_active` (columna) sombrea `UserMixin.is_active` (funciona, confuso).

---

## 6. Verificado como correcto ✅

- **CSRF**: `CSRFProtect` global (app.py:20); todos los `<form>` POST llevan `csrf_token`
  (24 formularios verificados); los `fetch` de JS envían `X-CSRFToken` desde el meta de
  base.html:6 (customer/cart.html:74-140, product_detail.html).
- **Contraseñas**: solo hashes bcrypt; jamás en texto plano.
- **SQL injection**: no hay SQL crudo (`text()`/`execute()` inexistentes) — todo ORM.
- **XSS**: autoescape activo; los cuatro `|safe` son `|tojson|safe` sobre datos controlados
  (admin/users.html:134, products.html:161, inventory.html:126, employees.html:95) — seguro.
- **Rutas admin/employee**: 100% con `@login_required` + decorador de rol
  (`utils/decorators.py:5-19`).

---

## 7. Tests y dependencias (estado previo a la reparación)

- `test_routes.py:2` hacía `os.chdir('...\la_condesa')` — directorio inexistente → error de
  colección de pytest. `test_full.py` no es coleccionable (script de ejecución lineal con
  parámetros tipo fixture) y apunta a una ruta inexistente `/employee/orders/1/mark-paid`
  (la real es `confirm-payment`).
- `pytest-flask` 1.2.0 no es compatible con Flask 3 (importa `_request_ctx_stack`, eliminado).
- Flask-WTF 1.1.1 instalado importaba `flask.Markup` (eliminado en Flask 3) → la app **no
  arrancaba** en el entorno local. Solucionado actualizando a Flask-WTF ≥1.2.1.

---

## 8. Despliegue (Render + GitHub)

La app está preparada para desplegarse desde este repo:

- `requirements.txt` con versiones compatibles + `gunicorn`.
- Init automático de BD al arrancar si no existe (esquema + categorías + admin), porque el
  disco SQLite del plano gratis de Render es efímero.
- Arranque: `gunicorn app:app` (`app.py` expone `app` a nivel de módulo).
- Variables de entorno obligatorias en Render: `SECRET_KEY`, `FLASK_ENV=production`.

Ver `README.md` § Despliegue para los pasos del dashboard.

**Limitación conocida**: en el plano gratis la base de datos se borra al reiniciar o
redeployar. Adecuado para demo; para persistencia usar Postgres free o disco de Render.

---

## 9. Mejoras futuras recomendadas (prioridad)

1. **Releer precios de la BD en `create_order`** — cerrar del todo la manipulación de precios (§5.4).
2. **Validar stock + cantidades al momento de crear el pedido**, con reserva o descuento
   inmediato (§5.2).
3. `customer_required` + rotación de sesión en login (§5.6, §5.11).
4. Validar en `admin.update_user` y manejar `int()` en todas las rutas (§5.5, §5.7).
5. Mover recibos fuera de `static/` detrás de una ruta autenticada (§5.3).
6. Completar `Order.STATUSES` con `cancelled` (§5.9) y cascadas en borrados (§5.10).
7. Modernizar APIs legadas (`db.session.get`, `datetime.now(timezone.utc)`) (§6 deuda).
8. Reparar o eliminar los tests rotos (§7).
