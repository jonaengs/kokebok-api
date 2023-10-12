import base64

from django.core.exceptions import ImproperlyConfigured

from kokebok import settings


def google_cloud_ocr(raw_img: bytes, hints: dict[str, str]) -> str:
    import google.auth
    from google.api_core.client_options import ClientOptions
    from google.auth.transport import requests
    from google.cloud import vision
    from google.cloud.vision_v1.types import ImageContext

    def text_to_dict(t):
        # Use if we ever want to return text bounds with text content
        vertices = [
            "({},{})".format(vertex.x, vertex.y)
            for vertex in t.bounding_poly.vertices
        ]
        return {"description": t.description, "bounds": vertices}

    def get_credentials():
        credentials, _project_id = google.auth.load_credentials_from_dict(
            settings.GOOGLE_CLOUD_CREDENTIALS
        )
        credentials = credentials.with_scopes(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        credentials.refresh(requests.Request())
        return credentials

    def get_vision_client(credentials) -> vision.ImageAnnotatorClient:
        opts = ClientOptions(api_endpoint="vision.googleapis.com")
        return vision.ImageAnnotatorClient(
            credentials=credentials, client_options=opts
        )

    client = get_vision_client(get_credentials())

    image_context = ImageContext(**hints)

    image = vision.Image(content=raw_img)
    response = client.text_detection(image=image, image_context=image_context)
    texts = response.text_annotations
    # Text annotations is a list where the first item seems to be
    # the complete recognized text as a single string
    # while the remaining items are each word recognized
    # along with the bounding box of each word
    # return text_to_dict(texts[0])
    full_text = texts[0]
    return full_text.description


def parse_img(b64_img: str, gpt_hint: str = "", ocr_lang_hint: str = "") -> str:
    # Takes a base64-encoded image file and
    # performs OCR on it before parsing the
    # resulting text into Recipe and RecipeIngredients model(s) (TODO)
    raw_img_data = base64.b64decode(b64_img)
    if settings.OCR_PROVIDER == "Google":
        img_text_content = google_cloud_ocr(
            raw_img_data,
            {"language_hints": ocr_lang_hint} if ocr_lang_hint else {},
        )
    else:
        raise ImproperlyConfigured("Select OCR provider is not supported")

    return img_text_content
