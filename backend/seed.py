# 1. Що це: Допоміжний скрипт початкового наповнення бази даних (Database Seeder).
# 2. Для чого: Для автоматичного додавання тестового користувача й базових товарів без ручного введення SQL-запитів.
# 3. Призначення: Забезпечити готові дані для тестування бекенду та верстки фронтенду напарником.


from database import SessionLocal
from models import User, Product

def seed_data():
    db = SessionLocal()
    
    # Перевірка, чи є вже дані, щоб не дублювати
    if db.query(User).first():
        print("База вже містить дані. Сідер зупинено.")
        db.close()
        return

    # 1. Створення тестового клієнта
    test_user = User(username="Andriy_client", role="client")
    db.add(test_user)

    # 2. Створення тестових товарів
    product1 = Product(name="Ноутбук AcerNitro", price=40000.00, description="Робочий ноутбук")
    product2 = Product(name="Мишка VXE", price=1900.50, description="Бездротова мишка")
    product3 = Product(name="Телефон Nothing", price=35000.00, description="Робочий телефон")
    product4 = Product(name="Навушники Anker", price=5000.00, description="Бездротові навушники")
    db.add_all([product1, product2, product3, product4])

    # Сейвінг в БД
    db.commit()
    print("Тестові дані успішно додані!")
    db.close()

if __name__ == "__main__":
    seed_data()