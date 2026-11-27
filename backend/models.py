# 1. Що це: Модуль опису сутностей бази даних на базі SQLAlchemy ORM.
# 2. Для чого: Для відображення таблиць БД (User, Product, Order, OrderItem) у вигляді Python-класів.
# 3. Призначення: Задати схему таблиць, типи колонок, первинні/зовнішні ключі та зв'язки між сутностями.


from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text
from sqlalchemy.orm import relationship, reconstructor
from database import Base
from fsm import (
    OrderState,
    NewOrder,
    Registered,
    Granted,
    Shipped,
    Invoiced,
    Cancelled,
    InvalidStateTransitionError,
    get_state_for_order,
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    phone = Column(String(20), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="client", nullable=False)  # 'client', 'employee', 'admin', 'superadmin'

    # Зв'язок із замовленнями
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    description = Column(Text, nullable=True)

    order_items = relationship("OrderItem", back_populates="product")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(50), default="NewOrder", nullable=False)
    total_price = Column(Float, default=0.0, nullable=False)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        if "status" not in kwargs or not kwargs["status"]:
            kwargs["status"] = NewOrder.name
        super().__init__(**kwargs)
        self._state: OrderState = get_state_for_order(self)

    @reconstructor
    def _init_on_load(self) -> None:
        """Відновлює об'єкт стану FSM під час завантаження запису з бази даних SQLAlchemy."""
        self._state = get_state_for_order(self)

    @property
    def state(self) -> OrderState:
        """Повертає актуальний екземпляр стану FSM, синхронізований із текстовим полем status."""
        if not hasattr(self, "_state") or self._state is None or self._state.name != self.status:
            self._state = get_state_for_order(self)
        return self._state

    def set_state(self, new_state: OrderState) -> None:
        """Змінює стан об'єкта FSM та автоматично синхронізує текстове поле status у моделі БД."""
        new_state.order = self
        self._state = new_state
        self.status = new_state.name

    # Делегування викликів переходів поточному стану FSM
    def register(self) -> None:
        """Перевести замовлення у стан Registered (Зареєстроване)."""
        self.state.register()

    def grant(self) -> None:
        """Перевести замовлення у стан Granted (Погоджене)."""
        self.state.grant()

    def ship(self) -> None:
        """Перевести замовлення у стан Shipped (Відправлене)."""
        self.state.ship()

    def invoice(self) -> None:
        """Перевести замовлення у стан Invoiced (Рахунок виставлено)."""
        self.state.invoice()

    def cancel(self) -> None:
        """Перевести замовлення у стан Cancelled (Скасоване)."""
        self.state.cancel()

    def transition_to(self, target_status: str) -> None:
        """Виконує перехід до цільового статусу через відповідний делегований метод FSM."""
        actions = {
            Registered.name: self.register,
            Granted.name: self.grant,
            Shipped.name: self.ship,
            Invoiced.name: self.invoice,
            Cancelled.name: self.cancel,
        }
        if target_status in actions:
            actions[target_status]()
        elif target_status == NewOrder.name:
            if self.status in (Invoiced.name, Cancelled.name):
                self.cancel()
            raise InvalidStateTransitionError(
                f"Порушення черговості кроків: неможливо повернути замовлення зі стану "
                f"'{self.status}' у початковий стан 'NewOrder'."
            )
        else:
            raise InvalidStateTransitionError(
                f"Невідомий статус '{target_status}'. Дозволені цільові статуси: "
                f"Registered, Granted, Shipped, Invoiced, Cancelled."
            )


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")