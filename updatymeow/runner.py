import subprocess
from typing import Callable, Optional

def execute_command(command: str, on_output: Optional[Callable[[str], None]] = None) -> tuple[int, str]:
    output_lines = []
    # shortcut: runs via shell=True so pipes or sudo wrapper work cleanly
    proc = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    if proc.stdout:
        for line in proc.stdout:
            cleaned = line.rstrip("\r\n")
            output_lines.append(cleaned)
            if on_output:
                on_output(cleaned)
        proc.stdout.close()

    proc.wait()
    return proc.returncode, "\n".join(output_lines)
