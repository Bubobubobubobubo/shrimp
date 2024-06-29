from baston import *
import signal

def interrupt_handler(sig, frame):
    """Handle the interrupt signal from the user"""
    print("\b\bSaved from infinite recursion!")
    clock.stop()

def recursive():
    print("Hello, World! My recursion is eternal!")
    clock.add(recursive, clock.next_bar())

if __name__ == "__main__":
    # We install a signal handler to stop the clock when the user presses Ctrl+C
    signal.signal(signal.SIGINT, interrupt_handler)
    clock.add(recursive, clock.next_bar())
    clock.play()

