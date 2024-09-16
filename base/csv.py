import zipfile
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

    # Correctly instantiate the BytesIO object
    bytes_io = BytesIO()
    with zipfile.ZipFile(bytes_io, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(file_name, file_str)

    # Set the buffer's position to the beginning
    bytes_io.seek(0)
    return FileResponse(bytes_io, as_attachment=True, filename=f"{file_name}.zip")
