import paramiko


class SSHRunner:
    """Runs commands on the VPS over SSH and returns (stdout, stderr, code)."""

    def __init__(self, config):
        self.config = config
        self._client = None

    def _connect(self):
        if self._client is None:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            kwargs = dict(
                hostname=self.config.host,
                port=self.config.port,
                username=self.config.user,
                timeout=20,
            )
            if self.config.key_path:
                kwargs['key_filename'] = self.config.key_path
            elif self.config.password:
                kwargs['password'] = self.config.password
            client.connect(**kwargs)
            self._client = client
        return self._client

    def run(self, command, timeout=300):
        client = self._connect()
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        code = stdout.channel.recv_exit_status()
        return stdout.read().decode(), stderr.read().decode(), code

    def read_file(self, path):
        stdout, _, _ = self.run('cat %s' % path)
        return stdout

    def write_file(self, path, content, mode=None):
        escaped = content.replace("'", "'\\''")
        _, _, code = self.run("printf '%s' '%s' > %s" % ('%s', escaped, path))
        if code != 0:
            raise RuntimeError('failed to write %s' % path)
        if mode:
            self.run('chmod %s %s' % (mode, path))

    def upload_tree(self, local_root, remote_root):
        import os
        sftp = self._connect().open_sftp()
        count = 0
        for dirpath, _dirnames, filenames in os.walk(local_root):
            rel = os.path.relpath(dirpath, local_root).replace(os.sep, '/')
            rdir = remote_root if rel == '.' else remote_root + '/' + rel
            try:
                sftp.stat(rdir)
            except FileNotFoundError:
                sftp.mkdir(rdir)
            for filename in filenames:
                sftp.put(os.path.join(dirpath, filename), rdir + '/' + filename)
                count += 1
        sftp.close()
        return count

    def close(self):
        if self._client is not None:
            self._client.close()
            self._client = None
