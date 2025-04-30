from pprint import pprint

import psycopg2


def _find_client_id(cursor, client_id):
    cursor.execute(
        """
        SELECT COUNT(*)
          FROM client
         WHERE client_id = %s;
        """,
        (client_id,)
    )
    result = cursor.fetchone()[0]
    return result


def _find_email(cursor, email):
    cursor.execute(
        """
        SELECT COUNT(*)
          FROM client
         WHERE email = %s;
        """,
        (email,)
    )
    result = cursor.fetchone()[0]
    return result


def _find_phone(cursor, phone_number):
    cursor.execute(
        """
        SELECT COUNT(*)
          FROM phone
         WHERE phone_number = %s;
        """,
        (phone_number,)
    )
    result = cursor.fetchone()[0]
    return result


def _get_client_phones_list(cursor, client_id):
    cursor.execute(
        """
        SELECT phone_number
          FROM phone
         WHERE client_id = %s;
        """,
        (client_id,)
    )
    phones_list = [number[0] for number in cursor.fetchall()]
    return phones_list


def create_db(connect, cursor):
    cursor.execute(
        """
        DROP TABLE IF EXISTS phone;
        DROP TABLE IF EXISTS client;
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS client (
            client_id  SERIAL      PRIMARY KEY,
            first_name VARCHAR(40) NOT NULL,
            last_name  VARCHAR(40) NOT NULL,
            email      VARCHAR(40) UNIQUE NOT NULL
        );
        CREATE TABLE IF NOT EXISTS phone (
            phone_number VARCHAR(12) PRIMARY KEY,
            client_id    INTEGER     NOT NULL REFERENCES client (client_id)
        );
        """
    )
    connect.commit()
    return 'База данных успешно создана.'


def add_client(connect, cursor, first_name, last_name, email, phone_number=None):
    check1 = _find_email(cursor, email)
    if check1:
        return 'Такой email уже существует.'
    if phone_number:
        check2 = _find_phone(cursor, phone_number)
        if check2:
            return 'Такой номер телефона уже существует.'
        cursor.execute(
            """
            INSERT INTO client (first_name, last_name, email)
            VALUES (%s, %s, %s)
            RETURNING client_id;
            """,
            (first_name, last_name, email)
        )
        client_id = cursor.fetchone()
        cursor.execute(
            """
            INSERT INTO phone (phone_number, client_id)
            VALUES (%s, %s);
            """,
            (phone_number, client_id)
        )
        connect.commit()
        return 'Клиент успешно добавлен.'
    else:
        cursor.execute(
            """
            INSERT INTO client (first_name, last_name, email)
            VALUES (%s, %s, %s);
            """,
            (first_name, last_name, email)
        )
        connect.commit()
        return 'Клиент успешно добавлен.'


def change_client(connect, cursor, client_id, first_name=None, last_name=None, email=None, phone_number=None):
    check1 = _find_client_id(cursor, client_id)
    if not check1:
        return 'Клиента с таким ID не существует.'
    if first_name:
        cursor.execute(
            """
            UPDATE client
               SET first_name = %s
             WHERE client_id = %s;
            """,
            (first_name, client_id)
        )
    if last_name:
        cursor.execute(
            """
            UPDATE client
               SET last_name = %s
             WHERE client_id = %s;
            """,
            (last_name, client_id)
        )
    if email:
        check2 = _find_email(cursor, email)
        if check2:
            connect.rollback()
            return 'Такой email уже существует.'
        cursor.execute(
            """
            UPDATE client
               SET email = %s
             WHERE client_id = %s;
            """,
            (email, client_id)
        )
    if phone_number:
        check3 = _find_phone(cursor, phone_number)
        if check3:
            connect.rollback()
            return 'Такой номер телефона уже существует.'
        phones_list = _get_client_phones_list(cursor, client_id)
        phones_count = len(phones_list)
        if phones_count == 0:
            cursor.execute(
                """
                INSERT INTO phone (phone_number, client_id)
                VALUES (%s, %s);
                """,
                (phone_number, client_id)
            )
            connect.commit()
            return 'Данные клиента успешно обновлены.'
        if phones_count == 1:
            cursor.execute(
                """
                UPDATE phone
                   SET phone_number = %s
                 WHERE client_id = %s;
                """,
                (phone_number, client_id)
            )
            connect.commit()
            return 'Данные клиента успешно обновлены.'
        if phones_count > 1:
            while True:
                replacement_phone = input(
                    f'Выберите из списка номер телефона, который нужно заменить ({(", ".join(phones_list))}): '
                ).strip()
                if replacement_phone in phones_list:
                    break
                print('Номер телефона указан неверно.')
            cursor.execute(
                """
                UPDATE phone
                   SET phone_number = %s
                 WHERE client_id = %s
                   AND phone_number = %s;
                """,
                (phone_number, client_id, replacement_phone)
            )
            connect.commit()
            return 'Данные клиента успешно обновлены.'
    connect.commit()
    return 'Данные клиента успешно обновлены.'


def delete_client(connect, cursor, client_id):
    check = _find_client_id(cursor, client_id)
    if not check:
        return 'Клиента с таким ID не существует.'
    cursor.execute(
        """
        DELETE FROM phone
         WHERE client_id = %s;

        DELETE FROM client
         WHERE client_id = %s;
        """,
        (client_id, client_id)
    )
    connect.commit()
    return 'Клиент успешно удалён.'


def add_phone(connect, cursor, client_id, phone_number):
    check1 = _find_client_id(cursor, client_id)
    if not check1:
        return 'Клиента с таким ID не существует.'
    check2 = _find_phone(cursor, phone_number)
    if check2:
        return 'Такой номер телефона уже существует.'
    cursor.execute(
        """
        INSERT INTO phone (phone_number, client_id)
        VALUES (%s, %s);
        """,
        (phone_number, client_id)
    )
    connect.commit()
    return 'Номер телефона успешно добавлен.'


def delete_phone(connect, cursor, phone_number):
    check = _find_phone(cursor, phone_number)
    if not check:
        return 'Такого номера телефона не существует.'
    cursor.execute(
        """
        DELETE FROM phone
         WHERE phone_number = %s;
        """,
        (phone_number,)
    )
    connect.commit()
    return 'Номер телефона успешно удалён.'


def delete_all_phones(connect, cursor, client_id):
    check = _find_client_id(cursor, client_id)
    if not check:
        return 'Клиента с таким ID не существует.'
    cursor.execute(
        """
        DELETE FROM phone
         WHERE client_id = %s;
        """,
        (client_id,)
    )
    connect.commit()
    return 'Все номера телефонов успешно удалены.'


def find_client(cursor, first_name='%%', last_name='%%', email='%%', phone_number=None):
    if phone_number:
        cursor.execute(
            """
            SELECT c.client_id, first_name, last_name, email, phone_number
              FROM client AS c
                   LEFT JOIN phone AS p
                   ON c.client_id = p.client_id
             WHERE first_name ILIKE %s
               AND last_name ILIKE %s
               AND email ILIKE %s
               AND phone_number LIKE %s;
            """,
            (first_name, last_name, email, phone_number)
        )
    else:
        cursor.execute(
            """
            SELECT c.client_id, first_name, last_name, email, phone_number
              FROM client AS c
                   LEFT JOIN phone AS p
                   ON c.client_id = p.client_id
             WHERE first_name ILIKE %s
               AND last_name ILIKE %s
               AND email ILIKE %s;
            """,
            (first_name, last_name, email)
        )
    result = cursor.fetchall()
    if result:
        pprint(result)
    else:
        print('Ничего не найдено.')


if __name__ == '__main__':
    with psycopg2.connect(database='clients_db', user='postgres', password='postgres') as conn:
        with conn.cursor() as cur:
            print(create_db(conn, cur))

            print(add_client(conn, cur, 'Антон', 'Богданов', 'a_bogdanov@mail.ru', '+79505000024'))
            print(add_client(conn, cur, 'Мария', 'Пшеничникова', 'p_mariya@bk.ru', '+79505000134'))
            print(add_client(conn, cur, 'Николай', 'Коробов', 'iron_man@mail.ru', '+79100000036'))
            print(add_client(conn, cur, 'Сергей', 'Кузнецов', 'kuznecov@yandex.ru', '+79600000057'))
            print(add_client(conn, cur, 'Антон', 'Озеров', 'ozerov@gmail.com'))

            print(add_phone(conn, cur, 2, '+79005006000'))

            print(change_client(conn, cur, 5, phone_number='+79900000370'))
            print(change_client(conn, cur, 2, last_name='Коваленко', email='mir@yandex.ru', phone_number='+79501505050'))
            print(change_client(conn, cur, 2, email='p_mariya@bk.ru'))
            print(change_client(conn, cur, 2, first_name='Мария', last_name='Пшеничникова'))

            print(delete_client(conn, cur, 4))

            print(delete_phone(conn, cur, '+79501505050'))
            print(delete_phone(conn, cur, '+79900000370'))

            print(delete_all_phones(conn, cur, 2))

            find_client(cur, first_name='Антон')
            find_client(cur, last_name='Коробов')
            find_client(cur, email='ozerov@gmail.com')
            find_client(cur, phone_number='+79100000036')
            find_client(cur, first_name='Антон', email='a_bogdanov@mail.ru')
