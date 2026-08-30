from datetime import date
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import Base, engine, get_db
from .models import User, Customer, Invoice, InvoiceItem, Quotation, QuotationItem, FinanceEntry, Payment
from .schemas import LoginIn, ProfileIn, PasswordIn, CustomerIn, InvoiceIn, QuotationIn, FinanceIn, PaymentIn
from .auth import hash_password, verify_password, create_token, get_current_user
from .pdf import make_document

Base.metadata.create_all(bind=engine)
app=FastAPI(title='Auralix Technologies Billing API', version='3.0')
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:5173','http://127.0.0.1:5173'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

def next_number(db, model, prefix):
    year=date.today().year
    count=db.query(model).count()+1
    return f'{prefix}-{year}-{count:04d}'

def calc(items,gst,discount):
    subtotal=round(sum(float(x.quantity)*float(x.rate) for x in items),2)
    taxable=max(subtotal-float(discount),0)
    gst_amount=round(taxable*float(gst)/100,2)
    total=round(taxable+gst_amount,2)
    return subtotal,gst_amount,total

def user_json(u):
    return {'id':u.id,'name':u.name,'email':u.email,'phone':u.phone or '', 'role':u.role}

def doc_json(doc, kind):
    customer=doc.customer
    return {'id':doc.id,'number':doc.invoice_no if kind=='invoice' else doc.quotation_no,'customer_id':doc.customer_id,
      'customer':{'name':customer.name,'company':customer.company,'email':customer.email,'phone':customer.phone,'address':customer.address,'gstin':customer.gstin},
      'date':(doc.invoice_date if kind=='invoice' else doc.quotation_date).isoformat(),
      'due_date':(doc.due_date if kind=='invoice' else doc.valid_until).isoformat() if (doc.due_date if kind=='invoice' else doc.valid_until) else None,
      'gst_percent':doc.gst_percent,'gst_type':getattr(doc,'gst_type','CGST/SGST'),'discount':doc.discount,'gst_amount':doc.gst_amount,
      'subtotal':doc.subtotal,'total':doc.total,'status':doc.payment_status if kind=='invoice' else doc.status,
      'subject':getattr(doc,'subject',''),'notes':doc.notes,
      'items':[{'id':i.id,'description':i.description,'quantity':i.quantity,'rate':i.rate,'amount':i.amount} for i in doc.items]}

@app.get('/')
def root(): return {'message':'Auralix Technologies API is running'}

@app.post('/api/auth/login')
def login(data:LoginIn, db:Session=Depends(get_db)):
    user=db.query(User).filter(func.lower(User.email)==data.email.lower()).first()
    if not user or not verify_password(data.password,user.password_hash): raise HTTPException(401,'Invalid email or password')
    return {'access_token':create_token(user),'token_type':'bearer','user':user_json(user)}

@app.get('/api/me')
def me(user=Depends(get_current_user)): return user_json(user)

@app.put('/api/me')
def update_me(data:ProfileIn, db:Session=Depends(get_db), user=Depends(get_current_user)):
    other=db.query(User).filter(func.lower(User.email)==data.email.lower(), User.id != user.id).first()
    if other: raise HTTPException(409,'That email address is already used by another user')
    user.name=data.name.strip(); user.email=data.email.lower().strip(); user.phone=data.phone.strip()
    db.commit(); db.refresh(user)
    return user_json(user)

@app.post('/api/me/change-password')
def change_password(data:PasswordIn, db:Session=Depends(get_db), user=Depends(get_current_user)):
    if not verify_password(data.current_password,user.password_hash): raise HTTPException(400,'Current password is incorrect')
    if data.current_password == data.new_password: raise HTTPException(400,'New password must be different from the current password')
    user.password_hash=hash_password(data.new_password)
    db.commit()
    return {'message':'Password changed successfully. Please sign in again.'}

@app.get('/api/customers')
def customers(db:Session=Depends(get_db), user=Depends(get_current_user)):
    return [{'id':c.id,'name':c.name,'company':c.company,'email':c.email,'phone':c.phone,'address':c.address,'gstin':c.gstin} for c in db.query(Customer).order_by(Customer.name).all()]
@app.post('/api/customers')
def add_customer(data:CustomerIn, db:Session=Depends(get_db), user=Depends(get_current_user)):
    c=Customer(**data.model_dump()); db.add(c); db.commit(); db.refresh(c); return {'id':c.id}

@app.delete('/api/customers/{customer_id}')
def delete_customer(customer_id:int, db:Session=Depends(get_db), user=Depends(get_current_user)):
    c=db.get(Customer, customer_id)
    if not c:
        raise HTTPException(404, 'Customer not found')
    invoice_count=db.query(Invoice).filter(Invoice.customer_id==customer_id).count()
    quotation_count=db.query(Quotation).filter(Quotation.customer_id==customer_id).count()
    if invoice_count or quotation_count:
        raise HTTPException(409, f'Cannot delete this customer because they have {invoice_count} invoice(s) and {quotation_count} quotation(s). Delete those documents first.')
    db.delete(c)
    db.commit()
    return {'message':'Customer deleted successfully'}

@app.delete('/api/customers')
def clear_customers(db:Session=Depends(get_db), user=Depends(get_current_user)):
    customer_count=db.query(Customer).count()
    linked_invoices=db.query(Invoice).count()
    linked_quotations=db.query(Quotation).count()
    if linked_invoices or linked_quotations:
        raise HTTPException(409, f'Customer data cannot be cleared while invoices ({linked_invoices}) or quotations ({linked_quotations}) exist. Delete those documents first.')
    db.query(Customer).delete(synchronize_session=False)
    db.commit()
    return {'message':f'{customer_count} customer record(s) cleared successfully'}

@app.get('/api/invoices')
def invoices(db:Session=Depends(get_db), user=Depends(get_current_user)):
    return [doc_json(x,'invoice') for x in db.query(Invoice).order_by(Invoice.id.desc()).all()]
@app.get('/api/invoices/{invoice_id}')
def invoice(invoice_id:int,db:Session=Depends(get_db),user=Depends(get_current_user)):
    x=db.get(Invoice,invoice_id)
    if not x: raise HTTPException(404,'Invoice not found')
    return doc_json(x,'invoice')
@app.post('/api/invoices')
def create_invoice(data:InvoiceIn,db:Session=Depends(get_db),user=Depends(get_current_user)):
    if not data.items: raise HTTPException(400,'Add at least one item')
    c=db.get(Customer,data.customer_id)
    if not c: raise HTTPException(400,'Customer not found')
    subtotal,gst,total=calc(data.items,data.gst_percent,data.discount)
    x=Invoice(invoice_no=next_number(db,Invoice,'INV'),customer_id=c.id,invoice_date=data.invoice_date,due_date=data.due_date,gst_percent=data.gst_percent,gst_type=data.gst_type,discount=data.discount,payment_status=data.payment_status,notes=data.notes,subtotal=subtotal,gst_amount=gst,total=total)
    db.add(x); db.flush()
    for it in data.items: db.add(InvoiceItem(invoice_id=x.id,description=it.description.strip(),quantity=it.quantity,rate=it.rate,amount=round(it.quantity*it.rate,2)))
    db.commit(); db.refresh(x); return doc_json(x,'invoice')
@app.put('/api/invoices/{invoice_id}')
def update_invoice(invoice_id:int,data:InvoiceIn,db:Session=Depends(get_db),user=Depends(get_current_user)):
    x=db.get(Invoice,invoice_id)
    if not x: raise HTTPException(404,'Invoice not found')
    if not db.get(Customer,data.customer_id): raise HTTPException(400,'Customer not found')
    subtotal,gst,total=calc(data.items,data.gst_percent,data.discount)
    x.customer_id=data.customer_id; x.invoice_date=data.invoice_date; x.due_date=data.due_date; x.gst_percent=data.gst_percent; x.gst_type=data.gst_type; x.discount=data.discount; x.payment_status=data.payment_status; x.notes=data.notes; x.subtotal=subtotal; x.gst_amount=gst; x.total=total
    x.items.clear()
    for it in data.items: x.items.append(InvoiceItem(description=it.description.strip(),quantity=it.quantity,rate=it.rate,amount=round(it.quantity*it.rate,2)))
    db.commit(); db.refresh(x); return doc_json(x,'invoice')
@app.delete('/api/invoices/{invoice_id}')
def delete_invoice(invoice_id:int,db:Session=Depends(get_db),user=Depends(get_current_user)):
    x=db.get(Invoice,invoice_id)
    if not x: raise HTTPException(404,'Invoice not found')
    db.delete(x); db.commit(); return {'message':'Invoice deleted'}
@app.get('/api/invoices/{invoice_id}/pdf')
def invoice_pdf(invoice_id:int,db:Session=Depends(get_db),user=Depends(get_current_user)):
    x=db.get(Invoice,invoice_id)
    if not x: raise HTTPException(404,'Invoice not found')
    buf=make_document('invoice',x,x.customer,x.items)
    return StreamingResponse(buf,media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename={x.invoice_no}.pdf'})

@app.get('/api/quotations')
def quotations(db:Session=Depends(get_db),user=Depends(get_current_user)):
    return [doc_json(x,'quotation') for x in db.query(Quotation).order_by(Quotation.id.desc()).all()]
@app.post('/api/quotations')
def create_quotation(data:QuotationIn,db:Session=Depends(get_db),user=Depends(get_current_user)):
    if not data.items: raise HTTPException(400,'Add at least one item')
    if not db.get(Customer,data.customer_id): raise HTTPException(400,'Customer not found')
    subtotal,gst,total=calc(data.items,data.gst_percent,data.discount)
    x=Quotation(quotation_no=next_number(db,Quotation,'QT'),customer_id=data.customer_id,quotation_date=data.quotation_date,valid_until=data.valid_until,gst_percent=data.gst_percent,gst_type=data.gst_type,discount=data.discount,status=data.status,subject=data.subject,notes=data.notes,subtotal=subtotal,gst_amount=gst,total=total)
    db.add(x); db.flush()
    for it in data.items: db.add(QuotationItem(quotation_id=x.id,description=it.description.strip(),quantity=it.quantity,rate=it.rate,amount=round(it.quantity*it.rate,2)))
    db.commit(); db.refresh(x); return doc_json(x,'quotation')
@app.put('/api/quotations/{quotation_id}')
def update_quotation(quotation_id:int,data:QuotationIn,db:Session=Depends(get_db),user=Depends(get_current_user)):
    x=db.get(Quotation,quotation_id)
    if not x: raise HTTPException(404,'Quotation not found')
    if not db.get(Customer,data.customer_id): raise HTTPException(400,'Customer not found')
    subtotal,gst,total=calc(data.items,data.gst_percent,data.discount)
    x.customer_id=data.customer_id; x.quotation_date=data.quotation_date; x.valid_until=data.valid_until; x.gst_percent=data.gst_percent; x.gst_type=data.gst_type; x.discount=data.discount; x.status=data.status; x.subject=data.subject; x.notes=data.notes; x.subtotal=subtotal; x.gst_amount=gst; x.total=total
    x.items.clear()
    for it in data.items: x.items.append(QuotationItem(description=it.description.strip(),quantity=it.quantity,rate=it.rate,amount=round(it.quantity*it.rate,2)))
    db.commit(); db.refresh(x); return doc_json(x,'quotation')
@app.delete('/api/quotations/{quotation_id}')
def delete_quotation(quotation_id:int,db:Session=Depends(get_db),user=Depends(get_current_user)):
    x=db.get(Quotation,quotation_id)
    if not x: raise HTTPException(404,'Quotation not found')
    db.delete(x); db.commit(); return {'message':'Quotation deleted'}
@app.get('/api/quotations/{quotation_id}/pdf')
def quotation_pdf(quotation_id:int,db:Session=Depends(get_db),user=Depends(get_current_user)):
    x=db.get(Quotation,quotation_id)
    if not x: raise HTTPException(404,'Quotation not found')
    buf=make_document('quotation',x,x.customer,x.items)
    return StreamingResponse(buf,media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename={x.quotation_no}.pdf'})

@app.post('/api/finance')
def add_finance(data:FinanceIn,db:Session=Depends(get_db),user=Depends(get_current_user)):
    if data.entry_type not in ('revenue','expense'): raise HTTPException(400,'entry_type must be revenue or expense')
    x=FinanceEntry(**data.model_dump()); db.add(x); db.commit(); db.refresh(x); return {'id':x.id}
@app.get('/api/finance')
def finance(db:Session=Depends(get_db),user=Depends(get_current_user)):
    return [{'id':x.id,'entry_type':x.entry_type,'category':x.category,'description':x.description,'amount':x.amount,'entry_date':x.entry_date.isoformat(),'reference':x.reference} for x in db.query(FinanceEntry).order_by(FinanceEntry.entry_date.desc()).all()]

@app.post('/api/invoices/{invoice_id}/payments')
def add_payment(invoice_id:int,data:PaymentIn,db:Session=Depends(get_db),user=Depends(get_current_user)):
    inv=db.get(Invoice,invoice_id)
    if not inv: raise HTTPException(404,'Invoice not found')
    paid_before=db.query(func.coalesce(func.sum(Payment.amount),0)).filter(Payment.invoice_id==invoice_id).scalar() or 0
    if paid_before + data.amount > inv.total + 0.01: raise HTTPException(400,'Payment exceeds invoice balance')
    p=Payment(invoice_id=invoice_id,**data.model_dump()); db.add(p)
    paid=paid_before + data.amount
    inv.payment_status='Paid' if paid >= inv.total - 0.01 else 'Partial'
    db.commit(); return {'paid':round(paid,2),'balance':round(max(inv.total-paid,0),2),'status':inv.payment_status}

@app.get('/api/dashboard')
def dashboard(db:Session=Depends(get_db),user=Depends(get_current_user)):
    revenue=(db.query(func.coalesce(func.sum(FinanceEntry.amount),0)).filter(FinanceEntry.entry_type=='revenue').scalar() or 0)
    expenses=(db.query(func.coalesce(func.sum(FinanceEntry.amount),0)).filter(FinanceEntry.entry_type=='expense').scalar() or 0)
    invoice_total=(db.query(func.coalesce(func.sum(Invoice.total),0)).filter(Invoice.payment_status=='Paid').scalar() or 0)
    revenue += invoice_total
    pending=(db.query(func.coalesce(func.sum(Invoice.total),0)).filter(Invoice.payment_status.in_(['Pending','Partial'])).scalar() or 0)
    return {'revenue':round(revenue,2),'expenses':round(expenses,2),'profit':round(revenue-expenses,2),'pending':round(pending,2),'invoices':db.query(Invoice).count(),'quotations':db.query(Quotation).count(),'customers':db.query(Customer).count()}

@app.get('/api/reports')
def reports(start:str=None,end:str=None,db:Session=Depends(get_db),user=Depends(get_current_user)):
    s=date.fromisoformat(start) if start else date(date.today().year,1,1); e=date.fromisoformat(end) if end else date.today()
    inv=(db.query(func.coalesce(func.sum(Invoice.total),0)).filter(Invoice.invoice_date>=s,Invoice.invoice_date<=e,Invoice.payment_status=='Paid').scalar() or 0)
    finrev=(db.query(func.coalesce(func.sum(FinanceEntry.amount),0)).filter(FinanceEntry.entry_type=='revenue',FinanceEntry.entry_date>=s,FinanceEntry.entry_date<=e).scalar() or 0)
    exp=(db.query(func.coalesce(func.sum(FinanceEntry.amount),0)).filter(FinanceEntry.entry_type=='expense',FinanceEntry.entry_date>=s,FinanceEntry.entry_date<=e).scalar() or 0)
    return {'start':s.isoformat(),'end':e.isoformat(),'revenue':round(inv+finrev,2),'expenses':round(exp,2),'profit':round(inv+finrev-exp,2),'invoice_count':db.query(Invoice).filter(Invoice.invoice_date>=s,Invoice.invoice_date<=e).count(),'quotation_count':db.query(Quotation).filter(Quotation.quotation_date>=s,Quotation.quotation_date<=e).count()}

@app.get('/api/users')
def users(db:Session=Depends(get_db),user=Depends(get_current_user)):
    return [{'id':x.id,'name':x.name,'email':x.email,'phone':x.phone or '', 'role':x.role,'active':bool(x.active)} for x in db.query(User).order_by(User.id).all()]
