from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date, time

class VoucherBase(BaseModel):
    voucher_id: Optional[int] = Field(None, alias='voucher_id')
    voucher_code: str
    voucher_type: Literal['percentage discount','fixed amount discount','free item']
    description: str
    discount_value: float
    expiry_date: date
    begin_date: date
    required_points: Optional[int] = Field(None, alias='required_points')
    usage_limit: Optional[int] = Field(None, alias='usage_limit')

class VoucherRequirementBase(BaseModel):
    voucher_id: Optional[int] = Field(None, alias='voucher_id')
    applicable_item_id: Optional[int] = Field(None, alias='applicable_item_id')
    requirement_time: time
    minimum_spend: float
    capped_amount: Optional[float] = Field(None, alias='capped_amount')

class UserVoucherInput(BaseModel):
    user_id: int
    voucher_id: int
    used_date: Optional[date] = None
