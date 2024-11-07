from vmc.proxy.manager import VirtualModelManager
from vmc.utils import LazyObjProxy

vmm: VirtualModelManager = LazyObjProxy(lambda: _get_vmm())
_vmm: VirtualModelManager = None


def _get_vmm():
    if _vmm is None:
        raise ValueError("VMM not initialized")
    return _vmm


def init_vmm(vmm: VirtualModelManager):
    global _vmm

    _vmm = vmm
    assert _vmm is not None, "Cannot initialize VMM with None"
