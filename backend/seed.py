# 1. Що це: Допоміжний скрипт початкового наповнення бази даних (Database Seeder).
# 2. Для чого: Для автоматичного додавання тестового користувача й базових товарів без ручного введення SQL-запитів.
# 3. Призначення: Забезпечити готові дані для тестування бекенду та верстки фронтенду напарником.


from database import engine, SessionLocal, Base
from fsm import NewOrder, Registered, Granted, Shipped, Invoiced
from models import User, Product, Order, OrderItem
from security import get_password_hash

def seed_database():
    # Очищення та перестворення таблиць з новою структурою колонок
    print("Перестворення таблиць у poshta_db...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Додавання тест акаунтів під усі 4 ролі
        users = [
            User(
                username="client_andriy",
                phone="+380501112233",
                email=None,
                password_hash=get_password_hash("client123"),
                role="client"
            ),
            User(
                username="worker_pavlo",
                phone=None,
                email="pavlo@poshta.ua",
                password_hash=get_password_hash("worker123"),
                role="employee"
            ),
            User(
                username="admin_denys",
                phone="+380674445566",
                email="admin@poshta.ua",
                password_hash=get_password_hash("admin123"),
                role="admin"
            ),
            User(
                username="superadmin_root",
                phone="+380990000000",
                email="root@poshta.ua",
                password_hash=get_password_hash("root123"),
                role="superadmin"
            ),
        ]
        db.add_all(users)

        # Додавання товарів для каталогу
        products = [
            Product(name="Ігровий монітор 24.5' 165Hz", price=6200.0, description="IPS панель, 1ms, DisplayPort/HDMI"),
            Product(name="Бездротові навушники Bluetooth", price=1850.0, description="Підтримка AAC/SBC, автономність до 50 годин"),
            Product(name="Механічна клавіатура TKL", price=2400.0, description="Червоні лінійні світчі, RGB-підсвічування"),
            Product(name="USB-C Hub 8-in-1", price=1100.0, description="HDMI 4K, 3x USB 3.0, Gigabit Ethernet"),
        ]
        db.add_all(products)
        db.flush()

        # Додавання тестових замовлень у різних станах FSM для перевірки черги та фінансової статистики (/stats)
        client_user = users[0]
        order1 = Order(
            user_id=client_user.id,
            status=NewOrder.name,
            total_price=round(products[0].price * 1 + products[1].price * 2, 2),
        )
        order2 = Order(
            user_id=client_user.id,
            status=Registered.name,
            total_price=round(products[2].price * 1 + products[3].price * 1, 2),
        )
        order3 = Order(
            user_id=client_user.id,
            status=Invoiced.name,
            total_price=round(products[0].price * 1 + products[2].price * 1, 2),
        )
        order4 = Order(
            user_id=client_user.id,
            status=Shipped.name,
            total_price=round(products[1].price * 1 + products[3].price * 2, 2),
        )
        db.add_all([order1, order2, order3, order4])
        db.flush()

        order_items = [
            OrderItem(order_id=order1.id, product_id=products[0].id, quantity=1),
            OrderItem(order_id=order1.id, product_id=products[1].id, quantity=2),
            OrderItem(order_id=order2.id, product_id=products[2].id, quantity=1),
            OrderItem(order_id=order2.id, product_id=products[3].id, quantity=1),
            OrderItem(order_id=order3.id, product_id=products[0].id, quantity=1),
            OrderItem(order_id=order3.id, product_id=products[2].id, quantity=1),
            OrderItem(order_id=order4.id, product_id=products[1].id, quantity=1),
            OrderItem(order_id=order4.id, product_id=products[3].id, quantity=2),
        ]
        db.add_all(order_items)

        db.commit()
        print(
            "Базу даних успішно оновлено. Створено 4 акаунти різних ролей "
            "(client_andriy, worker_pavlo, admin_denys, superadmin_root), "
            "каталог товарів та тестові замовлення (включно з Invoiced для /stats)."
        )

    except Exception as e:
        db.rollback()
        print(f"Помилка наповнення бази: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()