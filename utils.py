from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from base64 import b64encode
import csv, re


class Config:
    BASE_URL = "https://asesweb.governoeletronico.gov.br/"
    MAX_WORKERS = 10
    PAGE_INFO_FILENAME = "data/page_info.csv"
    ERR_WARN_SUMMARY_FILENAME = "data/err_warn_summary.csv"
    EMAG_SUMMARY_FILENAME = "data/emag_summary.csv"


def encode_url(url: str) -> str:
    """Encodes the given URL using base64 for file saving.

    Args:
        url (str): The URL to encode.

    Returns:
        str: The encoded URL.

    """
    url = re.sub(r"https?://", "", url)
    return b64encode(url.encode("iso-8859-1")).decode("utf-8")


def insert_data(
    driver, input_element: str, button_element: str, data, action_chains: bool = False
) -> None:
    """Inserts the given data into the input element and clicks the submit button.

    Args:
        driver: The WebDriver instance.
        input_element: The CSS selector of the input element.
        button_element: The CSS selector of the submit button element.
        data: The data to be inserted into the input element.
        action_chains: If True, uses ActionChains to perform the click action.

    Returns:
        None
    """
    input_holder = driver.find_element(By.CSS_SELECTOR, input_element)
    input_holder.clear()
    input_holder.send_keys(data)

    submit_button = driver.find_element(By.CSS_SELECTOR, button_element)
    if action_chains:
        ActionChains(driver).move_to_element(submit_button).click().perform()
    else:
        submit_button.click()

    return None


def create_csv_file(model, filename: str) -> None:
    """Create a CSV file with the given filename and write the header using
    the model's field names.

    Args:
        model: The model object containing the field names.
        filename (str): The name of the CSV file to be created.

    Returns:
        None
    """
    fieldnames = list(model.model_fields.keys())
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

    return None


def store(data, filename: str) -> None:
    """
    Store the given data in a CSV file.

    Args:
        data: The data to be stored.
        filename (str): The name of the CSV file.

    Returns:
        None
    """
    with open(filename, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(data.dict().values())

    return None
