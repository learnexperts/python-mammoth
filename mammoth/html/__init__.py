from ..lists import flat_map
from .nodes import TextNode, Tag, Element, ForceWrite, NodeVisitor


def text(value):
    return TextNode(value)


def tag(tag_names, attributes=None, collapsible=None, separator=None):
    if not isinstance(tag_names, list):
        tag_names = [tag_names]
    if attributes is None:
        attributes = {}
    return Tag(tag_names=tag_names, attributes=attributes, collapsible=bool(collapsible), separator=separator)


def element(tag_names, attributes=None, children=None, collapsible=None, separator=None):
    if children is None:
        children = []
        
    element_tag = tag(tag_names=tag_names, attributes=attributes, collapsible=collapsible, separator=separator)
    return Element(element_tag, children)


def collapsible_element(tag_names, attributes=None, children=None):
    return element(tag_names, attributes, children, collapsible=True)


force_write = ForceWrite()


def strip_empty(nodes):
    return flat_map(_strip_empty_node, nodes)


def _strip_empty_node(node):
    return StripEmpty().visit(node)


class StripEmpty(NodeVisitor):
    def visit_text_node(self, node):
        if node.value:
            return [node]
        else:
            return []
    
    def visit_element(self, element):
        children = strip_empty(element.children)
        if len(children) == 0 and not element.is_void():
            return []
        else:
            return [Element(element.tag, children, element.extra_attributes)]
    
    def visit_force_write(self, node):
        return [node]


def collapse(nodes):
    collapsed = []
    
    for node in nodes:
        _collapsing_add(collapsed, node)
    
    return collapsed

class _CollapseNode(NodeVisitor):
    def visit_text_node(self, node):
        return node
    
    def visit_element(self, element):
        return Element(element.tag, collapse(element.children), element.extra_attributes)
    
    def visit_force_write(self, node):
        return node
    
_collapse_node = _CollapseNode().visit


def _collapsing_add(collapsed, node):
    collapsed_node = _collapse_node(node)
    if not _try_collapse(collapsed, collapsed_node):
        collapsed.append(collapsed_node)
    
def _try_collapse(collapsed, node):
    if not collapsed:
        return False

    last = collapsed[-1]
    if not isinstance(last, Element) or not isinstance(node, Element):
        return False
    
    if not node.collapsible:
        return False
        
    if not _is_match(last, node):
        return False
    
    if node.separator:
        last.children.append(text(node.separator))
    
    for child in node.children:
        _collapsing_add(last.children, child)
        
    return True

def _is_match(first, second):
    if first.tag_name not in second.tag_names or first.attributes != second.attributes:
        return False

    # extra_attributes set from the docx numbering format (e.g. type="a" on
    # ol) are part of the element's identity: an alphabetic list must not
    # collapse into a preceding plain numbered one. The check is one-sided
    # because only the innermost list element of a paragraph's html path gets
    # those attributes — the outer ol/li wrappers of a nested list carry none
    # and must keep collapsing into whatever list they continue.
    first_attributes = _effective_attributes(first)
    return all(
        first_attributes.get(key) == value
        for key, value in _identity_attributes(second).items()
    )


# Per-item metadata rather than element identity: every list item carries a
# different data-li-order, so comparing it would stop list items from ever
# collapsing.
_IDENTITY_IGNORED_ATTRIBUTES = frozenset(["data-li-order"])


def _identity_attributes(element):
    if not element.extra_attributes:
        return {}
    return dict(
        (key, value)
        for key, value in element.extra_attributes.items()
        if key not in _IDENTITY_IGNORED_ATTRIBUTES
    )


def _effective_attributes(element):
    attributes = element.attributes.copy()
    attributes.update(_identity_attributes(element))
    return attributes


def write(writer, nodes):
    visitor = _NodeWriter(writer)
    visitor.visit_all(nodes)
        

class _NodeWriter(NodeVisitor):
    def __init__(self, writer):
        self._writer = writer
    
    def visit_text_node(self, node):
        self._writer.text(node.value)
    
    def visit_element(self, element):
      
        if element.extra_attributes is not None:
            attrs = element.attributes.copy()
            attrs.update( element.extra_attributes )
        else:
            attrs = element.attributes

        if element.is_void():
            self._writer.self_closing(element.tag_name, attrs)
        else:
            self._writer.start(element.tag_name, attrs)
            self.visit_all(element.children)
            self._writer.end(element.tag_name)
    
    def visit_force_write(self, element):
        pass
    
    def visit_all(self, nodes):
        for node in nodes:
            self.visit(node)
