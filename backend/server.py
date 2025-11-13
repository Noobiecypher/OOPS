# backend/server.py
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import bcrypt, jwt, os, uuid, logging

# ==================== CONFIG ====================
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

MONGO_URL = os.getenv("MONGO_URL", "").strip()
DB_NAME = os.getenv("DB_NAME", "oops_db").strip()
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7))

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="LiveMART API")

# ==================== FIXED CORS ====================
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://blueprint-web-6.preview.emergentagent.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,         # 👈 your frontends
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== ROUTER SETUP ====================
api_router = APIRouter(prefix="/api")

client: AsyncIOMotorClient | None = None
db = None
mongo_connected = False

# ==================== MODELS ====================
class UserBase(BaseModel):
    email: EmailStr
    name: str
    phone: str
    role: str
    address: Optional[str] = None
    location: Optional[Dict[str, float]] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    verified: bool = False

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User

class Category(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None

class ProductBase(BaseModel):
    name: str
    description: str
    category_id: str
    price: float
    stock: int
    image_url: Optional[str] = None
    unit: str = "piece"
    available: bool = True

class ProductCreate(ProductBase):
    seller_id: str

class Product(ProductBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    seller_id: str
    seller_name: Optional[str] = None
    rating: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ==================== HELPERS ====================
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def serialize_datetime(obj):
    if isinstance(obj, dict):
        return {k: serialize_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(i) for i in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return obj

def deserialize_datetime(obj):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in ["created_at", "updated_at"] and isinstance(v, str):
                try:
                    out[k] = datetime.fromisoformat(v)
                except:
                    out[k] = v
            else:
                out[k] = deserialize_datetime(v)
        return out
    elif isinstance(obj, list):
        return [deserialize_datetime(i) for i in obj]
    return obj

def send_otp(phone: str) -> bool:
    logger.info(f"Mock OTP sent to {phone}: 123456")
    return True

# ==================== STARTUP / SHUTDOWN ====================
@app.on_event("startup")
async def startup_event():
    global client, db, mongo_connected
    if not MONGO_URL:
        logger.error("MONGO_URL not set.")
        mongo_connected = False
        return
    try:
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        await client.admin.command("ping")
        mongo_connected = True
        logger.info("Connected to MongoDB successfully.")
    except Exception as e:
        logger.exception("Failed to connect MongoDB: %s", e)
        mongo_connected = False

@app.on_event("shutdown")
async def shutdown_event():
    global client
    if client:
        client.close()
        logger.info("MongoDB client closed.")

# ==================== ROOT ====================
@app.get("/", tags=["health"])
async def health_check():
    return {
        "message": "Live MART API",
        "version": "1.0.0",
        "status": "running",
        "mongodb": "connected" if mongo_connected else "disconnected",
        "allowed_origins": origins,
    }

# ==================== AUTH ROUTES ====================
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = hash_password(user_data.password)
    user_dict = user_data.model_dump()
    user_dict.pop("password")
    user = User(**user_dict)
    doc = user.model_dump()
    doc["password"] = hashed
    doc = serialize_datetime(doc)
    await db.users.insert_one(doc)
    send_otp(user.phone)
    token = create_access_token({"sub": user.email, "user_id": user.id, "role": user.role})
    return Token(access_token=token, user=user)

@api_router.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    user_doc = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user_doc or not verify_password(credentials.password, user_doc["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user_doc = deserialize_datetime(user_doc)
    user_doc.pop("password")
    user = User(**user_doc)
    token = create_access_token({"sub": user.email, "user_id": user.id, "role": user.role})
    return Token(access_token=token, user=user)

@api_router.post("/auth/verify-otp")
async def verify_otp(data: Dict[str, str]):
    if data.get("otp") == "123456":
        return {"success": True, "message": "OTP verified successfully"}
    return {"success": False, "message": "Invalid OTP"}

# ==================== CATEGORY ENDPOINTS ====================
@api_router.get("/categories", response_model=List[Category])
async def get_categories():
    return await db.categories.find({}, {"_id": 0}).to_list(1000)

@api_router.post("/categories", response_model=Category)
async def create_category(category_data: Dict[str, Any]):
    cat = Category(**category_data)
    await db.categories.insert_one(cat.model_dump())
    return cat

# ==================== PRODUCT ENDPOINTS ====================
@api_router.get("/products", response_model=List[Product])
async def get_products():
    products = await db.products.find({}, {"_id": 0}).to_list(1000)
    return [deserialize_datetime(p) for p in products]

# ==================== ROUTER INCLUDE ====================
app.include_router(api_router)