from io import BytesIO
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ORANGE = colors.HexColor('#f26b21')
BASE = Path(__file__).resolve().parent
LOGO = BASE / 'auralix-logo.jpg'
FONT = BASE / 'DejaVuSans.ttf'
FONT_BOLD = BASE / 'DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('AuralixSans', str(FONT)))
pdfmetrics.registerFont(TTFont('AuralixSansBold', str(FONT_BOLD)))

def money(v):
    return f'₹ {float(v or 0):,.2f}'

def esc(value):
    return str(value or '').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

def make_document(kind, doc, customer, items):
    buf = BytesIO()
    pdf = SimpleDocTemplate(buf, pagesize=A4, rightMargin=14*mm, leftMargin=14*mm, topMargin=10*mm, bottomMargin=12*mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='AuralixSmall', fontName='AuralixSans', fontSize=8.5, leading=11))
    styles.add(ParagraphStyle(name='AuralixNormal', fontName='AuralixSans', fontSize=9.5, leading=13))
    styles.add(ParagraphStyle(name='AuralixBold', fontName='AuralixSansBold', fontSize=9.5, leading=13))
    styles.add(ParagraphStyle(name='AuralixTitle', fontName='AuralixSansBold', textColor=ORANGE, alignment=1, fontSize=20, leading=24))
    story=[]
    if LOGO.exists():
        im=Image(str(LOGO), width=30*mm, height=30*mm)
    else:
        im=Paragraph('<b>AURALIX TECHNOLOGIES</b>', styles['AuralixBold'])
    company = Paragraph('<b>AURALIX TECHNOLOGIES</b><br/><font color="#f26b21">Your Vision Our Expertise</font>', styles['AuralixNormal'])
    contact = Paragraph('<b>Email :</b> auralix.org@gmail.com<br/><b>Phone Number :</b> 8531008601', styles['AuralixSmall'])
    header = Table([[im, company, contact]], colWidths=[35*mm, 82*mm, 58*mm])
    header.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ALIGN',(2,0),(2,0),'RIGHT'),('LEFTPADDING',(0,0),(-1,-1),2),('RIGHTPADDING',(0,0),(-1,-1),2)]))
    story += [header, Spacer(1,3*mm)]
    story.append(Table([['']], colWidths=[175*mm], rowHeights=[1.4*mm], style=[('BACKGROUND',(0,0),(-1,-1),ORANGE)]))
    story += [Spacer(1,3*mm), Paragraph('INVOICE' if kind=='invoice' else 'QUOTATION', styles['AuralixTitle']), Spacer(1,3*mm)]
    number = doc.invoice_no if kind=='invoice' else doc.quotation_no
    dlabel = 'Invoice Date' if kind=='invoice' else 'Quotation Date'
    datev = doc.invoice_date if kind=='invoice' else doc.quotation_date
    due = doc.due_date if kind=='invoice' else doc.valid_until
    right = f'<b>{number}</b><br/><b>{dlabel} :</b> {datev.strftime("%d-%m-%Y")}<br/><b>{"Due Date" if kind=="invoice" else "Valid Until"} :</b> {due.strftime("%d-%m-%Y") if due else "-"}<br/><b>Status :</b> {esc(doc.payment_status if kind=="invoice" else doc.status)}'
    left = f'<b>Bill To :</b><br/>{esc(customer.name)}<br/>{esc(customer.company)}<br/>{esc(customer.address)}<br/><b>Email :</b> {esc(customer.email)}<br/><b>Phone Number :</b> {esc(customer.phone)}<br/><b>GSTIN :</b> {esc(customer.gstin or "-")}'
    info=Table([[Paragraph(left,styles['AuralixSmall']), Paragraph(right,styles['AuralixSmall'])]], colWidths=[105*mm,70*mm])
    info.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('ALIGN',(1,0),(1,0),'RIGHT')]))
    story += [info, Spacer(1,5*mm)]
    rows=[['#','Description','Qty','Rate (₹)','Amount (₹)']]
    for i,it in enumerate(items,1):
        rows.append([str(i), Paragraph(esc(it.description), styles['AuralixSmall']), f'{it.quantity:g}', money(it.rate), money(it.amount)])
    t=Table(rows,colWidths=[10*mm,82*mm,18*mm,32*mm,33*mm],repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),ORANGE),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'AuralixSansBold'),('GRID',(0,0),(-1,-1),0.4,colors.grey),('ALIGN',(0,0),(0,-1),'CENTER'),('ALIGN',(2,1),(-1,-1),'RIGHT'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('FONTNAME',(0,1),(-1,-1),'AuralixSans'),('FONTSIZE',(0,0),(-1,-1),8.5),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, colors.HexColor('#f7f7f7')])]))
    story += [t, Spacer(1,5*mm)]
    discount=float(doc.discount or 0); gst=float(doc.gst_amount or 0)
    gst_type=getattr(doc,'gst_type','CGST/SGST')
    if gst_type == 'CGST/SGST':
        gst_rows=[['CGST (9%)',money(gst/2)],['SGST (9%)',money(gst/2)]] if abs(float(doc.gst_percent or 0)-18)<0.0001 else [['CGST/SGST',money(gst)]]
    else:
        gst_rows=[['IGST',money(gst)]]
    totals=[['Sub Total',money(doc.subtotal)],['Discount',money(discount)]] + gst_rows + [['TOTAL AMOUNT',money(doc.total)]]
    tt=Table(totals,colWidths=[45*mm,45*mm],hAlign='RIGHT')
    tt.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'AuralixSans'),('ALIGN',(1,0),(1,-1),'RIGHT'),('FONTNAME',(0,-1),(-1,-1),'AuralixSansBold'),('BACKGROUND',(0,-1),(-1,-1),colors.HexColor('#fff0e6')),('TEXTCOLOR',(0,-1),(-1,-1),ORANGE),('GRID',(0,0),(-1,-1),0.4,colors.grey)]))
    story += [tt, Spacer(1,6*mm)]
    if getattr(doc,'subject',''):
        story += [Paragraph(f'<b>Subject :</b> {esc(doc.subject)}', styles['AuralixSmall']), Spacer(1,3*mm)]
    story += [Paragraph(f'<b>Notes :</b> {esc(doc.notes or "Thank you for your business!")}', styles['AuralixSmall']), Spacer(1,9*mm)]
    story.append(Paragraph('<b>AURALIX TECHNOLOGIES</b><br/>Thank you for your business.', styles['AuralixNormal']))
    pdf.build(story)
    buf.seek(0)
    return buf
