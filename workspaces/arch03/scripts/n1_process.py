"""N1 child lifetime and stage-local ledger under the unchanged shared lock.

Shared owner.json is written once. Every accepted child is waited for before
an exception can escape or the lock can be released. Python 3.6 standard lib.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import stat
import subprocess
import time
import uuid


def require(condition,message):
    if not condition:raise ValueError(message)


def now():return datetime.datetime.now().isoformat()


def identity(path):
    value=Path(path).lstat()
    require(not stat.S_ISLNK(value.st_mode),'Symlink in N1 process identity: '+str(path))
    return value.st_dev,value.st_ino,value.st_uid,value.st_gid,value.st_mode


def encoded(value):return (json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n').encode('utf8')


def atomic_save(path,value):
    """Stage-local only. Preserve an incomplete temp file if writing fails."""
    path=Path(path);temporary=path.with_name(path.name+'.tmp-'+uuid.uuid4().hex)
    raw=encoded(value)
    with temporary.open('xb') as stream:
        stream.write(raw);stream.flush();os.fsync(stream.fileno())
    os.replace(str(temporary),str(path))


def write_initial_owner(path,raw):
    # No shared owner.tmp and no replacement of another owner's file.
    with Path(path).open('xb') as stream:
        stream.write(raw);stream.flush();os.fsync(stream.fileno())


class ProcessLedger:
    def __init__(self,common,lock,session):
        self.common=common;self.lock=Path(lock).absolute();self.session=Path(session).absolute()
        self.bundle=Path(common.ROOT).absolute();self.ledger=self.session/'process_ledger'
        self.owner=dict(pid=os.getpid(),host=socket.gethostname(),bundle=str(self.bundle),session=self.session.name,
            schema='arch03-n1-process-lock-v1',token=uuid.uuid4().hex,child_ledger=str(self.ledger))
        self.owner_raw=encoded(self.owner);self.lock_identity=None;self.owner_identity=None
        self.acquired=False;self.initialized=False;self.sequence=0;self.active=None

    def acquire(self):
        require(self.common.ACTIVE_CHILD is None,'Existing active child prevents N1 lock acquisition')
        require(self.session.parent==self.bundle/'runs','N1 ledger must belong to this bundle session')
        self.lock.mkdir()  # Never remove or take over an existing lock.
        self.lock_identity=identity(self.lock)
        try:
            write_initial_owner(self.lock/'owner.json',self.owner_raw)
            self.owner_identity=identity(self.lock/'owner.json')
            self.check_owner()
        except BaseException:
            # Only our positively identified, still-empty directory is removable.
            # A partial owner/unknown member is preserved for manual recovery.
            try:
                if identity(self.lock)==self.lock_identity and not any(self.lock.iterdir()):self.lock.rmdir()
            except OSError:pass
            raise
        self.acquired=True;self.common.LOCK=self.lock
        return dict(self.owner)

    def check_owner(self):
        require(self.lock_identity is not None and identity(self.lock)==self.lock_identity,
            'N1 shared lock directory identity changed')
        path=self.lock/'owner.json'
        require(self.owner_identity is not None and identity(path)==self.owner_identity and
            path.read_bytes()==self.owner_raw,'N1 shared lock owner identity changed')

    def initialize(self):
        self.check_owner()
        require(self.session.is_dir() and not self.session.is_symlink(),'N1 session directory is not ready')
        self.ledger.mkdir(mode=0o700)
        self.ledger_identity=identity(self.ledger)
        atomic_save(self.ledger/'identity.json',dict(schema='arch03-n1-process-ledger-v1',owner=self.owner,
            shared_lock=str(self.lock),shared_lock_identity=list(self.lock_identity),
            shared_owner_identity=list(self.owner_identity),shared_owner_sha256=hashlib.sha256(self.owner_raw).hexdigest(),
            process_tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            created=now(),shared_owner_updates_after_acquisition=False))
        self.initialized=True

    def check_ledger(self):
        require(self.initialized and identity(self.ledger)==self.ledger_identity,'N1 private ledger identity changed')

    def record(self,path,value):
        self.check_ledger();atomic_save(path,value)

    def drain(self,child):
        """Do not abandon a child because waiting itself was interrupted."""
        interruptions=[]
        while True:
            try:
                code=child.wait()
                require(isinstance(code,int),'Child wait did not provide an exit code')
                return code,interruptions
            except BaseException as error:
                if not interruptions:interruptions.append(error)
                try:
                    code=child.poll()
                    if code is not None:return code,interruptions
                except BaseException as poll_error:
                    if len(interruptions)==1:interruptions.append(poll_error)
                # Persistent inability to reap keeps the lock and ACTIVE_CHILD;
                # do not spin or pretend that an unobserved child has exited.
                try:time.sleep(0.05)
                except BaseException as pause_error:
                    if len(interruptions)<3:interruptions.append(pause_error)

    def call(self,cmd,run,log):
        self.check_owner();self.check_ledger()
        require(self.common.ACTIVE_CHILD is None and self.active is None,'N1 already has an accepted child')
        run=Path(run).absolute();run.relative_to(self.session)
        require(run.resolve()==run and run.is_dir(),'Noncanonical N1 child run directory')
        relative=Path(log)
        require(not relative.is_absolute() and '..' not in relative.parts,'N1 child log must stay in its run')
        logfile=run/relative
        require(logfile.parent.resolve()==logfile.parent and not logfile.exists() and not logfile.is_symlink(),
            'N1 child log exists or has an unsafe parent')
        command=[str(part) for part in cmd];require(command,'Empty N1 child command')
        self.sequence+=1;record_path=self.ledger/('child_%06d.json'%self.sequence)
        row=dict(schema='arch03-n1-child-process-v1',sequence=self.sequence,owner_token=self.owner['token'],
            driver_pid=self.owner['pid'],host=self.owner['host'],bundle=str(self.bundle),session=self.session.name,
            run=str(run),log=str(logfile),command=command,status='prepared',prepared=now(),pid=None)
        self.record(record_path,row)  # Private ENOSPC here prevents spawning.
        self.check_owner()  # Recheck immediately before the accepted operation.
        child=None;errors=[];code=None
        stream=logfile.open('x')
        try:
            try:
                child=subprocess.Popen(command,cwd=str(run),stdout=stream,stderr=subprocess.STDOUT)
                self.active=child;self.common.ACTIVE_CHILD=child
                row.update(status='running',pid=child.pid,started=now())
                self.record(record_path,row)
                print('CHILD_PID',child.pid,'LOG',logfile,'LEDGER',record_path,flush=True)
            except BaseException as error:
                errors.append(error)
            finally:
                if child is not None:
                    # This also covers failed PID recording, print failures,
                    # SystemExit/KeyboardInterrupt, and wait interruptions.
                    code,interrupted=self.drain(child);errors.extend(interrupted)
                    self.common.ACTIVE_CHILD=None;self.active=None
        finally:
            # Closing the driver's log handle can itself fail on a filesystem.
            # The child has already been reaped; still record this as failure.
            try:stream.close()
            except BaseException as error:errors.append(error)
        if child is not None:
            row.update(status='exited',returncode=code,finished=now(),wait_completed=True)
        else:
            row.update(status='spawn_failed',finished=now(),wait_completed=False)
        try:self.check_owner()
        except BaseException as error:errors.append(error)
        if not errors:
            try:
                text=logfile.read_text(errors='replace')
                if code or re.search(r'(?im)^\s*(Error-|Fatal:|Error:)',text):
                    raise RuntimeError('Tool failed '+str(logfile)+' exit='+str(code))
            except BaseException as error:errors.append(error)
        row['errors']=[dict(type=type(error).__name__,message=str(error)) for error in errors]
        row['call_status']='failed' if errors else 'passed'
        try:self.record(record_path,row)
        except BaseException as error:errors.append(error)
        if errors:
            if len(errors)==1:raise errors[0]
            raise RuntimeError('N1 child call failed after wait: '+'; '.join(type(error).__name__+': '+str(error) for error in errors)) from errors[0]
        return text

    def release(self):
        require(self.acquired,'N1 process lock was never fully acquired')
        if self.active is not None:
            require(self.common.ACTIVE_CHILD is self.active,'N1 active child ownership changed; preserve lock')
            _,errors=self.drain(self.active)
            self.common.ACTIVE_CHILD=None;self.active=None
            if errors:raise errors[0]  # conservatively retain lock if cleanup was interrupted
        require(self.common.ACTIVE_CHILD is None,'An unknown child remains active; preserve N1 lock')
        self.check_owner()
        require({p.name for p in self.lock.iterdir()}=={'owner.json'},'Unexpected shared lock members; preserve lock')
        self.check_owner()
        (self.lock/'owner.json').unlink();self.lock.rmdir()
        self.acquired=False;self.common.LOCK=None
