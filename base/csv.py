from io import BytesIO
from typing import Any

from django.http import FileResponse


def get_file_str(headers: list[str], data: list[list[Any]]):
    COL_SEP = ","
    ROW_SEP = "\n"

    first_row = COL_SEP.join(headers)
    data_rows = ROW_SEP.join(
        COL_SEP.join(
            ("~" if entry is None else str(entry) for entry in row),
        )
        for row in data
    )
    return first_row + ROW_SEP + data_rows


def create_csv_response(
    file_name: str,
    headers: list[str],
    data: list[list[Any]],
) -> FileResponse:

    file_str = get_file_str(headers, data)
    bytes_io = BytesIO(file_str.encode())
    return FileResponse(bytes_io, as_attachment=True, filename=file_name)
