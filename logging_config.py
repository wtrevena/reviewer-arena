import logging

def setup_logging():
    logging.basicConfig(
        filename="arena.log",
        level=logging.DEBUG,  # Change to DEBUG level
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.info("Logging setup complete.")