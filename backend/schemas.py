# 1. Що це: Модуль схем валідації Pydantic (DTO — Data Transfer Objects).
# 2. Для чого: Для перевірки типів вхідних даних від клієнта та серіалізації вихідних відповідей сервера.
# 3. Призначення: Відокремити публічний контракт REST API від внутрішніх моделей бази даних.


from pydantic import BaseModel
from typing import List, Optional

# Product Schemas
class ProductBase(BaseModel):
    name: str
    price: float
    description: Optional[str] = None

class ProductResponse(ProductBase):
    id: int

    class Config:
        from_attributes = True  # Дозволяє Pydantic читати дані з об'єктів SQLAlchemy


# OrderItem Schemas
class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int

class OrderItemResponse(OrderItemCreate):
    id: int
    order_id: int

    class Config:
        from_attributes = True


# Order Schemas
class OrderCreate(BaseModel):
    user_id: int
    items: List[OrderItemCreate]

class OrderResponse(BaseModel):
    id: int
    status: str
    total_price: float
    user_id: int
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True