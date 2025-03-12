from loguru import logger
from selenium.common import StaleElementReferenceException, TimeoutException, ElementNotVisibleException, \
    InvalidElementStateException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from Constant import Constant


# def wait_for_element(_driver, _element):
#     timeout = Constant.WEBDRIVER_TIMEOUT
#     ignored_exceptions = (StaleElementReferenceException,)
#     try:
#         element_present = ec.presence_of_element_located((By.XPATH, _element))
#         WebDriverWait(_driver, timeout, ignored_exceptions=ignored_exceptions).until(element_present)
#         element_visible = ec.presence_of_element_located((By.XPATH, _element))
#         WebDriverWait(_driver, timeout, ignored_exceptions=ignored_exceptions).until(element_visible)
#         element_clickable = ec.presence_of_element_located((By.XPATH, _element))
#         WebDriverWait(_driver, timeout, ignored_exceptions=ignored_exceptions).until(element_clickable)
#         logger.debug(f"Element found: {_element}")
#     except TimeoutException:
#         logger.debug(f"Timeout awaiting for element to load: {_element}")


def wait_for_element(_driver, _element):
    timeout = Constant.WEBDRIVER_TIMEOUT
    ignored_exceptions = (StaleElementReferenceException,)

    def _wait_for_condition(condition):
        return WebDriverWait(_driver, timeout, ignored_exceptions=ignored_exceptions).until(condition)

    try:
        # Wait for the element to be present in the DOM
        _wait_for_condition(ec.presence_of_element_located((By.XPATH, _element)))

        # Since StaleElementReferenceException might still occur, retry finding the element
        for attempt in range(3):  # Retry up to 3 times
            try:
                # Now, ensure it's visible (implies presence)
                element_visible = _wait_for_condition(ec.visibility_of_element_located((By.XPATH, _element)))
                # Ensure the element is clickable as well
                _wait_for_condition(ec.element_to_be_clickable((By.XPATH, _element)))
                logger.debug(f"Element found and interactable: {_element}")
                return element_visible  # Return the visible (and interactable) element
            except StaleElementReferenceException:
                logger.warning(f"StaleElementReferenceException caught, retrying... Attempt {attempt + 1}")
                if attempt == 2:  # If it's the last attempt, raise the exception
                    raise
    except TimeoutException:
        logger.error(f"Timeout awaiting for element: {_element}")


def write_on_element(_driver, _element, _text):
    wait_for_element(_driver, _element)
    _driver.find_element(By.XPATH, _element).clear()
    _driver.find_element(By.XPATH, _element).send_keys(_text)


def click(_driver, _element):
    wait_for_element(_driver, _element)
    _driver.find_element(By.XPATH, _element).click()


def get_value(_driver, _element) -> str:
    wait_for_element(_driver, _element)
    return _driver.find_element(By.XPATH, _element).get_attribute('value')


def get_text(_driver, _element) -> str:
    wait_for_element(_driver, _element)
    return _driver.find_element(By.XPATH, _element).text


def does_element_exist(_driver, _element):
    timeout = Constant.WEBDRIVER_TIMEOUT_EXISTENCE
    ignored_exceptions = (StaleElementReferenceException, ElementNotVisibleException, InvalidElementStateException,
                          NoSuchElementException)
    try:
        element_present = ec.presence_of_element_located((By.XPATH, _element))
        WebDriverWait(_driver, timeout, ignored_exceptions=ignored_exceptions).until(element_present)
        element_visible = ec.presence_of_element_located((By.XPATH, _element))
        WebDriverWait(_driver, timeout, ignored_exceptions=ignored_exceptions).until(element_visible)
        element_clickable = ec.presence_of_element_located((By.XPATH, _element))
        WebDriverWait(_driver, timeout, ignored_exceptions=ignored_exceptions).until(element_clickable)
        logger.debug(f"Element does exist: {_element}")
        return True
    except TimeoutException:
        logger.debug(f"Element does not exist: {_element}")
        return False


def get_elements(_driver, _element):
    wait_for_element(_driver, _element)
    return _driver.find_elements(By.XPATH, _element)


def switch_to_iframe(_driver, iframe_id):
    timeout = Constant.WEBDRIVER_TIMEOUT_EXISTENCE
    try:
        iframe = WebDriverWait(_driver, timeout).until(ec.presence_of_element_located((By.ID, iframe_id)))
        _driver.switch_to.frame(iframe)
        logger.debug("Switched to iframe:", iframe_id)
    except Exception as e:
        logger.debug(f"Error: {e}")
