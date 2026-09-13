from __future__ import annotations

import hashlib
import io
import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class KnowledgeError(ValueError):
    pass


class KnowledgeStore:
    """Durable owner-controlled document knowledge, separate from personal memory."""

    MAX_FILE_BYTES = 10 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'.txt', '.md', '.markdown', '.csv', '.json', '.pdf', '.docx', '.xlsx'}

    def __init__(self, path: Path, object_dir: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.object_dir = Path(object_dir)
        self.object_dir.mkdir(parents=True, exist_ok=True)
        self.lock = RLock()
        self._init()

    def _con(self):
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA foreign_keys=ON')
        return con

    def _init(self):
        with self._con() as con:
            con.executescript(
                '''
                CREATE TABLE IF NOT EXISTS knowledge_documents(
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    media_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    access_class TEXT NOT NULL DEFAULT 'owner',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    object_name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_knowledge_checksum ON knowledge_documents(checksum);
                CREATE INDEX IF NOT EXISTS idx_knowledge_updated ON knowledge_documents(updated_at);
                CREATE TABLE IF NOT EXISTS knowledge_chunks(
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(document_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_document ON knowledge_chunks(document_id,position);
                CREATE TABLE IF NOT EXISTS knowledge_memory_links(
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    memory_id TEXT NOT NULL,
                    relationship TEXT NOT NULL,
                    rationale TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(document_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE
                );
                '''
            )

    @staticmethod
    def _safe_filename(filename: str) -> str:
        clean = Path(str(filename or '')).name.strip()
        clean = re.sub(r'[^A-Za-z0-9._ -]+', '_', clean)[:180]
        if not clean or clean in {'.', '..'}:
            raise KnowledgeError('A safe filename is required')
        return clean

    @classmethod
    def _extract_text(cls, filename: str, data: bytes) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix not in cls.ALLOWED_EXTENSIONS:
            raise KnowledgeError(f'Unsupported file type: {suffix or "unknown"}')
        try:
            if suffix == '.pdf':
                from pypdf import PdfReader

                return '\n'.join(page.extract_text() or '' for page in PdfReader(io.BytesIO(data)))
            if suffix == '.docx':
                from docx import Document

                return '\n'.join(paragraph.text for paragraph in Document(io.BytesIO(data)).paragraphs)
            if suffix == '.xlsx':
                from openpyxl import load_workbook

                workbook = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
                rows = []
                for sheet in workbook.worksheets:
                    rows.append(f'# {sheet.title}')
                    rows.extend('\t'.join('' if cell is None else str(cell) for cell in row) for row in sheet.iter_rows(values_only=True))
                return '\n'.join(rows)
            text = data.decode('utf-8-sig')
            if suffix == '.json':
                return json.dumps(json.loads(text), ensure_ascii=False, indent=2)
            return text
        except KnowledgeError:
            raise
        except Exception as exc:
            raise KnowledgeError('The uploaded file could not be read safely') from exc

    @staticmethod
    def _chunks(text: str, size: int = 1400, overlap: int = 180):
        clean = re.sub(r'\r\n?', '\n', text).strip()
        if not clean:
            return []
        chunks = []
        start = 0
        while start < len(clean):
            end = min(len(clean), start + size)
            if end < len(clean):
                boundary = max(clean.rfind('\n', start, end), clean.rfind('. ', start, end))
                if boundary > start + size // 2:
                    end = boundary + 1
            chunks.append(clean[start:end].strip())
            if end >= len(clean):
                break
            start = max(start + 1, end - overlap)
        return [chunk for chunk in chunks if chunk]

    def ingest(self, *, filename: str, data: bytes, title: str | None = None, media_type: str = 'application/octet-stream', source: str = 'owner-upload', access_class: str = 'owner', metadata: dict | None = None):
        filename = self._safe_filename(filename)
        if not data:
            raise KnowledgeError('The uploaded file is empty')
        if len(data) > self.MAX_FILE_BYTES:
            raise KnowledgeError('The uploaded file exceeds the 10 MB limit')
        if access_class not in {'owner', 'trusted-devices', 'private'}:
            raise KnowledgeError('Invalid knowledge access class')
        text = self._extract_text(filename, data)
        chunks = self._chunks(text)
        if not chunks:
            raise KnowledgeError('No readable text was found in the uploaded file')
        checksum = hashlib.sha256(data).hexdigest()
        with self.lock, self._con() as con:
            existing = con.execute('SELECT id FROM knowledge_documents WHERE checksum=?', (checksum,)).fetchone()
            if existing:
                return self.detail(existing['id'])
            document_id = str(uuid.uuid4())
            stamp = now()
            object_name = f'{document_id}{Path(filename).suffix.lower()}'
            object_path = self.object_dir / object_name
            object_path.write_bytes(data)
            try:
                con.execute(
                    '''INSERT INTO knowledge_documents(
                        id,title,filename,media_type,source,checksum,size_bytes,access_class,
                        metadata_json,object_name,created_at,updated_at)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (
                        document_id,
                        str(title or Path(filename).stem).strip()[:240],
                        filename,
                        str(media_type or 'application/octet-stream')[:160],
                        str(source or 'owner-upload')[:500],
                        checksum,
                        len(data),
                        access_class,
                        json.dumps(metadata or {}, default=str),
                        object_name,
                        stamp,
                        stamp,
                    ),
                )
                con.executemany(
                    'INSERT INTO knowledge_chunks VALUES(?,?,?,?,?)',
                    [(str(uuid.uuid4()), document_id, index, chunk, stamp) for index, chunk in enumerate(chunks)],
                )
            except Exception:
                object_path.unlink(missing_ok=True)
                raise
        return self.detail(document_id)

    @staticmethod
    def _document(row) -> dict:
        item = dict(row)
        item['metadata'] = json.loads(item.pop('metadata_json') or '{}')
        item.pop('object_name', None)
        return item

    def list(self, query: str = '', limit: int = 100, *, access_classes: set[str] | None = None):
        term = f'%{query.strip()}%'
        with self._con() as con:
            if query.strip():
                rows = con.execute(
                    '''SELECT DISTINCT d.* FROM knowledge_documents d
                       LEFT JOIN knowledge_chunks c ON c.document_id=d.id
                       WHERE d.title LIKE ? OR d.filename LIKE ? OR d.source LIKE ? OR c.content LIKE ?
                       ORDER BY d.updated_at DESC LIMIT ?''',
                    (term, term, term, term, max(1, min(int(limit), 500))),
                ).fetchall()
            else:
                rows = con.execute(
                    'SELECT * FROM knowledge_documents ORDER BY updated_at DESC LIMIT ?',
                    (max(1, min(int(limit), 500)),),
                ).fetchall()
        documents = [self._document(row) for row in rows]
        if access_classes is not None:
            documents = [item for item in documents if item['access_class'] in access_classes]
        return documents

    def detail(self, document_id: str):
        with self._con() as con:
            row = con.execute('SELECT * FROM knowledge_documents WHERE id=?', (document_id,)).fetchone()
            if not row:
                return None
            chunks = con.execute(
                'SELECT id,position,content,created_at FROM knowledge_chunks WHERE document_id=? ORDER BY position',
                (document_id,),
            ).fetchall()
            links = con.execute(
                'SELECT id,memory_id,relationship,rationale,created_at FROM knowledge_memory_links WHERE document_id=? ORDER BY created_at',
                (document_id,),
            ).fetchall()
        return {**self._document(row), 'chunks': [dict(item) for item in chunks], 'memory_links': [dict(item) for item in links]}

    def search(self, query: str, limit: int = 12, *, access_classes: set[str] | None = None):
        query = str(query or '').strip()
        if not query:
            return []
        tokens = [token.lower() for token in re.findall(r'[\w-]{2,}', query)[:12]]
        with self._con() as con:
            rows = con.execute(
                '''SELECT c.id AS chunk_id,c.position,c.content,d.id AS document_id,d.title,d.filename,
                          d.source,d.checksum,d.access_class,d.updated_at
                   FROM knowledge_chunks c JOIN knowledge_documents d ON d.id=c.document_id
                   WHERE c.content LIKE ? OR d.title LIKE ? ORDER BY d.updated_at DESC LIMIT 300''',
                (f'%{query}%', f'%{query}%'),
            ).fetchall()
            if not rows and tokens:
                clauses = ' OR '.join('lower(c.content) LIKE ?' for _ in tokens)
                rows = con.execute(
                    f'''SELECT c.id AS chunk_id,c.position,c.content,d.id AS document_id,d.title,d.filename,
                               d.source,d.checksum,d.access_class,d.updated_at
                        FROM knowledge_chunks c JOIN knowledge_documents d ON d.id=c.document_id
                        WHERE {clauses} ORDER BY d.updated_at DESC LIMIT 300''',
                    [f'%{token}%' for token in tokens],
                ).fetchall()
        ranked = []
        for row in rows:
            item = dict(row)
            if access_classes is not None and item['access_class'] not in access_classes:
                continue
            haystack = item['content'].lower()
            score = sum(haystack.count(token) for token in tokens) + (3 if query.lower() in haystack else 0)
            item['score'] = score
            item['excerpt'] = item.pop('content')[:600]
            item['citation'] = {
                'document_id': item['document_id'],
                'title': item['title'],
                'source': item['source'],
                'chunk': item['position'],
                'checksum': item['checksum'],
            }
            ranked.append(item)
        ranked.sort(key=lambda item: (item['score'], item['updated_at']), reverse=True)
        return ranked[: max(1, min(int(limit), 50))]

    def update(self, document_id: str, *, title: str | None = None, source: str | None = None, access_class: str | None = None, metadata: dict | None = None):
        changes = {}
        if title is not None:
            clean = str(title).strip()[:240]
            if not clean:
                raise KnowledgeError('Knowledge title is required')
            changes['title'] = clean
        if source is not None:
            changes['source'] = str(source).strip()[:500]
        if access_class is not None:
            if access_class not in {'owner', 'trusted-devices', 'private'}:
                raise KnowledgeError('Invalid knowledge access class')
            changes['access_class'] = access_class
        if metadata is not None:
            changes['metadata_json'] = json.dumps(metadata, default=str)
        if not changes:
            return self.detail(document_id)
        changes['updated_at'] = now()
        with self.lock, self._con() as con:
            cur = con.execute(
                f"UPDATE knowledge_documents SET {','.join(f'{key}=?' for key in changes)} WHERE id=?",
                [*changes.values(), document_id],
            )
        if cur.rowcount != 1:
            raise KeyError('Knowledge document not found')
        return self.detail(document_id)

    def link_memory(self, document_id: str, memory_id: str, *, relationship: str = 'supports', rationale: str = ''):
        if not self.detail(document_id):
            raise KeyError('Knowledge document not found')
        link_id = str(uuid.uuid4())
        with self.lock, self._con() as con:
            con.execute(
                'INSERT INTO knowledge_memory_links VALUES(?,?,?,?,?,?)',
                (link_id, document_id, str(memory_id), str(relationship)[:80], str(rationale)[:500], now()),
            )
        return link_id

    def delete(self, document_id: str):
        with self.lock, self._con() as con:
            row = con.execute('SELECT object_name FROM knowledge_documents WHERE id=?', (document_id,)).fetchone()
            if not row:
                return False
            con.execute('DELETE FROM knowledge_documents WHERE id=?', (document_id,))
        (self.object_dir / row['object_name']).unlink(missing_ok=True)
        return True

    def export(self, *, access_classes: set[str] | None = None):
        return {
            'version': 1,
            'exported_at': now(),
            'documents': [
                self.detail(item['id'])
                for item in self.list(limit=500, access_classes=access_classes)
            ],
        }
