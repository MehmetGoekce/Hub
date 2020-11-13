import hub
from hub.utils import batch
from hub.compute.transform import Transform

try:
    from pathos.pools import ProcessPool
    from pathos.pools import ThreadPool
except Exception:
    pass


class PathosTransform(Transform):
    def __init__(self, func, schema, ds):
        Transform.__init__(self, func, schema, ds)
        self.map = ThreadPool(nodes=8).map

    def store(self, url, token=None):
        """
        mary chunks with compute
        """
        ds = hub.Dataset(
            url, mode="w", shape=self._ds.shape, schema=self._schema, token=token, cache=False
        )

        # Chunkwise compute
        batch_size = ds.chunksize

        def batchify(ds):
            return tuple(batch(ds, batch_size))

        def batched_func(i_xs):
            i, xs = i_xs
            xs = [self._func(x) for x in xs]
            self._transfer_batch(ds, i, xs)

        batched = batchify(ds)

        results = self.map(batched_func, enumerate(batched))
        results = list(results)
        return ds

    def _transfer_batch(self, ds, i, results):
        for j, result in enumerate(results):
            for key in result:
                ds[key, i * ds.chunksize + j] = result[key]