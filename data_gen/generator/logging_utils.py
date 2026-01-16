import logging
import os
import sys


def setup_logger(
    name: str, log_basename: str | None = None, logs_dir: str | None = None, level: int = logging.INFO
) -> logging.Logger:
    """Create and return a module-level logger with stream and file handlers.

    - `name` is the logger name (usually __name__).
    - `log_basename` if given will be used as the logfile base name, otherwise the logger name.
    - `logs_dir` defaults to cwd/logs.
    - `level` sets both the logger and handler levels.
    """
    logger = logging.getLogger(name)

    if logs_dir is None:
        # Resolve path relative to this file: data_gen/generator/logging_utils.py -> data_gen/logs
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        data_gen_dir = os.path.dirname(current_file_dir)
        logs_dir = os.path.join(data_gen_dir, "logs")

    os.makedirs(logs_dir, exist_ok=True)

    # choose a safe filename
    safe_basename = log_basename or name
    log_file = os.path.join(logs_dir, f"{safe_basename}.log")

    if not logger.handlers:
        fmt = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(fmt)
        sh.setLevel(level)

        fh = logging.FileHandler(log_file, mode="w")
        fh.setFormatter(fmt)
        fh.setLevel(level)

        logger.addHandler(sh)
        logger.addHandler(fh)

    logger.setLevel(level)
    return logger
