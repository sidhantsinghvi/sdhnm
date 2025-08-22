import datetime
import logging

def is_date_valid(date_text, format):
    try:
        datetime.datetime.strptime(date_text, format)
        return True
    except ValueError:
        logging.error(f"Incorrect data format: {date_text}")
        return False