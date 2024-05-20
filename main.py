from selectolax.parser import HTMLParser
from os import path
from selenium import webdriver
from rich.logging import RichHandler

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By

from utils import insert_data, encode_url, store, create_csv_file, Config
from os.path import getsize
from bs4 import UnicodeDammit
from concurrent.futures import ThreadPoolExecutor
import models, logging, time

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s (%(levelname)s)]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8",
    handlers=[
        RichHandler(rich_tracebacks=True),
        logging.FileHandler(
            f"logs/log_{time.strftime('%Y%m%d%H%M%S')}.log", mode="a", encoding="utf-8"
        ),
    ],
)


def get_html(url: str) -> tuple[HTMLParser | None, str]:
    """
    Uses Selenium WebDriver to interact with a web page to return an HTML parser.

    The function attempts to insert data into the page and parse the page source with
    an HTMLParser. If this attempt fails, the function navigates to the provided URL,
    retrieves the page source, and saves it to a file. It then navigates back to the
    base URL and tries to process using the HTML file from the URL.

    Args:
        url (str): The URL to be evaluated.

    Returns:
        tuple[HTMLParser | None, str]: A tuple containing the HTMLParser object and the URL.
            - HTMLParser: An HTML parser object that can be used to parse the page source.
            - url (str): The URL that was evaluated.
    """

    options = webdriver.ChromeOptions()
    options.page_load_strategy = "eager"

    driver = webdriver.Remote(
        command_executor="http://localhost:4444",
        options=options,
    )

    driver.get(Config.BASE_URL)
    WebDriverWait(driver, timeout=2).until(
        ec.presence_of_element_located((By.CSS_SELECTOR, "div.containerTab"))
    )
    
    if url == "":
        return None, url

    try:
        insert_data(driver, "input#url", "input#input_tab_1.submit", url)
        tree = HTMLParser(driver.page_source)

        ok = bool(tree.select("h2").text_contains("Página Avaliada").matches)
        logging.info(f"{url=}, {ok=}")

        if not ok:
            logging.info(f"Retrieving HTML file for {url=}")
            driver.get(url)
            page_source = driver.page_source

            html_file = f"html_files/{encode_url(url)}.html"
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(UnicodeDammit(page_source, is_html=True).unicode_markup)

            logging.info(f"{url=} {html_file=} ({getsize(html_file) / 1_000:.2f}KB)")

            driver.get(Config.BASE_URL)
            WebDriverWait(driver, timeout=2).until(
                ec.presence_of_element_located((By.CSS_SELECTOR, "div.containerTab"))
            )

            driver.find_element(
                By.CSS_SELECTOR, "label#validacaoPeloArquivo.rarios"
            ).click()

            insert_data(
                driver,
                "input#up_file",
                "input#input_tab_2.submit",
                path.abspath(html_file),
                True,
            )

            tree = HTMLParser(driver.page_source)

            ok = bool(tree.select("h2").text_contains("Página Avaliada").matches)
            logging.info(f"[HTML] {url=}, {ok=}")
            if not ok:
                driver.quit()
                with open("broken_urls.txt", "a") as f:
                    f.write(url + "\n")

                return None, url

    except Exception as e:
        logging.error(f"[{url=}] {e}")
        driver.quit()
        with open("broken_urls.txt", "a") as f:
            f.write(url + "\n")
        return None, url

    driver.quit()

    return tree, url


def get_page_info(tree: HTMLParser, url: str) -> models.PageInfo:
    """
    Extracts page information from an HTML tree and returns a PageInfo object.

    Args:
        tree (HTMLParser): The HTML tree to extract information from.
        url (str): The URL of the page.

    Returns:
        models.PageInfo: The extracted page information.

    """
    strong_elements = tree.css("div.tile strong")
    num_lines_of_code = len(tree.css_first("code").text().split("\n"))
    page_info_dict = {}

    for element in strong_elements:
        key = element.text(strip=True)[:-1]
        info = element.next.text(strip=True)
        page_info_dict[key] = info

    page_info = models.PageInfo(
        url=page_info_dict.get("Página", url),
        name=page_info_dict["Título"],
        size_bytes=float(page_info_dict["Tamanho"].replace(" Bytes", "")) / 1_000,
        with_html="Página" not in page_info_dict,
        num_lines_of_code=num_lines_of_code,
    )

    return page_info


def get_ases_summary(tree: HTMLParser, url: str) -> models.ErrorsWarningsSummary:
    """
    Retrieves the summary of errors and warnings from the given HTML parser tree.

    Args:
        tree (HTMLParser): The HTML parser tree.
        url (str): The URL of the webpage.

    Returns:
        models.ErrorsWarningsSummary: The summary of errors and warnings.

    """

    ases_pct = tree.css_first("div#webaxscore span").text(strip=True)
    ases_pct = float(ases_pct.replace("%", "")) / 100

    summary_table = tree.css("table#tabelaErros tbody td")
    summary = [td.text(strip=True) for td in summary_table]

    summary = models.ErrorsWarningsSummary(
        url=url,
        ases_pct=ases_pct,
        n_markup_errors=int(summary[1]),
        n_behavior_errors=int(summary[4]),
        n_information_errors=int(summary[7]),
        n_presentation_errors=int(summary[10]),
        n_multimedia_errors=int(summary[13]),
        n_form_errors=int(summary[16]),
        n_markup_warnings=int(summary[2]),
        n_behavior_warnings=int(summary[5]),
        n_information_warnings=int(summary[8]),
        n_presentation_warnings=int(summary[11]),
        n_multimedia_warnings=int(summary[14]),
        n_form_warnings=int(summary[17]),
    )

    return summary


def get_emag_summary(tree: HTMLParser, url: str) -> list[models.ErrorsWarningsEMAG]:
    """
    Extracts error and warning information from the given HTML tree and returns a summary.

    Args:
        tree (HTMLParser): The HTML tree to extract information from.
        url (str): The URL associated with the extracted information.

    Returns:
        list[models.ErrorsWarningsEMAG]: A list of objects representing the extracted information.
    """

    tables = tree.css("table[class*=_error], table[class*=_warning]")

    emag_summary = []
    for table in tables:
        category, info_type = table.attributes["class"].split("_")
        data = [td.text(strip=True) for td in table.css("td")]

        if len(data) == 0:
            continue

        for i in range(0, len(data), 3):
            recommendation, quantity, code_lines = data[i : i + 3]
            recommendation = recommendation[:3]
            code_lines = list(map(str.strip, code_lines.split(",")))

            emag_info = models.ErrorsWarningsEMAG(
                url=url,
                category=category,
                info_type=info_type,
                recommendation=recommendation,
                quantity=quantity,
                source_code_lines=code_lines,
            )

            emag_summary.append(emag_info)

    return emag_summary


def run(tree: HTMLParser, url: str) -> None:
    """
    Runs the crawler on the given HTML tree and URL.

    Args:
        tree (HTMLParser): The HTML tree to crawl.
        url (str): The URL of the page to crawl.

    Returns:
        None
    """

    if tree is None:
        return None

    page_info = get_page_info(tree, url)
    store(page_info, Config.PAGE_INFO_FILENAME)

    summary_info = get_ases_summary(tree, page_info.url)
    store(summary_info, Config.ERR_WARN_SUMMARY_FILENAME)

    emag_info = get_emag_summary(tree, page_info.url)
    for info in emag_info:
        store(info, Config.EMAG_SUMMARY_FILENAME)

    return None


def main() -> None:
    for target in ("urls.txt", "broken_urls.txt"):
        logging.info(f"[{target}] Starting processing all URLs.")

        with open(target, "r") as f:
            urls = f.read().split("\n")

        if target == "broken_urls.txt":
            open(target, "w").close()

        if urls:    
            with ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
                results = list(executor.map(get_html, urls))

            for tree, url in results:
                run(tree, url)

        logging.info(f"[{target}] Finished processing all URLs.")

    return None


if __name__ == "__main__":
    open("broken_urls.txt", "w").close()
    create_csv_file(models.PageInfo, Config.PAGE_INFO_FILENAME)
    create_csv_file(models.ErrorsWarningsSummary, Config.ERR_WARN_SUMMARY_FILENAME)
    create_csv_file(models.ErrorsWarningsEMAG, Config.EMAG_SUMMARY_FILENAME)

    main()
