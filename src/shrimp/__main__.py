from shrimp import *
from ptpython.repl import embed
from shrimp.configuration import read_configuration, get_ptpython_history_file
import logging

# This is annoying but this line is necessary to stop parso from spamming the logs
logging.getLogger("parso").setLevel(logging.WARNING)

CONFIGURATION = read_configuration()


def exit():
    """Custom override for the exit function"""
    clock._stop()
    raise SystemExit


if __name__ == "__main__":
    match CONFIGURATION["editor"]["default_shell"]:
        case "ptpython":
            logging.info("Entering ptpython shell.")
            from ptpython.repl import embed

            embed(
                patch_stdout=CONFIGURATION["editor"]["print_above"],
                title="Shrimp",
                locals=locals(),
                globals=globals(),
                history_filename=get_ptpython_history_file(),
                vi_mode=CONFIGURATION["editor"]["vim_mode"],
            )
        case "python":
            logging.info("Entering Python shell.")
            import code

            code.interact(local=locals(), banner="", exitmsg="")
            exit()
        case _:
            print("Invalid shell selection. Exiting.")
