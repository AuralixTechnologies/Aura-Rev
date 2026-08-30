from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    phone = Column(String(50), default='')
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), default='Staff')
    active = Column(Integer, default=1)

class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    company = Column(String(150), default='')
    email = Column(String(150), default='')
    phone = Column(String(50), default='')
    address = Column(Text, default='')
    gstin = Column(String(50), default='')

class Invoice(Base):
    __tablename__ = 'invoices'
    id = Column(Integer, primary_key=True)
    invoice_no = Column(String(50), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    invoice_date = Column(Date, default=date.today)
    due_date = Column(Date, nullable=True)
    gst_percent = Column(Float, default=18)
    gst_type = Column(String(20), default='CGST/SGST')
    discount = Column(Float, default=0)
    payment_status = Column(String(30), default='Pending')
    notes = Column(Text, default='')
    subtotal = Column(Float, default=0)
    gst_amount = Column(Float, default=0)
    total = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    customer = relationship('Customer')
    items = relationship('InvoiceItem', cascade='all, delete-orphan', back_populates='invoice')
    payments = relationship('Payment', cascade='all, delete-orphan', back_populates='invoice')

class InvoiceItem(Base):
    __tablename__ = 'invoice_items'
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False)
    description = Column(String(300), nullable=False)
    quantity = Column(Float, default=1)
    rate = Column(Float, default=0)
    amount = Column(Float, default=0)
    invoice = relationship('Invoice', back_populates='items')

class Quotation(Base):
    __tablename__ = 'quotations'
    id = Column(Integer, primary_key=True)
    quotation_no = Column(String(50), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    quotation_date = Column(Date, default=date.today)
    valid_until = Column(Date, nullable=True)
    gst_percent = Column(Float, default=18)
    gst_type = Column(String(20), default='CGST/SGST')
    discount = Column(Float, default=0)
    status = Column(String(30), default='Draft')
    subject = Column(String(300), default='')
    notes = Column(Text, default='')
    subtotal = Column(Float, default=0)
    gst_amount = Column(Float, default=0)
    total = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    customer = relationship('Customer')
    items = relationship('QuotationItem', cascade='all, delete-orphan', back_populates='quotation')

class QuotationItem(Base):
    __tablename__ = 'quotation_items'
    id = Column(Integer, primary_key=True)
    quotation_id = Column(Integer, ForeignKey('quotations.id'), nullable=False)
    description = Column(String(300), nullable=False)
    quantity = Column(Float, default=1)
    rate = Column(Float, default=0)
    amount = Column(Float, default=0)
    quotation = relationship('Quotation', back_populates='items')

class FinanceEntry(Base):
    __tablename__ = 'finance_entries'
    id = Column(Integer, primary_key=True)
    entry_type = Column(String(20), nullable=False)
    category = Column(String(100), default='General')
    description = Column(String(300), default='')
    amount = Column(Float, default=0)
    entry_date = Column(Date, default=date.today)
    reference = Column(String(100), default='')

class Payment(Base):
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False)
    payment_date = Column(Date, default=date.today)
    amount = Column(Float, default=0)
    method = Column(String(50), default='Bank Transfer')
    reference = Column(String(100), default='')
    invoice = relationship('Invoice', back_populates='payments')
