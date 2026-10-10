Миксины - это классы, которые ничем не отличаются от обычных. Их главная особенность заключается в том, что они не предназначены для создания экземпляров напрямую. Их основная цель - создать переиспользуемый инструмент, который будет использоваться субклассами для расширения их функционала.

Рассмотрим следующий пример:

```python
class CraneMixin:
    def lift(self, thing):
        return '{} is lifted'.format(thing)


class Transport:
    def go(self):
        return 'Whoom'

    def carry_goods(self):
        return 'Carrying goods'


class Car(Transport):
    def carry_passengers(self):
        return 'Carrying passengers'


class TruckWithCrane(Transport, CraneMixin):
    def carry_things(self):
        return 'Carrying things'


class MotorBoatWithCrane(Transport, CraneMixin):
    def dock(self):
        return 'Stopped and docked'
```

В данном примере я создал миксин CraneMixin, который самостоятельно не несет какой-либо ценности, но при этом расширяет функциональные возможости субклассов TruckWithCrane, MotorBoatWithCrane. Использовать слово Mixin в названии не обязательно, но является хорошей практикой, подсказывая разработчику о том, что данный класс обладает дополнительным функционалом.
