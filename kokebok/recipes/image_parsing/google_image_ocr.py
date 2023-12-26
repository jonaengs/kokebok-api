import google.auth
from google.api_core.client_options import ClientOptions
from google.auth.transport import requests
from google.cloud import vision
from google.cloud.vision_v1.types import ImageContext, TextAnnotation

from kokebok import settings


def _text_to_dict(t):
    # Use if we ever want to return text bounds with text content
    vertices = [
        "({},{})".format(vertex.x, vertex.y) for vertex in t.bounding_poly.vertices
    ]
    return {"description": t.description, "bounds": vertices}


def _get_credentials():
    credentials, _project_id = google.auth.load_credentials_from_dict(
        settings.GOOGLE_CLOUD_CREDENTIALS
    )
    credentials = credentials.with_scopes(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(requests.Request())
    return credentials


def _get_vision_client(credentials) -> vision.ImageAnnotatorClient:
    opts = ClientOptions(api_endpoint="vision.googleapis.com")
    return vision.ImageAnnotatorClient(credentials=credentials, client_options=opts)


def alternate_google_cloud_ocr(raw_img: bytes, hints: dict[str, str]) -> str:
    """
    Unfinished.
    Tries to extract more information about the positions of
    blocks of texts.

    Resources:
    * On grouping text: https://stackoverflow.com/a/52389731
    * Tutorial: https://cloud.google.com/vision/docs/fulltext-annotations
    * On grouping text: https://stackoverflow.com/a/52086299
    """

    BreakType = TextAnnotation.DetectedBreak.BreakType
    break_to_symbol = {
        BreakType.UNKNOWN: "",
        BreakType.SPACE: " ",
        BreakType.SURE_SPACE: " ",
        BreakType.EOL_SURE_SPACE: "\n",
        BreakType.HYPHEN: "",
        BreakType.LINE_BREAK: "\n",
    }

    client = _get_vision_client(_get_credentials())

    image_context = ImageContext(**hints)

    image = vision.Image(content=raw_img)
    # Note: uses document_text_detection instead of text_detection
    # This gives access to more info about text groupings,
    # and possibly gives better OCR results in general?
    response = client.document_text_detection(image=image, image_context=image_context)
    texts = response.text_annotations

    full_text = response.full_text_annotation
    print("PAGES:")
    for page in full_text.pages:
        # print(page.__dict__)
        print(page.property)
        print("BLOCKS:")
        for block in page.blocks:
            text = ""
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    for symbol in word.symbols:
                        text += symbol.text
                        if hasattr(symbol, "property"):
                            break_type = symbol.property.detected_break.type
                            text += break_to_symbol[break_type]

            print(text)
            print("---------")
    full_text = texts[0]
    return full_text.description


def google_cloud_ocr(raw_img: bytes, hints: dict[str, str]) -> str:
    client = _get_vision_client(_get_credentials())

    image_context = ImageContext(**hints)

    image = vision.Image(content=raw_img)
    response = client.text_detection(image=image, image_context=image_context)
    texts = response.text_annotations
    # Text annotations is a list where the first item seems to be
    # the complete recognized text as a single string
    # while the remaining items are each word recognized
    # along with the bounding box of each word
    # return _text_to_dict(texts[0])
    full_text = texts[0]
    return full_text.description
