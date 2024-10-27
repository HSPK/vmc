import sys
from typing import TYPE_CHECKING

from .manager import VirtualModelManager

if TYPE_CHECKING:
    vmm: VirtualModelManager

class _M(sys.__class__):
    _vmm = None

    @property
    def vmm(self):
        if self._vmm is None:
            self._vmm = VirtualModelManager.from_yaml(None)
        return self._vmm

    @vmm.setter
    def vmm(self, value):
        self._vmm = value


sys.modules[__name__].__class__ = _M
