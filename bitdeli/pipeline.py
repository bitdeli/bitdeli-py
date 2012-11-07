import traceback, threading, sys

class ExitPipeline(Exception):
    pass

class Pipeline(object):
    def __init__(self, pipeline):
        self.lock = threading.Condition(threading.Lock())
        self.thread = threading.Thread(target=self._run, args=(pipeline,))
        self.item = None
        self.error = None
        self.active = False
        self.exit = False
        self.thread.start()

    def _run(self, pipeline):
        try:
            for x in pipeline(self._iter()):
                pass
        except ExitPipeline:
            pass
        except:
            self.error = traceback.format_exc()
            # there are two ways how we may end up here:
            if not self.active:
                # case 1) initialization of the pipeline crashes
                # before we get to 'yield item' in _iter below: We must
                # wait for the main thread to call next(), so we can
                # release it properly below.
                self.lock.acquire()
                while self.item == None:
                    self.lock.wait()
            # case 2) crash occurs after 'yield item' moves control to
            # the other stages in the pipeline: release lock as if we
            # had processed the item as usual.
            self.lock.notify()
            self.lock.release()

    def _iter(self):
        while True:
            self.lock.acquire()
            self.active = True
            while self.item == None:
                self.lock.wait()
            if self.exit:
                if self.error:
                    raise ExitPipeline()
                else:
                    return
            item = self.item
            self.item = None
            yield item
            self.lock.notify()
            self.lock.release()

    def next(self, item):
        self.lock.acquire()
        self.item = item
        self.lock.notify()
        self.lock.wait()
        self.lock.release()
        return self.error

    def close(self, error):
        self.lock.acquire()
        self.item = True
        self.exit = True
        self.error = error
        self.lock.notify()
        self.lock.release()
        self.thread.join()
        return self.error

def run(source, pipelines):
    def run(pipes):
        for item in source:
            for pipe in pipes:
                error = pipe.next(item)
                if error:
                    return error
        return False
    pipes = [Pipeline(p) for p in pipelines]
    error = run(pipes)
    for pipe in pipes:
        error = pipe.close(error)
    if error:
        sys.stderr.write(error)
        return False
    return True
