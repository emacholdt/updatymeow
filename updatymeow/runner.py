import re
import subprocess
from typing import Callable, Optional

def execute_command(
    command: str,
    on_output: Optional[Callable[[str], None]] = None,
    sudo_password: Optional[str] = None,
) -> tuple[int, str]:
    output_lines = []

    # If sudo password provided, ensure sudo reads from stdin silently
    if sudo_password:
        command = re.sub(r"^(pkexec|sudo)\s+", 'sudo -S -p "" ', command)

    proc = subprocess.Popen(
        command,
        shell=True,
        stdin=subprocess.PIPE if sudo_password else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    if sudo_password and proc.stdin:
        try:
            proc.stdin.write(f"{sudo_password}\n")
            proc.stdin.flush()
            proc.stdin.close()
        except (BrokenPipeError, OSError):
            pass

    if proc.stdout:
        for line in proc.stdout:
            cleaned = line.rstrip("\r\n")
            output_lines.append(cleaned)
            if on_output:
                on_output(cleaned)
        proc.stdout.close()

    proc.wait()
    return proc.returncode, "\n".join(output_lines)
