from importlib.metadata import version
from rich.panel import Panel
from rich import print

BASTON_LOGO = """
    __               __            
   / /_  ____ ______/ /_____  ____ 
  / __ \/ __ `/ ___/ __/ __ \/ __ \\
 / /_/ / /_/ (__  ) /_/ /_/ / / / /
/_.___/\__,_/____/\__/\____/_/ /_/ 
"""


def info_message(message: str, should_print: bool = False) -> None:
    """Print an information message"""
    if should_print:
        print(Panel(f"[bold blue]{message}[/bold blue]"))


def greeter() -> None:
    print(
        f"[bold blue]{BASTON_LOGO}[/bold blue]\n[bold yellow]> Live Coding tool, BuboBubo {version('baston')}[/bold yellow]\n"
    )
