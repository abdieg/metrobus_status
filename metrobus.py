import os
import time
import requests
import schedule as schedule
from loguru import logger
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from datetime import datetime, time as dt_time
from zoneinfo import ZoneInfo
import webdriver_functions as wdfn
from selenium import webdriver
from Constant import Constant
from dotenv import load_dotenv

load_dotenv()  # Load .env variables


# logger.add("scrapper_metrobus_{time}.log", rotation="1 day", level="INFO")

HEADLESS = True
SCHEDULED = False

TESTING_URL: str = "https://www.metrobus.cdmx.gob.mx/ServicioMB"

iframe_container = "iFrameEstatus"
locator_table_container = "//tbody[contains(.,'EstadoServicio')]"

# Global variable to store previous scrape results
previous_results = None


def get_locator(line_number, cell_index):
    """
    Returns an XPath locator string for a given MB line number and cell index.

    :param line_number: The MB line number as an integer (e.g., 1 for MB1).
    :param cell_index: The index of the <td> cell (e.g., 2, 3, or 4). 2 = ESTADO, 3 = ESTACIONES, 4 = INFORMACION
    :return: A formatted XPath locator string.
    """
    return f"//tbody//tr//img[contains(@src, 'MB{line_number}')]/parent::td/parent::tr/td[{cell_index}]"


def initialize_driver():
    # Setup webdriver as a service
    service = Service(Constant.WEBDRIVER_PATH)
    chrome_options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def initialize_headless_driver():
    # Setup webdriver as a service (headless)
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Enable headless mode
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security model, Chromium only
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    service = Service(Constant.WEBDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def perform_research():
    """
    Opens the Metrobus website, switches to the proper iframe, waits for the table to load,
    scrapes the desired data for metrobus lines 1-7, logs the values, and returns a dictionary of results.
    """

    if HEADLESS:
        driver = initialize_headless_driver()
    else:
        driver = initialize_driver()

    try:
        driver.get(TESTING_URL)

        wdfn.switch_to_iframe(driver, iframe_container)
        wdfn.wait_for_element(driver, locator_table_container)

        results = {}
        for line in range(1, 8):
            results[line] = {
                'estado': wdfn.get_text(driver, get_locator(line, 2)),
                'estaciones_afectadas': wdfn.get_text(driver, get_locator(line, 3)),
                'info_adicional': wdfn.get_text(driver, get_locator(line, 4)),
            }
            logger.info(f"Linea {line}")
            for key, value in results[line].items():
                logger.info(f"{key.title()}: {value}")

    except Exception as e:
        logger.exception("Error during research: %s", e)
        raise

    finally:
        driver.quit()

    return results


def send_notification(line_number, line_data):
    """
    Sends a notification for a specific Metrobus line to its respective topic.

    The notification includes:
      - Metrobus Line number
      - Estado
      - Información adicional
      - Estaciones afectadas

    The topic URL follows the format:
      http://url/metrobus_linea_N
    where N is the metrobus line number (1 to 7).

    :param line_number: The metrobus line number (1 to 7)
    :param line_data: Dictionary with keys 'estado', 'info_adicional', and 'estaciones_afectadas'
    """
    ntfy_ip = os.environ.get("NTFY_IP")
    ntfy_port = os.environ.get("NTFY_PORT")
    logger.debug(f"Notify IP: {ntfy_ip}")
    logger.debug(f"Notify PORT: {ntfy_port}")

    try:
        topic = f"metrobus_linea_{line_number}"
        ntfy_url = f"http://{ntfy_ip}:{ntfy_port}/{topic}"
        logger.debug(f"Notify URL: {ntfy_url}")
        headers = {'Title': f'Metrobus Linea {line_number}'}
        message = (
            f"Estado: {line_data.get('estado', 'N/A')}\n"
            f"Información adicional: {line_data.get('info_adicional', 'N/A')}\n"
            f"Estaciones afectadas: {line_data.get('estaciones_afectadas', 'N/A')}"
        )
        response = requests.post(ntfy_url, data=message.encode('utf-8'), headers=headers)
        response.raise_for_status()  # Raises an exception for HTTP error responses
        logger.info(f"Notification sent successfully for line {line_number}")
    except Exception as e:
        logger.exception(f"Failed to send notification for line {line_number}: {e}")


def job():
    """
    Function that combines checking the website and sending a message
    Checks if the current Mexico City time is between 5 AM and 11 PM.
    If so, performs the scraping and compares the new data with previous data.
    For each metrobus line (1-7):
      - On the first run, if the data does not match the happy path (i.e.,
        'estado' is not 'Servicio Regular', or 'info_adicional' is not empty, or
        'estaciones_afectadas' is not 'Ninguna'), a notification is sent.
      - On subsequent runs, if any field has changed, a notification is sent
        to the corresponding topic (e.g., 'metrobus_linea_1').
    """
    try:
        # Set Mexico City timezone
        mexico_tz = ZoneInfo("America/Mexico_City")
        current_time_mexico = datetime.now(mexico_tz).time()

        # Only run if current time is between 5:00 and 23:00
        if not (dt_time(Constant.INITIAL_TIME, 0) <= current_time_mexico <= dt_time(Constant.FINAL_TIME, 0)):
            logger.info("Current time is outside the scheduled window. Skipping this run.")
            return
        else:
            logger.info("Current time is in Mexico. We are good to continue.")

        logger.info("Starting scraping job...")
        new_results = perform_research()
        global previous_results

        if previous_results is None:
            # First run: send notification if the data is not the happy path.
            for line in range(1, 8):
                curr = new_results.get(line, {})
                estado = curr.get('estado', '')
                info_adicional = curr.get('info_adicional', '')
                estaciones_afectadas = curr.get('estaciones_afectadas', '')
                if estado != "Servicio Regular" or info_adicional.strip() != "" or estaciones_afectadas != "Ninguna":
                    try:
                        send_notification(line, curr)
                    except Exception as e:
                        logger.exception(f"Error sending initial notification for line {line}: {e}")
                else:
                    logger.info(f"Initial happy path for line {line}. No notification sent.")
            previous_results = new_results
            logger.info("Initial scrape completed.")
        else:
            # Subsequent runs: compare each line's values to previous values.
            for line in range(1, 8):
                prev = previous_results.get(line, {})
                curr = new_results.get(line, {})
                if (prev.get('estado') != curr.get('estado') or
                        prev.get('estaciones_afectadas') != curr.get('estaciones_afectadas') or
                        prev.get('info_adicional') != curr.get('info_adicional')):
                    try:
                        send_notification(line, curr)
                    except Exception as e:
                        logger.exception(f"Error sending notification for line {line}: {e}")
                else:
                    logger.info(f"No changes detected for line {line}.")
            previous_results = new_results
    except Exception as e:
        logger.exception("Error in job: %s", e)


def main() -> None:

    if SCHEDULED:
        # Schedule the job every X time
        schedule.every(Constant.SCRAPPER_REFRESH_TIME).minutes.do(job)

        # Run the scheduled job
        while True:
            schedule.run_pending()
            time.sleep(1)

    else:
        # Run standalone without scheduler
        job()


if __name__ == '__main__':
    main()
