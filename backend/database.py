# 1. Що це: Модуль конфігурації підключення до бази даних MariaDB через SQLAlchemy.
# 2. Для чого: Для створення рушія БД, фабрики сесій та керування життєвим циклом транзакцій.
# 3. Призначення: Ініціалізувати з'єднання з базою та надавати функцію get_db() для ізольованих сесій у FastAPI.


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "mysql+pymysql://orders_user:orders_password123@localhost/poshta_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency для отримання сесії БД у FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()