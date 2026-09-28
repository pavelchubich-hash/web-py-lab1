import time

TIME_WINDOW = 300

persons = []
commands = []
results = []


def create_person(ip: str, platform: str, user_agent: str) -> int:
    """Create a new person record as a tuple."""
    identifier = len(persons)
    created = int(time.time())
    record = (identifier, created, ip, platform, user_agent)
    persons.append(record)
    return identifier


def delete_person(identifier: int) -> bool:
    """Delete a person record by identifier."""
    for idx, item in enumerate(persons):
        if item[0] == identifier:
            persons.pop(idx)
            return True
    return False


def get_persons() -> list:
    """Return all person records."""
    return persons


def create_command(
    data: str, person: int, tags: str, status: str, triggered: int
) -> int:
    """Create a new command record as a tuple."""
    identifier = len(commands)
    created = int(time.time())
    record = (
        identifier,
        created,
        data,
        person,
        tags,
        status,
        triggered,
    )
    commands.append(record)
    return identifier


def delete_command(identifier: int) -> bool:
    """Delete a command record by identifier."""
    for idx, item in enumerate(commands):
        if item[0] == identifier:
            commands.pop(idx)
            return True
    return False


def get_commands() -> list:
    """Return all command records."""
    return commands


def create_result(
    result: str, status: str, exception: str, command: int
) -> int:
    """Create a new result record as a tuple."""
    identifier = len(results)
    created = int(time.time())
    record = (identifier, created, result, status, exception, command)
    results.append(record)
    return identifier


def delete_result(identifier: int) -> bool:
    """Delete a result record by identifier."""
    for idx, item in enumerate(results):
        if item[0] == identifier:
            results.pop(idx)
            return True
    return False


def get_results() -> list:
    """Return all result records."""
    return results


def select_data() -> list:
    """Select command tags and result value for recent entries."""
    now = int(time.time())
    threshold = now - TIME_WINDOW
    output = []
    for cmd in commands:
        for res in results:
            if cmd[0] == res[5] and res[1] > threshold:
                output.append((cmd[4], res[2]))
    return output


def handle_repl_command(cmd: str) -> bool:
    """Execute single REPL command."""
    if cmd == "exit":
        return False
    if cmd == "create_person":
        pid = create_person("127.0.0.1", "Linux", "Mozilla/5.0")
        print(f"Created person with id: {pid}")
    elif cmd == "get_persons":
        print(get_persons())
    elif cmd == "select":
        print(select_data())
    else:
        print("Unknown command or parameters error")
    return True


def repl() -> None:
    """Interactive REPL mode."""
    print("REPL started. Type 'exit' to quit.")
    running = True
    while running:
        try:
            user_input = input("> ").strip()
            if user_input:
                running = handle_repl_command(user_input)
        except (EOFError, KeyboardInterrupt):
            break


if __name__ == "__main__":
    p0 = create_person("192.168.1.1", "Windows", "Chrome")
    c0 = create_command("run_task", p0, "urgent", "active", 1)
    r0 = create_result("success", "completed", "none", c0)

    print("Initial selection test:", select_data())
    repl()