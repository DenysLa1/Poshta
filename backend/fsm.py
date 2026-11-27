# 1. Що це: Модуль реалізації скінченного автомата (FSM) на базі патерну проектування State.
# 2. Для чого: Для інкапсуляції бізнес-правил переходів між статусами замовлення та блокування невалідних операцій.
# 3. Призначення: Керувати життєвим циклом замовлення (NewOrder -> Registered -> Granted -> Shipped -> Invoiced / Cancelled).


from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Type

if TYPE_CHECKING:
    from models import Order


class InvalidStateTransitionError(ValueError):
    """Виняток, що генерується при спробі виконати заборонений правилами FSM перехід."""
    pass


class OrderState(ABC):
    """
    Абстрактний базовий клас стану замовлення (патерн State).
    Визначає інтерфейс методів переходів між етапами обробки замовлення.
    """
    name: str = ""
    label: str = ""

    def __init__(self, order: "Order" = None):
        self.order = order

    @abstractmethod
    def register(self) -> None:
        """Реєстрація нового замовлення у відділенні (перехід до Registered)."""
        pass

    @abstractmethod
    def grant(self) -> None:
        """Погодження зареєстрованого замовлення (перехід до Granted)."""
        pass

    @abstractmethod
    def ship(self) -> None:
        """Відправлення погодженого замовлення (перехід до Shipped)."""
        pass

    @abstractmethod
    def invoice(self) -> None:
        """Виставлення рахунку після відправлення (перехід до Invoiced)."""
        pass

    @abstractmethod
    def cancel(self) -> None:
        """Скасування замовлення (перехід до Cancelled)."""
        pass


class NewOrder(OrderState):
    """Стартовий стан: Нове замовлення (дозволено: Registered, Cancelled)."""
    name = "NewOrder"
    label = "Нове"

    def register(self) -> None:
        self.order.set_state(Registered(self.order))

    def grant(self) -> None:
        raise InvalidStateTransitionError(
            "Порушення черговості кроків: неможливо погодити замовлення зі стану 'Нове' (NewOrder). "
            "Спочатку замовлення необхідно зареєструвати (Registered)."
        )

    def ship(self) -> None:
        raise InvalidStateTransitionError(
            "Порушення черговості кроків: неможливо відправити замовлення зі стану 'Нове' (NewOrder). "
            "Замовлення має послідовно пройти реєстрацію (Registered) та погодження (Granted)."
        )

    def invoice(self) -> None:
        raise InvalidStateTransitionError(
            "Порушення черговості кроків: неможливо виставити рахунок зі стану 'Нове' (NewOrder). "
            "Рахунок виставляється лише після відправлення замовлення (Shipped)."
        )

    def cancel(self) -> None:
        self.order.set_state(Cancelled(self.order))


class Registered(OrderState):
    """Стан: Зареєстроване замовлення (дозволено: Granted, Cancelled)."""
    name = "Registered"
    label = "Зареєстроване"

    def register(self) -> None:
        raise InvalidStateTransitionError(
            "Порушення черговості кроків: замовлення вже перебуває у стані 'Зареєстроване' (Registered). "
            "Наступний крок — погодження (Granted) або скасування (Cancelled)."
        )

    def grant(self) -> None:
        self.order.set_state(Granted(self.order))

    def ship(self) -> None:
        raise InvalidStateTransitionError(
            "Порушення черговості кроків: неможливо відправити замовлення зі стану 'Зареєстроване' (Registered) "
            "без попереднього погодження (Granted)."
        )

    def invoice(self) -> None:
        raise InvalidStateTransitionError(
            "Порушення черговості кроків: неможливо виставити рахунок зі стану 'Зареєстроване' (Registered). "
            "Спочатку замовлення потрібно погодити (Granted) та відправити (Shipped)."
        )

    def cancel(self) -> None:
        self.order.set_state(Cancelled(self.order))


class Granted(OrderState):
    """Стан: Погоджене замовлення (дозволено: Shipped, Cancelled)."""
    name = "Granted"
    label = "Погоджене"

    def register(self) -> None:
        raise InvalidStateTransitionError(
            "Порушення черговості кроків: замовлення вже погоджене (Granted), "
            "повернення до попереднього стану 'Зареєстроване' (Registered) заборонено."
        )

    def grant(self) -> None:
        raise InvalidStateTransitionError(
            "Порушення черговості кроків: замовлення вже перебуває у стані 'Погоджене' (Granted). "
            "Наступний крок — відправлення (Shipped) або скасування (Cancelled)."
        )

    def ship(self) -> None:
        self.order.set_state(Shipped(self.order))

    def invoice(self) -> None:
        raise InvalidStateTransitionError(
            "Порушення черговості кроків: неможливо виставити рахунок зі стану 'Погоджене' (Granted) "
            "до фактичного відправлення замовлення (Shipped)."
        )

    def cancel(self) -> None:
        self.order.set_state(Cancelled(self.order))


class Shipped(OrderState):
    """Стан: Відправлене замовлення (дозволено лише: Invoiced)."""
    name = "Shipped"
    label = "Відправлене"

    def register(self) -> None:
        raise InvalidStateTransitionError(
            "Порушення черговості кроків: замовлення вже відправлене (Shipped), "
            "повернення до стану 'Зареєстроване' (Registered) неможливе."
        )

    def grant(self) -> None:
        raise InvalidStateTransitionError(
            "Порушення черговості кроків: замовлення вже відправлене (Shipped), "
            "повернення до стану 'Погоджене' (Granted) неможливе."
        )

    def ship(self) -> None:
        raise InvalidStateTransitionError(
            "Порушення черговості кроків: замовлення вже перебуває у стані 'Відправлене' (Shipped). "
            "Наступний дозволений крок — виставлення рахунку (Invoiced)."
        )

    def invoice(self) -> None:
        self.order.set_state(Invoiced(self.order))

    def cancel(self) -> None:
        raise InvalidStateTransitionError(
            "Порушення правил FSM: неможливо скасувати замовлення, яке вже відправлене (Shipped)."
        )


class Invoiced(OrderState):
    """Фінальний стан: Рахунок виставлено (будь-які подальші переходи заблоковані)."""
    name = "Invoiced"
    label = "Рахунок виставлено"

    def _raise_final_error(self) -> None:
        raise InvalidStateTransitionError(
            "Замовлення перебуває у фінальному стані 'Рахунок виставлено' (Invoiced). "
            "Будь-які подальші маніпуляції або зміни статусу заблоковані."
        )

    def register(self) -> None:
        self._raise_final_error()

    def grant(self) -> None:
        self._raise_final_error()

    def ship(self) -> None:
        self._raise_final_error()

    def invoice(self) -> None:
        self._raise_final_error()

    def cancel(self) -> None:
        self._raise_final_error()


class Cancelled(OrderState):
    """Фінальний стан: Скасоване замовлення (будь-які подальші переходи заблоковані)."""
    name = "Cancelled"
    label = "Скасоване"

    def _raise_final_error(self) -> None:
        raise InvalidStateTransitionError(
            "Замовлення перебуває у фінальному стані 'Скасоване' (Cancelled). "
            "Будь-які подальші маніпуляції або зміни статусу заблоковані."
        )

    def register(self) -> None:
        self._raise_final_error()

    def grant(self) -> None:
        self._raise_final_error()

    def ship(self) -> None:
        self._raise_final_error()

    def invoice(self) -> None:
        self._raise_final_error()

    def cancel(self) -> None:
        self._raise_final_error()


# Словник відповідності рядкових назв статусів
STATE_CLASSES: Dict[str, Type[OrderState]] = {
    NewOrder.name: NewOrder,
    Registered.name: Registered,
    Granted.name: Granted,
    Shipped.name: Shipped,
    Invoiced.name: Invoiced,
    Cancelled.name: Cancelled,
}


def get_state_for_order(order: "Order") -> OrderState:
    """Фабрична функція для створення екземпляра стану відповідно до текстового поля order.status."""
    status_str = getattr(order, "status", None) or NewOrder.name
    state_cls = STATE_CLASSES.get(status_str)
    if not state_cls:
        raise InvalidStateTransitionError(
            f"Невідомий статус замовлення '{status_str}'. "
            f"Допустимі стани: {', '.join(STATE_CLASSES.keys())}."
        )
    return state_cls(order)
