class FakeSSHRunner:
    """In-memory SSH runner for tests; records commands, returns canned output."""

    def __init__(self):
        self.commands = []
        self.outputs = {}
        self.files = {}
        self.uploaded = []

    def run(self, command, timeout=300):
        self.commands.append((command, timeout, None))
        for key, value in self.outputs.items():
            if command.startswith(key):
                return value
        if command.startswith('command -v'):
            return ('', 'not found', 1)
        return ('', '', 0)

    def read_file(self, path):
        if path in self.files:
            return self.files[path]
        key = 'cat %s' % path
        if key in self.outputs:
            stdout, _stderr, code = self.outputs[key]
            return stdout if code == 0 else ''
        return ''

    def write_file(self, path, content, mode=None):
        self.files[path] = content
        self.commands.append(('write:%s' % path, 0, mode))

    def upload_tree(self, local_root, remote_root):
        self.uploaded.append((local_root, remote_root))
        return 0

    def close(self):
        pass
