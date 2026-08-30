from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class ProfileIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(default='', max_length=50)

class PasswordIn(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)

class CustomerIn(BaseModel):
    name: str
    company: str = ''
    email: str = ''
    phone: str = ''
    address: str = ''
    gstin: str = ''

class ItemIn(BaseModel):
    description: str = Field(min_length=1)
    quantity: float = Field(gt=0)
    rate: float = Field(ge=0)

class InvoiceIn(BaseModel):
    customer_id: int
    invoice_date: date
    due_date: Optional[date] = None
    gst_percent: float = Field(default=18, ge=0, le=100)
    gst_type: str = 'CGST/SGST'
    discount: float = Field(default=0, ge=0)
    payment_status: str = 'Pending'
    notes: str = ''
    items: List[ItemIn]

class QuotationIn(BaseModel):
    customer_id: int
    quotation_date: date
    valid_until: Optional[date] = None
    gst_percent: float = Field(default=18, ge=0, le=100)
    gst_type: str = 'CGST/SGST'
    discount: float = Field(default=0, ge=0)
    status: str = 'Draft'
    subject: str = ''
    notes: str = ''
    items: List[ItemIn]

class FinanceIn(BaseModel):
    entry_type: str
    category: str = 'General'
    description: str = ''
    amount: float = Field(gt=0)
    entry_date: date
    reference: str = ''

class PaymentIn(BaseModel):
    payment_date: date
    amount: float = Field(gt=0)
    method: str = 'Bank Transfer'
    reference: str = ''
