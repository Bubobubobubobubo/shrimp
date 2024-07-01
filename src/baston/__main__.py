from baston import *
from ptpython.repl import embed
from baston.configuration import read_configuration, get_ptpython_history_file

CONFIGURATION = read_configuration()


def exit():
    """Custom override for the exit function"""
    clock.stop()
    raise SystemExit


if __name__ == "__main__":
    match CONFIGURATION["editor"]["default_shell"]:
        case "ptpython":
            from ptpython.repl import embed

            embed(
                title="Baston",
                locals=locals(),
                globals=globals(),
                history_filename=get_ptpython_history_file(),
                vi_mode=CONFIGURATION["editor"]["vim_mode"],
            )
        case "python":
            import code

            code.interact(local=locals(), banner="", exitmsg="")
            exit()
        case _:
            print("Invalid shell selection. Exiting.")
