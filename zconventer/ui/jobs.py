from collections.abc import Callable
from dataclasses import replace

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

from ..core.downloader import Cancelled, Downloader, Request, humanize


class Job(QObject):
    title = Signal(str)
    progress = Signal(object, str)
    status = Signal(str)
    done = Signal(list)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, req: Request):
        super().__init__()
        self.req = req
        self.state = "queued"  # queued | running | done | failed | cancelled
        self._downloader: Downloader | None = None

    def cancel(self):
        if self.state == "queued":
            self.state = "cancelled"
            self.cancelled.emit()
        elif self._downloader:
            self._downloader.cancel()


class _JobRunner(QRunnable):
    def __init__(self, job: Job):
        super().__init__()
        self.job = job

    def run(self):
        job = self.job
        if job.state != "queued":
            return
        job.state = "running"
        dl = Downloader(replace(job.req), lambda kind, *a: getattr(job, kind).emit(*a))
        job._downloader = dl
        try:
            paths = dl.run()
        except Cancelled:
            job.state = "cancelled"
            job.cancelled.emit()
        except Exception as e:
            job.state = "failed"
            job.failed.emit(humanize(e))
        else:
            job.state = "done"
            job.done.emit(paths)


class JobManager(QObject):
    added = Signal(Job)

    def __init__(self, parallel: int):
        super().__init__()
        self.pool = QThreadPool(self)
        self.set_parallel(parallel)

    def set_parallel(self, n: int):
        self.pool.setMaxThreadCount(max(1, min(4, n)))

    def submit(self, req: Request) -> Job:
        job = Job(req)
        self.added.emit(job)
        self.pool.start(_JobRunner(job))
        return job


class _Signals(QObject):
    ok = Signal(object)
    err = Signal(str)


class _Task(QRunnable):
    def __init__(self, fn, signals):
        super().__init__()
        self.fn = fn
        self.signals = signals

    def run(self):
        try:
            result = self.fn()
        except Exception as e:
            self.signals.err.emit(str(e) or e.__class__.__name__)
        else:
            self.signals.ok.emit(result)


def run_async(fn: Callable, on_ok: Callable, on_err: Callable, parent: QObject) -> None:
    """Run fn on the global pool and deliver the result on the GUI thread."""
    signals = _Signals(parent)
    signals.ok.connect(on_ok)
    signals.err.connect(on_err)
    signals.ok.connect(signals.deleteLater)
    signals.err.connect(signals.deleteLater)
    QThreadPool.globalInstance().start(_Task(fn, signals))
