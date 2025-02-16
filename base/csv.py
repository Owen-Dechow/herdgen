from io import BytesIO
from random import choice
from typing import Any, Iterator
import zipfile

from background_task import background
import boto3
from django.conf import settings
from django.core.mail import send_mail
from django.http import FileResponse

from base import models

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


@background(schedule=0)
def create_animal_csv(classid: int, userid: int):
    import boto3
    from io import BytesIO

    s3 = boto3.client("s3")
    bucketname = settings.AWS_STORAGE_BUCKET_NAME
    uid = "".join(choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(10))
    filekey = f"animal_charts/AnimalChart-{uid}.csv"
    connectedclass = models.Class.objects.get(id=classid)
    headers = connectedclass.get_animal_file_headers()
    data_keys = connectedclass.get_animal_file_data_order()

    def iterator() -> Iterator[list[Any]]:
        for animal in models.Animal.objects.filter(
            connectedclass=connectedclass
        ).iterator(chunk_size=5_000):
            row = []
            for key in data_keys:
                row.append(animal.resolve_data_key(key))
            yield row

    # Initialize multipart upload
    response = s3.create_multipart_upload(Bucket=bucketname, Key=filekey)
    upload_id = response["UploadId"]
    part_number = 1
    parts = []
    min_part_size = 5 * 1024 * 1024  # 5MB

    buffer = BytesIO()
    buffer.write(f"{convert_data_row(headers)}{ROW_SEP}".encode("utf-8"))

    for item in iterator():
        buffer.write(f"{convert_data_row(item)}{ROW_SEP}".encode("utf-8"))

        if buffer.tell() >= min_part_size:
            buffer.seek(0)
            response = s3.upload_part(
                Bucket=bucketname,
                Key=filekey,
                PartNumber=part_number,
                UploadId=upload_id,
                Body=buffer,
            )
            parts.append({"PartNumber": part_number, "ETag": response["ETag"]})
            part_number += 1
            buffer = BytesIO()

    # Upload the last part
    if buffer.tell() > 0:
        buffer.seek(0)
        response = s3.upload_part(
            Bucket=bucketname,
            Key=filekey,
            PartNumber=part_number,
            UploadId=upload_id,
            Body=buffer,
        )
        parts.append({"PartNumber": part_number, "ETag": response["ETag"]})

    # Complete multipart upload
    s3.complete_multipart_upload(
        Bucket=bucketname,
        Key=filekey,
        UploadId=upload_id,
        MultipartUpload={"Parts": parts},
    )

    user = models.User.objects.get(id=userid)
    link = f"https://{bucketname}.s3.amazonaws.com/{filekey}"

    send_mail(
        "Animal Chart Ready",
        "The animal chart you requested from HerdGenetics is ready."
        + f" You can download the file at {link}",
        settings.EMAIL_HOST_USER,
        [user.email],
        fail_silently=False,
    )
