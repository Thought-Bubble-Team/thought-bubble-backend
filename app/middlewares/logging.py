import logging

def setup_logging():
    """
    Set up application-wide logging.
    Includes console handler with a standard format.
    """
    # Define logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Set the default logging level

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formatter for logs
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)

    # Avoid duplicate handlers
    if not logger.handlers:
        logger.addHandler(console_handler)
