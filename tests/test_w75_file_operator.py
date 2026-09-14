from pathlib import Path
import pytest

from desktop.file_operator import SafeFileAdapter
from security.policy_targets import TargetValidationError


def test_metadata_and_checksum(tmp_path):
    f=tmp_path/'a.txt'; f.write_text('hello'); op=SafeFileAdapter(); m=op.metadata(str(f),[str(tmp_path)])
    assert m['size']==5 and len(m['sha256'])==64 and op.checksum(f)==m['sha256']

def test_read_text_rejects_binary_document(tmp_path):
    f=tmp_path/'x.pdf'; f.write_bytes(b'%PDF-1.4'); op=SafeFileAdapter()
    with pytest.raises(TargetValidationError) as e: op.read_text(str(f),[str(tmp_path)])
    assert e.value.reason_code=='file_type_not_allowed'

def test_read_text_size_limit(tmp_path):
    f=tmp_path/'big.txt'; f.write_bytes(b'x'*20); op=SafeFileAdapter()
    with pytest.raises(TargetValidationError): op.read_text(str(f),[str(tmp_path)],max_bytes=10)

def test_create_file_no_overwrite(tmp_path):
    f=tmp_path/'a.txt'; f.write_text('old'); op=SafeFileAdapter()
    with pytest.raises(FileExistsError): op.create_file(str(f),[str(tmp_path)],'new')
    assert f.read_text()=='old'

def test_create_file_verified(tmp_path):
    f=tmp_path/'a.txt'; r=SafeFileAdapter().create_file(str(f),[str(tmp_path)],'hello')
    assert r.verified and r.rollback=='reversible' and f.read_text()=='hello'

def test_copy_checksum_and_no_blind_overwrite(tmp_path):
    s=tmp_path/'s.txt'; d=tmp_path/'d.txt'; s.write_text('abc'); op=SafeFileAdapter(); r=op.copy(str(s),str(d),[str(tmp_path)])
    assert r.verified and r.evidence['source_sha256']==r.evidence['destination_sha256']
    with pytest.raises(FileExistsError): op.copy(str(s),str(d),[str(tmp_path)])

def test_move_verified_source_absent(tmp_path):
    s=tmp_path/'s.txt'; d=tmp_path/'d.txt'; s.write_text('abc'); r=SafeFileAdapter().move(str(s),str(d),[str(tmp_path)])
    assert r.verified and d.exists() and not s.exists()

def test_trash_retains_recovery_metadata(tmp_path):
    trash=tmp_path/'trash'; trash.mkdir(); f=tmp_path/'x.txt'; f.write_text('x'); r=SafeFileAdapter().trash(str(f),[str(tmp_path)],str(trash))
    assert r.verified and r.rollback=='compensating_action_available' and Path(r.evidence['trash_path']).exists()

def test_permanent_delete_truthfully_irreversible(tmp_path):
    f=tmp_path/'x.txt'; f.write_text('x'); r=SafeFileAdapter().permanent_delete(str(f),[str(tmp_path)])
    assert r.verified and r.rollback=='irreversible' and r.evidence['no_rollback'] is True

def test_nonempty_directory_permanent_delete_blocked(tmp_path):
    d=tmp_path/'d'; d.mkdir(); (d/'x').write_text('x')
    with pytest.raises(OSError): SafeFileAdapter().permanent_delete(str(d),[str(tmp_path)])

def test_path_escape_blocked(tmp_path):
    with pytest.raises(TargetValidationError): SafeFileAdapter().metadata(str(tmp_path/'..'/'escape'),[str(tmp_path)])

def test_symlink_swap_blocked(tmp_path):
    target=tmp_path/'target'; target.mkdir(); link=tmp_path/'link'
    try: link.symlink_to(target,target_is_directory=True)
    except OSError: pytest.skip('symlink unavailable')
    with pytest.raises(TargetValidationError): SafeFileAdapter().metadata(str(link),[str(tmp_path)])
