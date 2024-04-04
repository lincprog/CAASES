from typing import List
from pydantic import BaseModel


class PageInfo(BaseModel):
    url: str
    name: str
    size_bytes: float
    with_html: bool
    num_lines_of_code: int


class ErrorsWarningsSummary(BaseModel):
    url: str
    ases_pct: float

    n_markup_errors: int
    n_behavior_errors: int
    n_information_errors: int
    n_presentation_errors: int
    n_multimedia_errors: int
    n_form_errors: int

    n_markup_warnings: int
    n_behavior_warnings: int
    n_information_warnings: int
    n_presentation_warnings: int
    n_multimedia_warnings: int
    n_form_warnings: int


class ErrorsWarningsEMAG(BaseModel):
    url: str
    category: str
    info_type: str
    recommendation: str
    quantity: int
    source_code_lines: List[str]
