"""Runs the CBRecord script."""
#     _____ ____  _____  ______ _____ ____  _____  _____
#    / ____|  _ \|  __ \|  ____/ ____/ __ \|  __ \|  __ \
#   | |    | |_) | |__) | |__ | |   | |  | | |__) | |  | |
#   | |    |  _ <|  _  /|  __|| |   | |  | |  _  /| |  | |
#   | |____| |_) | | \ \| |___| |___| |__| | | \ \| |__| |
#    \_____|____/|_|  \_\______\_____\____/|_|  \_\_____/

import time


def main():
    """Entry point."""
    print("\033c")
    print("############")
    print("# CBRecord #")
    print("############")
    print("\nTo terminate the script press Ctrl-C.\n")

    cbr = None
    try:
        from cbrecord import cbr

        cbr = cbr.CBRecord()
        while True:
            cbr.do_cycle()
            time.sleep(cbr.cbr_config['crtimer'])
    except KeyboardInterrupt:
        try:
            cbr.kill_processes()
        except AttributeError:
            pass
        print("\nUser interruption.")
        raise SystemExit(0)
    except ImportError:
        print("Requirements not satisfied.")
        print("Run 'pip install -r requirements.txt'.")
        raise SystemExit(1)
    '''except Exception as ex:
        print("An unexpected error occured.")
        print("Error message: " + str(ex))
        raise SystemExit(1)'''


if __name__ == "__main__":
    main()
