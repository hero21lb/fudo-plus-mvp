from contextlib import asynccontextmanager
import hmac
import os
from pathlib import Path
import secrets
from typing import Literal

import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from authlib.integrations.starlette_client import OAuth, OAuthError
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator
from starlette.middleware.sessions import SessionMiddleware

from app import auth, db


ROOT = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.initialize_database()
    yield


app = FastAPI(title="FUDO Plus", lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET") or secrets.token_urlsafe(48),
    session_cookie="fudo_admin",
    max_age=60 * 60 * 8,
    same_site="lax",
    https_only=bool(os.getenv("RAILWAY_ENVIRONMENT")),
)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

oauth = OAuth()
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    client_kwargs={"scope": "openid email profile"},
)


class LoginInput(BaseModel):
    username: str
    password: str


class OrderItemInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=100)


class OrderInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    customer_name: str = Field(min_length=1, max_length=120)
    customer_phone: str = Field(min_length=1, max_length=40)
    fulfillment_method: Literal["pickup", "delivery"]
    delivery_address: str | None = Field(default=None, max_length=500)
    delivery_reference: str | None = Field(default=None, max_length=500)
    payment_method: Literal["cash", "simulated"] = "cash"
    items: list[OrderItemInput] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_order(self):
        if self.fulfillment_method == "delivery" and not self.delivery_address:
            raise ValueError("Ingresá la dirección de entrega")
        ids = [item.product_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("Agrupá las cantidades de cada producto")
        if self.fulfillment_method == "pickup":
            self.delivery_address = self.delivery_reference = None
        return self


@app.post("/api/orders", status_code=201)
def create_order(order: OrderInput):
    try:
        return db.create_order(order.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except (psycopg.Error, RuntimeError) as error:
        raise HTTPException(status_code=503, detail="No se pudo guardar el pedido. Intentá más tarde.") from error


class ProductInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)
    image_url: HttpUrl | None = None
    price_cents: int = Field(ge=0, le=100_000_000)
    is_published: bool = False
    is_available: bool = True

    @field_validator("name")
    @classmethod
    def nonempty_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El nombre no puede estar vacío")
        return value

    @field_validator("image_url")
    @classmethod
    def secure_image(cls, value: HttpUrl | None) -> HttpUrl | None:
        if value is not None and value.scheme != "https":
            raise ValueError("La foto debe usar HTTPS")
        return value


def require_admin(request: Request) -> Request:
    if not request.session.get("admin"):
        raise HTTPException(status_code=401, detail="Iniciá sesión para continuar.")
    return request


def require_csrf(
    request: Request = Depends(require_admin),
    x_csrf_token: str | None = Header(default=None),
) -> Request:
    expected = request.session.get("csrf", "")
    if not expected or not x_csrf_token or not hmac.compare_digest(expected, x_csrf_token):
        raise HTTPException(status_code=403, detail="Sesión inválida. Actualizá la página.")
    return request


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/admin/login", include_in_schema=False)
def admin_login_page(request: Request):
    if request.session.get("admin"):
        return RedirectResponse("/admin", status_code=303)
    return FileResponse(ROOT / "static" / "login.html", headers={"Cache-Control": "no-store"})


@app.get("/auth/google", include_in_schema=False)
async def google_login(request: Request):
    if not auth.google_oauth_is_configured():
        raise HTTPException(status_code=503, detail="El acceso con Google aún no está configurado.")
    google = oauth.create_client("google")
    return await google.authorize_redirect(request, os.environ["GOOGLE_REDIRECT_URI"])


@app.get("/auth/google/callback", include_in_schema=False)
async def google_callback(request: Request):
    if not auth.google_oauth_is_configured():
        raise HTTPException(status_code=503, detail="El acceso con Google aún no está configurado.")
    google = oauth.create_client("google")
    try:
        token = await google.authorize_access_token(request)
    except OAuthError as error:
        if error.error == "access_denied":
            return RedirectResponse("/admin/login?error=cancelled", status_code=303)
        raise HTTPException(status_code=401, detail="No se pudo validar el acceso con Google.") from error

    user = token.get("userinfo") or {}
    email = str(user.get("email", "")).strip().casefold()
    if (
        not user.get("email_verified")
        or not email
        or not any(hmac.compare_digest(email, allowed) for allowed in auth.google_admin_emails())
    ):
        request.session.clear()
        return RedirectResponse("/admin/login?error=unauthorized", status_code=303)

    request.session.clear()
    request.session.update({"admin": True, "admin_email": email, "csrf": secrets.token_urlsafe(32)})
    return RedirectResponse("/admin", status_code=303)


@app.get("/admin", include_in_schema=False)
def admin_page(request: Request):
    if not request.session.get("admin"):
        return RedirectResponse("/admin/login", status_code=303)
    return FileResponse(ROOT / "static" / "admin.html", headers={"Cache-Control": "no-store"})


@app.post("/api/admin/login", include_in_schema=False)
def admin_login(credentials: LoginInput, request: Request):
    if not auth.admin_is_configured():
        raise HTTPException(status_code=503, detail="El acceso del negocio aún no está configurado.")
    if not auth.valid_credentials(credentials.username, credentials.password):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos.")
    request.session.clear()
    request.session.update({"admin": True, "csrf": secrets.token_urlsafe(32)})
    return {"status": "ok"}


@app.get("/api/admin/session", include_in_schema=False)
def admin_session(request: Request = Depends(require_admin)):
    return {"csrf_token": request.session["csrf"]}


@app.post("/api/admin/logout", include_in_schema=False)
def admin_logout(request: Request = Depends(require_csrf)):
    request.session.clear()
    return {"status": "ok"}


@app.get("/api/admin/products", include_in_schema=False)
def admin_products(_request: Request = Depends(require_admin)):
    try:
        return db.list_admin_products()
    except (psycopg.Error, RuntimeError) as error:
        raise HTTPException(status_code=503, detail="No se pudieron cargar los productos.") from error


@app.get("/api/admin/orders", include_in_schema=False)
def admin_orders(_request: Request = Depends(require_admin)):
    try:
        return db.list_orders()
    except (psycopg.Error, RuntimeError) as error:
        raise HTTPException(status_code=503, detail="No se pudieron cargar los pedidos.") from error


@app.post("/api/admin/products", status_code=201, include_in_schema=False)
def admin_create_product(product: ProductInput, _request: Request = Depends(require_csrf)):
    try:
        return db.create_product(product.model_dump(mode="json"))
    except (psycopg.Error, RuntimeError) as error:
        raise HTTPException(status_code=503, detail="No se pudo guardar el producto.") from error


@app.put("/api/admin/products/{product_id}", include_in_schema=False)
def admin_update_product(product_id: int, product: ProductInput, _request: Request = Depends(require_csrf)):
    try:
        saved = db.update_product(product_id, product.model_dump(mode="json"))
    except (psycopg.Error, RuntimeError) as error:
        raise HTTPException(status_code=503, detail="No se pudo guardar el producto.") from error
    if saved is None:
        raise HTTPException(status_code=404, detail="El producto no existe.")
    return saved


@app.get("/api/products")
def products():
    try:
        return db.list_published_products()
    except (psycopg.Error, RuntimeError) as error:
        raise HTTPException(status_code=503, detail="El menú no está disponible por ahora.") from error


@app.get("/ready", include_in_schema=False)
def ready():
    try:
        db.database_is_ready()
    except (psycopg.Error, RuntimeError) as error:
        raise HTTPException(status_code=503, detail="Base de datos no disponible") from error
    return {"status": "ok"}
