import zipfile
from io import BytesIO
from typing import Any, Callable, Generator
from django.http import FileResponse, StreamingHttpResponse

COL_SEP = ","
ROW_SEP = "\n"


def convert_data_row(data: list[Any]):
    return COL_SEP.join(
        ("~" if entry is None else str(entry) for entry in data),
    )


def get_file_str(headers: list[str], data: list[list[Any]]):

    first_row = convert_data_row(headers)
    data_rows = ROW_SEP.join(convert_data_row(row) for row in data)
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


def create_csv_streaming_response(
    file_name: str, headers: list[str], data_generator: Generator[list[Any], None, None]
):
    def generate_file():
        yield convert_data_row(headers) + ROW_SEP
        for item in data_generator:
            yield convert_data_row(item) + ROW_SEP

    response = StreamingHttpResponse(generate_file())
    response["Content-Disposition"] = f'attachement; filename="{file_name}"'
    return response
