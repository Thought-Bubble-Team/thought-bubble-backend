import logging

def setup_logging():
    """Set up logging with reduced verbosity for third-party libraries."""
    
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Keep DEBUG for our app

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Default to INFO, override for specific needs

    # Log format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    )
    console_handler.setFormatter(formatter)

    # Avoid multiple handlers
    if not logger.hasHandlers():
        logger.addHandler(console_handler)

    # Reduce verbosity of third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("hpack").setLevel(logging.WARNING)