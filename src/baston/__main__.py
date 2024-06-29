from baston import *
from ptpython.repl import embed
from .configuration import read_configuration
CONFIGURATION = read_configuration()


if __name__ == "__main__":
    match CONFIGURATION.get("default_shell", "python"):
        case "ptpython":
            from ptpython.repl import embed
            embed(locals(), globals())
        case "python":
            import code
            code.interact(local=locals(), banner="", exitmsg="Bye!")
        case _:
            print("Invalid shell selection. Exiting.")
    exit()