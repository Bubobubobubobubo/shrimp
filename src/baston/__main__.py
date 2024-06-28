from .configuration import read_configuration
from .clock import Clock 
import code

CONFIGURATION = read_configuration()
clock = Clock(CONFIGURATION["tempo"])
clock.start()

def exit():
    """Exit the interactive shell"""
    clock.stop()
    raise SystemExit

if __name__ == "__main__":
    code.interact(
        local=locals(),
        banner="Welcome to the Baston interactive shell!", 
        exitmsg="Goodbye!"
    )
    exit()