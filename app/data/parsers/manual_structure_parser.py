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
    "节能驾驶",
    "冬季驾驶",
    "斜坡驻车",
    "充电安全警告",
    "胎压低报警",
    "使用安全带",
    "系紧安全带",
    "安全带清洁",
    "快速充电",
    "车载充电设备",
    "松开安全带",
    "安全带检查",
    "安全带使用",
    "正确使用安全带",
    "自动驻车",
    "危险警告灯",
    "前机舱盖",
    "低压蓄电池",
    "雨刮",
    "轮辋",
    "加油",
    "外部塑料饰件",
    "转向助力",
}
EXACT_SECTION_TITLES = {
    "使用安全带",
    "系紧安全带",
    "松开安全带",
    "安全带清洁",
    "安全带检查",
    "安全带使用",
    "正确使用安全带",
    "胎压低报警",
    "胎压监测系统",
    "儿童锁",
    "涉水驾驶",
    "充电安全警告",
    "快速充电",
    "车载充电设备",
    "节能驾驶",
    "冬季驾驶",
    "斜坡驻车",
}

HIGH_RISK_KEYWORDS = {
    "警告！",
    "生命危险",
    "人身伤害",
    "高压",
    "安全气囊",
    "气囊",
    "制动失效",
    "充电安全",
    "禁止",
    "不得",
    "切勿",
    "儿童单独留在车内",
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
LIST_INTRO_TERMS = {
    "下列检查",
    "以下检查",
    "执行下列",
    "注意以下事项",
    "应注意以下事项",
    "包括以下",
    "如下",
}
BODY_SECTION_REJECT_TERMS = {
    "应",
    "请",
    "需要",
    "建议",
    "可以",
    "确保",
    "检查",
    "注意以下",
    "下列",
    "如下",
    "以下",
    "点击",
}
EXPLANATORY_SECTION_REJECT_TERMS = {
    "图标",
    "警告灯图标",
    "显示屏显示",
    "组合仪表",
    "指示灯",
}
BODY_TONE_TERMS = {
    "请",
    "应",
    "如果",
    "当",
    "为了",
    "确保",
    "建议",
    "可以",
    "需要",
    "位于",
}
OPERATION_VERBS = {
    "按下",
    "拉出",
    "插入",
    "转动",
    "检查",
    "启用",
    "关闭",
    "打开",
    "调节",
    "选择",
    "点击",
    "缓慢拉出",
    "锁舌",
    "锁扣",
    "腰部安全带",
    "肩部安全带",
    "插入锁扣",
    "拉紧",
}
ACTION_HEADING_PREFIXES = (
    "使用",
    "打开",
    "关闭",
    "开启",
    "启用",
    "释放",
    "检查",
    "保养",
    "维护",
    "更换",
    "调节",
    "连接",
    "断开",
    "清洁",
    "加油",
)
TITLE_SUFFIXES = (
    "系统",
    "功能",
    "设备",
    "装置",
    "工具",
    "警告",
    "安全警告",
    "冲洗",
    "清洗",
    "维护",
    "保养",
    "车灯",
    "雨刮片",
    "轮辋",
    "前机舱盖",
)
GENERIC_SECTION_REJECT_TITLES = {
    "功能状态说明",
    "操作步骤",
    "注意事项",
    "说明",
    "警告",
    "注意",
}


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
        section_rejected_count = 0
        flushed_blocks_count = 0

        for document in documents:
            lines = self._extract_lines(document.text)
            page_skips_heading = self._should_skip_heading_update(document)
            if page_skips_heading:
                skipped_toc_pages += 1

            buffer: list[str] = []
            for index, line in enumerate(lines):
                next_line = self._next_meaningful_line(lines, index)
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

                if not page_skips_heading:
                    is_section, rejected = self._classify_section_heading(line, next_line)
                    if rejected:
                        section_rejected_count += 1
                else:
                    is_section = False

                if is_section:
                    self._flush_buffer(
                        blocks,
                        buffer,
                        document,
                        current_chapter,
                        current_section,
                    )
                    flushed_blocks_count += 1
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
                    flushed_blocks_count += 1
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
            "Manual parser finished: blocks=%s skipped_toc_pages=%s section_rejected=%s flushed_blocks=%s content_type=%s risk_level=%s elapsed=%.2fs",
            len(blocks),
            skipped_toc_pages,
            section_rejected_count,
            flushed_blocks_count,
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
        is_section, _ = self._classify_section_heading(line)
        return is_section

    def _classify_section_heading(
        self,
        line: str,
        next_line: str | None = None,
    ) -> tuple[bool, bool]:
        normalized = self._normalize_heading(line)
        if len(normalized) < 2:
            return False, False
        if normalized in GENERIC_SECTION_REJECT_TITLES:
            return False, True
        if normalized in EXACT_SECTION_TITLES:
            return True, False
        if self._is_list_line(normalized):
            return False, True
        if self._looks_like_explanatory_label(normalized):
            return False, True
        if any(term in normalized for term in BODY_TONE_TERMS) and self._chinese_char_count(normalized) > 10:
            return False, True
        if self._looks_like_body_text(normalized):
            return False, True
        if self._has_body_section_reject_terms(normalized):
            return False, True
        if self._punctuation_count(normalized) >= 1:
            return False, True
        if self._starts_with_step_like_number(normalized):
            return False, True
        if self._chinese_char_count(normalized) > 18:
            return False, True
        if len(normalized) > 28:
            return False, True
        if self._looks_like_body_text(normalized) or self._is_list_line(normalized):
            return False, True
        if normalized in CHAPTER_TITLES:
            return False, False
        if any(hint in normalized for hint in SECTION_HINTS):
            return True, False
        return self._looks_like_contextual_section_heading(normalized, next_line), False

    def _normalize_heading(self, line: str) -> str:
        return re.sub(r"\s+", " ", line).strip()

    def _looks_like_body_text(self, line: str) -> bool:
        if line.endswith(("。", "；", "，", "、", "！", "？", ".", ";", ",")):
            return True
        if line.endswith(("：", ":")) and self._is_list_intro(line):
            return True
        return False

    def _starts_new_semantic_block(self, line: str) -> bool:
        return line.startswith(("警告", "警告！", "注意", "注意！", "说明", "说明！"))

    def _next_meaningful_line(self, lines: list[str], index: int) -> str | None:
        for candidate in lines[index + 1:]:
            candidate = candidate.strip()
            if candidate:
                return candidate
        return None

    def _is_list_line(self, line: str) -> bool:
        return bool(PROCEDURE_PATTERN.search(line))

    def _is_list_intro(self, line: str) -> bool:
        return any(term in line for term in LIST_INTRO_TERMS)

    def _has_body_section_reject_terms(self, line: str) -> bool:
        if (
            line.startswith(ACTION_HEADING_PREFIXES)
            and self._chinese_char_count(line) <= 14
            and not self._looks_like_body_text(line)
        ):
            return False
        return any(term in line for term in BODY_SECTION_REJECT_TERMS)

    def _looks_like_explanatory_label(self, line: str) -> bool:
        if any(term in line for term in EXPLANATORY_SECTION_REJECT_TERMS):
            return True
        if "警告灯" in line and not line.startswith(ACTION_HEADING_PREFIXES):
            return True
        return False

    def _looks_like_contextual_section_heading(
        self,
        line: str,
        next_line: str | None,
    ) -> bool:
        if not next_line:
            return False
        chinese_count = self._chinese_char_count(line)
        if chinese_count < 2 or chinese_count > 14:
            return False
        if not self._has_heading_following_context(next_line):
            return False
        if line.startswith(ACTION_HEADING_PREFIXES):
            return True
        if line.endswith(TITLE_SUFFIXES):
            return True
        return self._looks_like_short_noun_heading(line)

    def _has_heading_following_context(self, next_line: str) -> bool:
        normalized = self._normalize_heading(next_line)
        if not normalized:
            return False
        if self._starts_new_semantic_block(normalized) or self._is_list_line(normalized):
            return True
        if self._looks_like_body_text(normalized):
            return True
        if self._starts_with_step_like_number(normalized):
            return True
        if any(term in normalized for term in BODY_TONE_TERMS):
            return True
        if any(verb in normalized for verb in OPERATION_VERBS):
            return True
        return self._chinese_char_count(normalized) >= 8

    def _looks_like_short_noun_heading(self, line: str) -> bool:
        if re.search(r"[A-Za-z0-9]", line):
            return False
        if any(term in line for term in BODY_TONE_TERMS):
            return False
        if any(verb in line for verb in OPERATION_VERBS):
            return False
        if "，" in line or "。" in line or "；" in line or "：" in line:
            return False
        return 2 <= self._chinese_char_count(line) <= 8

    def _punctuation_count(self, line: str) -> int:
        return sum(line.count(mark) for mark in ("，", "、", "；", "。", "：", ":", ",", ";"))

    def _chinese_char_count(self, line: str) -> int:
        return len(re.findall(r"[\u4e00-\u9fff]", line))

    def _starts_with_step_like_number(self, line: str) -> bool:
        return bool(re.match(r"^\d{1,3}", line)) and any(
            verb in line for verb in OPERATION_VERBS
        )

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
    if _is_warning_block(text):
        return "warning"
    if _is_caution_block(text):
        return "caution"
    if _is_note_block(text):
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
    return (
        bool(PROCEDURE_PATTERN.search(text))
        or any(term in text for term in ("步骤", "执行下列", "请按以下", "按以下", "如何"))
        or sum(1 for keyword in OPERATION_VERBS if keyword in text) >= 1
    )


def _first_meaningful_line(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line
    return text.strip()


def _is_warning_block(text: str) -> bool:
    first_line = _first_meaningful_line(text)
    if "警告灯" in first_line or "警告图标" in first_line or "警告信息" in first_line:
        return False
    return first_line.startswith("警告！") or first_line == "警告" or first_line.startswith("警告 ")


def _is_caution_block(text: str) -> bool:
    first_line = _first_meaningful_line(text)
    return first_line.startswith("注意！") or first_line == "注意" or first_line.startswith("注意 ")


def _is_note_block(text: str) -> bool:
    first_line = _first_meaningful_line(text)
    return first_line.startswith("说明！") or first_line == "说明" or first_line.startswith("说明 ")
