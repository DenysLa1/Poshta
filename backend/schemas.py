# 1. Що це: Модуль схем валідації Pydantic (DTO — Data Transfer Objects).
# 2. Для чого: Для перевірки типів вхідних даних від клієнта та серіалізації вихідних відповідей сервера.
# 3. Призначення: Відокремити публічний контракт REST API від внутрішніх моделей бази даних.


from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import List, Optional


# схеми авторизації та користувачів

class UserRegister(BaseModel):
    """Схема для публічної реєстрації клієнтів (роль призначити не можна)."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: Optional[str] = None
    phone: Optional[str] = None

    @model_validator(mode="after")
    def check_email_or_phone(self):
        if not self.email and not self.phone:
            raise ValueError("Необхідно вказати хоча б один контакт: email або номер телефону")
        return self


class UserCreateAdmin(UserRegister):
    """Схема для суперадміна: дозволяє призначати конкретну роль."""
    role: str = Field(default="client", pattern="^(client|employee|admin|superadmin)$")


class UserResponse(BaseModel):
    """Безпечна відповідь сервера (без паролів та хешів)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str


# схеми товарів

class ProductBase(BaseModel):
    name: str
    price: float
    description: Optional[str] = None


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


# схеми замовлень

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)


class OrderCreate(BaseModel):
    user_id: int
    items: List[OrderItemCreate]


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: int


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    status: str
    total_price: float
    items: List[OrderItemResponse] = []