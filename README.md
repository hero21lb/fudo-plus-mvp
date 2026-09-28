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

El proyecto ya está creado en Railway. El menú de demostración está en [fudo-plus-mvp-production.up.railway.app](https://fudo-plus-mvp-production.up.railway.app/).

Para reproducir la configuración:

1. Crear un proyecto con el repositorio GitHub y agregar un servicio PostgreSQL.
2. En el servicio web, establecer `DATABASE_URL=${{Postgres.DATABASE_URL}}`, `PORT=8000` y, para la primera demostración, `SEED_DEMO_PRODUCTS=true`.
3. Configurar el comando de inicio `uvicorn app.main:app --host 0.0.0.0 --port $PORT` y el healthcheck `/ready` en los ajustes del servicio.
4. Generar un dominio público apuntando al puerto `8000`. La base de datos no necesita dominio público.

No copiar credenciales al repositorio ni exponer la base al público para que la aplicación funcione. Por ahora el menú es de consulta; la administración de productos y los pedidos corresponden a incrementos posteriores.

## Colaboración

Antes de crear ramas o pedir ayuda a una IA, leer [AI-AND-GIT-GUIDE.md](AI-AND-GIT-GUIDE.md).

## Producto y alcance

La definición corregida del proyecto está en [ALCANCE-DEL-PROYECTO.md](ALCANCE-DEL-PROYECTO.md).
