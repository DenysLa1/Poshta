# 1. Що це: Головна точка входу вебсервера та шар контролерів на FastAPI.
# 2. Для чого: Для маршрутизації вхідних HTTP-запитів і координації взаємодії між API та базою даних.
# 3. Призначення: Створювати таблиці на старті та обробляти маршрути каталогу товарів і оформлення замовлень.


from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import engine, get_db, Base
from models import User, Product, Order, OrderItem
from schemas import (
    UserRegister, UserResponse,
    ProductResponse,
    OrderCreate, OrderResponse
)
from security import get_password_hash

# Створення таблиць (якщо ще не створені)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Поштова служба - API", version="1.0.0")


# авторизація та користувачі

@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    # Перевірка унікальності логіна
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Користувач із таким логіном уже існує")

    # Перевірка унікальності пошти (якщо вказана)
    if user_data.email and db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Користувач із таким email уже існує")

    # Перевірка унікальності телефону (якщо вказаний)
    if user_data.phone and db.query(User).filter(User.phone == user_data.phone).first():
        raise HTTPException(status_code=400, detail="Користувач із таким номером телефону уже існує")

    # Створення клієнта з хешованим паролем та роллю "client"
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        phone=user_data.phone,
        password_hash=get_password_hash(user_data.password),
        role="client"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# Товари

@app.get("/products", response_model=List[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).all()


# Замовлення

@app.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    # 1. Перевірка існування користувача
    user = db.query(User).filter(User.id == order_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")

    # Правило - Замовлення можуть оформлювати лише клієнти
    if user.role != "client":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Користувачам із роллю '{user.role}' заборонено оформлювати замовлення. Використовуйте акаунт клієнта."
        )

    # Розрахунок вартості та створення замовлення
    total_price = 0.0
    db_order = Order(user_id=user.id, status="NewOrder", total_price=0.0)
    db.add(db_order)
    db.flush()  # генерує db_order.id

    for item in order_data.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"Товар з id={item.product_id} не знайдено")
        
        total_price += product.price * item.quantity
        order_item = OrderItem(
            order_id=db_order.id,
            product_id=product.id,
            quantity=item.quantity
        )
        db.add(order_item)

    db_order.total_price = round(total_price, 2)
    db.commit()
    db.refresh(db_order)
    return db_order