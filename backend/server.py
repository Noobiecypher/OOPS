from fastapi import FastAPI, APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import random

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

# User Models
class UserBase(BaseModel):
    email: EmailStr
    name: str
    phone: str
    role: str  # customer, retailer, wholesaler
    address: Optional[str] = None
    location: Optional[Dict[str, float]] = None  # {lat, lng}

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

# Category Models
class Category(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None

# Product Models
class ProductBase(BaseModel):
    name: str
    description: str
    category_id: str
    price: float
    stock: int
    image_url: Optional[str] = None
    unit: str = "piece"  # kg, liter, piece, etc.
    available: bool = True

class ProductCreate(ProductBase):
    seller_id: str  # retailer or wholesaler id

class Product(ProductBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    seller_id: str
    seller_name: Optional[str] = None
    rating: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Cart Models
class CartItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    product_id: str
    quantity: int
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CartItemCreate(BaseModel):
    product_id: str
    quantity: int

# Order Models
class OrderItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    price: float
    total: float

class OrderCreate(BaseModel):
    items: List[OrderItem]
    delivery_address: str
    payment_method: str  # online, offline
    total_amount: float

class Order(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    items: List[OrderItem]
    delivery_address: str
    payment_method: str
    payment_status: str = "pending"  # pending, completed, failed
    order_status: str = "placed"  # placed, confirmed, packed, shipped, delivered, cancelled
    total_amount: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Feedback Models
class FeedbackCreate(BaseModel):
    product_id: str
    rating: int  # 1-5
    comment: Optional[str] = None

class Feedback(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_name: str
    product_id: str
    rating: int
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Shop Models (for location-based listing)
class Shop(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner_id: str
    name: str
    address: str
    location: Dict[str, float]  # {lat, lng}
    distance: Optional[float] = None  # in km
    rating: float = 0.0

# ==================== HELPER FUNCTIONS ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def serialize_datetime(obj):
    """Convert datetime to ISO string for MongoDB"""
    if isinstance(obj, dict):
        return {k: serialize_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return obj

def deserialize_datetime(obj):
    """Convert ISO string back to datetime"""
    if isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            if k in ['created_at', 'updated_at', 'added_at', 'timestamp'] and isinstance(v, str):
                try:
                    result[k] = datetime.fromisoformat(v)
                except:
                    result[k] = v
            else:
                result[k] = deserialize_datetime(v)
        return result
    elif isinstance(obj, list):
        return [deserialize_datetime(item) for item in obj]
    return obj

# Mock OTP Service
def send_otp(phone: str) -> bool:
    """Mock OTP sending - returns True"""
    logger.info(f"Mock OTP sent to {phone}: 123456")
    return True

# Mock Payment Service
def process_payment(amount: float, method: str) -> Dict[str, Any]:
    """Mock payment processing"""
    logger.info(f"Mock payment processed: ${amount} via {method}")
    return {
        "success": True,
        "transaction_id": str(uuid.uuid4()),
        "message": "Payment successful"
    }

# ==================== AUTHENTICATION ROUTES ====================

@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    """Register a new user"""
    # Check if user already exists
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Create user
    user_dict = user_data.model_dump()
    user_dict.pop('password')
    user = User(**user_dict)
    
    # Store in DB
    doc = user.model_dump()
    doc['password'] = hashed_password
    doc = serialize_datetime(doc)
    
    await db.users.insert_one(doc)
    
    # Send mock OTP
    send_otp(user.phone)
    
    # Create token
    access_token = create_access_token({"sub": user.email, "user_id": user.id, "role": user.role})
    
    return Token(access_token=access_token, user=user)

@api_router.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    """Login user"""
    # Find user
    user_doc = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    if not verify_password(credentials.password, user_doc['password']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Deserialize and create user object
    user_doc = deserialize_datetime(user_doc)
    user_doc.pop('password')
    user = User(**user_doc)
    
    # Create token
    access_token = create_access_token({"sub": user.email, "user_id": user.id, "role": user.role})
    
    return Token(access_token=access_token, user=user)

@api_router.post("/auth/verify-otp")
async def verify_otp(data: Dict[str, str]):
    """Mock OTP verification"""
    # Mock: always returns success if OTP is 123456
    if data.get("otp") == "123456":
        return {"success": True, "message": "OTP verified successfully"}
    return {"success": False, "message": "Invalid OTP"}

# ==================== CATEGORY ROUTES ====================

@api_router.get("/categories", response_model=List[Category])
async def get_categories():
    """Get all categories"""
    categories = await db.categories.find({}, {"_id": 0}).to_list(1000)
    return categories

@api_router.post("/categories", response_model=Category)
async def create_category(category_data: Dict[str, Any]):
    """Create a new category"""
    category = Category(**category_data)
    doc = category.model_dump()
    await db.categories.insert_one(doc)
    return category

# ==================== PRODUCT ROUTES ====================

@api_router.get("/products", response_model=List[Product])
async def get_products(
    category_id: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    available_only: bool = True
):
    """Get products with filters"""
    query = {}
    
    if category_id:
        query["category_id"] = category_id
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    if min_price is not None:
        query["price"] = query.get("price", {})
        query["price"]["$gte"] = min_price
    
    if max_price is not None:
        query["price"] = query.get("price", {})
        query["price"]["$lte"] = max_price
    
    if available_only:
        query["available"] = True
        query["stock"] = {"$gt": 0}
    
    products = await db.products.find(query, {"_id": 0}).to_list(1000)
    products = [deserialize_datetime(p) for p in products]
    return products

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    """Get single product"""
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return deserialize_datetime(product)

@api_router.post("/products", response_model=Product)
async def create_product(product_data: ProductCreate):
    """Create a new product (retailer/wholesaler only)"""
    # Get seller info
    seller = await db.users.find_one({"id": product_data.seller_id}, {"_id": 0, "name": 1})
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    
    product_dict = product_data.model_dump()
    product = Product(**product_dict, seller_name=seller.get("name"))
    
    doc = serialize_datetime(product.model_dump())
    await db.products.insert_one(doc)
    
    return product

@api_router.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: str, product_data: Dict[str, Any]):
    """Update product"""
    product_data["updated_at"] = datetime.now(timezone.utc)
    
    result = await db.products.update_one(
        {"id": product_id},
        {"$set": serialize_datetime(product_data)}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    updated = await db.products.find_one({"id": product_id}, {"_id": 0})
    return deserialize_datetime(updated)

@api_router.delete("/products/{product_id}")
async def delete_product(product_id: str):
    """Delete product"""
    result = await db.products.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"success": True, "message": "Product deleted"}

# ==================== CART ROUTES ====================

@api_router.get("/cart/{user_id}")
async def get_cart(user_id: str):
    """Get user's cart with product details"""
    cart_items = await db.cart.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    
    # Enrich with product details
    enriched_items = []
    for item in cart_items:
        product = await db.products.find_one({"id": item["product_id"]}, {"_id": 0})
        if product:
            enriched_items.append({
                **deserialize_datetime(item),
                "product": deserialize_datetime(product)
            })
    
    return enriched_items

@api_router.post("/cart/{user_id}")
async def add_to_cart(user_id: str, item_data: CartItemCreate):
    """Add item to cart"""
    # Check if item already in cart
    existing = await db.cart.find_one({
        "user_id": user_id,
        "product_id": item_data.product_id
    })
    
    if existing:
        # Update quantity
        new_quantity = existing["quantity"] + item_data.quantity
        await db.cart.update_one(
            {"id": existing["id"]},
            {"$set": {"quantity": new_quantity}}
        )
        return {"success": True, "message": "Cart updated"}
    else:
        # Add new item
        cart_item = CartItem(user_id=user_id, **item_data.model_dump())
        doc = serialize_datetime(cart_item.model_dump())
        await db.cart.insert_one(doc)
        return {"success": True, "message": "Added to cart"}

@api_router.put("/cart/{user_id}/{item_id}")
async def update_cart_item(user_id: str, item_id: str, quantity: int):
    """Update cart item quantity"""
    result = await db.cart.update_one(
        {"id": item_id, "user_id": user_id},
        {"$set": {"quantity": quantity}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    return {"success": True, "message": "Cart updated"}

@api_router.delete("/cart/{user_id}/{item_id}")
async def remove_from_cart(user_id: str, item_id: str):
    """Remove item from cart"""
    result = await db.cart.delete_one({"id": item_id, "user_id": user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    return {"success": True, "message": "Item removed from cart"}

@api_router.delete("/cart/{user_id}")
async def clear_cart(user_id: str):
    """Clear entire cart"""
    await db.cart.delete_many({"user_id": user_id})
    return {"success": True, "message": "Cart cleared"}

# ==================== ORDER ROUTES ====================

@api_router.post("/orders/{user_id}", response_model=Order)
async def create_order(user_id: str, order_data: OrderCreate):
    """Create a new order"""
    order = Order(user_id=user_id, **order_data.model_dump())
    
    # Process payment (mock)
    payment_result = process_payment(order.total_amount, order.payment_method)
    
    if payment_result["success"]:
        order.payment_status = "completed"
    else:
        order.payment_status = "failed"
        raise HTTPException(status_code=400, detail="Payment failed")
    
    # Update product stock
    for item in order.items:
        await db.products.update_one(
            {"id": item.product_id},
            {"$inc": {"stock": -item.quantity}}
        )
    
    # Save order
    doc = serialize_datetime(order.model_dump())
    await db.orders.insert_one(doc)
    
    # Clear cart
    await db.cart.delete_many({"user_id": user_id})
    
    # Mock notification
    logger.info(f"Order confirmation sent to user {user_id}")
    
    return order

@api_router.get("/orders/{user_id}", response_model=List[Order])
async def get_user_orders(user_id: str):
    """Get user's order history"""
    orders = await db.orders.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return [deserialize_datetime(o) for o in orders]

@api_router.get("/orders/detail/{order_id}", response_model=Order)
async def get_order_detail(order_id: str):
    """Get order details"""
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return deserialize_datetime(order)

@api_router.put("/orders/{order_id}/status")
async def update_order_status(order_id: str, status_data: Dict[str, str]):
    """Update order status"""
    new_status = status_data.get("status")
    
    result = await db.orders.update_one(
        {"id": order_id},
        {"$set": {"order_status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Mock notification
    logger.info(f"Order {order_id} status updated to {new_status}")
    
    return {"success": True, "message": "Order status updated"}

# ==================== FEEDBACK ROUTES ====================

@api_router.post("/feedback/{user_id}", response_model=Feedback)
async def add_feedback(user_id: str, feedback_data: FeedbackCreate):
    """Add product feedback"""
    # Get user info
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "name": 1})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    feedback = Feedback(
        user_id=user_id,
        user_name=user.get("name"),
        **feedback_data.model_dump()
    )
    
    doc = serialize_datetime(feedback.model_dump())
    await db.feedback.insert_one(doc)
    
    # Update product rating (simple average)
    all_feedback = await db.feedback.find({"product_id": feedback.product_id}, {"_id": 0, "rating": 1}).to_list(1000)
    avg_rating = sum(f["rating"] for f in all_feedback) / len(all_feedback)
    
    await db.products.update_one(
        {"id": feedback.product_id},
        {"$set": {"rating": round(avg_rating, 1)}}
    )
    
    return feedback

@api_router.get("/feedback/product/{product_id}", response_model=List[Feedback])
async def get_product_feedback(product_id: str):
    """Get all feedback for a product"""
    feedback = await db.feedback.find({"product_id": product_id}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return [deserialize_datetime(f) for f in feedback]

# ==================== SHOP/LOCATION ROUTES ====================

@api_router.get("/shops", response_model=List[Shop])
async def get_nearby_shops(lat: float = 0, lng: float = 0, radius: float = 10):
    """Get nearby shops (mock location-based search)"""
    # Get all retailers and wholesalers
    sellers = await db.users.find(
        {"role": {"$in": ["retailer", "wholesaler"]}},
        {"_id": 0}
    ).to_list(1000)
    
    shops = []
    for seller in sellers:
        # Mock distance calculation
        mock_distance = random.uniform(0.5, radius)
        shop = Shop(
            owner_id=seller["id"],
            name=f"{seller['name']}'s Shop",
            address=seller.get("address", "Address not provided"),
            location=seller.get("location", {"lat": lat, "lng": lng}),
            distance=round(mock_distance, 2),
            rating=random.uniform(3.5, 5.0)
        )
        shops.append(shop)
    
    # Sort by distance
    shops.sort(key=lambda x: x.distance)
    
    return shops

# ==================== DASHBOARD/STATS ROUTES ====================

@api_router.get("/dashboard/retailer/{user_id}")
async def get_retailer_dashboard(user_id: str):
    """Get retailer dashboard stats"""
    # Get products count
    products_count = await db.products.count_documents({"seller_id": user_id})
    
    # Get total sales (orders containing retailer's products)
    orders = await db.orders.find({}, {"_id": 0, "items": 1, "total_amount": 1}).to_list(10000)
    
    retailer_orders = []
    total_revenue = 0
    
    for order in orders:
        for item in order["items"]:
            product = await db.products.find_one({"id": item["product_id"], "seller_id": user_id})
            if product:
                retailer_orders.append(order)
                total_revenue += item["total"]
                break
    
    return {
        "products_count": products_count,
        "orders_count": len(retailer_orders),
        "total_revenue": round(total_revenue, 2),
        "recent_orders": retailer_orders[:10]
    }

@api_router.get("/dashboard/wholesaler/{user_id}")
async def get_wholesaler_dashboard(user_id: str):
    """Get wholesaler dashboard stats"""
    # Similar to retailer dashboard
    products_count = await db.products.count_documents({"seller_id": user_id})
    
    orders = await db.orders.find({}, {"_id": 0, "items": 1, "total_amount": 1}).to_list(10000)
    
    wholesaler_orders = []
    total_revenue = 0
    
    for order in orders:
        for item in order["items"]:
            product = await db.products.find_one({"id": item["product_id"], "seller_id": user_id})
            if product:
                wholesaler_orders.append(order)
                total_revenue += item["total"]
                break
    
    return {
        "products_count": products_count,
        "orders_count": len(wholesaler_orders),
        "total_revenue": round(total_revenue, 2),
        "recent_orders": wholesaler_orders[:10]
    }

# ==================== SEED DATA ROUTE ====================

@api_router.post("/seed-data")
async def seed_data():
    """Seed initial categories and sample products"""
    # Check if already seeded
    existing_categories = await db.categories.count_documents({})
    if existing_categories > 0:
        return {"message": "Data already seeded"}
    
    # Create categories
    categories_data = [
        {"name": "Fruits & Vegetables", "description": "Fresh fruits and vegetables", "image_url": "https://images.unsplash.com/photo-1610832958506-aa56368176cf"},
        {"name": "Dairy & Eggs", "description": "Milk, cheese, yogurt, eggs", "image_url": "https://images.unsplash.com/photo-1628088062854-d1870b4553da"},
        {"name": "Meat & Seafood", "description": "Fresh meat and seafood", "image_url": "https://images.unsplash.com/photo-1607623814075-e51df1bdc82f"},
        {"name": "Bakery", "description": "Bread, pastries, cakes", "image_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff"},
        {"name": "Beverages", "description": "Drinks, juices, water", "image_url": "https://images.unsplash.com/photo-1544145945-f90425340c7e"},
        {"name": "Snacks", "description": "Chips, cookies, crackers", "image_url": "https://images.unsplash.com/photo-1599490659213-e2b9527bd087"},
        {"name": "Grains & Rice", "description": "Rice, wheat, pulses", "image_url": "https://images.unsplash.com/photo-1586201375761-83865001e31c"},
        {"name": "Personal Care", "description": "Soaps, shampoos, cosmetics", "image_url": "https://images.unsplash.com/photo-1556228578-8c89e6adf883"}
    ]
    
    created_categories = []
    for cat_data in categories_data:
        category = Category(**cat_data)
        await db.categories.insert_one(category.model_dump())
        created_categories.append(category)
    
    logger.info(f"Seeded {len(created_categories)} categories")
    
    return {
        "success": True,
        "message": f"Seeded {len(created_categories)} categories",
        "categories": created_categories
    }

# ==================== ROOT ROUTE ====================

@api_router.get("/")
async def root():
    return {
        "message": "Live MART API",
        "version": "1.0.0",
        "status": "running"
    }

# Include the router in the main app
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()