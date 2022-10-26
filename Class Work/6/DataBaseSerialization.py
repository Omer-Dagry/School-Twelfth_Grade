from BaseDatabase import BaseDatabase


class DataBaseSerialization(BaseDatabase):
    def __init__(self, max_reads_together: int = 10):
        super().__init__(max_reads_together=max_reads_together)
