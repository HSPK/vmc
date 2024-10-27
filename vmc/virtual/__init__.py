import sys
from typing import TYPE_CHECKING

from .manager import VirtualModelManager

if TYPE_CHECKING:
    vmm: VirtualModelManager


class LazyVMM:
    def __init__(self):
        self._vmm = None

    def __getattr__(self, name):
        if self._vmm is None:
            self._vmm = VirtualModelManager.from_yaml(None)
        return getattr(self._vmm, name)

    def __setattr__(self, name, value):
        if name == "_vmm":
            super().__setattr__(name, value)
        else:
            setattr(self._vmm, name, value)

    def set_vmm(self, vmm):
        self._vmm = vmm


class _M(sys.__class__):
    _vmm = LazyVMM()

    @property
    def vmm(self):
        return self._vmm

    def set_vmm(self, vmm):
        self._vmm.set_vmm(vmm)


sys.modules[__name__].__class__ = _M
