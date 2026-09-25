# 1. Що це: Модуль опису сутностей бази даних на базі SQLAlchemy ORM.
# 2. Для чого: Для відображення таблиць БД (User, Product, Order, OrderItem) у вигляді Python-класів.
# 3. Призначення: Задати схему таблиць, типи колонок, первинні/зовнішні ключі та зв'язки між сутностями.


from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    role = Column(String(20), nullable=False, default="client") # client або admin

    # Зв'язок 1 до багатьох з Order
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String(255))

    # Зв'язок 1 до багатьох з OrderItem
    order_items = relationship("OrderItem", back_populates="product")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(50), nullable=False, default="NewOrder") # Стартовий статус
    total_price = Column(Float, nullable=False, default=0.0)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Зв'язки
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)

    # Зв'язки
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")