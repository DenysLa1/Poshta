# 1. Що це: Допоміжний скрипт початкового наповнення бази даних (Database Seeder).
# 2. Для чого: Для автоматичного додавання тестового користувача й базових товарів без ручного введення SQL-запитів.
# 3. Призначення: Забезпечити готові дані для тестування бекенду та верстки фронтенду напарником.


from database import engine, SessionLocal, Base
from models import User, Product
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

        db.commit()
        print("Базу даних успішно оновлено. Створено 4 акаунти різних ролей та каталог товарів.")

    except Exception as e:
        db.rollback()
        print(f"Помилка наповнення бази: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()