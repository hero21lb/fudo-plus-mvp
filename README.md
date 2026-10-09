# FUDO Plus MVP

Sistema web para que un negocio de comida publique su menú y reciba pedidos para delivery o retiro.

## Stack

- API: FastAPI
- Base de datos: PostgreSQL
- Frontend: HTML, CSS y JavaScript

## Ejecutar en una computadora

Requiere Python 3.11+ y PostgreSQL. En PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Crear la base `fudo_plus` en PostgreSQL y completar `DATABASE_URL` en `.env` con la conexión local. Luego:

```powershell
uvicorn app.main:app --reload
```

Abrir `http://127.0.0.1:8000/`. La aplicación crea la tabla de productos al arrancar. Si `SEED_DEMO_PRODUCTS=true`, carga tres productos de muestra **solo cuando la tabla está vacía**. Para ejecutar las pruebas: `pytest`.

## Despliegue en Railway

El proyecto ya está creado en Railway. El menú de demostración está en [fudo-plus.nwaresoluciones.com](https://fudo-plus.nwaresoluciones.com/).

El negocio administra sus productos en [fudo-plus.nwaresoluciones.com/admin](https://fudo-plus.nwaresoluciones.com/admin). Desde ahí puede crear y editar productos, publicarlos y marcarlos como disponibles o agotados. La foto se carga mediante una URL HTTPS. El acceso puede configurarse con usuario y contraseña, o con Google OAuth y un correo autorizado; las credenciales se guardan como variables privadas del servicio web, nunca en el repositorio.

### Ingreso con Google

El panel también admite OAuth de Google. Solo pueden ingresar las cuentas cuyos correos estén configurados en `ADMIN_GOOGLE_EMAILS`; Google debe informar que cada correo está verificado. Los correos se separan con comas. El identificador de cliente y el secreto OAuth son variables privadas del servicio, nunca se guardan en Git.

1. En Google Cloud Console, elegí o creá un proyecto y configurá la pantalla de consentimiento OAuth. Para una prueba interna, agregá las cuentas de prueba que correspondan; para uso externo puede ser necesario completar la publicación y verificación que solicite Google.
2. En **Clientes**, creá un cliente OAuth de tipo **Aplicación web**. Como origen autorizado agregá `https://fudo-plus.nwaresoluciones.com`. Como URI de redirección autorizada agregá exactamente `https://fudo-plus.nwaresoluciones.com/auth/google/callback`.
3. Copiá el ID y el secreto del cliente a las variables del servicio web en Railway: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI=https://fudo-plus.nwaresoluciones.com/auth/google/callback` y `ADMIN_GOOGLE_EMAILS=admin@gmail.com,otra-cuenta@gmail.com`. Conservá `SESSION_SECRET` estable y privado.
4. Para desarrollo local, agregá `http://127.0.0.1:8000` como origen autorizado y `http://127.0.0.1:8000/auth/google/callback` como URI de redirección autorizada. En el `.env` local usá ese mismo callback y la cuenta autorizada. No subas el archivo `.env`.
5. Reiniciá o desplegá el servicio y probá `/admin/login`. El botón **Continuar con Google** debe abrir Google; al volver, el correo autorizado entra al panel y cualquier otra cuenta queda fuera.

El callback registrado en Google debe coincidir carácter por carácter con `GOOGLE_REDIRECT_URI`. Las credenciales OAuth existentes se administran desde Google Cloud Console; la aplicación no las crea ni las publica.

Para reproducir la configuración:

1. Crear un proyecto con el repositorio GitHub y agregar un servicio PostgreSQL.
2. En el servicio web, establecer `DATABASE_URL=${{Postgres.DATABASE_URL}}`, `PORT=8000` y, para la primera demostración, `SEED_DEMO_PRODUCTS=true`. Configurar también `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH` y `SESSION_SECRET` según `.env.example`. El hash y el secreto se generan con `python -m app.auth hash-password` y `python -m app.auth session-secret`.
3. Configurar el comando de inicio `uvicorn app.main:app --host 0.0.0.0 --port $PORT` y el healthcheck `/ready` en los ajustes del servicio.
4. Agregar `fudo-plus.nwaresoluciones.com` como dominio público apuntando al puerto `8000`. En Cloudflare, cargar los registros CNAME y TXT que indique Railway para verificar el dominio. La base de datos no necesita dominio público.

No copiar credenciales al repositorio ni exponer la base al público para que la aplicación funcione. Por ahora el menú es de consulta; el carrito, los pedidos y la vista de tickets corresponden a incrementos posteriores.

## Colaboración

Antes de crear ramas o pedir ayuda a una IA, leer [AI-AND-GIT-GUIDE.md](AI-AND-GIT-GUIDE.md).

## Producto y alcance

La definición corregida del proyecto está en [ALCANCE-DEL-PROYECTO.md](ALCANCE-DEL-PROYECTO.md).

## Pedidos de invitados

El menú público permite agregar productos, cambiar cantidades y enviar un pedido sin crear una cuenta. El cliente completa nombre y teléfono, elige retiro o delivery (con dirección obligatoria), y selecciona efectivo o pago simulado, claramente identificado y sin cobro real. El pago online todavía no está implementado.

`POST /api/orders` recibe `customer_name`, `customer_phone`, `fulfillment_method`, `delivery_address`, `delivery_reference`, `payment_method` e `items` con `product_id` y `quantity`. El servidor valida disponibilidad y publicación, toma nombres y precios desde `products` y guarda el pedido y sus ítems en una sola transacción. No acepta totales, precios ni estados de pago del navegador. Para invitados, `customer_id` queda nulo y los datos de contacto se conservan en el pedido; no se crean cuentas ni se deduce una identidad a partir del teléfono.

El arranque aplica `app/orders.sql` después de crear `products`, dentro de la transacción de inicialización. Es la migración aditiva de `customers`, `orders` y `order_items`; conserva los productos existentes. Si el esquema ya se aplicó, las tablas e índices existentes se mantienen. `CREATE TABLE IF NOT EXISTS` no corrige tablas preexistentes con una estructura diferente.

El panel `/admin` muestra los últimos 100 tickets, con productos, cantidades, total, contacto, modalidad, dirección y estado del pago. El botón **Actualizar pedidos** consulta los nuevos tickets; requiere la sesión de administrador. En esta entrega el estado inicial es `pending` y la vista de tickets es de consulta.
