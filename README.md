
# **CAASES**

[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/Pandas)](https://www.python.org/downloads/)  [![License: MIT](https://img.shields.io/badge/License-MIT-red.svg)](https://www.gnu.org/licenses/mit)  

CAASES is a web crawler created for extracting accessibility information from websites through the [Avaliador e Simulador de Acessibilidade em Sítios (ASES)](https://asesweb.governoeletronico.gov.br/)

The collected information includes:

## ASES Percentage

Initial evaluation of the page: URL, page size in bytes, and the accessibility percentage, ranging from 0 to 100%.

```json
{
  "url": "https://www.example.com/",
  "size": "1000",
  "perc_ases": "80.0%"
}
```

## Accessibility Summary (eMAG) - General

The accessibility summary based on [eMAG](https://emag.governoeletronico.gov.br/) recommendations presents errors and warnings for six evaluation sections: **markup**, **behavior**, **content/information**, **presentation/design**, **multimedia** and **forms**.

```json
{
  "errors_behavior": 0,
  "errors_forms": 0,
  "errors_information": 32,
  "errors_markup": 19,
  "errors_multimedia": 0,
  "errors_presentation": 1,
  "errors_total": 52,
  "warnings_behavior": 4,
  "warnings_forms": 0,
  "warnings_information": 35,
  "warnings_markup": 213,
  "warnings_multimedia": 2,
  "warnings_presentation": 0,
  "warnings_total": 254,
  "url": "https://www.example.com/"
}
```

## Accessibility Summary (eMAG) - Specific

For each error and warning in the sections above, ASES provides a recommendation based on eMAG. Possible indices for recommendations are defined on the eMAG website, the type can take values `["ERROR", "WARNING"]`, and the category can be `["MARK", "BEHAVIOR", "INFORMATION", "PRESENTATION", "MULTIMEDIA", "FORM"]`.

```json
{
  "recommendation": "1.2",
  "quantity": 10,
  "category": "MARK",
  "type": "ERROR",
  "url": "https://www.example.com/"
}
```

In the example above, ASES identified 10 errors in the markup category and, for these, makes the recommendation [Recomendação 1.2 – Organizar o código HTML de forma lógica e semântica](https://emag.governoeletronico.gov.br/#:~:text=Recomenda%C3%A7%C3%A3o%201.2%20%E2%80%93%20Organizar%20o%20c%C3%B3digo%20HTML%20de%20forma%20l%C3%B3gica%20e%20sem%C3%A2ntica)

## Installation

CAASES can be installed directly from the source using the following commands

```bash
git clone https://github.com/lincprog/CAASES.git
pip install -r requirements.txt
```

## Usage/Examples

The project structure is defined as follows:

```batch
📦ases-crawler
 ┣ 📂data  # data collected by the crawler
 ┃ ┣ 📜ases.parquet
 ┃ ┣ 📜errors_warnings.parquet
 ┃ ┗ 📜accessibility_summary.parquet
 ┣ 📂logs
 ┣ 📂temp
 ┃ ┗ 📜site.html
 ┣ 📜README.md
 ┣ 📜requirements.txt  # dependencies
 ┣ 📜utils.py   # utility functions used in the notebook
 ┗ 📜web_crawler_ases.ipynb
 ```

In the `web_crawler_ases.ipynb` file, in the section `1. Parameter Configuration`, define the URLs to be processed in the indicated field:

```python
# Insert the list of URLs to be processed:
urls: list[str] = ["https://www.site1.com/", "https://www.site2.com/"]
```

Finally, to start the processing, in section `2.1. Extraction, Processing, and Storage`, execute the cell

```python
pipeline.process()
```
