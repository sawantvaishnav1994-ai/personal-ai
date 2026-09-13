from types import SimpleNamespace

import pytest

from tools.files import register
from tools.registry import Risk, ToolRegistry


def test_file_tools_are_confined_and_overwrite_requires_destructive_tool(tmp_path):
    root = tmp_path / 'approved'
    registry = ToolRegistry(SimpleNamespace(autonomy_mode='ask'))
    register(registry, SimpleNamespace(file_roots=(root,), data_dir=tmp_path))

    created = registry.get('write_file').handler({'path': str(root / 'note.txt'), 'content': 'one'})
    assert created['ok'] is True
    assert registry.get('read_file').handler({'path': str(root / 'note.txt')}) == 'one'
    with pytest.raises(FileExistsError):
        registry.get('write_file').handler({'path': str(root / 'note.txt'), 'content': 'two'})
    assert registry.get('overwrite_file').risk == Risk.DESTRUCTIVE
    registry.get('overwrite_file').handler({'path': str(root / 'note.txt'), 'content': 'two'})
    assert (root / 'note.txt').read_text() == 'two'

    with pytest.raises(PermissionError):
        registry.get('read_file').handler({'path': str(tmp_path / 'outside.txt')})


def test_file_tools_hide_secret_bearing_paths(tmp_path):
    root = tmp_path / 'approved'
    root.mkdir()
    (root / '.env').write_text('SECRET=value')
    registry = ToolRegistry(SimpleNamespace(autonomy_mode='ask'))
    register(registry, SimpleNamespace(file_roots=(root,), data_dir=tmp_path))

    assert '.env' not in {row['name'] for row in registry.get('list_dir').handler({'path': str(root)})}
    with pytest.raises(PermissionError):
        registry.get('read_file').handler({'path': str(root / '.env')})
