## Абстрактные классы

*Абстрактные классы* \- это классы, содержащие один или несколько *абстрактных методов*. *Абстрактный метод* \- это метод, который создан, но не содержит *имплементации*, не реализован (в методе нет кода).

От абстрактных классов нельзя напрямую создавать экземпляры. От них можно только наследоваться, и в субклассах необходимо реализовать методы. Давайте, взглянем на следующий пример:

```python
class AbstractClass:
    def do_something(self):
        pass


class NewAbsctractClass(AbstractClass):
    pass


a = AbstractClass()
new_a = NewAbsctractClass()
```

Как мы видим из предыдущего примера, недостатком является то, что *мы можем создать экземпляр* от нашего AbstractClass. А класс NewAbsctractClass не выполнил главное требование абстрактных классов - *реализацию метода* (в данном случае, в классе NewAbsctractClass нужно было реализовать метод do\_something).  
Для того, чтобы применить строгие правила абстрактных классов, можно использовать модуль abc (Abstract Base Class):

```python
from abc import ABC, abstractmethod


class AbstractClassExample(ABC):
    def __init__(self, value):
        self.value = value
        super().__init__()

    @abstractmethod
    def do_something(self):
        pass
```

Теперь попробуем создать субкласс без реализации метода do\_something

```python
class MyAbstractSubClass(AbstractClassExample):
    pass


x = MyAbstractSubClass()
```

При выполнении кода мы получим следующую ошибку:

```python
TypeError: Can't instantiate abstract class MyAbstractSubClass with abstract methods do_something
```

Ошибка вышла потому что субклассы абстрактных классов должны реализовать/переопределить методы абстрактного класса. Теперь, давайте, сделаем все правильно:

```python
from abc import ABC, abstractmethod


class AbstractClassExample(ABC):
    def __init__(self, value):
        self.value = value
        super().__init__()

    @abstractmethod
    def do_something(self):
        pass


class MyAbstractSubClass(AbstractClassExample):
    def do_something(self):
        print('Just doing something')


x = MyAbstractSubClass()
x.do_something()
```

Иногда импортируют весь модуль abc, после чего код выше приобретает следующий вид:

```python
import abc


class AbstractClassExample(abc.ABC):
    def __init__(self, value):
        self.value = value
        super().__init__()

    @abc.abstractmethod
    def do_something(self):
        pass


class MyAbstractSubClass(AbstractClassExample):
    def do_something(self):
        print('Just doing something')


x = MyAbstractSubClass()
x.do_something()
```

Возможно у вас сложилось впечатление, что в абстрактном классе абстрактные методы не могут быть имплементированы. Это не так. Но даже если они реализованы (т.е. написан код метода), программист должен реализовать метод в субклассе. Как при обычном наследовании, абстрактный метод может быть переопределен / дополнен с помощью super(). Это делается, когда есть необходимость в создании поведения по  
умолчанию. Давайте, взглянем на следующий пример:

```python
from abc import ABC, abstractmethod


class AbstractClassExample(ABC):
    @abstractmethod
    def do_something(self):
        print('Some implementation!')


class AnotherSubclass(AbstractClassExample):
    def do_something(self):
        super().do_something()
        print('The enrichment from AnotherSubclass')


x = AnotherSubclass()
x.do_something()
```

При исполнении этого примера кода, вы заметите, что к имеющимся инструкциям в абстрактном классе AbstractClassExample мы добавили дополнительный вывод на экран текста *"The enrichment from AnotherSubclass'"*.
