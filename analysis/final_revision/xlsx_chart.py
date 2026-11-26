"""Stdlib-only .xlsx writer with native (editable) Excel charts. No openpyxl / xlsxwriter on GoCom (11-27).
Charts reference worksheet cell ranges, so editing the table in Excel updates the chart; values are also cached in the chart
part so viewers that do not recalculate still draw it.

    wb = Workbook(); ws = wb.sheet('Name')
    r = ws.write(row, col, value, style=None)          # 0-based row/col; style in STYLES
    ws.table(row, col, header, rows) -> (first_data_row, last_data_row)
    ws.chart(kind, anchor_row, anchor_col, series=[...], title=, x_title=, y_title=, ...)
    wb.save(path)
kind: 'bar' (clustered columns, category axis), 'line' (category axis, markers; line optional), 'scatter' (x/y numeric).
series item: dict(name=str, cat=(r1, c1, r2, c2) or None, val=(r1, c1, r2, c2), plus=(...)/None, minus=(...)/None,
                  sheet=<Sheet> (defaults to the chart's sheet), line=True/False, marker=True/False)
Error bars use custom ranges (plus / minus cell ranges)."""
import zipfile
from xml.sax.saxutils import escape

PALETTE = ['2A78D6', 'EB6834', '1BAF7A', 'EDA100', 'E87BA4', '008300', '6250D6', 'E34948']   # dataviz reference palette, fixed order
STYLES = {None: 0, 'head': 1, 'wrap': 2, 'title': 3, 'num4': 4, 'bold': 5, 'note': 6, 'num1': 7, 'warn': 8}


def col_name(i):
    s = ''
    i += 1
    while i:
        i, r = divmod(i - 1, 26); s = chr(65 + r) + s
    return s


def ref(sheet, r1, c1, r2, c2):
    return f"'{sheet.replace(chr(39), chr(39) * 2)}'!${col_name(c1)}${r1 + 1}:${col_name(c2)}${r2 + 1}"


def _num(v):
    if isinstance(v, bool) or v is None: return None
    if isinstance(v, (int, float)): return v if v == v and abs(v) != float('inf') else None
    return None


class Sheet:
    def __init__(self, wb, name):
        self.wb, self.name, self.cells, self.widths, self.charts, self.merges = wb, name[:31], {}, {}, [], []

    def write(self, r, c, v, style=None):
        self.cells[(r, c)] = (v, STYLES[style]); return r + 1

    def row(self, r, c, values, style=None):
        for i, v in enumerate(values): self.write(r, c + i, v, style)
        return r + 1

    def table(self, r, c, header, rows, num_style=None):
        self.row(r, c, header, 'head')
        for i, row in enumerate(rows):
            for j, v in enumerate(row): self.write(r + 1 + i, c + j, v, num_style if _num(v) is not None and num_style else None)
        return r + 1, r + len(rows)

    def width(self, c, w):
        self.widths[c] = w

    def get(self, r, c):
        return self.cells.get((r, c), (None, 0))[0]

    def chart(self, kind, ar, ac, series, title='', x_title='', y_title='', w=9, h=20, log_y=False, y_min=None, y_max=None,
              x_min=None, x_max=None, legend=True, gap=80):
        self.charts.append(dict(kind=kind, ar=ar, ac=ac, series=series, title=title, x_title=x_title, y_title=y_title, w=w, h=h,
                                log_y=log_y, y_min=y_min, y_max=y_max, x_min=x_min, x_max=x_max, legend=legend, gap=gap))


def _cell_xml(r, c, v, s):
    a = f'r="{col_name(c)}{r + 1}"' + (f' s="{s}"' if s else '')
    n = _num(v)
    if n is not None: return f'<c {a}><v>{n!r}</v></c>'
    if v is None or v == '': return f'<c {a}/>' if s else ''
    return f'<c {a} t="inlineStr"><is><t xml:space="preserve">{escape(str(v))}</t></is></c>'


def _sheet_xml(sh, drawing_rid):
    rows = {}
    for (r, c), (v, s) in sh.cells.items(): rows.setdefault(r, []).append((c, v, s))
    out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
           'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheetViews><sheetView workbookViewId="0"/></sheetViews>'
           '<sheetFormatPr defaultRowHeight="15"/>']
    if sh.widths:
        out.append('<cols>' + ''.join(f'<col min="{c + 1}" max="{c + 1}" width="{w}" customWidth="1"/>' for c, w in sorted(sh.widths.items())) + '</cols>')
    out.append('<sheetData>')
    for r in sorted(rows):
        out.append(f'<row r="{r + 1}">' + ''.join(_cell_xml(r, c, v, s) for c, v, s in sorted(rows[r], key=lambda x: x[0])) + '</row>')
    out.append('</sheetData>')
    if drawing_rid: out.append(f'<drawing r:id="{drawing_rid}"/>')
    out.append('</worksheet>')
    return ''.join(out)


def _rich(text, sz=1200, b=1):
    return (f'<c:tx><c:rich><a:bodyPr/><a:lstStyle/><a:p><a:pPr><a:defRPr sz="{sz}" b="{b}"/></a:pPr><a:r><a:rPr lang="ko-KR" sz="{sz}" b="{b}"/>'
            f'<a:t>{escape(text)}</a:t></a:r></a:p></c:rich></c:tx><c:overlay val="0"/>')


def _title(text, sz=1200, b=1):
    return f'<c:title>{_rich(text, sz, b)}</c:title>' if text else ''


def _vals(sheet, rng):
    r1, c1, r2, c2 = rng
    return [sheet.get(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]


def _numref(sheet, rng):
    v = _vals(sheet, rng)
    pts = ''.join(f'<c:pt idx="{i}"><c:v>{_num(x)!r}</c:v></c:pt>' for i, x in enumerate(v) if _num(x) is not None)
    return (f'<c:numRef><c:f>{escape(ref(sheet.name, *rng))}</c:f><c:numCache><c:formatCode>General</c:formatCode>'
            f'<c:ptCount val="{len(v)}"/>{pts}</c:numCache></c:numRef>')


def _strref(sheet, rng):
    v = _vals(sheet, rng)
    pts = ''.join(f'<c:pt idx="{i}"><c:v>{escape("" if x is None else str(x))}</c:v></c:pt>' for i, x in enumerate(v))
    return f'<c:strRef><c:f>{escape(ref(sheet.name, *rng))}</c:f><c:strCache><c:ptCount val="{len(v)}"/>{pts}</c:strCache></c:strRef>'


def _err(sheet, s, scatter):
    if not s.get('plus'): return ''
    return ('<c:errBars>' + ('<c:errDir val="y"/>' if scatter else '') + '<c:errBarType val="both"/><c:errValType val="cust"/><c:noEndCap val="0"/>'
            f'<c:plus>{_numref(sheet, s["plus"])}</c:plus><c:minus>{_numref(sheet, s.get("minus") or s["plus"])}</c:minus>'
            '<c:spPr><a:ln w="15875"><a:solidFill><a:srgbClr val="333333"/></a:solidFill></a:ln></c:spPr></c:errBars>')


def _chart_xml(sh, ch):
    kind = ch['kind']; scatter = kind == 'scatter'; sers = []
    for i, s in enumerate(ch['series']):
        sheet = s.get('sheet', sh); col = s.get('color') or PALETTE[i % len(PALETTE)]
        tx = f'<c:tx><c:v>{escape(s["name"])}</c:v></c:tx>'
        if kind == 'bar':
            sp = f'<c:spPr><a:solidFill><a:srgbClr val="{col}"/></a:solidFill><a:ln><a:noFill/></a:ln></c:spPr><c:invertIfNegative val="0"/>'
            body = _err(sheet, s, False) + f'<c:cat>{_strref(sheet, s["cat"])}</c:cat><c:val>{_numref(sheet, s["val"])}</c:val>'
        else:
            ln = (f'<a:ln w="22225"><a:solidFill><a:srgbClr val="{col}"/></a:solidFill></a:ln>' if s.get('line', True) else '<a:ln><a:noFill/></a:ln>')
            mk = (f'<c:marker><c:symbol val="circle"/><c:size val="7"/><c:spPr><a:solidFill><a:srgbClr val="{col}"/></a:solidFill>'
                  f'<a:ln><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill></a:ln></c:spPr></c:marker>' if s.get('marker', True)
                  else '<c:marker><c:symbol val="none"/></c:marker>')
            sp = f'<c:spPr>{ln}</c:spPr>{mk}'
            if scatter:
                body = _err(sheet, s, True) + f'<c:xVal>{_numref(sheet, s["cat"])}</c:xVal><c:yVal>{_numref(sheet, s["val"])}</c:yVal><c:smooth val="0"/>'
            else:
                body = _err(sheet, s, False) + f'<c:cat>{_strref(sheet, s["cat"])}</c:cat><c:val>{_numref(sheet, s["val"])}</c:val><c:smooth val="0"/>'
        sers.append(f'<c:ser><c:idx val="{i}"/><c:order val="{i}"/>{tx}{sp}{body}</c:ser>')
    sers = ''.join(sers)
    if kind == 'bar':
        plot = f'<c:barChart><c:barDir val="col"/><c:grouping val="clustered"/><c:varyColors val="0"/>{sers}<c:gapWidth val="{ch["gap"]}"/><c:axId val="10"/><c:axId val="20"/></c:barChart>'
    elif kind == 'line':
        plot = f'<c:lineChart><c:grouping val="standard"/><c:varyColors val="0"/>{sers}<c:marker val="1"/><c:axId val="10"/><c:axId val="20"/></c:lineChart>'
    else:
        plot = f'<c:scatterChart><c:scatterStyle val="lineMarker"/><c:varyColors val="0"/>{sers}<c:axId val="10"/><c:axId val="20"/></c:scatterChart>'
    grid = '<c:majorGridlines><c:spPr><a:ln w="6350"><a:solidFill><a:srgbClr val="E0E0E0"/></a:solidFill></a:ln></c:spPr></c:majorGridlines>'
    axln = '<c:spPr><a:ln w="9525"><a:solidFill><a:srgbClr val="808080"/></a:solidFill></a:ln></c:spPr><c:txPr><a:bodyPr/><a:lstStyle/><a:p><a:pPr><a:defRPr sz="900"/></a:pPr><a:endParaRPr lang="ko-KR"/></a:p></c:txPr>'

    def scal(lo, hi, log=False):
        return ('<c:scaling>' + ('<c:logBase val="10"/>' if log else '') + '<c:orientation val="minMax"/>' + (f'<c:max val="{hi}"/>' if hi is not None else '')
                + (f'<c:min val="{lo}"/>' if lo is not None else '') + '</c:scaling>')
    xt = _title(ch['x_title'], 1000, 0); yt = _title(ch['y_title'], 1000, 0)
    if scatter:
        xax = (f'<c:valAx><c:axId val="10"/>{scal(ch["x_min"], ch["x_max"])}<c:delete val="0"/><c:axPos val="b"/>{xt}<c:numFmt formatCode="General" sourceLinked="0"/>'
               f'<c:majorTickMark val="out"/><c:minorTickMark val="none"/><c:tickLblPos val="low"/>{axln}<c:crossAx val="20"/><c:crosses val="autoZero"/><c:crossBetween val="midCat"/></c:valAx>')
    else:
        xax = (f'<c:catAx><c:axId val="10"/>{scal(None, None)}<c:delete val="0"/><c:axPos val="b"/>{xt}<c:numFmt formatCode="General" sourceLinked="0"/>'
               f'<c:majorTickMark val="out"/><c:minorTickMark val="none"/><c:tickLblPos val="low"/>{axln}<c:crossAx val="20"/><c:crosses val="autoZero"/>'
               '<c:auto val="1"/><c:lblAlgn val="ctr"/><c:lblOffset val="100"/><c:noMultiLvlLbl val="0"/></c:catAx>')
    yax = (f'<c:valAx><c:axId val="20"/>{scal(ch["y_min"], ch["y_max"], ch["log_y"])}<c:delete val="0"/><c:axPos val="l"/>{grid}{yt}'
           f'<c:numFmt formatCode="General" sourceLinked="0"/><c:majorTickMark val="out"/><c:minorTickMark val="none"/><c:tickLblPos val="nextTo"/>{axln}'
           f'<c:crossAx val="10"/><c:crosses val="autoZero"/><c:crossBetween val="{"midCat" if scatter else "between"}"/></c:valAx>')
    leg = '<c:legend><c:legendPos val="b"/><c:overlay val="0"/></c:legend>' if ch['legend'] else ''
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" '
            'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f'<c:roundedCorners val="0"/><c:chart>{_title(ch["title"])}<c:autoTitleDeleted val="0"/><c:plotArea><c:layout/>{plot}{xax}{yax}</c:plotArea>'
            f'{leg}<c:plotVisOnly val="1"/><c:dispBlanksAs val="gap"/></c:chart></c:chartSpace>')


def _drawing_xml(charts):
    out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?><xdr:wsDr xmlns:xdr="http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing" '
           'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">']
    for i, ch in enumerate(charts):
        out.append(f'<xdr:twoCellAnchor editAs="oneCell"><xdr:from><xdr:col>{ch["ac"]}</xdr:col><xdr:colOff>0</xdr:colOff><xdr:row>{ch["ar"]}</xdr:row><xdr:rowOff>0</xdr:rowOff></xdr:from>'
                   f'<xdr:to><xdr:col>{ch["ac"] + ch["w"]}</xdr:col><xdr:colOff>0</xdr:colOff><xdr:row>{ch["ar"] + ch["h"]}</xdr:row><xdr:rowOff>0</xdr:rowOff></xdr:to>'
                   f'<xdr:graphicFrame macro=""><xdr:nvGraphicFramePr><xdr:cNvPr id="{i + 2}" name="Chart {i + 1}"/><xdr:cNvGraphicFramePr/></xdr:nvGraphicFramePr>'
                   '<xdr:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/></xdr:xfrm><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/chart">'
                   f'<c:chart xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" r:id="rId{i + 1}"/>'
                   '</a:graphicData></a:graphic></xdr:graphicFrame><xdr:clientData/></xdr:twoCellAnchor>')
    out.append('</xdr:wsDr>')
    return ''.join(out)


STYLES_XML = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
              '<numFmts count="2"><numFmt numFmtId="164" formatCode="0.0000"/><numFmt numFmtId="165" formatCode="#,##0.0"/></numFmts>'
              '<fonts count="5"><font><sz val="10"/><name val="Malgun Gothic"/></font><font><b/><sz val="10"/><name val="Malgun Gothic"/></font>'
              '<font><b/><sz val="14"/><name val="Malgun Gothic"/></font><font><i/><sz val="9"/><color rgb="FF555555"/><name val="Malgun Gothic"/></font>'
              '<font><b/><sz val="10"/><color rgb="FFB00020"/><name val="Malgun Gothic"/></font></fonts>'
              '<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill>'
              '<fill><patternFill patternType="solid"><fgColor rgb="FFDDE8F5"/><bgColor indexed="64"/></patternFill></fill></fills>'
              '<borders count="2"><border><left/><right/><top/><bottom/><diagonal/></border>'
              '<border><left/><right/><top/><bottom style="thin"><color rgb="FF808080"/></bottom><diagonal/></border></borders>'
              '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="9">'
              '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
              '<xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment wrapText="1" vertical="top"/></xf>'
              '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment wrapText="1" vertical="top"/></xf>'
              '<xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1"/>'
              '<xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>'
              '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1" applyAlignment="1"><alignment wrapText="1" vertical="top"/></xf>'
              '<xf numFmtId="0" fontId="3" fillId="0" borderId="0" xfId="0" applyFont="1"/>'
              '<xf numFmtId="165" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>'
              '<xf numFmtId="0" fontId="4" fillId="0" borderId="0" xfId="0" applyFont="1" applyAlignment="1"><alignment wrapText="1" vertical="top"/></xf>'
              '</cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>')


class Workbook:
    def __init__(self):
        self.sheets = []

    def sheet(self, name):
        s = Sheet(self, name); self.sheets.append(s); return s

    def save(self, path):
        R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
        PR = 'http://schemas.openxmlformats.org/package/2006/relationships'
        ct = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
              '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
              '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
              '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>']
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
            n_chart = 0; n_draw = 0
            for i, sh in enumerate(self.sheets):
                ct.append(f'<Override PartName="/xl/worksheets/sheet{i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')
                rid = None
                if sh.charts:
                    n_draw += 1; rid = 'rId1'
                    z.writestr(f'xl/worksheets/_rels/sheet{i + 1}.xml.rels', f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{PR}">'
                               f'<Relationship Id="rId1" Type="{R}/drawing" Target="../drawings/drawing{n_draw}.xml"/></Relationships>')
                    ct.append(f'<Override PartName="/xl/drawings/drawing{n_draw}.xml" ContentType="application/vnd.openxmlformats-officedocument.drawing+xml"/>')
                    z.writestr(f'xl/drawings/drawing{n_draw}.xml', _drawing_xml(sh.charts))
                    rels = []
                    for j, ch in enumerate(sh.charts):
                        n_chart += 1
                        z.writestr(f'xl/charts/chart{n_chart}.xml', _chart_xml(sh, ch))
                        ct.append(f'<Override PartName="/xl/charts/chart{n_chart}.xml" ContentType="application/vnd.openxmlformats-officedocument.drawingml.chart+xml"/>')
                        rels.append(f'<Relationship Id="rId{j + 1}" Type="{R}/chart" Target="../charts/chart{n_chart}.xml"/>')
                    z.writestr(f'xl/drawings/_rels/drawing{n_draw}.xml.rels', f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{PR}">' + ''.join(rels) + '</Relationships>')
                z.writestr(f'xl/worksheets/sheet{i + 1}.xml', _sheet_xml(sh, rid))
            ct.append('</Types>')
            z.writestr('[Content_Types].xml', ''.join(ct))
            z.writestr('_rels/.rels', f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{PR}">'
                       f'<Relationship Id="rId1" Type="{R}/officeDocument" Target="xl/workbook.xml"/></Relationships>')
            z.writestr('xl/workbook.xml', f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="{R}"><sheets>'
                       + ''.join(f'<sheet name="{escape(s.name)}" sheetId="{i + 1}" r:id="rId{i + 1}"/>' for i, s in enumerate(self.sheets)) + '</sheets></workbook>')
            n = len(self.sheets)
            z.writestr('xl/_rels/workbook.xml.rels', f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{PR}">'
                       + ''.join(f'<Relationship Id="rId{i + 1}" Type="{R}/worksheet" Target="worksheets/sheet{i + 1}.xml"/>' for i in range(n))
                       + f'<Relationship Id="rId{n + 1}" Type="{R}/styles" Target="styles.xml"/></Relationships>')
            z.writestr('xl/styles.xml', STYLES_XML)
        return n_chart
