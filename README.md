# Практическая работа №1 (Вариант 24)

## 1. Общее описание
Прототип веб-приложения с поддержкой удалённого вызова процедур (RPC) на базе протокола TCP. Приложение хранит данные в оперативной памяти в виде кортежей (tuples) и поддерживает работу с сущностями Person, Command и Result.

## 2. Описание всех функций и настроек
### Модель данных (`src/data_layer.py`):
* `create_person(ip, platform, user_agent)`: Создать запись Person.
* `delete_person(identifier)`: Удалить Person по ID.
* `get_persons()`: Получить список всех Person.
* `create_command(data, person, tags, status, triggered)`: Создать Command.
* `delete_command(identifier)`: Удалить Command по ID.
* `get_commands()`: Получить список всех Command.
* `create_result(result, status, exception, command)`: Создать Result.
* `delete_result(identifier)`: Удалить Result по ID.
* `get_results()`: Получить список всех Result.
* `select_data()`: Выборка тегов команд и результатов за последние 5 минут.

### Настройки RPC (`src/rpc_server.py`):
* `HOST`: IP-адрес сервера (`127.0.0.1`).
* `PORT`: Сетевой порт (`8024`).
* `TIME_WINDOW`: Временное окно выборки в секундах (`300`).

## 3. Описание команд для сборки и запуска тестов
Запуск Model-Based тестов и формирование отчёта о покрытии ветвей:
```bash
bash run.sh
```

### Ручной запуск тестов через Python:
```bash
python -m coverage run --source=src --branch -m pytest tests/test_rpc.py
python -m coverage report -m
```

## 4. Примеры использования
### Запуск сервера:
```bash
python src/rpc_server.py
```

### Запуск клиента в Python:
```python
from src.rpc_client import RPCClient

client = RPCClient()
client.connect()

pid = client.create_person("192.168.1.1", "Linux", "Firefox")
cid = client.create_command("run", pid, "test", "active", 1)
rid = client.create_result("success", "done", "none", cid)

print(client.get_persons())
print(client.select_data())

client.close()
```