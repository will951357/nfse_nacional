

from dataclasses import dataclass, field
from decimal import DefaultContext
from enum import Enum
from io import BytesIO
from numbers import Number
from typing import Union


class FontType(Enum):
    COURIER = "Courier"
    TIMES = "Times"
    HELVETICA = "Helvetica"

@dataclass
class Margins:
    top: Number = 3  # Reduzido de 5 para 3 para corresponder ao original
    right: Number = 3  # Reduzido de 5 para 3 para corresponder ao original
    bottom: Number = 3
    left: Number = 3  # Reduzido de 5 para 3 para corresponder ao original

@dataclass
class DecimalConfig:
    price_precision: int = 4
    quantity_precision: int = 4

class ReceiptPosition(Enum):
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"

@dataclass
class NfseConfig:
    nfse_logo: Union[str, BytesIO, bytes] = None
    pref_logo: Union[str, BytesIO, bytes] = None
    margins: Margins = field(default_factory=Margins)
    font_type: FontType = FontType.HELVETICA
    decimal_config: DecimalConfig = field(default_factory=DecimalConfig)
    receipt_pos: ReceiptPosition = ReceiptPosition.TOP