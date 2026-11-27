# 1. Що це: Модуль схем валідації Pydantic (DTO — Data Transfer Objects).
# 2. Для чого: Для перевірки типів вхідних даних від клієнта та серіалізації вихідних відповідей сервера.
# 3. Призначення: Відокремити публічний контракт REST API від внутрішніх моделей бази даних.


from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Dict, List, Optional


# схеми авторизації та користувачів

class UserRegister(BaseModel):
    """Схема для публічної реєстрації клієнтів (роль призначити не можна)."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: Optional[str] = None
    phone: Optional[str] = None

    @model_validator(mode="after")
    def check_email_or_phone(self):
        if self.email is not None:
            self.email = self.email.strip() or None
        if self.phone is not None:
            self.phone = self.phone.strip() or None
        if not self.email and not self.phone:
            raise ValueError("Необхідно вказати хоча б один контакт: email або номер телефону")
        return self


class UserCreateAdmin(BaseModel):
    """Схема для суперадміна: дозволяє створювати службові акаунти та призначати конкретну роль."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str = Field(default="employee", pattern="^(client|employee|admin|superadmin)$")

    @model_validator(mode="after")
    def normalize_contacts(self):
        if self.email is not None:
            self.email = self.email.strip() or None
        if self.phone is not None:
            self.phone = self.phone.strip() or None
        return self


class UserRoleUpdate(BaseModel):
    """Схема для зміни ролі існуючого користувача суперадміном."""
    role: str = Field(
        ...,
        pattern="^(client|employee|admin|superadmin)$",
        description="Нова роль користувача (client, employee, admin, superadmin)",
    )


class UserResponse(BaseModel):
    """Безпечна відповідь сервера (без паролів та хешів)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str


class UserLogin(BaseModel):
    """Схема вхідних даних для авторизації користувача."""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Схема відповіді сервера після успішного входу."""
    token: str
    user: UserResponse


# схеми товарів

class ProductBase(BaseModel):
    """Базова схема товару з обов'язковою перевіркою назви та додатної ціни."""
    name: str = Field(..., min_length=1, max_length=100, description="Назва товару")
    price: float = Field(..., gt=0, description="Ціна товару (має бути більшою за 0)")
    description: Optional[str] = None

    @model_validator(mode="after")
    def validate_name_not_blank(self):
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("Назва товару не може бути порожньою")
        return self


class ProductCreate(ProductBase):
    """Схема для створення нового товару адміністратором."""
    pass


class ProductUpdate(BaseModel):
    """Схема для оновлення товару або зміни його ціни (підтримує PUT та PATCH)."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Нова назва товару")
    price: Optional[float] = Field(default=None, gt=0, description="Нова ціна товару (більша за 0)")
    description: Optional[str] = None

    @model_validator(mode="after")
    def validate_update_fields(self):
        if self.name is not None:
            self.name = self.name.strip()
            if not self.name:
                raise ValueError("Назва товару не може бути порожньою")
        if self.name is None and self.price is None and self.description is None:
            raise ValueError("Необхідно передати хоча б одне поле для оновлення товару (name, price або description)")
        return self


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


# схеми замовлень

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)


class OrderCreate(BaseModel):
    user_id: int
    items: List[OrderItemCreate] = Field(..., min_length=1, description="Список позицій замовлення (щонайменше 1 товар)")


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


class OrderStatusUpdate(BaseModel):
    """Схема для перемикання стану замовлення через FSM."""
    status: str = Field(..., min_length=1, description="Цільовий статус замовлення (Registered, Granted, Shipped, Invoiced, Cancelled)")


# схеми бізнес-аналітики та звітності

class TopProductStat(BaseModel):
    """Статистика популярності товару в замовленнях."""
    product_id: int
    name: str
    price: float
    total_quantity: int
    orders_count: int
    total_amount: float


class StatsResponse(BaseModel):
    """Зведена фінансова та операційна аналітика для кабінету адміністратора."""
    total_revenue: float
    total_orders: int
    invoiced_orders_count: int
    average_check: float
    orders_by_status: Dict[str, int]
    top_products: List[TopProductStat] = []
    has_data: bool


class DeleteResponse(BaseModel):
    """Відповідь сервера після успішного видалення сутності."""
    detail: str