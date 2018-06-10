"""Runs the CBRecord script."""
#     _____ ____  _____  ______ _____ ____  _____  _____
#    / ____|  _ \|  __ \|  ____/ ____/ __ \|  __ \|  __ \
#   | |    | |_) | |__) | |__ | |   | |  | | |__) | |  | |
#   | |    |  _ <|  _  /|  __|| |   | |  | |  _  /| |  | |
#   | |____| |_) | | \ \| |___| |___| |__| | | \ \| |__| |
#    \_____|____/|_|  \_\______\_____\____/|_|  \_\_____/

import logging
import sys
import tempfile
import time

from datetime import datetime


# Establish logging
parent_logger = logging.getLogger('cbrecord')
parent_logger.setLevel(logging.DEBUG)

plsh = logging.StreamHandler(stream=sys.stdout)
plshf = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
plsh.setFormatter(plshf)
plsh.setLevel(logging.INFO)
parent_logger.addHandler(plsh)

temporary_log_file = tempfile.TemporaryFile(mode='w+', encoding='utf8')
tsh = logging.StreamHandler(stream=temporary_log_file)
tshf = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
tsh.setFormatter(tshf)
tsh.setLevel(logging.DEBUG)
parent_logger.addHandler(tsh)
# ----


def main():
    """Entry point."""
    logger = logging.getLogger('cbrecord.run.main')

    print("\033c")
    print("############")
    print("# CBRecord #")
    print("############")
    print("\nTo terminate the script press Ctrl-C.\n")

    cbr = None
    try:
        from cbrecord import cbr
        from cbrecord.const import LOGS_DIR

        finalize_logging(LOGS_DIR)

        cbr = cbr.CBRecord()
        while True:
            cbr.do_cycle()
            time.sleep(cbr.cbr_config['crtimer'])
    except KeyboardInterrupt:
        try:
            cbr.kill_processes()
        except AttributeError:
            pass
        logger.info("User interruption.")
        raise SystemExit(0)
    except ImportError:
        logger.exception("Import error occured.")
        raise SystemExit(1)
    except Exception as ex:
        logger.exception("An unexpected error occured.")
        raise SystemExit(1)
    finally:
        logger.info("CBRecord stopped.")


def finalize_logging(LOGS_DIR):
    """Todo."""
    logger = logging.getLogger('cbrecord.run.finalize_logging')

    datetime_now_string = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    log_file_path = LOGS_DIR / datetime_now_string
    log_file_path.mkdir(parents=True, exist_ok=True)

    # CBRecord file logger
    cbrecord_log_file_path = log_file_path / 'cbrecord.log'
    with open(cbrecord_log_file_path, mode='w', encoding='utf8') as f:
        temporary_log_file.seek(0)
        f.write(" CBRecord LOG ".center(79, '#'))
        f.write('\n')
        f.write(temporary_log_file.read())
        temporary_log_file.close()
    plfh = logging.FileHandler(cbrecord_log_file_path,
                               mode='a',
                               encoding='utf-8')
    plfhf = logging.Formatter("%(asctime)s [%(levelname)s] " +
                              "%(name)s: %(message)s")
    plfh.setFormatter(plfhf)
    plfh.setLevel(logging.DEBUG)
    # ----

    parent_logger.removeHandler(tsh)  # Remove temporary stream handler.
    parent_logger.addHandler(plfh)

    # Requests file logger
    requests_log_file_path = log_file_path / 'requests.log'
    with open(requests_log_file_path, 'w', encoding='utf8') as f:
        f.write(" Requests LOG ".center(79, '#'))
        f.write('\n')
    requests_logger = logging.getLogger('urllib3')
    requests_logger.setLevel(logging.DEBUG)
    rlfh = logging.FileHandler(requests_log_file_path,
                               mode='a',
                               encoding='utf-8')
    rlfhf = logging.Formatter("%(asctime)s [%(levelname)s] " +
                              "%(name)s: %(message)s")
    rlfh.setFormatter(rlfhf)
    rlfh.setLevel(logging.DEBUG)
    requests_logger.addHandler(rlfh)
    # ----

    logger.info("Logging OK.")


if __name__ == "__main__":
    main()
