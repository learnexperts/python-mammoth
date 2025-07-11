# coding=utf-8

from __future__ import unicode_literals

import base64
import io
import shutil
import os

import tempman
from nose.tools import istest, assert_equal

from .testing import test_path

import mammoth
from mammoth import results


@istest
def docx_containing_one_paragraph_is_converted_to_single_p_element():
    with open(test_path("single-paragraph.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj)
        assert_equal("<p>Walking on imported air</p>", result.value)
        assert_equal([], result.messages)


@istest
def can_read_xml_files_with_utf8_bom():
    with open(test_path("utf8-bom.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj)
        assert_equal("<p>This XML has a byte order mark.</p>", result.value)
        assert_equal([], result.messages)


@istest
def empty_paragraphs_are_ignored_by_default():
    with open(test_path("empty.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj)
        assert_equal("", result.value)
        assert_equal([], result.messages)


@istest
def empty_paragraphs_are_preserved_if_ignore_empty_paragraphs_is_false():
    with open(test_path("empty.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj, ignore_empty_paragraphs=False)
        assert_equal("<p></p>", result.value)
        assert_equal([], result.messages)


@istest
def embedded_style_map_is_used_if_present():
    with open(test_path("embedded-style-map.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj)
        assert_equal("<h1>Walking on imported air</h1>", result.value)
        assert_equal([], result.messages)


@istest
def explicit_style_map_takes_precedence_over_embedded_style_map():
    with open(test_path("embedded-style-map.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj, style_map="p => p")
        assert_equal("<p>Walking on imported air</p>", result.value)
        assert_equal([], result.messages)


@istest
def explicit_style_map_is_combined_with_embedded_style_map():
    with open(test_path("embedded-style-map.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj, style_map="r => strong")
        assert_equal("<h1><strong>Walking on imported air</strong></h1>", result.value)
        assert_equal([], result.messages)


@istest
def embedded_style_maps_can_be_disabled():
    with open(test_path("embedded-style-map.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj, include_embedded_style_map=False)
        assert_equal("<p>Walking on imported air</p>", result.value)
        assert_equal([], result.messages)


@istest
def embedded_style_map_can_be_written_and_then_read():
    with _copy_of_test_data("single-paragraph.docx") as fileobj:
        mammoth.embed_style_map(fileobj, "p => h1")
        result = mammoth.convert_to_html(fileobj=fileobj, ignore_empty_paragraphs=False)
        assert_equal("<h1>Walking on imported air</h1>", result.value)
        assert_equal([], result.messages)


@istest
def embedded_style_map_can_be_retrieved():
    with _copy_of_test_data("single-paragraph.docx") as fileobj:
        mammoth.embed_style_map(fileobj, "p => h1")
        assert_equal("p => h1", mammoth.read_embedded_style_map(fileobj))


@istest
def warning_if_style_mapping_is_not_understood():
    style_map = """
!!!!
p => h1"""
    with open(test_path("single-paragraph.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj, style_map=style_map)
        assert_equal("<h1>Walking on imported air</h1>", result.value)
        warning = "Did not understand this style mapping, so ignored it: !!!!"
        assert_equal([results.warning(warning)], result.messages)


@istest
def inline_images_referenced_by_path_relative_to_part_are_included_in_output():
    with open(test_path("tiny-picture.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj)
        html = result.value
        assert '<img' in html, "Expected an image in the output"
        assert 'src="data:image/png;base64' in html, "Expected base64 image in output"
        assert_equal([], result.messages)


@istest
def inline_images_referenced_by_path_relative_to_base_are_included_in_output():
    with open(test_path("tiny-picture-target-base-relative.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj)
        html = result.value
        assert '<img' in html, "Expected an image in the output"
        assert 'src="data:image/png;base64' in html, "Expected base64 image in output"
        assert_equal([], result.messages)


@istest
def images_stored_outside_of_document_are_included_in_output():
    with open(test_path("external-picture.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj)
        html = result.value
        assert '<img' in html, "Expected an image in the output"
        assert 'src="data:image/png;base64' in html, "Expected base64 image in output"
        assert_equal([], result.messages)


@istest
def warn_if_images_stored_outside_of_document_are_specified_when_passing_fileobj_without_name():
    fileobj = io.BytesIO()
    with open(test_path("external-picture.docx"), "rb") as source_fileobj:
        shutil.copyfileobj(source_fileobj, fileobj)
    
    result = mammoth.convert_to_html(fileobj=fileobj)
    assert_equal("", result.value)
    assert_equal([results.warning("could not find external image 'tiny-picture.png', fileobj has no name")], result.messages)


@istest
def warn_if_images_stored_outside_of_document_are_not_found():
    with tempman.create_temp_dir() as temp_dir:
        document_path = os.path.join(temp_dir.path, "document.docx")
        with open(document_path, "wb") as fileobj:
            with open(test_path("external-picture.docx"), "rb") as source_fileobj:
                shutil.copyfileobj(source_fileobj, fileobj)
    
        with open(document_path, "rb") as fileobj:
            result = mammoth.convert_to_html(fileobj=fileobj)
            assert_equal("", result.value)
            expected_warning = "could not open external image: 'tiny-picture.png'"
            assert_equal("warning", result.messages[0].type)
            assert result.messages[0].message.startswith(expected_warning), "message was: " + result.messages[0].message
            assert_equal(1, len(result.messages))


@istest
def image_conversion_can_be_customised():
    @mammoth.images.img_element
    def convert_image(image):
        with image.open() as image_bytes:
            encoded_src = base64.b64encode(image_bytes.read()).decode("ascii")
        
        return {
            "src": encoded_src[:2] + "," + image.content_type
        }
    
    with open(test_path("tiny-picture.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj, convert_image=convert_image)
        html = result.value
        assert '<img' in html, "Expected an image in the output"
        assert 'src="iV,image/png"' in html, "Expected customised image source in output"
        assert_equal([], result.messages)
        

@istest
def simple_list_is_converted_to_list_elements():
    with open(test_path("simple-list.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj)
        assert_equal([], result.messages)
        assert_equal("""<ul type="disc"><li data-li-order="1">Apple</li><li data-li-order="2">Banana</li></ul>""", result.value)


@istest
def word_tables_are_converted_to_html_tables():
    expected_html = ("<p>Above</p>" +
        "<table>" +
        "<tr><td><p>Top left</p></td><td><p>Top right</p></td></tr>" +
        "<tr><td><p>Bottom left</p></td><td><p>Bottom right</p></td></tr>" +
        "</table>" +
        "<p>Below</p>")
    
    
    with open(test_path("tables.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj)
        assert_equal([], result.messages)
        assert_equal(expected_html, result.value)


@istest
def footnotes_are_appended_to_text():
    # TODO: don't duplicate footnotes with multiple references
    expected_html = ('<p>Ouch' +
        '<sup><a href="#doc-42-footnote-1" id="doc-42-footnote-ref-1">[1]</a></sup>.' +
        '<sup><a href="#doc-42-footnote-2" id="doc-42-footnote-ref-2">[2]</a></sup></p>' +
        '<ol><li id="doc-42-footnote-1"><p> A tachyon walks into a bar. <a href="#doc-42-footnote-ref-1">↑</a></p></li>' +
        '<li id="doc-42-footnote-2"><p> Fin. <a href="#doc-42-footnote-ref-2">↑</a></p></li></ol>')
    
    with open(test_path("footnotes.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj, id_prefix="doc-42-")
        assert_equal([], result.messages)
        assert_equal(expected_html, result.value)


@istest
def endnotes_are_appended_to_text():
    expected_html = ('<p>Ouch' +
        '<sup><a href="#doc-42-endnote-2" id="doc-42-endnote-ref-2">[1]</a></sup>.' +
        '<sup><a href="#doc-42-endnote-3" id="doc-42-endnote-ref-3">[2]</a></sup></p>' +
        '<ol><li id="doc-42-endnote-2"><p> A tachyon walks into a bar. <a href="#doc-42-endnote-ref-2">↑</a></p></li>' +
        '<li id="doc-42-endnote-3"><p> Fin. <a href="#doc-42-endnote-ref-3">↑</a></p></li></ol>')
    
    with open(test_path("endnotes.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj, id_prefix="doc-42-")
        assert_equal([], result.messages)
        assert_equal(expected_html, result.value)


@istest
def relationships_are_handled_properly_in_footnotes():
    expected_html = (
        '<p><sup><a href="#doc-42-footnote-1" id="doc-42-footnote-ref-1">[1]</a></sup></p>' +
        '<ol><li id="doc-42-footnote-1"><p> <a href="http://www.example.com">Example</a> <a href="#doc-42-footnote-ref-1">↑</a></p></li></ol>')
    
    with open(test_path("footnote-hyperlink.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj, id_prefix="doc-42-")
        assert_equal([], result.messages)
        assert_equal(expected_html, result.value)


@istest
def when_style_mapping_is_defined_for_comment_references_then_comments_are_included():
    expected_html = (
        '<p>Ouch' +
        '<sup><a href="#doc-42-comment-0" id="doc-42-comment-ref-0">[MW1]</a></sup>.' +
        '<sup><a href="#doc-42-comment-2" id="doc-42-comment-ref-2">[MW2]</a></sup></p>' +
        '<dl><dt id="doc-42-comment-0">Comment [MW1]</dt><dd><p>A tachyon walks into a bar. <a href="#doc-42-comment-ref-0">↑</a></p></dd>' +
        '<dt id="doc-42-comment-2">Comment [MW2]</dt><dd><p>Fin. <a href="#doc-42-comment-ref-2">↑</a></p></dd></dl>'
    )
    
    with open(test_path("comments.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj, id_prefix="doc-42-", style_map="comment-reference => sup")
        assert_equal([], result.messages)
        assert_equal(expected_html, result.value)


@istest
def text_boxes_are_read():
    with open(test_path("text-box.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj)
        assert_equal('<p>Datum plane</p>', result.value)


@istest
def underline_is_ignored_by_default():
    with open(test_path("underline.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj)
        assert_equal('<p><strong>The Sunset Tree</strong></p>', result.value)


@istest
def underline_can_be_configured_with_style_mapping():
    with open(test_path("underline.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj, style_map="u => em")
        assert_equal('<p><strong>The <em>Sunset</em> Tree</strong></p>', result.value)


@istest
def strikethrough_is_converted_to_s_element_by_default():
    with open(test_path("strikethrough.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj)
        assert_equal("<p><s>Today's Special: Salmon</s> Sold out</p>", result.value)


@istest
def strikethrough_conversion_can_be_configured_with_style_mapping():
    with open(test_path("strikethrough.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj, style_map="strike => del")
        assert_equal("<p><del>Today's Special: Salmon</del> Sold out</p>", result.value)


@istest
def transform_document_is_applied_to_document_before_conversion():
    def transform_document(document):
        document.children[0].style_id = "Heading1"
        return document
    
    with open(test_path("single-paragraph.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj, transform_document=transform_document)
        assert_equal("<h1>Walking on imported air</h1>", result.value)
        assert_equal([], result.messages)


@istest
def paragraph_transform_only_transforms_paragraphs():
    def transform_paragraph(paragraph):
        return paragraph.copy(style_id="Heading1")
    transform_document = mammoth.transforms.paragraph(transform_paragraph)
    with open(test_path("single-paragraph.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj, transform_document=transform_document)
        assert_equal("<h1>Walking on imported air</h1>", result.value)
        assert_equal([], result.messages)


@istest
def docx_containing_one_paragraph_can_be_converted_to_markdown():
    with open(test_path("single-paragraph.docx"), "rb") as fileobj:
        result = mammoth.convert_to_markdown(fileobj=fileobj)
        assert_equal("Walking on imported air\n\n", result.value)
        assert_equal([], result.messages)


@istest
def can_extract_raw_text():
    with open(test_path("simple-list.docx"), "rb") as fileobj:
        result = mammoth.extract_raw_text(fileobj=fileobj)
        assert_equal([], result.messages)
        assert_equal("Apple\n\nBanana\n\n", result.value)

@istest
def ordered_lists_respect_the_start_number():
    with open(test_path("ordered-list-numbering.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj)
        assert_equal("""<ol><li data-li-order="7">Seven</li><li data-li-order="8">Eight</li><li data-li-order="9">Nine</li><li data-li-order="10">Ten</li><li data-li-order="11">Eleven</li><li data-li-order="1">One<ol type="a"><li data-li-order="5">EE</li><li data-li-order="6">FF</li></ol></li><li data-li-order="2">Two</li></ol>""", result.value)
                     
@istest
def ordered_lists_are_continued_from_previous():
    with open(test_path("ordered-nested-list-numbering.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj)
        assert_equal("""<ol><li data-li-order="1">One <ol type="a"><li data-li-order="1">One a </li><li data-li-order="2">One b </li><li data-li-order="3">One c </li></ol></li><li data-li-order="2">Two <ol type="a"><li data-li-order="1">Two a</li></ol></li></ol><p>Para 1</p><ul><li><ol type="a"><li data-li-order="2">Two b</li></ol></li></ul><ol><li data-li-order="3">Three<ol type="a"><li data-li-order="7">Three g</li><li data-li-order="8">Three h </li></ol></li></ol><p>Para 2</p><ol><li data-li-order="4">Four </li><li data-li-order="5">Five </li><li data-li-order="7">Seven</li></ol>""", result.value)

@istest
def paragraphs_are_aligned():
    with open(test_path("alignment.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj)
        assert_equal("""<p>Left</p><p data-alignment="center">Middle</p><p data-alignment="right">Right</p>""", result.value)

@istest
def paragraphs_have_style_names():
    with open(test_path("style_names.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj)
        assert_equal("""<p>Normal</p><p data-style-name="No Spacing">No Spacing</p><p data-style-name="Quote">Quote</p><p data-style-name="Intense Quote">Intense Quote</p>""", result.value)

def _copy_of_test_data(path):
    destination = io.BytesIO()
    with open(test_path(path), "rb") as source:
        shutil.copyfileobj(source, destination)
    return destination

@istest
def image_borders_are_preserved():
    with open(test_path("image-borders.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj)
        html = result.value
        
        # Count bordered images
        bordered_count = html.count('class="fr-bordered"')
        
        # Verify that bordered images have the correct class
        assert bordered_count > 0, "Should have at least one bordered image"
        
        # Count total images
        total_images = html.count('<img')
        
        # Verify that some images don't have borders (non-bordered images)
        non_bordered_count = total_images - bordered_count
        assert non_bordered_count > 0, "Should have at least one non-bordered image"
        
        # Verify that non-bordered images don't have the fr-bordered class
        assert html.count('class="fr-bordered"') == bordered_count, "Only bordered images should have fr-bordered class"
        assert "class=\"fr-bordered\"" in html
        
@istest
def font_colors_are_preserved():
    with open(test_path("font-colors.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj)
        html = result.value
        print("\nHTML Output:\n", html)
        assert 'style="color: #' in html

@istest
def paragraphs_with_numId_zero_stripped():
    with open(test_path("num-Id-numbered-list.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj)
        html = result.value
        print("\nHTML Output:\n", html)
        assert "<ol>" not in html, "No <ol> should be rendered for numId=0"
        assert "<ul>" not in html, "No <ul> should be rendered for numId=0"
        assert "<li>" not in html, "No <li> should be rendered for numId=0"
        assert "<p>" in html, "Should render normal paragraphs"
