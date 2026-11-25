"""Minimal stdlib .xlsx writer (no openpyxl on this host). Sheets of rows; numbers stay numeric, everything else is an inline string.
    write_xlsx(path, [(sheet_name, [[cell, ...], ...]), ...])"""
import zipfile
from xml.sax.saxutils import escape


def _col(i):
    s = ''
    while True:
        i, r = divmod(i, 26); s = chr(65 + r) + s
        if i == 0: return s
        i -= 1


def _cell(ref, v):
    if isinstance(v, bool) or v is None or v == '':
        v = '' if v is None else str(v)
    if isinstance(v, (int, float)): return f'<c r="{ref}"><v>{v!r}</v></c>'
    try:
        f = float(v)
        if v.strip() and v.strip().lower() not in ('nan', 'inf', '-inf', 'true', 'false'): return f'<c r="{ref}"><v>{f!r}</v></c>'
    except (ValueError, AttributeError): pass
    return f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">{escape(str(v))}</t></is></c>'


def write_xlsx(path, sheets):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        n = len(sheets)
        z.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   + ''.join(f'<Override PartName="/xl/worksheets/sheet{i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(n))
                   + '</Types>')
        z.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr('xl/workbook.xml', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
                   + ''.join(f'<sheet name="{escape(name[:31])}" sheetId="{i + 1}" r:id="rId{i + 1}"/>' for i, (name, _) in enumerate(sheets)) + '</sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   + ''.join(f'<Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i + 1}.xml"/>' for i in range(n))
                   + '</Relationships>')
        for i, (_, rows) in enumerate(sheets):
            body = ''.join(f'<row r="{r + 1}">' + ''.join(_cell(f'{_col(c)}{r + 1}', v) for c, v in enumerate(row)) + '</row>' for r, row in enumerate(rows))
            z.writestr(f'xl/worksheets/sheet{i + 1}.xml', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                       f'<sheetData>{body}</sheetData></worksheet>')
