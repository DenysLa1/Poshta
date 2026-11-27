# 1. Що це: Головна точка входу вебсервера та шар контролерів на FastAPI.
# 2. Для чого: Для маршрутизації вхідних HTTP-запитів і координації взаємодії між API, FSM та базою даних.
# 3. Призначення: Обробляти авторизацію, RBAC-обмеження, каталог товарів, життєвий цикл замовлень, аналітику та адміністрування.


from fastapi import FastAPI, Depends, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload
from typing import Dict, List, Optional

from database import engine, get_db, Base
from fsm import (
    InvalidStateTransitionError,
    NewOrder,
    Registered,
    Granted,
    Shipped,
    Invoiced,
    Cancelled,
    STATE_CLASSES,
)
from models import User, Product, Order, OrderItem
from schemas import (
    UserRegister,
    UserCreateAdmin,
    UserRoleUpdate,
    UserLogin,
    UserResponse,
    LoginResponse,
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    OrderCreate,
    OrderResponse,
    OrderStatusUpdate,
    TopProductStat,
    StatsResponse,
    DeleteResponse,
)
from security import (
    get_password_hash,
    verify_password,
    create_access_token,
    verify_access_token,
)

# Створення таблиць (якщо ще не створені)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Поштова служба - API", version="3.0.0")

# Налаштування CORS для безперешкодних запитів із портів React-застосунку (Vite / CRA)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security_scheme = HTTPBearer(auto_error=False)


# Глобальна обробка виняткових ситуацій бази даних

@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request: Request, exc: IntegrityError):
    """Перехоплює конфлікти цілісності БД (унікальні поля, зовнішні ключі) та повертає зрозумілий статус 400."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Помилка цілісності даних у базі: перевірте унікальність або зв'язки запису."},
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Перехоплює непередбачувані помилки рівня ORM/БД без витоку внутрішнього стектрейсу."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Внутрішня помилка бази даних сервера. Спробуйте пізніше."},
    )


# Залежності авторизації та перевірки ролей (RBAC)

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Перевіряє Bearer-токен із заголовка Authorization і повертає поточного користувача."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необхідна авторизація: токен доступу відсутній",
        )

    payload = verify_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недійсний або прострочений токен авторизації",
        )

    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Користувача, пов'язаного з токеном, не знайдено",
        )
    return user


def require_roles(*allowed_roles: str):
    """Фабрика залежностей RBAC: дозволяє доступ лише користувачам із вказаними ролями."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Доступ заборонено: операція дозволена лише для ролей "
                    f"{', '.join(allowed_roles)} (ваша роль: '{current_user.role}')."
                ),
            )
        return current_user

    return role_checker


# Авторизація та публічна реєстрація

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
        role="client",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/login", response_model=LoginResponse)
@app.post("/auth/login", response_model=LoginResponse)
def login_user(credentials: UserLogin, db: Session = Depends(get_db)):
    """Автентифікація користувача за логіном і паролем із видачею Bearer-токена."""
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невірний логін або пароль",
        )

    token = create_access_token(user_id=user.id, username=user.username, role=user.role)
    return {"token": token, "user": user}


# Товари та керування номенклатурою

@app.get("/products", response_model=List[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    """Отримання актуального каталогу товарів з цінами (публічний доступ)."""
    return db.query(Product).order_by(Product.id.asc()).all()


@app.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(require_roles("admin", "superadmin")),
    db: Session = Depends(get_db),
):
    """Додавання нового товару до номенклатури (доступно для ролей admin та superadmin)."""
    existing = db.query(Product).filter(Product.name == product_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Товар із назвою '{product_data.name}' уже існує в каталозі",
        )

    new_product = Product(
        name=product_data.name,
        price=round(product_data.price, 2),
        description=product_data.description,
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


@app.put("/products/{product_id}", response_model=ProductResponse)
@app.patch("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    current_user: User = Depends(require_roles("admin", "superadmin")),
    db: Session = Depends(get_db),
):
    """
    Редагування інформації або зміна ціни товару за його ID (підтримує PUT та PATCH).
    Доступно для ролей admin та superadmin.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Товар з id={product_id} не знайдено",
        )

    if product_data.name is not None:
        duplicate = (
            db.query(Product)
            .filter(Product.name == product_data.name, Product.id != product_id)
            .first()
        )
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Товар із назвою '{product_data.name}' уже існує в каталозі",
            )
        product.name = product_data.name

    if product_data.price is not None:
        product.price = round(product_data.price, 2)

    if product_data.description is not None:
        product.description = product_data.description

    db.commit()
    db.refresh(product)
    return product


@app.delete("/products/{product_id}", response_model=DeleteResponse)
def delete_product(
    product_id: int,
    current_user: User = Depends(require_roles("admin", "superadmin")),
    db: Session = Depends(get_db),
):
    """Видалення товару з каталогу (якщо він не використовується в існуючих замовленнях)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Товар з id={product_id} не знайдено",
        )

    in_use = db.query(OrderItem).filter(OrderItem.product_id == product_id).first()
    if in_use:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неможливо видалити товар, який вже фігурує в оформлених замовленнях",
        )

    db.delete(product)
    db.commit()
    return {"detail": f"Товар '{product.name}' успішно видалено", "id": product_id}


# Замовлення та керування життєвим циклом (FSM)

@app.get("/orders", response_model=List[OrderResponse])
def get_orders(
    search: Optional[str] = Query(default=None, description="Пошук за номером замовлення або логіном клієнта"),
    status_filter: Optional[str] = Query(default=None, alias="status", description="Фільтр за статусом замовлення"),
    user_id: Optional[int] = Query(default=None, description="Фільтр за ID клієнта"),
    current_user: User = Depends(require_roles("employee", "admin", "superadmin")),
    db: Session = Depends(get_db),
):
    """
    Вибірка посилок відділення із вкладеними позиціями (доступно для працівників та адмінів).
    Використовує joinedload для усунення проблеми N+1 запитів (S3-BACK-03).
    """
    query = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.product),
        joinedload(Order.user),
    )

    if status_filter:
        query = query.filter(Order.status == status_filter)

    if user_id is not None:
        query = query.filter(Order.user_id == user_id)

    if search and search.strip():
        term = search.strip()
        cleaned_num = term.lstrip("#")
        query = query.join(User, Order.user_id == User.id)
        if cleaned_num.isdigit():
            query = query.filter(
                or_(
                    Order.id == int(cleaned_num),
                    Order.user_id == int(cleaned_num),
                    User.username.ilike(f"%{term}%"),
                )
            )
        else:
            query = query.filter(User.username.ilike(f"%{term}%"))

    return query.order_by(Order.id.asc()).all()


@app.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order_data: OrderCreate,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
):
    # Якщо передано Bearer-токен, перевіряємо, що автор запиту є клієнтом
    if credentials and credentials.credentials:
        payload = verify_access_token(credentials.credentials)
        if not payload or "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недійсний або прострочений токен авторизації",
            )
        caller = db.query(User).filter(User.id == int(payload["sub"])).first()
        if not caller:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Користувача, пов'язаного з токеном, не знайдено",
            )
        if caller.role != "client":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Користувачам із роллю '{caller.role}' заборонено оформлювати замовлення. Використовуйте акаунт клієнта.",
            )

    # 1. Перевірка існування користувача
    user = db.query(User).filter(User.id == order_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")

    # Правило - Замовлення можуть оформлювати лише клієнти
    if user.role != "client":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Користувачам із роллю '{user.role}' заборонено оформлювати замовлення. Використовуйте акаунт клієнта.",
        )

    # Розрахунок вартості та створення замовлення у стартовому стані NewOrder
    total_price = 0.0
    db_order = Order(user_id=user.id, status=NewOrder.name, total_price=0.0)
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
            quantity=item.quantity,
        )
        db.add(order_item)

    db_order.total_price = round(total_price, 2)
    db.commit()

    return (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id == db_order.id)
        .first()
    )


@app.put("/orders/{order_id}/status", response_model=OrderResponse)
@app.patch("/orders/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    current_user: User = Depends(require_roles("employee", "admin", "superadmin")),
    db: Session = Depends(get_db),
):
    """
    Перемикання стану замовлення згідно з правилами скінченного автомата (FSM).
    Доступно лише для ролей employee та admin (і superadmin).
    """
    db_order = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id == order_id)
        .first()
    )
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Замовлення з id={order_id} не знайдено",
        )

    try:
        db_order.transition_to(status_data.status)
    except InvalidStateTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    db.commit()
    db.refresh(db_order)
    return db_order


# Модуль бізнес-аналітики та звітності

@app.get("/stats", response_model=StatsResponse)
def get_statistics(
    current_user: User = Depends(require_roles("admin", "superadmin")),
    db: Session = Depends(get_db),
):
    """
    Розрахунок фінансових та операційних показників відділення:
    - Загальний виторг за завершеними замовленнями (Invoiced);
    - Розподіл відправлень за категоріями статусів FSM;
    - Топ-товари за популярністю замовлень.
    Доступно для ролей admin та superadmin.
    """
    # 1. Загальний виторг та кількість завершених замовлень (Invoiced)
    invoiced_stats = (
        db.query(
            func.coalesce(func.sum(Order.total_price), 0.0).label("revenue"),
            func.count(Order.id).label("invoiced_count"),
        )
        .filter(Order.status == Invoiced.name)
        .first()
    )
    total_revenue = round(float(invoiced_stats.revenue if invoiced_stats else 0.0), 2)
    invoiced_orders_count = int(invoiced_stats.invoiced_count if invoiced_stats else 0)
    average_check = round(total_revenue / invoiced_orders_count, 2) if invoiced_orders_count > 0 else 0.0

    # 2. Агрегація розподілу замовлень за всіма категоріями статусів FSM
    orders_by_status: Dict[str, int] = {status_name: 0 for status_name in STATE_CLASSES.keys()}
    status_rows = (
        db.query(Order.status, func.count(Order.id))
        .group_by(Order.status)
        .all()
    )
    total_orders = 0
    for status_name, count in status_rows:
        count_int = int(count)
        orders_by_status[status_name] = count_int
        total_orders += count_int

    # 3. Вибірка топ-товарів за популярністю (сумарна кількість замовлених одиниць)
    top_products_rows = (
        db.query(
            Product.id.label("product_id"),
            Product.name.label("name"),
            Product.price.label("price"),
            func.coalesce(func.sum(OrderItem.quantity), 0).label("total_quantity"),
            func.count(func.distinct(OrderItem.order_id)).label("orders_count"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .group_by(Product.id, Product.name, Product.price)
        .order_by(func.sum(OrderItem.quantity).desc(), Product.id.asc())
        .limit(5)
        .all()
    )

    top_products = [
        TopProductStat(
            product_id=row.product_id,
            name=row.name,
            price=round(float(row.price), 2),
            total_quantity=int(row.total_quantity),
            orders_count=int(row.orders_count),
            total_amount=round(float(row.price) * int(row.total_quantity), 2),
        )
        for row in top_products_rows
    ]

    return StatsResponse(
        total_revenue=total_revenue,
        total_orders=total_orders,
        invoiced_orders_count=invoiced_orders_count,
        average_check=average_check,
        orders_by_status=orders_by_status,
        top_products=top_products,
        has_data=total_orders > 0,
    )


# Адміністрування користувачів та ролей суперадміном

@app.get("/users", response_model=List[UserResponse])
def get_users(
    role: Optional[str] = Query(default=None, description="Фільтр за роллю користувача"),
    search: Optional[str] = Query(default=None, description="Пошук за логіном, email або телефоном"),
    current_user: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
):
    """Отримання списку всіх користувачів системи з їхніми ролями (лише для superadmin)."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                User.username.ilike(term),
                User.email.ilike(term),
                User.phone.ilike(term),
            )
        )
    return query.order_by(User.id.asc()).all()


@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user_by_superadmin(
    user_data: UserCreateAdmin,
    current_user: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
):
    """Створення службового або клієнтського акаунта із призначенням ролі (лише для superadmin)."""
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Користувач із таким логіном уже існує")

    if user_data.email and db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Користувач із таким email уже існує")

    if user_data.phone and db.query(User).filter(User.phone == user_data.phone).first():
        raise HTTPException(status_code=400, detail="Користувач із таким номером телефону уже існує")

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        phone=user_data.phone,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.patch("/users/{user_id}", response_model=UserResponse)
@app.put("/users/{user_id}", response_model=UserResponse)
@app.patch("/users/{user_id}/role", response_model=UserResponse)
@app.put("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    role_data: UserRoleUpdate,
    current_user: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
):
    """Зміна ролі користувача суперадміном (із захистом від пониження власної ролі суперадміна)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Користувача з id={user_id} не знайдено",
        )

    if user.id == current_user.id and role_data.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Заборонено змінювати або понижувати роль власного акаунта суперадміна",
        )

    user.role = role_data.role
    db.commit()
    db.refresh(user)
    return user


@app.delete("/users/{user_id}", response_model=DeleteResponse)
def delete_user(
    user_id: int,
    current_user: User = Depends(require_roles("superadmin")),
    db: Session = Depends(get_db),
):
    """Видалення користувача із захистом від видалення власного акаунта суперадміна (S3-FRONT-03)."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Заборонено видаляти власний акаунт суперадміна",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Користувача з id={user_id} не знайдено",
        )

    username = user.username
    db.delete(user)
    db.commit()
    return {"detail": f"Користувача '{username}' успішно видалено", "id": user_id}
