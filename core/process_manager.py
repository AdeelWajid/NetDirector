from dataclasses import dataclass, field
import time
import psutil
from services.process_service import matching_processes


@dataclass
class Session:
    rule_id: str
    executable: str
    name: str
    backend: str
    expected_ip: str
    started: float
    monitor_children: bool
    processes: dict[int, float] = field(default_factory=dict)
    status: str = "Waiting for target process"
    ever_found: bool = False


class ProcessManager:
    """Track PID + creation time; never confuse a recycled PID for the original process."""
    def __init__(self):
        self.sessions = {}

    def register(self, rule, result):
        session = Session(rule.id, rule.executable, rule.name, result.backend,
                          result.expected_ip, result.started, rule.children)
        if not result.loader:
            try:
                session.processes[result.pid] = psutil.Process(result.pid).create_time()
                session.ever_found = True
            except psutil.Error:
                pass
        self.sessions[rule.id] = session

    def update(self):
        for session in self.sessions.values():
            if not session.ever_found and time.time() - session.started < 20:
                for process in matching_processes(session.executable, session.started - 0.2):
                    try:
                        session.processes[process.pid] = process.create_time()
                        session.ever_found = True
                    except psutil.Error:
                        pass
            alive = {}
            for pid, created in list(session.processes.items()):
                try:
                    process = psutil.Process(pid)
                    if process.create_time() != created or not process.is_running():
                        continue
                    alive[pid] = created
                    if session.monitor_children:
                        for child in process.children(recursive=True):
                            try:
                                alive[child.pid] = child.create_time()
                            except psutil.Error:
                                pass
                except psutil.Error:
                    continue
            session.processes = alive
            if alive:
                session.status = "Running • binding unverified" if session.expected_ip else "Running • Windows default"
            elif session.ever_found:
                session.status = "Exited"
            elif time.time() - session.started >= 20:
                session.status = "Target not observed • launch unverified"
        return {key: {"status": s.status, "pids": list(s.processes), "backend": s.backend,
                      "expected_ip": s.expected_ip} for key, s in self.sessions.items()}

    def diagnostics(self, rule):
        self.update()
        session = self.sessions.get(rule.id)
        processes = {}
        if session:
            processes.update(session.processes)
        # Also inspect apps started outside NetDirector; do not claim they were bound here.
        for root in matching_processes(rule.executable):
            try:
                processes[root.pid] = root.create_time()
                if rule.children:
                    for child in root.children(recursive=True):
                        processes[child.pid] = child.create_time()
            except psutil.Error:
                pass
        rows = []
        for pid, created in processes.items():
            try:
                process = psutil.Process(pid)
                if process.create_time() != created:
                    continue
                name = process.name()
                connections = process.net_connections(kind="inet")
                if not connections:
                    rows.append(dict(process=name, pid=pid, local="—", status="No observable sockets", verdict="Unverified"))
                for connection in connections:
                    local = connection.laddr.ip if connection.laddr else ""
                    expected = session.expected_ip if session else ""
                    verdict = "Unverified"
                    if local in ("0.0.0.0", "::", "127.0.0.1", "::1", ""):
                        verdict = "Wildcard / loopback"
                    elif expected:
                        verdict = "Matches launch IP" if local == expected else "Different local IP"
                    rows.append(dict(process=name, pid=pid, local=local or "—", status=connection.status, verdict=verdict))
            except psutil.AccessDenied:
                rows.append(dict(process="Access denied", pid=pid, local="—", status="Permission needed to inspect this process", verdict="Unavailable"))
            except psutil.Error:
                pass
        return rows
