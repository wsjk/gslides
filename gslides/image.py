from . import creds
from typing import Optional, Tuple

class Image:
    def __init__(self) -> None:
        self.drive_service = creds.drive_service
        self.slide_service = creds.slide_service

    def upload_to_drive(self, file_path: str) -> Tuple[str, str]:
        import mimetypes
        import os
        from googleapiclient.http import MediaFileUpload
        mime_type, _ = mimetypes.guess_type(file_path)
        mime_type = mime_type or 'image/png'
        file_metadata = {'name': os.path.basename(file_path), 'mimeType': mime_type}
        media = MediaFileUpload(file_path, mimetype=mime_type)
        file = self.drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        file_id = file.get('id')
        if not file_id:
            raise RuntimeError("Failed to upload image to Google Drive.")
        # Make the file public so Google Slides API can access it
        self.drive_service.permissions().create(
            fileId=file_id,
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()
        url = f"https://drive.google.com/uc?id={file_id}"
        return url, file_id

    def insert_image_to_slide(
        self,
        presentation_id: str,
        slide_id: str,
        image_url: str,
        left: float,
        top: float,
        width: float,
        height: float,
        file_id: Optional[str] = None
    ) -> None:
        import uuid
        # Always attempt to delete the file from Drive, even if an error occurs
        try:
            image_id = f"image_{uuid.uuid4().hex}"
            requests = [{
                "createImage": {
                    "objectId": image_id,
                    "url": image_url,
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "height": {"magnitude": height, "unit": "PT"},
                            "width": {"magnitude": width, "unit": "PT"}
                        },
                        "transform": {
                            "scaleX": 1,
                            "scaleY": 1,
                            "translateX": left,
                            "translateY": top,
                            "unit": "PT"
                        }
                    }
                }
            }]
            self.slide_service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={"requests": requests}
            ).execute()
        finally:
            if file_id:
                try:
                    self.drive_service.files().delete(fileId=file_id).execute()
                except Exception:
                    pass
