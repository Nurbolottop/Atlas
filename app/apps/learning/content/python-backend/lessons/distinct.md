### DISTINCT

Предположим, что нам нужно узнать все имена, которые есть у наших пользователей. Самый простой способ сделать это — выполнить запрос не всех полей, а только имени:

```sql
-- получить список имён всех пользователей
SELECT first_name FROM users;
```

Но проблема в том, что эти имена наверняка дублируются: ведь разные люди вполне могут иметь одинаковые имена. Избавиться от дублей можно с помощью DISTINCT.

```sql
SELECT DISTINCT first_name FROM users;

 first_name
------------
 Delphine
 Hanna
 Maxwell
 Russell
 Mia
```

Такой запрос выведет только уникальные имена.

DISTINCT позволяет указывать не одно, а сразу несколько полей:

```sql
-- DISTINCT добавляется в запрос только один раз, независимо от того, сколько колонок перечисляется
SELECT DISTINCT first_name, last_name FROM users;

 first_name |   last_name
------------+---------------
 Rhiannon   | Tremblay
 Vesta      | Kassulke
 Ena        | Gorczany
 Florencio  | Collier
 Garrett    | Koss
```

В эту выборку попадут все значения с **уникальным сочетанием имён и фамилий**. Это значит, что имена и фамилии повторяться могут, но **пара всегда уникальна**. Если в DISTINCT добавить первичный ключ (`SELECT DISTINCT id, first_name FROM users`), то запрос извлечёт все записи. Такой результат является следствием уникальности первичного ключа.

DISTINCT можно совмещать с агрегатными функциями, с которыми мы познакомимся поближе позже: например, посчитать количество пользователей с уникальными именами:

```sql
SELECT COUNT(DISTINCT first_name) FROM users;
```

### DISTINCT ON

Эта форма DISTINCT ON настолько сильно отличается от своей исходной формы, что о ней стоит сказать подробнее. В отличие от базовой формы, DISTINCT ON позволяет отдельно указывать поля, по которым проверяется уникальность, и поля, которые должны оказаться в результирующей выборке.

```sql
-- Все записи, уникальные по user_id
SELECT DISTINCT ON (user_id) * FROM topics;

 id | user_id |              title              | body                  |       created_at
----|---------|---------------------------------|-----------------------|------------------------
  2 |       2 | molestiae voluptas velit        | Quod quasi molestiae. | 2019-06-02 23:42:30.688

-- Все title для уникальных user_id
SELECT DISTINCT ON (user_id) title FROM topics;

             title
-------------------------
 molestiae voluptas velit

SELECT DISTINCT user_id, title FROM topics;
-- Такой запрос вернет совершенно другие данные, он вернет все уникальные пары user_id-title
-- То есть здесь возможно повторение user_id в результирующей выборке

SELECT DISTINCT ON (user_id, title) user_id, title FROM topics;
-- Этот запрос равносилен тому, что был выше
```

При работе с DISTINCT ON важно правильно использовать сортировку.

```sql
SELECT DISTINCT ON (user_id) id, user_id, title, created_at
  FROM topics
  ORDER BY user_id, created_at;

 id | user_id |            title             |       created_at
----+---------+------------------------------+-------------------------
 48 |       1 | qui non velit                | 2018-12-05 21:49:52.631
  7 |       4 | delectus in nihil            | 2018-12-06 00:46:32.712
 26 |       6 | rerum rerum recusandae       | 2018-12-05 18:39:47.937
 34 |       7 | soluta non voluptas          | 2018-12-06 07:55:00.095
```

Такой запрос вернёт первый созданный топик для каждого пользователя. Запросы с DISTINCT ON требуют того, чтобы первыми полями в ORDER BY следовали те поля, которые идут после ON. Только тогда сортировка отработает так, как ожидается. В запросе выше это user\_id, он указан в сортировке первым. В противном случае (`ORDER BY created_at, user_id`), результат будет неверен.

### Дополнительные материалы

-   [Официальная документация](https://postgrespro.ru/docs/postgresql/11/sql-select#SQL-DISTINCT)
