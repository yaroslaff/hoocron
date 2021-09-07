class HoocronHookBase():
    def __init__():
        pass
    
    def add_argument_group(self, parser):
        pass

    def configure(self, jobs, args):
        pass

    def empty(self):
        # if empty - do not start it. Base class is always empty
        return True

    def start(self):
        pass

    def stop(self):
        pass

    def running(self):
        return False
        
