"""Named capacity profiles for copy-only archives; never source cleanup.

Both retain a 20% margin over the exact compressed size, checks during writes,
and complete readback. The normal reserve stays 2 GiB. A constrained-storage
profile uses 512 MiB; unrelated shared writers can exhaust either reserve.
"""
import shutil

CHUNK = 4*1024**2
RESERVES = {'standard_2GiB': 2*1024**3, 'copy_only_512MiB': 512*1024**2}


def policy(request):
    name = request.get('storage_profile', 'standard_2GiB')
    if not isinstance(name, str) or name not in RESERVES:
        raise ValueError('Unknown C32 copy-only storage profile')
    return dict(profile=name, reserve_bytes=RESERVES[name], margin_numerator=6,
                margin_denominator=5, source_deletion_authorized=False)


def required_bytes(size, selected):
    if type(size) is not int or size < 0 or selected != policy({'storage_profile': selected.get('profile')}):
        raise ValueError('Invalid exact size or capacity policy')
    return (size*6+4)//5+selected['reserve_bytes']


class Sink:
    def __init__(self, stream, directory, selected):
        required_bytes(0, selected)
        self.stream = stream
        self.directory = directory
        self.reserve = selected['reserve_bytes']
        self.count = 0
        self.next_guard = 0

    def write(self, raw):
        if self.count >= self.next_guard:
            if shutil.disk_usage(str(self.directory)).free < self.reserve+CHUNK+len(raw):
                raise ValueError('Shared reserve reached; source and partial C32 archive retained')
            self.next_guard = self.count+CHUNK
        written = self.stream.write(raw)
        if written != len(raw):
            raise OSError('Short archive write; retain partial and source')
        self.count += len(raw)
        return written

    def flush(self):
        self.stream.flush()

    def tell(self):
        return self.count
