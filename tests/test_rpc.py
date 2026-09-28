"""Model-Based Testing for TCP RPC Server and Client."""

import sys
import threading
import time
from hypothesis import strategies as st
from hypothesis.stateful import (
    Bundle,
    RuleBasedStateMachine,
    rule,
    run_state_machine_as_test,
)

sys.path.insert(0, "src")

import data_layer
from rpc_client import RPCClient
from rpc_server import HOST, PORT, run_server


class RPCStateMachine(RuleBasedStateMachine):
    """State machine testing RPC client against TCP server."""

    persons = Bundle("persons")
    commands = Bundle("commands")
    results = Bundle("results")

    def __init__(self) -> None:
        """Initialize state machine and connect client."""
        super().__init__()
        data_layer.persons.clear()
        data_layer.commands.clear()
        data_layer.results.clear()
        self.client = RPCClient(HOST, PORT)
        self.client.connect()

    def teardown(self) -> None:
        """Clean up client connection."""
        self.client.close()

    @rule(
        target=persons,
        ip=st.ip_addresses().map(str),
        platform=st.text(min_size=1, max_size=10),
        user_agent=st.text(min_size=1, max_size=10),
    )
    def create_person(self, ip: str, platform: str, user_agent: str):
        """Test create_person and get_persons via RPC."""
        pid = self.client.create_person(ip, platform, user_agent)
        all_p = self.client.get_persons()
        assert len(all_p) > 0
        return pid

    @rule(pid=persons)
    def delete_person(self, pid: int):
        """Test delete_person via RPC."""
        res = self.client.delete_person(pid)
        assert isinstance(res, bool)

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
        """Test create_command and get_commands via RPC."""
        cid = self.client.create_command(data, pid, tags, status, triggered)
        all_c = self.client.get_commands()
        assert len(all_c) > 0
        return cid

    @rule(cid=commands)
    def delete_command(self, cid: int):
        """Test delete_command via RPC."""
        res = self.client.delete_command(cid)
        assert isinstance(res, bool)

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
        """Test create_result and get_results via RPC."""
        rid = self.client.create_result(result, status, exception, cid)
        all_r = self.client.get_results()
        assert len(all_r) > 0
        return rid

    @rule(rid=results)
    def delete_result(self, rid: int):
        """Test delete_result via RPC."""
        res = self.client.delete_result(rid)
        assert isinstance(res, bool)

    @rule()
    def select_data(self):
        """Test select_data query via RPC."""
        res = self.client.select_data()
        assert isinstance(res, list)


def setup_module() -> None:
    """Start RPC Server in background thread before tests run."""
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(0.3)


def test_rpc_state_machine() -> None:
    """Execute state machine testing with pytest."""
    run_state_machine_as_test(RPCStateMachine)