Точно также как и генераторы списков, мы можем использовать генераторы словарей

Например:

У нас есть словарь студентов с их оценками. Мы ошиблись при оценивании и теперь должны всем добавить по 10 баллов.

```python
marks = {
    'Mark': 40,
    'Agnes': 50,
    'Helen': 80,
    'John': 65,
}
```

 Решение:

```python
new_marks = { k:v + 10 for k, v in marks.items() }
print(new_marks)

Output:
{'Mark': 50, 'Agnes': 60, 'Helen': 90, 'John': 75}
```

Задача 2:

Нам нужно добавить к именам букву их класса  "A"

```python
students_with_class = { k+" A":v for k, v in new_marks.items() }
print(students_with_class)

Output:
{'Mark A': 50, 'Agnes A': 60, 'Helen A': 90, 'John A': 75}
```

Приведи дальше свои примеры для того чтобы они лучше поняли
