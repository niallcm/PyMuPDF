# encoding utf-8
"""
* Confirm sample doc has no links and no annots.
* Confirm proper release of file handles via Document.close()
* Confirm properly raising exceptions in document creation
"""
import io
import os

import fitz
import pickle

scriptdir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(scriptdir, "resources", "001003ED.pdf")


def test_haslinks():
    doc = fitz.open(filename)
    assert doc.has_links() == False


def test_hasannots():
    doc = fitz.open(filename)
    assert doc.has_annots() == False


def test_haswidgets():
    doc = fitz.open(filename)
    assert doc.is_form_pdf == False


def test_isrepaired():
    doc = fitz.open(filename)
    assert doc.is_repaired == False
    fitz.TOOLS.mupdf_warnings()


def test_isdirty():
    doc = fitz.open(filename)
    assert doc.is_dirty == False


def test_cansaveincrementally():
    doc = fitz.open(filename)
    assert doc.can_save_incrementally() == True


def test_iswrapped():
    doc = fitz.open(filename)
    page = doc[0]
    assert page.is_wrapped


def test_wrapcontents():
    doc = fitz.open(filename)
    page = doc[0]
    page.wrap_contents()
    xref = page.get_contents()[0]
    cont = page.read_contents()
    doc.update_stream(xref, cont)
    page.set_contents(xref)
    assert len(page.get_contents()) == 1
    page.clean_contents()


def test_page_clean_contents():
    """Assert that page contents cleaning actually is invoked."""
    doc = fitz.open()
    page = doc.new_page()

    # draw two rectangles - will lead to two /Contents objects
    page.draw_rect((10, 10, 20, 20))
    page.draw_rect((20, 20, 30, 30))
    assert len(page.get_contents()) == 2
    assert page.read_contents().startswith(b"q") == False

    # clean / consolidate into one /Contents object
    page.clean_contents()
    assert len(page.get_contents()) == 1
    assert page.read_contents().startswith(b"q") == True


def test_annot_clean_contents():
    """Assert that annot contents cleaning actually is invoked."""
    doc = fitz.open()
    page = doc.new_page()
    annot = page.add_highlight_annot((10, 10, 20, 20))

    # the annotation appearance will not start with command b"q"
    assert annot._getAP().startswith(b"q") == False

    # invoke appearance stream cleaning and reformatting
    annot.clean_contents()

    # appearance stream should now indeed start with command b"q"
    assert annot._getAP().startswith(b"q") == True


def test_config():
    assert fitz.TOOLS.fitz_config["py-memory"] in (True, False)


def test_glyphnames():
    name = "infinity"
    infinity = fitz.glyph_name_to_unicode(name)
    assert fitz.unicode_to_glyph_name(infinity) == name


def test_rgbcodes():
    sRGB = 0xFFFFFF
    assert fitz.sRGB_to_pdf(sRGB) == (1, 1, 1)
    assert fitz.sRGB_to_rgb(sRGB) == (255, 255, 255)


def test_pdfstring():
    fitz.get_pdf_now()
    fitz.get_pdf_str("Beijing, chinesisch 北京")
    fitz.get_text_length("Beijing, chinesisch 北京", fontname="china-s")
    fitz.get_pdf_str("Latin characters êßöäü")


def test_open_exceptions():
    try:
        doc = fitz.open(filename, filetype="xps")
    except RuntimeError as e:
        assert repr(e).startswith("FileDataError")

    try:
        doc = fitz.open(filename, filetype="xxx")
    except Exception as e:
        assert repr(e).startswith("ValueError")

    try:
        doc = fitz.open("x.y")
    except Exception as e:
        assert repr(e).startswith("FileNotFoundError")

    try:
        doc = fitz.open("pdf", b"")
    except RuntimeError as e:
        assert repr(e).startswith("EmptyFileError")


def test_bug1945():
    pdf = fitz.open(f'{scriptdir}/resources/bug1945.pdf')
    buffer_ = io.BytesIO()
    pdf.save(buffer_, clean=True)


def test_bug1971():
    for _ in range(2):
        doc = fitz.Document(f'{scriptdir}/resources/bug1971.pdf')
        page = next(doc.pages())
        page.get_drawings()
        doc.close()
        assert doc.is_closed

def test_default_font():
    f = fitz.Font()
    assert str(f) == "Font('Noto Serif Regular')"
    assert repr(f) == "Font('Noto Serif Regular')"

def test_add_ink_annot():
    import math
    document = fitz.Document()
    page = document.new_page()
    line1 = []
    line2 = []
    for a in range( 0, 360*2, 15):
        x = a
        c = 300 + 200 * math.cos( a * math.pi/180)
        s = 300 + 100 * math.sin( a * math.pi/180)
        line1.append( (x, c))
        line2.append( (x, s))
    page.add_ink_annot( [line1, line2])
    page.insert_text((100, 72), 'Hello world')
    page.add_text_annot((200,200), "Some Text")
    page.get_bboxlog()
    path = f'{scriptdir}/resources/test_add_ink_annot.pdf'
    document.save( path)
    print( f'Have saved to: path={path!r}')

def test_techwriter_append():
    print(fitz.__doc__)
    doc = fitz.open()
    page = doc.new_page()
    tw = fitz.TextWriter(page.rect)
    text = "Red rectangle = TextWriter.text_rect, blue circle = .last_point"
    r = tw.append((100, 100), text)
    print(f'r={r!r}')
    tw.write_text(page)
    page.draw_rect(tw.text_rect, color=fitz.pdfcolor["red"])
    page.draw_circle(tw.last_point, 2, color=fitz.pdfcolor["blue"])
    path = f"{scriptdir}/resources/test_techwriter_append.pdf"
    doc.ez_save(path)
    print( f'Have saved to: {path}')

def test_opacity():
    doc = fitz.open()
    page = doc.new_page()

    annot1 = page.add_circle_annot((50, 50, 100, 100))
    annot1.set_colors(fill=(1, 0, 0), stroke=(1, 0, 0))
    annot1.set_opacity(2 / 3)
    annot1.update(blend_mode="Multiply")

    annot2 = page.add_circle_annot((75, 75, 125, 125))
    annot2.set_colors(fill=(0, 0, 1), stroke=(0, 0, 1))
    annot2.set_opacity(1 / 3)
    annot2.update(blend_mode="Multiply")
    outfile = f'{scriptdir}/resources/opacity.pdf'
    doc.save(outfile, expand=True, pretty=True)
    print("saved", outfile)

def test_get_text_dict():
    import json
    doc=fitz.open(f'{scriptdir}/resources/v110-changes.pdf')
    page=doc[0]
    blocks=page.get_text("dict")["blocks"]
    # Check no opaque types in `blocks`.
    json.dumps( blocks, indent=4)

def test_font():
    font = fitz.Font()
    print(repr(font))
    bbox = font.glyph_bbox( 65)
    print( f'bbox={bbox!r}')

def test_insert_font():
    doc=fitz.open(f'{scriptdir}/resources/v110-changes.pdf')
    page = doc[0]
    i = page.insert_font()
    print( f'page.insert_font() => {i}')

def test_2173():
    from fitz import IRect, Pixmap, CS_RGB, Colorspace
    for i in range( 100):
        #print( f'i={i!r}')
        image = Pixmap(Colorspace(CS_RGB), IRect(0, 0, 13, 37))
    print( 'test_2173() finished')

def test_texttrace():
    import time
    document = fitz.Document( f'{scriptdir}/resources/joined.pdf')
    t = time.time()
    for page in document:
        tt = page.get_texttrace()
    t = time.time() - t
    print( f'test_texttrace(): t={t!r}')

    # Repeat, this time writing data to file.
    import json
    path = f'{scriptdir}/resources/test_texttrace.txt'
    print( f'Writing to: {path}')
    with open( path, 'w') as f:
        for i, page in enumerate(document):
            tt = page.get_texttrace()
            print( f'page {i} json:\n{json.dumps(tt, indent="    ")}', file=f)


def test_2533():
    """Assert correct char bbox in page.get_texttrace().

    Search for a unique char on page and confirm that page.get_texttrace()
    returns the same bbox as the search method.
    """
    if hasattr(fitz, 'mupdf') and not fitz.g_use_extra:
        print('Not running test_2533() because rebased with use_extra=0 known to fail')
        return
    doc = fitz.open(os.path.join(scriptdir, "resources", "test_2533.pdf"))
    page = doc[0]
    NEEDLE = "民"
    ord_NEEDLE = ord(NEEDLE)
    for span in page.get_texttrace():
        for char in span["chars"]:
            if char[0] == ord_NEEDLE:
                bbox = fitz.Rect(char[3])
                break
    assert page.search_for(NEEDLE)[0] == bbox


def test_2645():
    """Assert same font size calculation in corner cases.
    """
    folder = os.path.join(scriptdir, "resources")
    files = ("test_2645_1.pdf", "test_2645_2.pdf", "test_2645_3.pdf")
    for f in files:
        doc = fitz.open(os.path.join(folder, f))
        page = doc[0]
        fontsize0 = page.get_texttrace()[0]["size"]
        fontsize1 = page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT)["blocks"][0]["lines"][
            0
        ]["spans"][0]["size"]
        assert abs(fontsize0 - fontsize1) < 1e-5


def test_2506():
    """Ensure expected font size across text writing angles."""
    doc = fitz.open()
    page = doc.new_page()
    point = fitz.Point(100, 300)  # insertion point
    fontsize = 11  # fontsize
    text = "Hello"  # text
    angles = (0, 30, 60, 90, 120)  # some angles

    # write text with different angles
    for angle in angles:
        page.insert_text(
            point, text, fontsize=fontsize, morph=(point, fitz.Matrix(angle))
        )

    # ensure correct fontsize for get_texttrace() - forgiving rounding problems
    for span in page.get_texttrace():
        print(span["dir"])
        assert round(span["size"]) == fontsize

    # ensure correct fontsize for get_text() - forgiving rounding problems
    for block in page.get_text("dict")["blocks"]:
        for line in block["lines"]:
            print(line["dir"])
            for span in line["spans"]:
                print(span["size"])
                assert round(span["size"]) == fontsize


def test_2108():
    doc = fitz.open(f'{scriptdir}/resources/test_2108.pdf')
    page = doc[0]
    areas = page.search_for("{sig}")
    rect = areas[0]
    page.add_redact_annot(rect)
    page.apply_redactions()
    text = page.get_text()

    text_expected = b'Frau\nClaire Dunphy\nTeststra\xc3\x9fe 5\n12345 Stadt\nVertragsnummer:  12345\nSehr geehrte Frau Dunphy,\nText\nMit freundlichen Gr\xc3\xbc\xc3\x9fen\nTestfirma\nVertrag:\n  12345\nAnsprechpartner:\nJay Pritchet\nTelefon:\n123456\nE-Mail:\ntest@test.de\nDatum:\n07.12.2022\n'.decode('utf8')

    if 1:
        # Verbose info.
        print(f'test_2108(): text is:\n{text}')
        print(f'')
        print(f'test_2108(): repr(text) is:\n{text!r}')
        print(f'')
        print(f'test_2108(): repr(text.encode("utf8")) is:\n{text.encode("utf8")!r}')
        print(f'')
        print(f'test_2108(): text_expected is:\n{text_expected}')
        print(f'')
        print(f'test_2108(): repr(text_expected) is:\n{text_expected!r}')
        print(f'')
        print(f'test_2108(): repr(text_expected.encode("utf8")) is:\n{text_expected.encode("utf8")!r}')

        ok1 = (text == text_expected)
        ok2 = (text.encode("utf8") == text_expected.encode("utf8"))
        ok3 = (repr(text.encode("utf8")) == repr(text_expected.encode("utf8")))

        print(f'')
        print(f'ok1={ok1}')
        print(f'ok2={ok2}')
        print(f'ok3={ok3}')

        print(f'')

    print(f'fitz.mupdf_version_tuple={fitz.mupdf_version_tuple}')
    if fitz.mupdf_version_tuple >= (1, 21, 2):
        print('Asserting text==text_expected')
        assert text == text_expected
    else:
        print('Asserting text!=text_expected')
        assert text != text_expected


def test_2238():
    filepath = f'{scriptdir}/resources/test2238.pdf'
    doc = fitz.open(filepath)

    first_page = doc.load_page(0).get_text('text', fitz.INFINITE_RECT())
    last_page = doc.load_page(-1).get_text('text', fitz.INFINITE_RECT())

    print(f'first_page={first_page!r}')
    print(f'last_page={last_page!r}')
    assert first_page == 'Hello World\n'
    assert last_page == 'Hello World\n'

    first_page = doc.load_page(0).get_text('text')
    last_page = doc.load_page(-1).get_text('text')

    print(f'first_page={first_page!r}')
    print(f'last_page={last_page!r}')
    assert first_page == 'Hello World\n'
    assert last_page == 'Hello World\n'


def test_2093():
    doc = fitz.open(f'{scriptdir}/resources/test2093.pdf')

    def average_color(page):
        pixmap = page.get_pixmap()
        p_average = [0] * pixmap.n
        for y in range(pixmap.height):
            for x in range(pixmap.width):
                p = pixmap.pixel(x, y)
                for i in range(pixmap.n):
                    p_average[i] += p[i]
        for i in range(pixmap.n):
            p_average[i] /= (pixmap.height * pixmap.width)
        return p_average

    page = doc.load_page(0)
    pixel_average_before = average_color(page)

    rx=135.123
    ry=123.56878
    rw=69.8409
    rh=9.46397

    x0 = rx
    y0 = ry
    x1 = rx + rw
    y1 = ry + rh

    rect = fitz.Rect(x0, y0, x1, y1)

    font = fitz.Font("Helvetica")
    fill_color=(0,0,0)
    page.add_redact_annot(
        quad=rect,
        #text="null",
        fontname=font.name,
        fontsize=12,
        align=fitz.TEXT_ALIGN_CENTER,
        fill=fill_color,
        text_color=(1,1,1),
    )

    page.apply_redactions()
    pixel_average_after = average_color(page)

    print(f'pixel_average_before={pixel_average_before!r}')
    print(f'pixel_average_after={pixel_average_after!r}')

    # Before this bug was fixed:
    #   pixel_average_before=[130.864323120088, 115.23577810900859, 92.9268559996174]
    #   pixel_average_after=[138.68844553555772, 123.05687162237561, 100.74275056194105]
    # After fix:
    #   pixel_average_before=[130.864323120088, 115.23577810900859, 92.9268559996174]
    #   pixel_average_after=[130.8889209934799, 115.25722751837269, 92.94327384463327]
    #
    if fitz.mupdf_version_tuple[:2] >= (1, 22):
        for i in range(len(pixel_average_before)):
            diff = pixel_average_before[i] - pixel_average_after[i]
            assert abs(diff) < 0.1

    out = f'{scriptdir}/resources/test2093-out.pdf'
    doc.save(out)
    print(f'Have written to: {out}')


def test_2182():
    print(f'test_2182() started')
    doc = fitz.open(f'{scriptdir}/resources/test2182.pdf')
    page = doc[0]
    for annot in page.annots():
        print(annot)
    print(f'test_2182() finished')


def test_2246():
    """
    Test / confirm identical text positions generated by
    * page.insert_text()
    versus
    * TextWriter.write_text()

    ... under varying situations as follows:

    1. MediaBox does not start at (0, 0)
    2. CropBox origin is different from that of MediaBox
    3. Check for all 4 possible page rotations

    The test writes the same text at the same positions using `page.insert_text()`,
    respectively `TextWriter.write_text()`.
    Then extracts the text spans and confirms that they all occupy the same bbox.
    This ensures coincidence of text positions of page.of insert_text()
    (which is assumed correct) and TextWriter.write_text().
    """
    def bbox_count(rot):
        """Make a page and insert identical text via different methods.

        Desired page rotation is a parameter. MediaBox and CropBox are chosen
        to be "awkward": MediaBox does not start at (0,0) and CropBox is a
        true subset of MediaBox.
        """
        # bboxes of spans on page: same text positions are represented by ONE bbox
        bboxes = set()
        doc = fitz.open()
        # prepare a page with desired MediaBox / CropBox peculiarities
        mediabox = fitz.paper_rect("letter")
        page = doc.new_page(width=mediabox.width, height=mediabox.height)
        xref = page.xref
        newmbox = list(map(float, doc.xref_get_key(xref, "MediaBox")[1][1:-1].split()))
        newmbox = fitz.Rect(newmbox)
        mbox = newmbox + (10, 20, 10, 20)
        cbox = mbox + (10, 10, -10, -10)
        doc.xref_set_key(xref, "MediaBox", "[%g %g %g %g]" % tuple(mbox))
        doc.xref_set_key(xref, "CrobBox", "[%g %g %g %g]" % tuple(cbox))
        # set page to desired rotation
        page.set_rotation(rot)
        page.insert_text((50, 50), "Text inserted at (50,50)")
        tw = fitz.TextWriter(page.rect)
        tw.append((50, 50), "Text inserted at (50,50)")
        tw.write_text(page)
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            for l in b["lines"]:
                for s in l["spans"]:
                    # store bbox rounded to 3 decimal places
                    bboxes.add(fitz.Rect(fitz.JM_TUPLE3(s["bbox"])))
        return len(bboxes)  # should be 1!

    # the following tests must all pass
    assert bbox_count(0) == 1
    assert bbox_count(90) == 1
    assert bbox_count(180) == 1
    assert bbox_count(270) == 1


def test_2430():
    """Confirm that multiple font property checks will not destroy Py_None."""
    font = fitz.Font("helv")
    for i in range(1000):
        _ = font.flags

def test_2692():
    document = fitz.Document(f'{scriptdir}/resources/2.pdf')
    for page in document:
        pix = page.get_pixmap(clip=fitz.Rect(0,0,10,10))
        dl = page.get_displaylist(annots=True)
        pix = dl.get_pixmap(
                matrix=fitz.Identity,
                colorspace=fitz.csRGB,
                alpha=False,
                clip=fitz.Rect(0,0,10,10),
                )
        pix = dl.get_pixmap(
                matrix=fitz.Identity,
                #colorspace=fitz.csRGB,
                alpha=False,
                clip=fitz.Rect(0,0,10,10),
                )
    

def test_2596():
    """Cconfirm correctly abandoning cache when reloading a page."""
    doc = fitz.Document(f"{scriptdir}/resources/test_2596.pdf")
    page = doc[0]
    pix0 = page.get_pixmap()  # render the page
    _ = doc.tobytes(garbage=3)  # save with garbage collection

    # Note this will invalidate cache content for this page.
    # Reloading the page now empties the cache, so rendering
    # will deliver the same pixmap
    page = doc.reload_page(page)
    pix1 = page.get_pixmap()
    assert pix1.samples == pix0.samples


def test_2730():
    """Ensure identical output across text extractions."""
    doc = fitz.open(f"{scriptdir}/resources/test_2730.pdf")
    page = doc[0]
    s1 = set(page.get_text())  # plain text extraction
    s2 = set(page.get_text(sort=True))  # uses "blocks" extraction
    s3 = set(page.get_textbox(page.rect))
    assert s1 == s2
    assert s1 == s3


def test_2553():
    """Ensure identical output across text extractions."""
    doc = fitz.open(f"{scriptdir}/resources/test_2553.pdf")
    page = doc[0]

    # extract plain text, build set of all characters
    list1 = page.get_text()
    set1 = set(list1)

    # extract text blocks, build set of all characters
    list2 = page.get_text(sort=True)  # internally uses "blocks"
    set2 = set(list2)
    
    # extract textbox content, build set of all characters
    list3 = page.get_textbox(page.rect)
    set3 = set(list3)
    
    def show(l):
        ret = f'len={len(l)}\n'
        for c in l:
            cc = ord(c)
            if (cc >= 32 and cc < 127) or c == '\n':
                ret += c
            else:
                ret += f' [0x{hex(cc)}]'
        return ret
    print(f'list1:\n{show(list1)}')
    print(f'list2:\n{show(list2)}')
    print(f'list3:\n{show(list3)}')
    
    # all sets must be equal
    assert set1 == set2
    assert set1 == set3

    # With mupdf later than 1.23.4, this special page contains no invalid
    # Unicodes.
    #
    if fitz.mupdf_version_tuple > (1, 23, 4):
        print(f'Checking no occurrence of 0xFFFD, {fitz.mupdf_version_tuple=}.')
        assert chr(0xFFFD) not in set1
    else:
        print(f'Checking occurrence of 0xFFFD, {fitz.mupdf_version_tuple=}.')
        assert chr(0xFFFD) in set1

def test_2553_2():
    doc = fitz.open(f"{scriptdir}/resources/test_2553-2.pdf")
    page = doc[0]

    # extract plain text, ensure that there are no 0xFFFD characters
    text = page.get_text()
    if fitz.mupdf_version_tuple >= (1, 23, 7):
        assert chr(0xfffd) not in text
    else:
        # Bug not fixed in MuPDF.
        assert chr(0xfffd) in text

def test_2635():
    """Rendering a page before and after cleaning it should yield the same pixmap."""
    doc = fitz.open(f"{scriptdir}/resources/test_2635.pdf")
    page = doc[0]
    pix1 = page.get_pixmap()  # pixmap before cleaning

    page.clean_contents()  # clean page
    pix2 = page.get_pixmap()  # pixmap after cleaning
    assert pix1.samples == pix2.samples  # assert equality


def test_resolve_names():
    """Test PDF name resolution."""
    # guard against wrong PyMuPDF architecture version
    if not hasattr(fitz.Document, "resolve_names"):
        print("PyMuPDF version does not support resolving PDF names")
        return
    pickle_in = open(f"{scriptdir}/resources/cython.pickle", "rb")
    old_names = pickle.load(pickle_in)
    doc = fitz.open(f"{scriptdir}/resources/cython.pdf")
    new_names = doc.resolve_names()
    assert new_names == old_names

def test_2777():
    document = fitz.Document()
    page = document.new_page()
    print(page.mediabox.width)

def test_2710():
    doc = fitz.open(f'{scriptdir}/resources/test_2710.pdf')
    page = doc.load_page(0)
    
    print(f'test_2710(): {page.cropbox=}')
    print(f'test_2710(): {page.mediabox=}')
    print(f'test_2710(): {page.rect=}')
    
    def numbers_approx_eq(a, b):
        return abs(a-b) < 0.001
    def points_approx_eq(a, b):
        return numbers_approx_eq(a.x, b.x) and numbers_approx_eq(a.y, b.y)
    def rects_approx_eq(a, b):
        return points_approx_eq(a.bottom_left, b.bottom_left) and points_approx_eq(a.top_right, b.top_right)
    def assert_rects_approx_eq(a, b):
        assert rects_approx_eq(a, b), f'Not nearly identical: {a=} {b=}'
                
    blocks = page.get_text('blocks')
    print(f'test_2710(): {blocks=}')
    assert len(blocks) == 2
    block = blocks[1]
    rect = fitz.Rect(block[:4])
    text = block[4]
    print(f'test_2710(): {rect=}')
    print(f'test_2710(): {text=}')
    assert text == 'Text at left page border\n'
    
    assert_rects_approx_eq(page.cropbox, fitz.Rect(30.0, 30.0, 565.3200073242188, 811.9199829101562))
    assert_rects_approx_eq(page.mediabox, fitz.Rect(0.0, 0.0, 595.3200073242188, 841.9199829101562))
    print(f'test_2710(): {fitz.mupdf_version_tuple=}')
    if fitz.mupdf_version_tuple < (1, 23, 5):
        print(f'test_2710(): Not Checking page.rect and rect.')
    elif fitz.mupdf_version_tuple < (1, 24.0):
        print(f'test_2710(): Checking page.rect and rect.')
        assert_rects_approx_eq(page.rect, fitz.Rect(0.0, 0.0, 535.3200073242188, 781.9199829101562))
        assert_rects_approx_eq(rect, fitz.Rect(0.7872352600097656, 64.7560043334961, 124.85531616210938, 78.1622543334961))
    else:
        # 2023-11-05: Currently broken in mupdf master.
        print(f'test_2710(): Not Checking page.rect and rect.')


def test_2736():
    """Check handling of CropBox changes vis-a-vis a MediaBox with
       negative coordinates."""
    doc = fitz.open()
    page = doc.new_page()

    # fake a MediaBox for demo purposes
    doc.xref_set_key(page.xref, "MediaBox", "[-30 -20 595 842]")

    assert page.cropbox == fitz.Rect(-30, 0, 595, 862)
    assert page.rect == fitz.Rect(0, 0, 625, 862)

    # change the CropBox: shift by (10, 10) in both dimensions. Please note:
    # To achieve this, 10 must be subtracted from 862! yo must never be negative!
    page.set_cropbox(fitz.Rect(-20, 0, 595, 852))

    # get CropBox from the page definition
    assert doc.xref_get_key(page.xref, "CropBox")[1] == "[-20 -10 595 842]"
    assert page.rect == fitz.Rect(0, 0, 615, 852)

    error = False
    text = ""
    try:  # check error detection
        page.set_cropbox((-35, -10, 595, 842))
    except Exception as e:
        text = str(e)
        error = True
    assert error == True
    assert text == "CropBox not in MediaBox"


def test_subset_fonts():
    """Confirm subset_fonts is working."""
    if not hasattr(fitz, "mupdf"):
        print("Not testing 'test_subset_fonts' in classic.")
        return
    text = "Just some arbitrary text."
    arch = fitz.Archive()
    css = fitz.css_for_pymupdf_font("ubuntu", archive=arch)
    css += "* {font-family: ubuntu;}"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_htmlbox(page.rect, text, css=css, archive=arch)
    doc.subset_fonts(verbose=True)
    found = False
    for xref in range(1, doc.xref_length()):
        if doc.xref_is_font(xref):
            if "+Ubuntu#20Regular" in doc.xref_object(xref):
                found = True
                break
    assert found is True


def test_2957_1():
    """Text following a redaction must not change coordinates."""
    # test file with redactions
    doc = fitz.open(os.path.join(scriptdir, "resources", "test_2957_1.pdf"))
    page = doc[0]
    # search for string that must not move by redactions
    rects0 = page.search_for("6e9f73dfb4384a2b8af6ebba")
    # sort rectangles vertically
    rects0 = sorted(rects0, key=lambda r: r.y1)
    assert len(rects0) == 2  # must be 2 redactions
    page.apply_redactions()

    # reload page to finalize updates
    page = doc.reload_page(page)

    # the two string must retain their positions (except rounding errors)
    rects1 = page.search_for("6e9f73dfb4384a2b8af6ebba")
    rects1 = sorted(rects1, key=lambda r: r.y1)

    assert page.first_annot is None  # make sure annotations have disappeared
    for i in range(2):
        r0 = rects0[i].irect  # take rounded rects
        r1 = rects1[i].irect
        assert r0 == r1


def test_2957_2():
    """Redacted text must not change positions of remaining text."""
    doc = fitz.open(os.path.join(scriptdir, "resources", "test_2957_2.pdf"))
    page = doc[0]
    words0 = page.get_text("words")  # all words before redacting
    page.apply_redactions()  # remove/redact the word "longer"
    words1 = page.get_text("words")  # extract words again
    assert len(words1) == len(words0) - 1  # must be one word less
    assert words0[3][4] == "longer"  # just confirm test file is correc one
    del words0[3]  # remove the redacted word from first list
    for i in range(len(words1)):  # compare words
        w1 = words1[i]  # word after redaction
        bbox1 = fitz.Rect(w1[:4]).irect  # its IRect coordinates
        w0 = words0[i]  # word before redaction
        bbox0 = fitz.Rect(w0[:4]).irect  # its IRect coordinates
        assert bbox0 == bbox1  # must be same coordinates
