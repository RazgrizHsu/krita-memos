import json
from datetime import datetime
from typing import List, Dict, Optional
from krita import Krita


class Memo:
    def __init__(self, content: str, hashtags: List[str] = None,
                 uid: str = None, created: str = None):
        self.uid = uid or self._gen_uid()
        self.content = content
        self.hashtags = hashtags or []
        self.created = created or datetime.now().isoformat()
        self.modified = datetime.now().isoformat()

    @staticmethod
    def _gen_uid():
        from uuid import uuid4
        return str(uuid4())

    def to_dict(self) -> Dict:
        return {
            "uid": self.uid,
            "content": self.content,
            "hashtags": self.hashtags,
            "created": self.created,
            "modified": self.modified
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Memo':
        return cls(
            content=data["content"],
            hashtags=data.get("hashtags", []),
            uid=data.get("uid"),
            created=data.get("created")
        )

    def matches(self, query: str) -> bool:
        ql = query.lower()
        if ql in self.content.lower():
            return True
        for tag in self.hashtags:
            if ql in tag.lower():
                return True
        return False


class MemoStore:
    ANNOTATION_KEY = "krita_memos_data"

    def __init__(self):
        self.memos: List[Memo] = []
        self.doc = None

    def set_document(self, doc):
        self.doc = doc
        self.load()

    def load(self):
        if not self.doc:
            self.memos = []
            return

        try:
            data = self.doc.annotation(self.ANNOTATION_KEY)
            if not data:
                self.memos = []
                return

            dataStr = bytes(data).decode('utf-8')
            parsed = json.loads(dataStr)
            self.memos = [Memo.from_dict(m) for m in parsed.get("memos", [])]
        except Exception as e:
            print(f"[Memos] Load error: {e}")
            self.memos = []

    def save(self):
        if not self.doc:
            return

        try:
            data = {
                "version": 1,
                "memos": [m.to_dict() for m in self.memos]
            }
            jsonStr = json.dumps(data)
            jsonBytes = jsonStr.encode('utf-8')
            self.doc.setAnnotation(self.ANNOTATION_KEY, "memos_data", jsonBytes)
        except Exception as e:
            print(f"[Memos] Save error: {e}")
            import traceback
            traceback.print_exc()

    def add(self, memo: Memo):
        self.memos.append(memo)
        self.save()

    def update(self, uid: str, content: str, hashtags: List[str]):
        for m in self.memos:
            if m.uid == uid:
                m.content = content
                m.hashtags = hashtags
                m.modified = datetime.now().isoformat()
                self.save()
                return True
        return False

    def delete(self, uid: str):
        self.memos = [m for m in self.memos if m.uid != uid]
        self.save()

    def get(self, uid: str) -> Optional[Memo]:
        for m in self.memos:
            if m.uid == uid:
                return m
        return None

    def search(self, query: str) -> List[Memo]:
        if not query:
            return self.memos[:]
        return [m for m in self.memos if m.matches(query)]

    def filter_by_hashtag(self, hashtag: str) -> List[Memo]:
        if not hashtag:
            return self.memos[:]
        return [m for m in self.memos if hashtag in m.hashtags]

    def get_hashtags(self) -> List[str]:
        tags = set()
        for m in self.memos:
            tags.update(m.hashtags)
        return sorted(tags)
