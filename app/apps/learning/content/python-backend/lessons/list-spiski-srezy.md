Список Python — это последовательность значений любого типа: строки, числа, числа с плавающей точкой или даже смешанного типа. В этом материале речь пойдет о функциях списков, о том, как создавать их, добавлять элементы, представлять в обратном порядке и многих других.

### Создать списки Python

Для создания списка Python нужно заключить элементы в квадратные скобки:

<aside class="callout" data-icon="💡" markdown="1">

my\_list = \[1, 2, 3, 4, 5\]

</aside>

Список может выглядеть так:

<aside class="callout" data-icon="💡" markdown="1">

my\_list = \['один', 'два', 'три', 'четыре', 'пять'\]

</aside>

Можно смешивать типы содержимого:

<aside class="callout" data-icon="💡" markdown="1">

my\_list = \['один', 10, 2.25, \[5, 15\], 'пять'\]

</aside>

Поддерживаются вложенные списки как в примере выше.

Получать доступ к любому элементу списка можно через его индекс. В Python используется система индексации, начиная с нуля.

<aside class="callout" data-icon="💡" markdown="1">

third\_elem  =  my\_list\[2\]

</aside>

Принцип похож на строки.

### Изменение списка

Списки — это изменяемые объекты, поэтому их элементы могут изменяться, или же может меняться их порядок.

Если есть такой список:

<aside class="callout" data-icon="💡" markdown="1">

my\_list = \['один', 'два', 'три', 'четыре', 'пять'\]

</aside>

То его третий элемент можно изменить следующим образом:

<aside class="callout" data-icon="💡" markdown="1">

my\_list\[2\]  =  'ноль'

</aside>

Если сейчас вывести его на экран, то он будет выглядеть вот так:

<aside class="callout" data-icon="💡" markdown="1">

\['один', 'два', 'ноль', 'четыре', 'пять'\]

</aside>

Если индекс — отрицательное число, то он будет считаться с последнего элемента.

<aside class="callout" data-icon="💡" markdown="1">

my\_list = \['один', 'два', 'три', 'четыре', 'пять'\]  
elem  =  my\_list\[-1\]  
print(elem)

</aside>

Вывод этого кода — ‘пять’.

### Проход (итерация) по списку

Читать элементы списка можно с помощью следующего цикла:

<aside class="callout" data-icon="💡" markdown="1">

my\_list = \['один', 'два', 'три', 'четыре', 'пять'\]  
for elem in my\_list:  
    print(elem)

</aside>

Таким образом можно читать элементы списка. А вот что касается их обновления:

<aside class="callout" data-icon="💡" markdown="1">

my\_list = \[1, 2, 3, 4, 5\]  
for i in range(len(my\_list)):  
    my\_list\[i\]+=5  
    print(my\_list)

</aside>

Результат будет следующим:

<aside class="callout" data-icon="💡" markdown="1">

\[6, 7, 8, 9, 10\]

</aside>

Функция `len()` используется для возврата количества элементов, а `range()` — списка индексов.

Стоит запомнить, что вложенный список — это всегда один элемент вне зависимости от количества его элементов.

<aside class="callout" data-icon="💡" markdown="1">

my\_list = \['один', 10, 2.25, \[5, 15\], 'пять'\]  
print(len(my\_list))

</aside>

Результат кода выше — 5.

### Срез списка

Можно получить срез списка с помощью оператора (:):

<aside class="callout" data-icon="💡" markdown="1">

my\_list = \['один', 'два', 'три', 'четыре', 'пять'\]  
print(my\_list\[1:3\])

</aside>

Результат кода выше — `['два', 'три']`

Если убрать первое число, от срез будет начинаться с первого элемента, а если второе — с последнего.

Если убрать числа и оставить только двоеточие, то скопируется весь список.

<aside class="callout" data-icon="💡" markdown="1">

my\_list = \['один', 'два', 'три', 'четыре', 'пять'\]  
print(my\_list\[1:3\])  
print(my\_list\[1:\])  
print(my\_list\[:3\])  
print(my\_list\[:\])

</aside>

Результат этого года:

<aside class="callout" data-icon="💡" markdown="1">

\['два', 'три'\]  
\['два', 'три', 'четыре', 'пять'\]  
\['один', 'два', 'три'\]  
\['один', 'два', 'три', 'четыре', 'пять'\]

</aside>

Поскольку списки изменяемые, менять элементы можно с помощью оператора среза:

<aside class="callout" data-icon="💡" markdown="1">

my\_list = \['один', 'два', 'три', 'четыре', 'пять'\]  
my\_list\[1:3\]  =  \['Привет',  'Мир'\]  
print(my\_list)

</aside>

Результат:

<aside class="callout" data-icon="💡" markdown="1">

\['один', 'Привет', 'Мир', 'четыре', 'пять'\]

</aside>

### Вставить в список

Метод insert можно использовать, чтобы вставить элемент в список:

<aside class="callout" data-icon="💡" markdown="1">

my\_list = \[1, 2, 3, 4, 5\]  
my\_list.insert(1,'Привет')  
print(my\_list)

</aside>

Результат:

<aside class="callout" data-icon="💡" markdown="1">

\[1, 'Привет', 2, 3, 4, 5\]

</aside>

Индексы для вставляемых элементов также начинаются с нуля.

### Добавить в список

Метод append можно использовать для добавления элемента в список:

<aside class="callout" data-icon="💡" markdown="1">

my\_list = \['один', 'два', 'три', 'четыре', 'пять'\]  
my\_list.append('ещё один')  
print(my\_list)

</aside>

Результат:

<aside class="callout" data-icon="💡" markdown="1">

\['один', 'два', 'три', 'четыре', 'пять', 'ещё один'\]

</aside>

Можно добавить и больше одного элемента таким способом:

<aside class="callout" data-icon="💡" markdown="1">

my\_list = \['один', 'два', 'три', 'четыре', 'пять'\]  
list\_2  =  \['шесть',  'семь'\]  
my\_list.extend(list\_2)  
print(my\_list)

</aside>

Результат:

<aside class="callout" data-icon="💡" markdown="1">

\['один', 'два', 'три', 'четыре', 'пять', 'шесть',  'семь'\]

</aside>

При этом list\_2 не поменяется.

### Отсортировать список

Для сортировки списка нужно использовать метод sort.

<aside class="callout" data-icon="💡" markdown="1">

my\_list = \['cde', 'fgh', 'abc', 'klm', 'opq'\]  
list\_2 = \[3, 5, 2, 4, 1\]  
my\_list.sort()  
list\_2.sort()  
print(my\_list)  
print(list\_2)

</aside>

Вывод:

<aside class="callout" data-icon="💡" markdown="1">

\['abc', 'cde', 'fgh', 'klm', 'opq'\]  
\[1, 2, 3, 4, 5\]

</aside>

## **Перевернуть список**

Можно развернуть порядок элементов в списке с помощью метода `reverse`:

```python
my_list = [1, 2, 3, 4, 5]
my_list.reverse()
print(my_list)
```

Результат:

```text
[5, 4, 3, 2, 1]
```

## **Индекс элемента**

Метод `index` можно использовать для получения индекса элемента:

```python
my_list = ['один', 'два', 'три', 'четыре', 'пять']
print(my_list.index('два'))
```

Результат `1`.

Если в списке больше одного такого же элемента, [**функция вернет**](https://pythonru.com/osnovy/funkcii-v-python) индекс первого.

## **Удалить элемент**

Удалить элемент можно, написав его индекс в методе `pop`:

```python
my_list = ['один', 'два', 'три', 'четыре', 'пять']
removed = my_list.pop(2)
print(my_list)
print(removed)
```

Результат:

```text
['один', 'два', 'четыре', 'пять']
три
```

Если не указывать индекс, то функция удалит последний элемент.

```python
my_list = ['один', 'два', 'три', 'четыре', 'пять']
removed = my_list.pop()
print(my_list)
print(removed)
```

Результат:

```python
['один', 'два', 'три', 'четыре']
пять
```

Элемент можно удалить с помощью метода `remove`.

```python
my_list = ['один', 'два', 'три', 'четыре', 'пять']
my_list.remove('два')
print(my_list)
```

Результат:

```text
['один', 'три', 'четыре', 'пять']
```

Оператор `del` можно использовать для тех же целей:

```python
my_list = ['один', 'два', 'три', 'четыре', 'пять']
del my_list[2]
print(my_list)
```

Результат:

```text
['один', 'два', 'четыре', 'пять']
```

Можно удалить несколько элементов с помощью оператора среза:

```python
my_list = ['один', 'два', 'три', 'четыре', 'пять']
del my_list[1:3]
print(my_list)
```

Результат:

```text
['один', 'четыре', 'пять']
```

### Операция in

С помощью in мы можем проверить наличие элемента в списке, строке и любой другой итерируемой переменной.

```python
fruits = ['Apple', 'Grape', 'Peach', 'Banan', 'Orange']
if 'Apple' in fruits:
    print('В списке есть элемент Apple')
```

<aside class="callout" data-icon="💡" markdown="1">

\>>> В списке есть элемент Apple

</aside>

```python
fruits = ['Apple', 'Grape', 'Peach', 'Banan', 'Orange']
if 'Lemon' in fruits:
    print('В списке есть элемент Lemon')
else:'
    print('В списке НЕТ элемента Lemon')
```

<aside class="callout" data-icon="💡" markdown="1">

\>>> В списке НЕТ элемента Lemon

</aside>

Приведу более сложный пример:

```python
all_fruits = ['Apple', 'Grape', 'Peach', 'Banan', 'Orange']
my_favorite_fruits = ['Apple', 'Banan', 'Orange']
for item in all_fruits:
    if item in my_favorite_fruits:
        print(item + ' is my favorite fruit')
    else:
        print('I do not like ' + item)
```

<aside class="callout" data-icon="💡" markdown="1">

\>>> Apple is my favorite fruit  
\>>> I do not like Grape  
\>>> I do not like Peach  
\>>> Banan is my favorite fruit  
\>>> Orange is my favorite fruit

</aside>

## Методы для работы со списками

### **Таблица "методы списков"**

| Что делает | Метод |
| --- | --- |
| Добавляет элемент в конец списка | **list.append**(x) |
| Расширяет список list, добавляя в конец все элементы списка L | **list.extend**(L) |
| Вставляет на i-ый элемент значение x | **list.insert**(i, x) |
| Удаляет первый элемент в списке, имеющий значение x. ValueError, если такого элемента не существует | **list.remove**(x) |
| Удаляет i-ый элемент и возвращает его. Если индекс не указан, удаляется последний элемент | **list.pop**(\[i\]) |
| Возвращает положение первого элемента со значением x (при этом поиск ведется от start до end) | **list.index**(x, \[start \[, end\]\]) |
| Возвращает количество элементов со значением x | **list.count**(x) |
| Сортирует список на основе функции | **list.sort**(\[key=функция\]) |
| Разворачивает список | **list.reverse**() |
| Поверхностная копия списка | **list.copy**() |
| Очищает список | **list.clear**() |

Начнем с метода append(), который добавляет элемент в конец списка:

```python
# Создаем список, состоящий из четных чисел от 0 до 8 включительно
numbers = list(range(0,10,2))
# Добавляем число 200 в конец списка
numbers.append(200)
numbers.append(1)
numbers.append(2)
numbers.append(3)
print(numbers)
```

<aside class="callout" data-icon="💡" markdown="1">

\>>> \[0, 2, 4, 6, 8, 200, 1, 2, 3\]

</aside>

Мы можем передавать методу append() абсолютно любые значения:

```python
all_types = [10, 3.14, 'Python', ['I', 'am', 'list']]
all_types.append(1024)
all_types.append('Hello world!')
all_types.append([1, 2, 3])
print(all_types)
```

<aside class="callout" data-icon="💡" markdown="1">

\>>> \[10, 3.14, 'Python', \['I', 'am', 'list'\], 1024, 'Hello world!', \[1, 2, 3\]\]

</aside>

Метод append() отлично выполняет свою функцию. Но, что делать, если нам нужно добавить элемент в середину списка? Это умеет метод insert(). Он добавляет элемент в список на произвольную позицию. insert() принимает в качестве первого аргумента позицию, на которую нужно вставить элемент, а вторым — сам элемент.

```python
# Создадим список чисел от 0 до 9
numbers = list(range(10))
# Добавление элемента 999 на позицию с индексом 0
numbers.insert(0, 999)
print(numbers) # первый print
numbers.insert(2, 1024)
print(numbers) # второй print
numbers.insert(5, 'Засланная строка-шпион')
print(numbers) # третий print
```

<aside class="callout" data-icon="💡" markdown="1">

\>>> \[999, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9\] # первый print  
\>>> \[999, 0, 1024, 1, 2, 3, 4, 5, 6, 7, 8, 9\] # второй print  
\>>> \[999, 0, 1024, 1, 2, 'Засланная строка-шпион', 3, 4, 5, 6, 7, 8, 9\] # третий print

</aside>

Отлично! Добавлять элементы в список мы научились, осталось понять, как их из него удалять. Метод pop() удаляет элемент из списка по его индексу:

```python
numbers = list(range(10))
print(numbers) # 1
# Удаляем первый элемент
numbers.pop(0)
print(numbers) # 2
numbers.pop(0)
print(numbers) # 3
numbers.pop(2)
print(numbers) # 4
# Чтобы удалить последний элемент, вызовем метод pop без аргументов
numbers.pop()
print(numbers) # 5
numbers.pop()
print(numbers) # 6
```

<aside class="callout" data-icon="💡" markdown="1">

\>>> \[0, 1, 2, 3, 4, 5, 6, 7, 8, 9\] # 1  
\>>> \[1, 2, 3, 4, 5, 6, 7, 8, 9\] # 2  
\>>> \[2, 3, 4, 5, 6, 7, 8, 9\] # 3  
\>>> \[2, 3, 5, 6, 7, 8, 9\] # 4  
\>>> \[2, 3, 5, 6, 7, 8\] # 5  
\>>> \[2, 3, 5, 6, 7\] # 6

</aside>

Теперь мы знаем, как удалять элемент из списка по его индексу. Но что, если мы не знаем индекса элемента, но знаем его значение? Для такого случая у нас есть метод remove(), который удаляет первый найденный по значению элемент в списке.

```python
all_types = [10, 'Python', 10, 3.14, 'Python', ['I', 'am', 'list']]
all_types.remove(3.14)
print(all_types) # 1
all_types.remove(10)
print(all_types) # 2
all_types.remove('Python')
print(all_types) # 3
```

<aside class="callout" data-icon="💡" markdown="1">

\>>> \[10, 'Python', 10, 'Python', \['I', 'am', 'list'\]\] # 1  
\>>> \['Python', 10, 'Python', \['I', 'am', 'list'\]\] # 2  
\>>> \[10, 'Python', \['I', 'am', 'list'\]\] # 3

</aside>

А сейчас немного посчитаем, посчитаем элементы списка с помощью метода count()

```python
numbers = [100, 100, 100, 200, 200, 500, 500, 500, 500, 500, 999]
print(numbers.count(100)) # 1
print(numbers.count(200)) # 2
print(numbers.count(500)) # 3
print(numbers.count(999)) # 4
```

<aside class="callout" data-icon="💡" markdown="1">

\>>> 3 # 1  
\>>> 2 # 2  
\>>> 5 # 3  
\>>> 1 # 4

</aside>

В программировании, как и в жизни, проще работать с упорядоченными данными, в них легче ориентироваться и что-либо искать. Метод sort() сортирует список по возрастанию значений его элементов.

```python
numbers = [100, 2, 11, 9, 3, 1024, 567, 78]
numbers.sort()
print(numbers) # 1
fruits = ['Orange', 'Grape', 'Peach', 'Banan', 'Apple']
fruits.sort()
print(fruits) # 2
```

<aside class="callout" data-icon="💡" markdown="1">

\>>> \[2, 3, 9, 11, 78, 100, 567, 1024\] # 1  
\>>> \['Apple', 'Banan', 'Grape', 'Orange', 'Peach'\] # 2

</aside>

Мы можем изменять порядок сортировки с помощью параметра reverse. По умолчанию этот параметр равен False

```python
fruits = ['Orange', 'Grape', 'Peach', 'Banan', 'Apple']
fruits.sort()
print(fruits) # 1
fruits.sort(reverse=True)
print(fruits) # 2
```

<aside class="callout" data-icon="💡" markdown="1">

\>>> \['Apple', 'Banan', 'Grape', 'Orange', 'Peach'\] # 1  
\>>> \['Peach', 'Orange', 'Grape', 'Banan', 'Apple'\] # 2

</aside>

Иногда нам нужно перевернуть список, не спрашивайте меня зачем... Для этого в самом лучшем языке программирования на этой планете JavaScr..Python есть метод reverse():

```python
numbers = [100, 2, 11, 9, 3, 1024, 567, 78]
numbers.reverse()
print(numbers) # 1
fruits = ['Orange', 'Grape', 'Peach', 'Banan', 'Apple']
fruits.reverse()
print(fruits) # 2
```

<aside class="callout" data-icon="💡" markdown="1">

\>>> \[78, 567, 1024, 3, 9, 11, 2, 100\] # 1  
\>>> \['Apple', 'Banan', 'Peach', 'Grape', 'Orange'\] # 2

</aside>

Допустим, у нас есть два списка и нам нужно их объединить. Программисты на C++ cразу же кинулись писать циклы for, но мы пишем на python, а в python у списков есть полезный метод extend(). Этот метод вызывается для одного списка, а в качестве аргумента ему передается другой список, extend() записывает в конец первого из них начало второго:

```python
fruits = ['Banana', 'Apple', 'Grape']
vegetables = ['Tomato', 'Cucumber', 'Potato', 'Carrot']
fruits.extend(vegetables)
print(fruits)
```

<aside class="callout" data-icon="💡" markdown="1">

\>>> \['Banana', 'Apple', 'Grape', 'Tomato', 'Cucumber', 'Potato', 'Carrot'\]

</aside>

В природе существует специальный метод для очистки списка — clear()

```python
fruits = ['Banana', 'Apple', 'Grape']
vegetables = ['Tomato', 'Cucumber', 'Potato', 'Carrot']
fruits.clear()
vegetables.clear()
print(fruits)
print(vegetables)
```

<aside class="callout" data-icon="💡" markdown="1">

\>>> \[\]  
\>>> \[\]

</aside>

Осталось совсем чуть-чуть всего лишь пара методов, так что делаем последний рывок! Метод index() возвращает индекс элемента. Работает это так: вы передаете в качестве аргумента в index() значение элемента, а метод возвращает его индекс:

```python
fruits = ['Banana', 'Apple', 'Grape']
print(fruits.index('Apple'))
print(fruits.index('Banana'))
print(fruits.index('Grape'))
```

<aside class="callout" data-icon="💡" markdown="1">

\>>> 1  
\>>> 0  
\>>> 2

</aside>

Финишная прямая! Метод copy(), только не падайте, копирует список и возвра­щает его брата-близнеца. Вообще, копи­ро­вание списков - это тема доста­точно инте­ресная, давай­те рас­смотрим её по-подробнее.

Во-первых, если мы просто прис­воим уже сущест­вующий список новой пере­менной, то на первый взгляд всё выглядит неплохо:

```python
fruits = ['Banana', 'Apple', 'Grape']
new_fruits = fruits
print(fruits)
print(new_fruits)
```

<aside class="callout" data-icon="💡" markdown="1">

\>>> \['Banana', 'Apple', 'Grape'\]  
\>>> \['Banana', 'Apple', 'Grape'\]

</aside>

Но есть одно маленькое "НО":

```python
fruits = ['Banana', 'Apple', 'Grape']
new_fruits = fruits
fruits.pop()
print(fruits)
print(new_fruits)

# Внезапно, из списка new_fruits исчез последний элемент
>>> ['Banana', 'Apple']
>>> ['Banana', 'Apple']
```

При прямом присваивании списков копирования не происходит. Обе переменные начинают ссылаться на один и тот же список! То есть если мы изменим один из них, то изменится и другой. Что же тогда делать? Пользоваться методом copy(), конечно:

```python
fruits = ['Banana', 'Apple', 'Grape']
new_fruits = fruits.copy()
fruits.pop()
print(fruits)
print(new_fruits)

>>> ['Banana', 'Apple']
>>> ['Banana', 'Apple', 'Grape']
```

Отлично! Но что если у нас список в списке? Скопируется ли внутренний список с помощью метода copy() — нет:

```python
fruits = ['Banana', 'Apple', 'Grape', ['Orange','Peach']]
new_fruits = fruits.copy()
fruits[-1].pop()
print(fruits) # 1
print(new_fruits) # 2

>>> ['Banana', 'Apple', 'Grape', ['Orange']] # 1
>>> ['Banana', 'Apple', 'Grape', ['Orange']] # 2
```

## **Функции агрегации**

В Python есть некоторые агрегатные функции:

```python
my_list = [5, 3, 2, 4, 1]
print(len(my_list))
print(min(my_list))
print(max(my_list))
print(sum(my_list))
```

`sum()` работает только с числовыми значениями.

А `max()`, `len()` и другие можно использовать и со строками.

## **Сравнить списки**

В Python 2 сравнить элементы двух списком можно с помощью функции `cmp`:

```python
my_list = ['один', 'два', 'три', 'четыре', 'пять']
list_2 = ['три', 'один', 'пять', 'два', 'четыре']
print(cmp(my_list,list_2))
```

Она вернет `-1`, если списки не совпадают, и `1` в противном случае.

В Python 3 для этого используется оператор (`==`):

```python
my_list = ['один', 'два', 'три', 'четыре', 'пять']
list_2 = ['три', 'один', 'пять', 'два', 'четыре']
if (my_list == list_2):
    print('cовпадают')
else:
    print('не совпадают')
```

Результат `не совпадают`.

## **Математические операции на списках:**

Для объединения списков можно использовать [**оператор**](https://pythonru.com/uroki/operatory-v-python-uroki-po-python-dlja-nachinajushhih) (`+`):

```python
list_1 = [1, 2, 3]
list_2 = [4, 5, 6]
print(list_1 + list_2)
```

Результат:

```text
[1, 2, 3, 4, 5, 6]
```

Список можно повторить с помощью оператора умножения:

```python
list_1 = [1, 2, 3]
print(list_1  *  2)
```

Результат:

```text
[1, 2, 3, 1, 2, 3]
```

## **Списки и строки**

Для конвертации строки в набор символов, можно использовать функцию `list`:

```python
my_str = 'Monty Python'
my_list = list(my_str)
print(my_list)
```

Результат:

```text
['M', 'o', 'n', 't', 'y', ' ', 'P', 'y', 't', 'h', 'o', 'n']
```

Функция `list` используется для того, чтобы разбивать строку на отдельные символы.

Можно использовать метод `split` для [**разбития строки на слова**](https://pythonru.com/osnovy/stroki-python):

```python
my_str = 'Monty Python'
my_list = my_str.split()
print(my_list)
```

Результат:

```text
['Monty', 'Python']
```

Она возвращает обычный список, где с каждым словом можно взаимодействовать через индекс.

Символом разбития может служить любой знак, а не только пробел.

```python
my_str = 'Monty-Python'
my_list = my_str.split('-')
print(my_list)
```

Результат будет аналогичен:

```text
['Monty', 'Python']
```

## **Объединить список в строку**

Обратный процесс — объединение элементов [**списка в строку**](https://pythonru.com/osnovy/python-join).

Это делается с помощью метода `join`:

```python
my_list = ['Monty', 'Python']
delimiter = ' '
output = delimiter.join(my_list)
print(output)
```

Результат `Monty Python`.

## **Алиасинг (псевдонимы)**

Когда две переменные ссылаются на один и тот же объект:

```python
my_list = ['Monty', 'Python']
list_2 = my_list
```

Алиасинг значит, что на объект ссылается больше одного имени.

Следующий пример показывает, как меняются изменяемые списки:

```python
my_list = ['Monty', 'Python']
list_2 = my_list
list_2[1] = 'Java:)'
print(my_list)
```

Результат:

```text
['Monty', 'Java:)']
```

Изменился список `list_2`, но поскольку он ссылается на один и тот же объект, то оригинальный список тоже поменялся.Использовать “псевдонимы” при работе со списками не рекомендуется.В целом, работать со списками в Python очень просто.
