 Especificación de Requisitos de Software (ERS)

 Sistema Web de Gestión Comercial y Control de Inventario — La Condesa

 1. Introducción

 1.1 Propósito

Este documento especifica los requisitos de software de la plataforma web "La Condesa", diseñada para la gestión de procesos administrativos, comerciales y de control de inventario del establecimiento ubicado en la Avenida Miranda de Maturín, Monagas.

Las especificaciones están dirigidas a los desarrolladores del sistema, los directivos del negocio y los asesores académicos del Proyecto Socio-Tecnológico.

El documento sigue las directrices del estándar IEEE Std. 830-1998.

 1.2 Ambito del Sistema

Nombre: La Condesa — Plataforma Web de Gestión Comercial

El sistema es una aplicación web con arquitectura responsive que digitaliza los procesos de facturación, control de inventario y ventas en línea del establecimiento.

Lo que el sistema hará:

- Gestión de usuarios con tres roles (Administrador, Empleado, Cliente).
- Catálogo público de productos con filtros por categoría, talla y precio.
- Carrito de compras y proceso de apartado en línea.
- Control de inventario con registro de movimientos.
- Reportes financieros y de ventas con exportación a CSV.
- Envío de correos de notificación y generación de códigos QR.

Lo que NO hará:

- No gestionará envíos a domicilio (el modelo es retiro en tienda).
- No integrará pasarelas de pago en línea.
- No será una aplicación móvil nativa.

 1.3 Definiciones

| Término | Definición |
|---------|------------|
| ERS | Especificación de Requisitos de Software |
| IEEE | Institute of Electrical and Electronics Engineers |
| CRUD | Create, Read, Update, Delete |
| ORM | Object-Relational Mapping |
| Flask | Microframework web para Python |
| SQLAlchemy | ORM para Python |
| SQLite | Base de datos relacional ligera |
| Bootstrap | Framework de diseño web |
| PST | Proyecto Socio-Tecnológico |
| COCOMO | Constructive Cost Model |
| ROI | Return on Investment |

 1.4 Referencias

| ID | Documento |
|----|-----------|
| [R1] | IEEE Std. 830-1998 |
| [R2] | PST IV Informe del Proyecto |
| [R3] | Documentación de Flask (flask.palletsprojects.com) |
| [R4] | Documentación de SQLAlchemy (docs.sqlalchemy.org) |

 2. Descripción General

 2.1 Perspectiva del Producto

El sistema es una aplicación web independiente, desplegada en Render (PaaS) con dominio en Cloudflare. Su arquitectura se compone de:

- Capa de presentación: HTML5, CSS3, JavaScript, Bootstrap 5
- Capa de aplicación: Python 3.9+, Flask 2.3, Blueprints
- Capa de datos: SQLAlchemy 2.0, SQLite

Los clientes acceden al catálogo público y realizan apartados en línea, mientras que el personal interno gestiona las operaciones desde el panel de administración.

 2.2 Funciones del Producto

- Autenticación y gestión de usuarios con tres roles.
- Catálogo de productos con búsqueda, filtros y carrito de compras.
- Gestión de inventario con registro de movimientos.
- Administración de pedidos con flujo de estados.
- Reportes y dashboard con métricas.
- Sistema de auditoría de acciones.

 2.3 Características de los Usuarios

| Rol | Descripción | Experiencia técnica |
|-----|-------------|---------------------|
| Administrador | Gerente o propietario del negocio | Uso básico de computadora y navegadores |
| Empleado | Personal que atiende en tienda | Uso básico de aplicaciones web |
| Cliente | Usuarios que compran en línea | Navegación web estándar |

 2.4 Restricciones

- Tecnológicas: Python 3.9+, Flask, SQLite, Bootstrap 5, hosting en Render.
- Seguridad: Contraseñas cifradas con bcrypt, tokens CSRF, sesiones con expiración.
- Organizacionales: Uso exclusivo del establecimiento, sin integración con sistemas externos.

 2.5 Suposiciones

- El establecimiento contará con conexión a internet estable.
- Los clientes contarán con navegadores web actualizados.
- El personal recibirá capacitación básica para el uso del sistema.

 3. Requisitos Específicos

 3.1 Interfaces Externas

 3.1.1 Interfaz de Usuario

El sistema se presenta como una aplicación web responsive accesible desde cualquier navegador.

Páginas públicas:

| Página | URL | Descripción |
|--------|-----|-------------|
| Principal | `/` | Productos destacados y categorías |
| Catálogo | `/catalog` | Listado con filtros |
| Detalle de Producto | `/product/<id>` | Ficha completa del producto |
| Contacto | `/contact` | Formulario de contacto |

Paneles de usuario (requieren autenticación):

| Panel | URL | Rol |
|-------|-----|-----|
| Dashboard Admin | `/admin/dashboard` | Administrador |
| Gestión de Usuarios | `/admin/users` | Administrador |
| Gestión de Productos | `/admin/products` | Administrador |
| Gestión de Pedidos | `/admin/orders` | Administrador |
| Inventario | `/admin/inventory` | Administrador |
| Dashboard Empleado | `/employee/dashboard` | Empleado |
| Pedidos Empleado | `/employee/orders` | Empleado |
| Dashboard Cliente | `/customer/dashboard` | Cliente |
| Carrito | `/customer/cart` | Cliente |
| Mis Pedidos | `/customer/orders` | Cliente |

 3.1.2 Interfaces de Software

| Componente | Versión | Propósito |
|------------|---------|-----------|
| Python | 3.9+ | Backend |
| Flask | 2.3 | Microframework web |
| SQLAlchemy | 2.0 | ORM |
| SQLite | 3.35+ | Base de datos |
| Bootstrap | 5.x | Frontend |
| Jinja2 | 3.1 | Plantillas |

 3.2 Funciones

Los requisitos se organizan por tipo de usuario.

 3.2.1 Funciones del Administrador


 CU1 — Autenticar Usuario

| Campo | Descripción |
|-------|-------------|
| ID | CU1 |
| Nombre | Autenticar usuario |
| Actores | Administrador |
| Descripción | Permite al Administrador ingresar al sistema validando sus credenciales. |
| Precondición | El Administrador debe estar registrado en el sistema. |
| Postcondición | Se inicia la sesión y se redirige al Dashboard. |

Flujo típico:

| Paso | Acción del Actor | Respuesta del Sistema |
|------|------------------|-----------------------|
| 1 | Accede al formulario de login. | Muestra los campos de credenciales. |
| 2 | Ingresa correo y contraseña. | — |
| 3 | Hace clic en "Iniciar Sesión". | Valida credenciales, verifica el rol y redirige al Dashboard. |

Flujo excepcional:

| Excepción | Respuesta |
|-----------|-----------|
| Campos vacíos | "Por favor, complete todos los campos." |
| Credenciales incorrectas | "Correo o contraseña incorrectos." |


 CU2 — Visualizar Dashboard

| Campo | Descripción |
|-------|-------------|
| ID | CU2 |
| Nombre | Visualizar dashboard |
| Actores | Administrador |
| Descripción | Muestra un panel con métricas del negocio (ventas, pedidos, usuarios). |
| Precondición | Sesión activa del Administrador. |
| Postcondición | Se despliegan las métricas actualizadas. |

Flujo típico:

| Paso | Acción del Actor | Respuesta del Sistema |
|------|------------------|-----------------------|
| 1 | Accede al dashboard tras login. | Consulta la base de datos y muestra métricas. |
| 2 | Visualiza la información. | — |

Flujo excepcional:

| Excepción | Respuesta |
|-----------|-----------|
| Sesión expirada | Redirige al login |


 CU3 — Administrar Empleados

| Campo | Descripción |
|-------|-------------|
| ID | CU3 |
| Nombre | Administrar empleados |
| Actores | Administrador |
| Descripción | CRUD de perfiles de empleados (registrar, editar, eliminar). |
| Precondición | Sesión activa del Administrador. |
| Postcondición | Los cambios se guardan en la base de datos. |

Flujo típico:

| Paso | Acción del Actor | Respuesta del Sistema |
|------|------------------|-----------------------|
| 1 | Selecciona "Administrar empleados". | Muestra la lista de empleados. |
| 2 | Registra un nuevo empleado con nombre, correo, contraseña y cargo. | Valida los datos y almacena el registro. |
| 3 | — | Muestra "Usuario creado exitosamente". |

Flujo excepcional:

| Excepción | Respuesta |
|-----------|-----------|
| Correo ya registrado | "El correo ya está registrado." |
| Campos vacíos | "Complete todos los campos obligatorios." |


 CU4 — Administrar Pedidos

| Campo | Descripción |
|-------|-------------|
| ID | CU4 |
| Nombre | Administrar pedidos |
| Actores | Administrador |
| Descripción | Supervisa y actualiza el estado de los pedidos (pendiente → pagado → preparando → listo → entregado). |
| Precondición | Sesión activa del Administrador. |
| Postcondición | El estado del pedido se actualiza y, al marcar como entregado, se descuenta el inventario. |

Flujo típico:

| Paso | Acción del Actor | Respuesta del Sistema |
|------|------------------|-----------------------|
| 1 | Accede a "Administrar pedidos". | Muestra la lista de pedidos. |
| 2 | Selecciona un pedido pendiente. | Muestra el detalle con artículos y monto. |
| 3 | Cambia el estado (ej. "Pagado"). | Actualiza el registro y muestra confirmación. |

Flujo excepcional:

| Excepción | Respuesta |
|-----------|-----------|
| Comprobante no subido | "El cliente aún no ha subido su comprobante." |
| Transición inválida | "Transición de estado inválida." |


 CU5 — Generar Reportes

| Campo | Descripción |
|-------|-------------|
| ID | CU5 |
| Nombre | Generar reportes |
| Actores | Administrador |
| Descripción | Genera informes de ventas, inventario y finanzas con opción de exportar a CSV. |
| Precondición | Sesión activa del Administrador. |
| Postcondición | Se muestra el reporte o se descarga el archivo CSV. |

Flujo típico:

| Paso | Acción del Actor | Respuesta del Sistema |
|------|------------------|-----------------------|
| 1 | Selecciona "Reportes Financieros". | Muestra los módulos disponibles. |
| 2 | Elige el período (7, 15, 30 o 90 días). | Filtra los datos. |
| 3 | Presiona "Generar Reporte". | Muestra tablas con la información. |
| 4 | Hace clic en "Exportar". | Genera y descarga el archivo CSV. |

Flujo excepcional:

| Excepción | Respuesta |
|-----------|-----------|
| Sin datos para el período | "No se encontraron registros." |


 CU6 — Administrar Catálogo

| Campo | Descripción |
|-------|-------------|
| ID | CU6 |
| Nombre | Administrar catálogo |
| Actores | Administrador |
| Descripción | Gestiona los productos del catálogo público (agregar, editar, eliminar). |
| Precondición | Sesión activa del Administrador. |
| Postcondición | Los cambios se reflejan en la vista pública del catálogo. |

Flujo típico:

| Paso | Acción del Actor | Respuesta del Sistema |
|------|------------------|-----------------------|
| 1 | Selecciona "Productos" en el menú. | Muestra el catálogo administrativo. |
| 2 | Agrega, edita o elimina productos. | Valida datos, almacena cambios y muestra confirmación. |

Flujo excepcional:

| Excepción | Respuesta |
|-----------|-----------|
| Imagen inválida o mayor a 5 MB | "Formato no válido. Máximo 5MB." |


 CU7 — Administrar Inventario

| Campo | Descripción |
|-------|-------------|
| ID | CU7 |
| Nombre | Administrar inventario |
| Actores | Administrador |
| Descripción | Control de stock con registro de movimientos (compra, devolución, pérdida, corrección). |
| Precondición | Sesión activa del Administrador. |
| Postcondición | El stock se actualiza y los movimientos quedan registrados. |

Flujo típico:

| Paso | Acción del Actor | Respuesta del Sistema |
|------|------------------|-----------------------|
| 1 | Selecciona "Inventario". | Muestra el listado de productos con stock. |
| 2 | Registra un movimiento de inventario. | Actualiza el stock y guarda el registro. |

Flujo excepcional:

| Excepción | Respuesta |
|-----------|-----------|
| Stock insuficiente | "Stock insuficiente para esta operación." |


 CU8 — Auditar Transacciones

| Campo | Descripción |
|-------|-------------|
| ID | CU8 |
| Nombre | Auditar transacciones |
| Actores | Administrador |
| Descripción | Consulta el historial de acciones del sistema (creaciones, modificaciones, pagos, movimientos). |
| Precondición | Sesión activa del Administrador. |
| Postcondición | Se muestra la bitácora en solo lectura. |

Flujo típico:

| Paso | Acción del Actor | Respuesta del Sistema |
|------|------------------|-----------------------|
| 1 | Selecciona "Logs de Auditoría". | Muestra los registros más recientes. |
| 2 | Filtra por tipo de entidad o acción. | Refresca los resultados. |

Flujo excepcional:

| Excepción | Respuesta |
|-----------|-----------|
| Sin registros | "No se encontraron registros." |

 3.2.2 Funciones del Empleado


 CU9 — Autenticar Usuario (Empleado)

| Campo | Descripción |
|-------|-------------|
| ID | CU9 |
| Nombre | Autenticar usuario |
| Actores | Empleado |
| Descripción | Inicio de sesión del empleado con credenciales. |
| Precondición | El empleado debe estar registrado por un Administrador. |
| Postcondición | Se inicia la sesión y se redirige al Dashboard del Empleado. |

Flujo típico:

| Paso | Acción del Actor | Respuesta del Sistema |
|------|------------------|-----------------------|
| 1 | Ingresa credenciales y hace clic en "Iniciar Sesión". | Valida credenciales, verifica rol "employee" y redirige al Dashboard. |

Flujo excepcional:

| Excepción | Respuesta |
|-----------|-----------|
| Credenciales incorrectas | "Correo o contraseña incorrectos." |
| Cuenta inactiva | "Usuario inactivo. Contacte al Administrador." |


 CU10 — Consultar Catálogo (Empleado)

| Campo | Descripción |
|-------|-------------|
| ID | CU10 |
| Nombre | Consultar catálogo |
| Actores | Empleado |
| Descripción | Visualización de productos en solo lectura con precios y stock. |
| Precondición | Sesión activa del empleado. |
| Postcondición | Se muestra la información actualizada. |

Flujo típico:

| Paso | Acción del Actor | Respuesta del Sistema |
|------|------------------|-----------------------|
| 1 | Selecciona "Catálogo de Productos". | Muestra el listado paginado. |
| 2 | Aplica filtros de búsqueda. | Refresca los resultados. |


 CU11 — Registrar Venta

| Campo | Descripción |
|-------|-------------|
| ID | CU11 |
| Nombre | Registrar venta |
| Actores | Empleado |
| Descripción | Registra una venta directa en tienda, seleccionando productos y calculando el total con impuestos (16%). |
| Precondición | Sesión activa, productos con stock disponible. |
| Postcondición | La venta se almacena y el stock se descuenta. |

Flujo típico:

| Paso | Acción del Actor | Respuesta del Sistema |
|------|------------------|-----------------------|
| 1 | Selecciona "Registrar venta". | Muestra el buscador de productos. |
| 2 | Busca y agrega productos con cantidades. | Verifica stock y calcula subtotal. |
| 3 | Indica método de pago. | Calcula el total con impuestos. |
| 4 | Confirma la venta. | Registra la venta y descuenta stock. |

Flujo excepcional:

| Excepción | Respuesta |
|-----------|-----------|
| Cantidad supera stock | "Cantidad solicitada supera el stock disponible." |
| Sin productos en el detalle | "Debe agregar al menos un producto." |


 CU12 — Registrar Apartado (Presencial)

| Campo | Descripción |
|-------|-------------|
| ID | CU12 |
| Nombre | Registrar apartado presencial |
| Actores | Empleado |
| Descripción | Registra una reserva de productos para un cliente que visita la tienda, con abono y plazo de retiro. |
| Precondición | Sesión activa, productos con stock. |
| Postcondición | El apartado se almacena y el stock se reserva. |

Flujo típico:

| Paso | Acción del Actor | Respuesta del Sistema |
|------|------------------|-----------------------|
| 1 | Selecciona los productos y cantidades. | Reserva stock y calcula el total. |
| 2 | Ingresa datos del cliente y monto de abono. | Valida el abono. |
| 3 | Establece fecha límite de retiro y confirma. | Almacena el apartado y genera comprobante. |

Flujo excepcional:

| Excepción | Respuesta |
|-----------|-----------|
| Abono insuficiente | "El abono no cumple con el mínimo permitido." |
| Fecha anterior a hoy | "La fecha debe ser posterior a la fecha actual." |

 3.2.3 Funciones del Cliente


 CU13 — Registrarse

| Campo | Descripción |
|-------|-------------|
| ID | CU13 |
| Nombre | Registrarse |
| Actores | Cliente |
| Descripción | Creación de cuenta con nombre, correo, teléfono y contraseña. |
| Precondición | El usuario no debe tener una cuenta con el mismo correo. |
| Postcondición | La cuenta se crea con contraseña cifrada. |

Flujo típico:

| Paso | Acción del Actor | Respuesta del Sistema |
|------|------------------|-----------------------|
| 1 | Hace clic en "Registrarse". | Muestra el formulario. |
| 2 | Completa los campos. | Valida formatos en tiempo real. |
| 3 | Confirma contraseña y crea la cuenta. | Cifra contraseña, almacena y redirige al login. |

Flujo excepcional:

| Excepción | Respuesta |
|-----------|-----------|
| Correo ya registrado | "Ya existe una cuenta con este correo." |
| Contraseñas no coinciden | "Las contraseñas no coinciden." |


 CU14 — Autenticar Usuario (Cliente)

| Campo | Descripción |
|-------|-------------|
| ID | CU14 |
| Nombre | Autenticar usuario |
| Actores | Cliente |
| Descripción | Inicio de sesión del cliente con credenciales. |
| Precondición | El cliente debe estar registrado (CU13). |
| Postcondición | Se inicia la sesión y se redirige al catálogo. |

Flujo típico:

| Paso | Acción del Actor | Respuesta del Sistema |
|------|------------------|-----------------------|
| 1 | Ingresa credenciales y hace clic en "Ingresar". | Valida credenciales, verifica rol y redirige al catálogo. |

Flujo excepcional:

| Excepción | Respuesta |
|-----------|-----------|
| Credenciales incorrectas | "Correo o contraseña incorrectos." |
| Cuenta inactiva | "Su cuenta está inactiva." |


 CU15 — Consultar Catálogo (Cliente)

| Campo | Descripción |
|-------|-------------|
| ID | CU15 |
| Nombre | Consultar catálogo |
| Actores | Cliente |
| Descripción | Navegación por el catálogo público con filtros por categoría, talla y precio. No requiere sesión. |
| Precondición | Ninguna (acceso público). |
| Postcondición | Se muestra el listado de productos disponibles. |

Flujo típico:

| Paso | Acción del Actor | Respuesta del Sistema |
|------|------------------|-----------------------|
| 1 | Accede al catálogo. | Muestra los productos paginados. |
| 2 | Aplica filtros. | Refresca los resultados. |
| 3 | Selecciona un producto. | Muestra la ficha detallada. |

Flujo excepcional:

| Excepción | Respuesta |
|-----------|-----------|
| Sin resultados | "No se encontraron productos." |


 CU16 — Gestionar Carrito y Apartado

| Campo | Descripción |
|-------|-------------|
| ID | CU16 |
| Nombre | Gestionar carrito y realizar apartado |
| Actores | Cliente |
| Descripción | El cliente agrega productos al carrito, ajusta cantidades y formaliza el apartado, generando un código que debe pagar por transferencia. |
| Casos de uso relacionados | CU15, CU14 |
| Precondición | Sesión activa del cliente, al menos un producto con stock. |
| Postcondición | El apartado se almacena, el stock se reserva y se redirige al pago. |

Flujo típico:

| Paso | Acción del Actor | Respuesta del Sistema |
|------|------------------|-----------------------|
| 1 | Agrega productos al carrito desde la ficha del producto (CU15). | Añade el producto al carrito. |
| 2 | Ajusta cantidades o elimina artículos. | Recalcula el total. |
| 3 | Hace clic en "Realizar apartado". | Muestra resumen y valida stock. |
| 4 | Confirma el apartado. | Genera código único, reserva stock y redirige a pago. |
| 5 | Adjunta comprobante de transferencia. | Registra el pago y actualiza el estado. |

Flujo excepcional:

| Excepción | Respuesta |
|-----------|-----------|
| Stock agotado durante el proceso | "Uno de los productos ya no está disponible." |
| Sin comprobante | "Adjunte el comprobante de pago para continuar." |
| Plazo vencido | "El plazo ha vencido. Realice un nuevo apartado." |

 3.3 Requisitos de Rendimiento

- Páginas: carga en menos de 3 segundos.
- Búsquedas: resultados en menos de 2 segundos.
- Exportaciones CSV: menos de 5 segundos.
- Soporte mínimo: 20 usuarios simultáneos.
- Sesiones: expiran tras 30 minutos de inactividad.
- Cookies: HttpOnly, SameSite=Lax, Secure en producción.

 3.4 Restricciones de Diseño

- Arquitectura MVC con Blueprints de Flask.
- Backend en Python 3.9+, frontend con Bootstrap 5 (sin frameworks JS adicionales).
- Contraseñas cifradas con bcrypt (12 rounds).
- Protección CSRF en todos los formularios.
- Despliegue en Render (PaaS) con DNS y SSL en Cloudflare.

 3.5 Atributos del Sistema

- Seguridad: Login con bcrypt, control de acceso por roles, cookies seguras, auditoría.
- Fiabilidad: Excepciones manejadas con try-except, validación de estados en pedidos.
- Disponibilidad: 24/7, dependencia del hosting Render.
- Mantenibilidad: Código modular en Blueprints, documentación en README.
- Portabilidad: Responsive con Bootstrap 5, compatible con Chrome, Firefox, Edge.

 3.6 Otros Requisitos

- Localización: Estados del sistema en español (filtros Jinja2 personalizados).
- Códigos QR: Generados para pedidos en estado "listo para recoger".
- Imágenes: Almacenadas en `static/images/` con formatos PNG, JPG, JPEG, GIF, WebP (máx. 5 MB).
- Exportación: Reportes en formato CSV.
- Correo: Notificaciones de confirmación, pedido listo y pedido entregado.

 4. Apéndices

 Apéndice A — Glosario

| # | Término | Definición |
|---|---------|------------|
| 1 | Apartado | Reserva de productos con plazo de pago y retiro |
| 2 | bcrypt | Algoritmo de hash de contraseñas con sal |
| 3 | Blueprint | Módulo de Flask para organizar rutas |
| 4 | CRUD | Operaciones de mantenimiento de datos |
| 5 | ERS | Especificación de Requisitos de Software |
| 6 | Flask | Microframework web para Python |
| 7 | ORM | Mapeo entre objetos Python y tablas de BD |
| 8 | SQLite | BD relacional ligera y embebida |

 Apéndice B — Tabla Consolidada de Casos de Uso

| Código | Caso de Uso | Actor |
|--------|-------------|-------|
| CU1 | Autenticar usuario | Administrador |
| CU2 | Visualizar dashboard | Administrador |
| CU3 | Administrar empleados | Administrador |
| CU4 | Administrar pedidos | Administrador |
| CU5 | Generar reportes | Administrador |
| CU6 | Administrar catálogo | Administrador |
| CU7 | Administrar inventario | Administrador |
| CU8 | Auditar transacciones | Administrador |
| CU9 | Autenticar usuario | Empleado |
| CU10 | Consultar catálogo | Empleado |
| CU11 | Registrar venta | Empleado |
| CU12 | Registrar apartado presencial | Empleado |
| CU13 | Registrarse | Cliente |
| CU14 | Autenticar usuario | Cliente |
| CU15 | Consultar catálogo | Cliente |
| CU16 | Gestionar carrito y apartado | Cliente |
