from ..extras import EXTRAS_ONLY
from ..types import Operations
from .builtins import BUILTINS

EXTRAS: Operations = {
    **BUILTINS,
    **EXTRAS_ONLY,
}
