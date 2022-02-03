from .. import documents


def read_document_xml_element(
        element,
        body_reader,
        notes=None,
        comments=None):

    if notes is None:
        notes = []
    if comments is None:
        comments = []

    body_element = element.find_child("w:body")
    if body_element is None:
        children = []
    else:
        children = body_element.children

    return body_reader.read_all(children) \
        .map(lambda children: documents.document(
            children,
            notes=documents.notes(notes),
            comments=comments
        ))
