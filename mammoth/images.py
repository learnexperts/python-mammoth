import base64

from . import html


def img_element(func):
    def convert_image(image):
        attributes = func(image).copy()       
        if getattr(image, "_has_border", False) or (image.attributes and image.attributes.get("_has_border")):
            print("convert_image: _has_border detected")
            existing_class = attributes.get("class", "")
            attributes["class"] = (existing_class + " fr-bordered").strip()            
        attributes.pop("_has_border", None)
                
        if image.alt_text:
            attributes["alt"] = image.alt_text
        if image.size:
            attributes["width"] = image.size.width
            attributes["height"] = image.size.height
            
        return [html.element("img", attributes)]
    
    return convert_image

# Undocumented, but retained for backwards-compatibility with 0.3.x
inline = img_element


@img_element
def data_uri(image):
    with image.open() as image_bytes:
        encoded_src = base64.b64encode(image_bytes.read()).decode("ascii")
    
    return {
        "src": "data:{0};base64,{1}".format(image.content_type, encoded_src)
    }
