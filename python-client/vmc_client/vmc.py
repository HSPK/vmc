from vmc_client._async_vmc import AsyncVMC
from vmc_client._sync_vmc import SyncVMC


class VMC:
    def __init__(self, *args, **kwargs):
        _sync = SyncVMC(*args, **kwargs)
        _async = AsyncVMC(*args, **kwargs)
        self.generate = _sync.generate
        self.embedding = _sync.embedding
        self.stream = _sync.stream
        self.rerank = _sync.rerank
        self.tokenize = _sync.tokenize
        self.transcribe = _sync.transcribe
        self.health = _sync.health
        self.supported_models = _sync.supported_models

        self.agenerate = _async.generate
        self.aembedding = _async.embedding
        self.astream = _async.stream
        self.arerank = _async.rerank
        self.atokenize = _async.tokenize
        self.atranscribe = _async.transcribe
        self.ahealth = _async.health
