"""Model-Based Testing for TCP RPC Server and Client with an Independent Reference Model."""

import threading
import time
from hypothesis import strategies as st
from hypothesis.stateful import (
    Bundle,
    RuleBasedStateMachine,
    invariant,
    rule,
    run_state_machine_as_test,
)

import data_layer
from rpc_client import RPCClient
from rpc_server import HOST, PORT, run_server


class ReferenceModel:
    """Независимая эталонная модель (Оракул).

    Хранит ожидаемое состояние системы и воспроизводит бизнес-логику data_layer.
    """

    def __init__(self) -> None:
        self.persons: list[tuple] = []
        self.commands: list[tuple] = []
        self.results: list[tuple] = []

    def create_person(self, ip: str, platform: str, user_agent: str) -> int:
        pid = len(self.persons)
        record = (pid, 0, ip, platform, user_agent)
        self.persons.append(record)
        return pid

    def delete_person(self, identifier: int) -> bool:
        for idx, item in enumerate(self.persons):
            if item[0] == identifier:
                self.persons.pop(idx)
                return True
        return False

    def create_command(
        self, data: str, person: int, tags: str, status: str, triggered: int
    ) -> int:
        cid = len(self.commands)
        record = (cid, 0, data, person, tags, status, triggered)
        self.commands.append(record)
        return cid

    def delete_command(self, identifier: int) -> bool:
        for idx, item in enumerate(self.commands):
            if item[0] == identifier:
                self.commands.pop(idx)
                return True
        return False

    def create_result(
        self, result: str, status: str, exception: str, command: int
    ) -> int:
        rid = len(self.results)
        record = (rid, 0, result, status, exception, command)
        self.results.append(record)
        return rid

    def delete_result(self, identifier: int) -> bool:
        for idx, item in enumerate(self.results):
            if item[0] == identifier:
                self.results.pop(idx)
                return True
        return False

    def select_data(self) -> list:
        output = []
        for cmd in self.commands:
            for res in self.results:
                if cmd[0] == res[5]:
                    output.append((cmd[4], res[2]))
        return output


def records_match(actual_records: list, expected_records: list) -> bool:
    """Сравнивает записи сервера (списки JSON) с эталонной моделью (кортежи)."""
    if len(actual_records) != len(expected_records):
        return False

    for act, exp in zip(actual_records, expected_records):
        act_t = tuple(act)
        exp_t = tuple(exp)

        if act_t[0] != exp_t[0]:  # Сравнение ID
            return False
        if not isinstance(act_t[1], int):  # Проверка формата timestamp
            return False
        if act_t[2:] != exp_t[2:]:  # Сравнение всех остальных полей
            return False
    return True


class RPCStateMachine(RuleBasedStateMachine):
    """Тестовый автомат Model-Based Testing."""

    persons = Bundle("persons")
    commands = Bundle("commands")
    results = Bundle("results")

    def __init__(self) -> None:
        super().__init__()
        # 1. Сброс состояния сервера перед каждым прогоном
        data_layer.persons.clear()
        data_layer.commands.clear()
        data_layer.results.clear()

        # 2. Подключение клиента
        self.client = RPCClient(HOST, PORT)
        self.client.connect()

        # 3. Инициализация независимой эталонной модели
        self.model = ReferenceModel()

    def teardown(self) -> None:
        """Закрытие соединения с сервером."""
        self.client.close()

    # --- ПРАВИЛА (RULES) ---

    @rule(
        target=persons,
        ip=st.ip_addresses().map(str),
        platform=st.text(min_size=1, max_size=10),
        user_agent=st.text(min_size=1, max_size=10),
    )
    def create_person(self, ip: str, platform: str, user_agent: str):
        pid = self.client.create_person(ip, platform, user_agent)
        model_pid = self.model.create_person(ip, platform, user_agent)

        assert pid == model_pid
        return pid

    @rule(pid=persons)
    def delete_person(self, pid: int):
        res_system = self.client.delete_person(pid)
        res_model = self.model.delete_person(pid)

        assert res_system == res_model

    @rule(
        target=commands,
        pid=persons,
        data=st.text(min_size=1, max_size=10),
        tags=st.text(min_size=1, max_size=10),
        status=st.text(min_size=1, max_size=10),
        triggered=st.integers(min_value=0, max_value=1),
    )
    def create_command(
        self, data: str, pid: int, tags: str, status: str, triggered: int
    ):
        cid = self.client.create_command(data, pid, tags, status, triggered)
        model_cid = self.model.create_command(
            data, pid, tags, status, triggered
        )

        assert cid == model_cid
        return cid

    @rule(cid=commands)
    def delete_command(self, cid: int):
        res_system = self.client.delete_command(cid)
        res_model = self.model.delete_command(cid)

        assert res_system == res_model

    @rule(
        target=results,
        cid=commands,
        result=st.text(min_size=1, max_size=10),
        status=st.text(min_size=1, max_size=10),
        exception=st.text(min_size=1, max_size=10),
    )
    def create_result(
        self, result: str, status: str, exception: str, cid: int
    ):
        rid = self.client.create_result(result, status, exception, cid)
        model_rid = self.model.create_result(result, status, exception, cid)

        assert rid == model_rid
        return rid

    @rule(rid=results)
    def delete_result(self, rid: int):
        res_system = self.client.delete_result(rid)
        res_model = self.model.delete_result(rid)

        assert res_system == res_model

    # --- ИНВАРИАНТЫ ---

    @invariant()
    def check_state_matches_model(self):
        """Проверка полного совпадения состояния сервера и оракула."""
        # 1. Проверка сущностей Person
        server_persons = sorted(self.client.get_persons(), key=lambda x: x[0])
        model_persons = sorted(self.model.persons, key=lambda x: x[0])
        assert records_match(server_persons, model_persons), (
            f"Mismatch in persons!\nServer: {server_persons}\nModel:  {model_persons}"
        )

        # 2. Проверка сущностей Command
        server_commands = sorted(self.client.get_commands(), key=lambda x: x[0])
        model_commands = sorted(self.model.commands, key=lambda x: x[0])
        assert records_match(server_commands, model_commands), (
            f"Mismatch in commands!\nServer: {server_commands}\nModel:  {model_commands}"
        )

        # 3. Проверка сущностей Result
        server_results = sorted(self.client.get_results(), key=lambda x: x[0])
        model_results = sorted(self.model.results, key=lambda x: x[0])
        assert records_match(server_results, model_results), (
            f"Mismatch in results!\nServer: {server_results}\nModel:  {model_results}"
        )

        # 4. Проверка работы выборки select_data()
        server_select = [tuple(x) for x in self.client.select_data()]
        model_select = [tuple(x) for x in self.model.select_data()]
        assert server_select == model_select, (
            f"Mismatch in select_data!\nServer: {server_select}\nModel:  {model_select}"
        )


def setup_module() -> None:
    """Запуск RPC-сервера в фоновом потоке перед стартом тестов."""
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(0.3)


def test_rpc_state_machine() -> None:
    """Запуск тестов Конечного Автомата."""
    run_state_machine_as_test(RPCStateMachine)
