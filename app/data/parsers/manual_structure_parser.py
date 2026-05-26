import re
from collections import Counter
from time import perf_counter
from uuid import NAMESPACE_URL, uuid5

from app.core.logger import get_logger
from app.data.schemas.models import Document, ManualBlock


logger = get_logger(__name__)


CHAPTER_TITLES = {
    "前言",
    "用车前准备",
    "装载货物",
    "上车和下车",
    "驾驶前的准备",
    "仪表和灯光",
    "安全出行",
    "启动和驾驶",
    "驾驶辅助",
    "泊车",
    "空调",
    "中央显示屏",
    "Lynk & Co App",
    "高压系统",
    "保养和维护",
    "OTA升级",
    "紧急情况下",
    "技术资料",
}

SECTION_HINTS = {
    "安全带",
    "胎压",
    "儿童锁",
    "涉水驾驶",
    "充电",
    "高压",
    "制动",
    "座椅",
    "车灯",
    "气囊",
    "驾驶员",
    "报警",
    "钥匙",
    "车门",
    "空调",
    "泊车",
}

HIGH_RISK_KEYWORDS = {
    "警告",
    "生命危险",
    "人身伤害",
    "高压",
    "安全气囊",
    "气囊",
    "制动",
    "儿童",
    "充电安全",
    "禁止",
    "不得",
}

MEDIUM_RISK_KEYWORDS = {
    "注意",
    "车辆损坏",
    "胎压",
    "涉水",
    "保养",
    "故障灯",
    "警告灯",
    "检查",
}

PROCEDURE_PATTERN = re.compile(r"(^|\n)\s*(?:■|-|•|\d+\.|（\d+）|[①②③④⑤⑥⑦⑧⑨⑩])")


class ManualStructureParser:
    """Rule-based parser for basic automotive manual structure."""

    def __init__(self, skip_toc_pages: int = 12, skip_toc_pages_enabled: bool = True) -> None:
        self.skip_toc_pages = skip_toc_pages
        self.skip_toc_pages_enabled = skip_toc_pages_enabled

    def parse(self, documents: list[Document]) -> list[ManualBlock]:
        start_time = perf_counter()
        logger.info("Manual parser started: documents=%s", len(documents))
        blocks: list[ManualBlock] = []
        current_chapter: str | None = None
        current_section: str | None = None
        skipped_toc_pages = 0

        for document in documents:
            lines = self._extract_lines(document.text)
            page_skips_heading = self._should_skip_heading_update(document)
            if page_skips_heading:
                skipped_toc_pages += 1

            buffer: list[str] = []
            for line in lines:
                if not line:
                    self._flush_buffer(
                        blocks,
                        buffer,
                        document,
                        current_chapter,
                        current_section,
                    )
                    buffer = []
                    continue

                if not page_skips_heading and self._is_chapter_heading(line):
                    self._flush_buffer(
                        blocks,
                        buffer,
                        document,
                        current_chapter,
                        current_section,
                    )
                    buffer = []
                    current_chapter = self._normalize_heading(line)
                    current_section = None
                    continue

                if not page_skips_heading and self._is_section_heading(line):
                    self._flush_buffer(
                        blocks,
                        buffer,
                        document,
                        current_chapter,
                        current_section,
                    )
                    buffer = []
                    current_section = self._normalize_heading(line)
                    continue

                if buffer and self._starts_new_semantic_block(line):
                    self._flush_buffer(
                        blocks,
                        buffer,
                        document,
                        current_chapter,
                        current_section,
                    )
                    buffer = []

                buffer.append(line)

            self._flush_buffer(
                blocks,
                buffer,
                document,
                current_chapter,
                current_section,
            )

        content_counter = Counter(block.content_type or "normal" for block in blocks)
        risk_counter = Counter(block.risk_level or "low" for block in blocks)
        logger.info(
            "Manual parser finished: blocks=%s skipped_toc_pages=%s content_type=%s risk_level=%s elapsed=%.2fs",
            len(blocks),
            skipped_toc_pages,
            dict(content_counter),
            dict(risk_counter),
            perf_counter() - start_time,
        )
        return blocks

    def _extract_lines(self, text: str) -> list[str]:
        return [line.strip() for line in text.splitlines()]

    def _should_skip_heading_update(self, document: Document) -> bool:
        if not self.skip_toc_pages_enabled or document.page > self.skip_toc_pages:
            return False
        text = document.text
        dot_line_count = sum(1 for line in text.splitlines() if "..." in line or "……" in line)
        chapter_hits = sum(1 for title in CHAPTER_TITLES if title in text)
        return dot_line_count >= 3 or chapter_hits >= 4 or "目录" in text

    def _is_chapter_heading(self, line: str) -> bool:
        normalized = self._normalize_heading(line)
        return normalized in CHAPTER_TITLES

    def _is_section_heading(self, line: str) -> bool:
        normalized = self._normalize_heading(line)
        if len(normalized) < 3 or len(normalized) > 24:
            return False
        if self._looks_like_body_text(normalized) or self._is_list_line(normalized):
            return False
        if normalized in CHAPTER_TITLES:
            return False
        return any(hint in normalized for hint in SECTION_HINTS)

    def _normalize_heading(self, line: str) -> str:
        return re.sub(r"\s+", " ", line).strip()

    def _looks_like_body_text(self, line: str) -> bool:
        return line.endswith(("。", "；", "，", "、", "！", "？", ".", ";", ","))

    def _starts_new_semantic_block(self, line: str) -> bool:
        return line.startswith(("警告", "警告！", "注意", "注意！", "说明", "说明！"))

    def _is_list_line(self, line: str) -> bool:
        return bool(PROCEDURE_PATTERN.search(line))

    def _flush_buffer(
        self,
        blocks: list[ManualBlock],
        buffer: list[str],
        document: Document,
        chapter: str | None,
        section: str | None,
    ) -> None:
        text = "\n".join(line for line in buffer if line).strip()
        if len(text) < 4:
            return

        content_type = detect_content_type(text)
        risk_level = detect_risk_level(text, content_type)
        heading_path = [heading for heading in (chapter, section) if heading]
        block_index = len(blocks)
        block_id = str(uuid5(NAMESPACE_URL, f"{document.doc_id}:{block_index}:{text[:40]}"))
        blocks.append(
            ManualBlock(
                block_id=block_id,
                source_file=document.source_file,
                start_page=document.page,
                end_page=document.page,
                text=text,
                chapter=chapter,
                section=section,
                heading_path=heading_path,
                content_type=content_type,
                risk_level=risk_level,
                metadata={
                    "source_pages": [document.page],
                    "has_warning": "警告" in text,
                    "has_caution": "注意" in text,
                    "has_note": "说明" in text,
                    "is_procedure": is_procedure_text(text),
                },
            )
        )


def detect_content_type(text: str) -> str:
    if "警告" in text:
        return "warning"
    if "注意" in text:
        return "caution"
    if "说明" in text:
        return "note"
    if is_procedure_text(text):
        return "procedure"
    return "normal"


def detect_risk_level(text: str, content_type: str | None = None) -> str:
    if content_type == "warning" or any(keyword in text for keyword in HIGH_RISK_KEYWORDS):
        return "high"
    if content_type == "caution" or any(keyword in text for keyword in MEDIUM_RISK_KEYWORDS):
        return "medium"
    return "low"


def is_procedure_text(text: str) -> bool:
    return bool(PROCEDURE_PATTERN.search(text)) or any(
        keyword in text
        for keyword in ("请", "应", "按下", "拉出", "插入", "检查")
    )
