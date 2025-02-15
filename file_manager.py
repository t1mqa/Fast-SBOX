from filelock import FileLock

class FileManager:
    def __init__(self, filename: str):
        self.filename = filename
        self.lock = FileLock(f"{filename}.lock")

    def write_line(self, line: str):
        with self.lock:
            with open(self.filename, "a", encoding="utf-8") as f:
                f.write(line + "\n")

results_manager = FileManager("results.txt")
unbanned_manager = FileManager("unbanned.txt")