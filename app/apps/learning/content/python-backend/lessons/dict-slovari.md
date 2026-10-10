Словарь — неупорядоченная структура данных, которая позволяет хранить пары «ключ — значение».

```python
# Создание словаря c помощью литерала

student = {'name': 'Ivan', 'age': 12}
credentials = {'email': 'hacker1337@mail.ru', 'password': '123456'}

# Создание словаря c помощью функции dict()

student = dict(name='Ivan', age=12)
credentials = dict(email='hacker1337@mail.ru', password='123456')
```

Для получения значения конкретного ключа используются квадратные скобки \[\].

```python
# Получаем значение с ключом 'name'

student = dict(name='Ivan', age=12)
print(student['name']) # -> Ivan
```

Обновление существующих значений происходит абсолютно также.

```python
# Получаем значение с ключом 'name'

student = dict(name='Ivan', age=12)
student['name'] = 'Vasya'

print(student['name']) # -> Vasya
```

Для удаления ключа и соответствующего значения из словаря можно использовать del

```python
# Удаление ключа 'age'

student = dict(name='Ivan', age=12)
del student['age']

print(student) # -> {'name': 'Ivan'}
```

Метод get() возвращает значение по указанному ключу. Если указанного ключа не существует, метод вернёт None. Также можно указать значение по умолчанию, которое будет возвращено вместо None, если ключа в словаре не окажется.

```python
# Использование метода get()

student = dict(name='Ivan', age=12)

print(student.get('name'))     # -> Ivan
print(student.get('lastname')) # -> None
print(student.get('lastname', 'No key')) # -> No key
```

Метод pop() удаляет ключ и возвращает соответствующее ему значение.

```python
# Использование метода pop()

sneakers = dict(brand='Adidas', price='9990 RUB', model='Nite Jogger')

model = sneakers.pop('model')

print(sneakers) # -> {'brand': 'Adidas', 'price': '9990 RUB'}
print(model)    # -> Nite Jogger
```

Метод keys() возвращает специальную коллекцию ключей в словаре.

```python
# Использование метода keys()

sneakers = dict(brand='Adidas', price='9990 RUB', model='Nite Jogger')

print(sneakers.keys()) # -> dict_keys(['brand', 'price', 'model'])

# dict_keys - это неизменяемая коллекция элементов.

keys = list(sneakers.keys())
print(keys) # -> ['brand', 'price', 'model']
```

Метод values() возвращает специальную коллекцию значений в словаре.

```python
# Использование метода values()

sneakers = dict(brand='Adidas', price='9990 RUB', model='Nite Jogger')

print(sneakers.values()) # -> dict_values(['Adidas', '9990 RUB', 'Nite Jogger'])

# dict_values - это неизменяемая коллекция элементов.

values = list(sneakers.values())
print(values) # -> ['Adidas', '9990 RUB', 'Nite Jogger']
```

Метод items() возвращает пары «ключ — значение» в формате кортежей.

```python
# Использование метода items()

sneakers = dict(brand='Adidas', price='9990 RUB', model='Nite Jogger')

print(sneakers.items()) # -> dict_items([('brand', 'Adidas'), ('price', '9990 RUB'), ('model', 'Nite Jogger')])

# dict_items - это неизменяемая коллекция элементов.

items = list(sneakers.items())
print(items) # -> [('brand', 'Adidas'), ('price', '9990 RUB'), ('model', 'Nite Jogger')]
```

```python
sneakers = dict(brand='Adidas', price='9990 RUB', model='Nite Jogger')

# Вывод ключей словаря с помощью цикла for

for key in sneakers:
    print(key)

# -> brand
# -> price
# -> model

# Вывод значений словаря с помощью цикла for

for value in sneakers.values():
    print(value)

# -> Adidas
# -> 9990 RUB
# -> Nite Jogger

# Вывод ключей и значений словаря с помощью цикла for

for key, value in sneakers.items():
    print(key, value)

# -> brand Adidas
# -> price 9990 RUB
# -> model Nite Jogger
```

Метод setdefault() возвращает значение ключа, но если его нет, создает ключ с указанным значением (по умолчанию None).

```python
# Метод setdefault()

student = dict(name='Ivan', age=12)
student.setdefault('lastname', 'Ivanov')

print(student) # -> {'name': 'Ivan', 'age': 12, 'lastname': 'Ivanov'}
```
