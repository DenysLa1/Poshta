# 1. Що це: Головна точка входу вебсервера та шар контролерів на FastAPI.
# 2. Для чого: Для маршрутизації вхідних HTTP-запитів і координації взаємодії між API та базою даних.
# 3. Призначення: Створювати таблиці на старті та обробляти маршрути каталогу товарів і оформлення замовлень.


from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from database import engine, get_db

# Створення таблиць у БД
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Poshta Order System API",
    description="API для системи замовлень (Спринт 1)",
    version="1.0.0"
)

@app.get("/products", response_model=List[schemas.ProductResponse], tags=["Catalog"])
def get_products(db: Session = Depends(get_db)):
    """
    Отримати список усіх доступних товарів.
    """
    products = db.query(models.Product).all()
    return products


@app.post("/orders", response_model=schemas.OrderResponse, tags=["Orders"])
def create_order(order_data: schemas.OrderCreate, db: Session = Depends(get_db)):
    """
    Оформлення замовлення. Приймає кошик, рахує загальну вартість 
    та створює запис зі статусом 'NewOrder'.
    """
    # 1. Перевірка чи існує користувач
    user = db.query(models.User).filter(models.User.id == order_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Перевірка товарів та підрахунок загальної вартості
    total_price = 0.0
    for item in order_data.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with id {item.product_id} not found")
        
        if item.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be greater than 0")
            
        total_price += product.price * item.quantity

    # 3. Створення замовлення зі стартовим статусом
    new_order = models.Order(
        user_id=order_data.user_id,
        status="NewOrder",
        total_price=total_price
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # 4. Додавання товарів до замовлення (OrderItems)
    for item in order_data.items:
        new_order_item = models.OrderItem(
            order_id=new_order.id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        db.add(new_order_item)
    
    db.commit()
    db.refresh(new_order) # Оновлюємо об'єкт, щоб підтягнути items через relationship

    return new_order