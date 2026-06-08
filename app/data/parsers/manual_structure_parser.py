import re
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
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

EXACT_SECTION_TITLES = {
    "本手册相关的重要信息", "敬告用户", "联系Lynk&Co领克", "事件数据记录系统", "远程监控系统",
    "原厂精装附件、选装装备和改装", "无线电设备", "所有权变更", "动力电池回收", "车辆报废", "隐私告知",
    "远程查询车辆状况", "安全检查", "车辆装载", "前排储物空间", "第二排储物空间", "后备厢储物空间", "折叠后排座椅",
    "使用手套箱密码保护", "后备厢载物", "遮物帘", "车内打开/关闭尾门", "车外打开/关闭尾门", "设置尾门开启角度",
    "车辆锁止/解锁状态", "使用遥控钥匙解锁和闭锁", "使用Lynk&Co App解锁和闭锁", "无钥匙进入系统", "车内解锁和闭锁",
    "车内打开/关闭车门", "车外打开/关闭车门", "主驾座椅迎宾", "开门预警系统", "防盗系统", "开启/关闭防盗系统",
    "调节驾驶员座椅", "位置记忆功能", "方向盘介绍", "调整方向盘", "调节外后视镜", "调节内后视镜", "内后视镜自动防眩目",
    "胎压监测系统", "前雨刮和洗涤器", "后雨刮和洗涤器", "组合仪表", "指示灯和警告灯", "查看组合仪表信息",
    "打开/关闭远近光灯", "打开/关闭自动大灯", "智能远近光控制系统", "大灯随动转向功能", "打开/关闭后雾灯",
    "打开/关闭位置灯", "打开/关闭转向指示灯", "使用阅读灯", "使用超车灯", "使用危险警告灯", "调节背光亮度",
    "设置车内氛围灯", "使用接近照明灯", "使用伴我回家灯", "欢迎灯和欢送灯", "安全系统", "安全带", "使用安全带",
    "安全气囊", "颈椎撞击保护系统", "打开/关闭车窗", "打开/关闭全景天窗", "调节副驾驶座椅", "前排座椅加热",
    "前排座椅通风", "头枕", "方向盘加热", "儿童锁", "儿童座椅固定装置", "推荐的儿童安全座椅规格", "语音助手",
    "车载12V电源", "智能设备充电", "外接行车记录仪", "遮阳板", "驾驶须知", "点火模式", "通过手机APP启动车辆",
    "通过遥控钥匙启动车辆", "车辆熄火", "换挡", "驾驶模式", "方向盘助力与驾驶模式联动", "抬头显示", "能量回收系统",
    "低速行驶提示音", "转向助力系统", "制动系统", "车身稳定控制系统", "制动防抱死系统", "电子驻车制动（EPB）",
    "自动驻车系统", "坡道辅助系统", "陡坡缓降系统", "加油", "车辆排放", "涉水驾驶", "节能驾驶", "冬季驾驶", "斜坡驻车",
    "驾驶辅助系统", "驾驶辅助系统传感器", "超速报警", "最高限速辅助系统", "自适应巡航系统", "高级智能驾驶",
    "交通标志识别系统", "驾驶员状态监测系统", "前方交叉路口预警系统", "后方横向来车预警系统", "车道辅助系统",
    "变道辅助系统", "前向碰撞减缓系统", "后方碰撞预警系统", "紧急转向避让辅助系统", "生命体检测系统", "泊车辅助传感器",
    "泊车辅助系统", "360°全景影像", "泊车紧急制动", "全自动泊车", "遥控泊车", "外后视镜倒车自动调节",
    "折叠/展开外后视镜", "开启/关闭空调", "调节空调温度", "调节空调风量", "空调模式", "调节空调出风方向",
    "主动式座舱清洁系统", "香氛系统", "空气质量管理系统", "空调除霜/除雾", "中央显示屏", "设置中央显示屏显示状态",
    "应用程序", "多媒体", "车辆功能界面", "连接设置", "系统设置", "账户设置", "检查车辆网络连接状态", "操作行车记录仪",
    "查看行车记录仪视频", "行车记录仪内存卡", "相机", "Lynk&Co App", "创建和删除蓝牙钥匙", "高压警告标签",
    "混合动力电池", "充电安全警告", "车载充电设备充电", "随车设备快速充电", "预约充电", "车辆供电", "存放车辆",
    "更换遥控钥匙电池", "保养和维护动力电池", "保养和维护低压蓄电池", "新车磨合", "更换保险丝", "使用诊断工具读取VIN码",
    "打开前机舱盖", "检查发动机机油", "检查制动液", "检查冷却液", "添加洗涤液", "更换雨刮片", "胎压标签", "保养轮胎",
    "清洁车辆", "保养漆面", "车身防腐", "保养内饰", "保养项目", "车辆远程升级（OTA）", "车辆检测", "处理车辆故障",
    "紧急救援", "道路救援求助服务指导", "应急解锁和锁止车门", "应急打开尾门", "应急解锁充电枪", "牵引车辆",
    "安全背心和三角警示牌", "补胎套装", "电池电量较低", "车辆标识", "车辆参数", "缩略语和术语"
}

HIGH_RISK_KEYWORDS = {
    "警告！",
    "生命危险",
    "人身伤害",
    "高压触电",
    "触电",
    "高压线缆",
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


class LineKind(Enum):
    BLANK = "blank"
    NOISE = "noise"
    CHAPTER = "chapter"
    SECTION = "section"
    SUBSECTION = "subsection"
    WARNING_MARKER = "warning_marker"
    CAUTION_MARKER = "caution_marker"
    NOTE_MARKER = "note_marker"
    LIST_ITEM = "list_item"
    BODY = "body"


@dataclass
class ParserState:
    current_chapter: str | None = None
    current_section: str | None = None
    current_subsection: str | None = None
    buffer: list[str] = field(default_factory=list)
    buffer_document: Document | None = None
    buffer_end_page: int | None = None


class ManualStructureParser:
    """Rule-based parser for basic automotive manual structure."""

    def __init__(self, skip_toc_pages: int = 12, skip_toc_pages_enabled: bool = True) -> None:
        self.skip_toc_pages = skip_toc_pages
        self.skip_toc_pages_enabled = skip_toc_pages_enabled

    def parse(self, documents: list[Document]) -> list[ManualBlock]:
        start_time = perf_counter()
        logger.info("Manual parser started: documents=%s", len(documents))
        blocks: list[ManualBlock] = []
        state = ParserState()
        skipped_toc_pages = 0
        flushed_blocks_count = 0
        line_kind_counter: Counter[str] = Counter()

        for document in documents:
            lines = self._extract_lines(document.text)
            page_skips_heading = self._should_skip_heading_update(document)
            if page_skips_heading:
                skipped_toc_pages += 1

            for index, line in enumerate(lines):
                next_line = self._next_meaningful_line(lines, index)
                kind = self._classify_line(line, next_line, page_skips_heading=page_skips_heading)
                line_kind_counter[kind.value] += 1

                if kind == LineKind.NOISE:
                    continue

                if kind == LineKind.BLANK:
                    continue

                if kind == LineKind.CHAPTER:
                    self._flush_state(blocks, state, end_page=document.page)
                    flushed_blocks_count += 1
                    state.current_chapter = self._normalize_heading(line)
                    state.current_section = None
                    state.current_subsection = None
                    continue

                if kind == LineKind.SECTION:
                    self._flush_state(blocks, state, end_page=document.page)
                    flushed_blocks_count += 1
                    state.current_section = self._normalize_heading(line)
                    state.current_subsection = None
                    continue

                if kind == LineKind.SUBSECTION:
                    self._flush_state(blocks, state, end_page=document.page)
                    flushed_blocks_count += 1
                    state.current_subsection = self._normalize_heading(line)
                    continue

                if kind in {LineKind.WARNING_MARKER, LineKind.CAUTION_MARKER, LineKind.NOTE_MARKER}:
                    if state.buffer and not self._should_carry_buffer_across_page(state.buffer):
                        self._flush_state(blocks, state, end_page=document.page)
                        flushed_blocks_count += 1
                    self._append_to_state(state, document, self._normalize_heading(line))
                    continue

                self._append_to_state(state, document, line)

        if state.buffer and state.buffer_document is not None:
            self._flush_state(blocks, state, end_page=state.buffer_end_page)
            flushed_blocks_count += 1

        content_counter = Counter(block.content_type or "normal" for block in blocks)
        risk_counter = Counter(block.risk_level or "low" for block in blocks)
        logger.info(
            "Manual parser finished: blocks=%s skipped_toc_pages=%s flushed_blocks=%s line_kind=%s content_type=%s risk_level=%s elapsed=%.2fs",
            len(blocks),
            skipped_toc_pages,
            flushed_blocks_count,
            dict(line_kind_counter),
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
        return self._normalize_heading(line) in EXACT_SECTION_TITLES

    def _classify_line(
        self,
        line: str,
        next_line: str | None,
        *,
        page_skips_heading: bool,
    ) -> LineKind:
        normalized = self._normalize_heading(line)
        if not normalized:
            return LineKind.BLANK
        if self._is_noise_line(normalized, page_skips_heading=page_skips_heading):
            return LineKind.NOISE
        if not page_skips_heading and self._is_chapter_heading(normalized):
            return LineKind.CHAPTER
        if not page_skips_heading and self._is_section_heading(normalized):
            return LineKind.SECTION
        if self._is_warning_marker(normalized):
            return LineKind.WARNING_MARKER
        if self._is_caution_marker(normalized):
            return LineKind.CAUTION_MARKER
        if self._is_note_marker(normalized):
            return LineKind.NOTE_MARKER
        if self._is_list_line(normalized):
            return LineKind.LIST_ITEM
        if not page_skips_heading and self._is_subsection_heading(normalized, next_line):
            return LineKind.SUBSECTION
        return LineKind.BODY

    def _normalize_heading(self, line: str) -> str:
        return re.sub(r"\s+", " ", line).strip()

    def _looks_like_body_text(self, line: str) -> bool:
        if line.endswith(("。", "；", "，", "、", "！", "？", ".", ";", ",")):
            return True
        if line.endswith(("：", ":")) and self._is_list_intro(line):
            return True
        return False

    def _next_meaningful_line(self, lines: list[str], index: int) -> str | None:
        for candidate in lines[index + 1:]:
            candidate = candidate.strip()
            if candidate and not self._is_noise_line(candidate, page_skips_heading=False):
                return candidate
        return None

    def _is_noise_line(self, line: str, *, page_skips_heading: bool) -> bool:
        normalized = self._normalize_heading(line)
        if not normalized:
            return False
        if self._is_page_number_line(normalized):
            return True
        if self._is_toc_line(normalized):
            return True
        if page_skips_heading and normalized in CHAPTER_TITLES:
            return True
        if normalized.lower() in {"copyright", "all rights reserved"}:
            return True
        return False

    def _is_page_number_line(self, line: str) -> bool:
        return bool(re.fullmatch(r"\d{1,4}", line))

    def _is_toc_line(self, line: str) -> bool:
        dot_run = r"[\.·•…]{5,}"
        if re.search(dot_run, line) and re.search(r"\d{1,4}\s*$", line):
            return True
        if re.fullmatch(rf"{dot_run}\s*\d{{1,4}}", line):
            return True
        return False

    def _should_carry_buffer_across_page(self, buffer: list[str]) -> bool:
        text = "\n".join(line for line in buffer if line).strip()
        return text in {"警告！", "警告", "注意！", "注意", "说明！", "说明"}

    def _is_list_line(self, line: str) -> bool:
        return bool(PROCEDURE_PATTERN.search(line))

    def _is_list_intro(self, line: str) -> bool:
        return any(term in line for term in LIST_INTRO_TERMS)

    def _is_subsection_heading(self, line: str, next_line: str | None) -> bool:
        if line in GENERIC_SECTION_REJECT_TITLES:
            return False
        if line in CHAPTER_TITLES or line in EXACT_SECTION_TITLES:
            return False
        if self._is_warning_marker(line) or self._is_caution_marker(line) or self._is_note_marker(line):
            return False
        if self._is_list_line(line) or self._starts_with_step_like_number(line):
            return False
        if self._looks_like_explanatory_label(line):
            return False
        if self._looks_like_body_text(line):
            return False
        if self._looks_like_fragment(line):
            return False
        if self._has_body_section_reject_terms(line):
            return False
        if self._punctuation_count(line) > 0:
            return False
        chinese_count = self._chinese_char_count(line)
        if chinese_count < 2 or chinese_count > 14:
            return False
        if len(line) > 24:
            return False
        if not next_line:
            return self._looks_like_page_end_subsection(line)
        if not self._has_subsection_following_context(next_line):
            return False
        if line.startswith(ACTION_HEADING_PREFIXES):
            return True
        if line.endswith(TITLE_SUFFIXES):
            return True
        return self._looks_like_short_noun_heading(line)

    def _has_body_section_reject_terms(self, line: str) -> bool:
        if line.startswith(ACTION_HEADING_PREFIXES) and self._chinese_char_count(line) <= 14:
            return False
        return any(term in line for term in BODY_SECTION_REJECT_TERMS)

    def _looks_like_explanatory_label(self, line: str) -> bool:
        if any(term in line for term in EXPLANATORY_SECTION_REJECT_TERMS):
            return True
        if "警告灯" in line and not line.startswith(ACTION_HEADING_PREFIXES):
            return True
        if line in {"人身伤害", "车辆损坏风险", "显示文本"}:
            return True
        return False

    def _looks_like_fragment(self, line: str) -> bool:
        if re.search(r"[A-Za-z0-9]", line) and self._chinese_char_count(line) <= 3:
            return True
        if re.fullmatch(r"[\W_]+", line):
            return True
        return False

    def _looks_like_page_end_subsection(self, line: str) -> bool:
        if re.search(r"[A-Za-z0-9]", line):
            return False
        if self._looks_like_body_text(line):
            return False
        if line.startswith(ACTION_HEADING_PREFIXES):
            return True
        if line.endswith(TITLE_SUFFIXES):
            return True
        return False

    def _has_subsection_following_context(self, next_line: str) -> bool:
        normalized = self._normalize_heading(next_line)
        if not normalized:
            return False
        if self._is_warning_marker(normalized) or self._is_caution_marker(normalized) or self._is_note_marker(normalized):
            return True
        if self._is_list_line(normalized):
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

    def _is_warning_marker(self, line: str) -> bool:
        return line.startswith("警告！") or line == "警告" or line.startswith("警告 ")

    def _is_caution_marker(self, line: str) -> bool:
        return line.startswith("注意！") or line == "注意" or line.startswith("注意 ")

    def _is_note_marker(self, line: str) -> bool:
        return line.startswith("说明！") or line == "说明" or line.startswith("说明 ")

    def _append_to_state(self, state: ParserState, document: Document, line: str) -> None:
        if not state.buffer:
            state.buffer_document = document
        state.buffer_end_page = document.page
        state.buffer.append(line)

    def _flush_state(
        self,
        blocks: list[ManualBlock],
        state: ParserState,
        *,
        end_page: int | None,
    ) -> None:
        if state.buffer_document is not None:
            self._flush_buffer(
                blocks,
                state.buffer,
                state.buffer_document,
                state.current_chapter,
                state.current_section,
                state.current_subsection,
                end_page=state.buffer_end_page or end_page,
            )
        state.buffer = []
        state.buffer_document = None
        state.buffer_end_page = None

    def _flush_buffer(
        self,
        blocks: list[ManualBlock],
        buffer: list[str],
        document: Document,
        chapter: str | None,
        section: str | None,
        subsection: str | None,
        *,
        end_page: int | None = None,
    ) -> None:
        text = "\n".join(line for line in buffer if line).strip()
        if len(text) < 4:
            return

        content_type = detect_content_type(text)
        risk_level = detect_risk_level(text, content_type)
        heading_path = [heading for heading in (chapter, section, subsection) if heading]
        block_index = len(blocks)
        block_id = str(uuid5(NAMESPACE_URL, f"{document.doc_id}:{block_index}:{text[:40]}"))
        blocks.append(
            ManualBlock(
                block_id=block_id,
                source_file=document.source_file,
                start_page=document.page,
                end_page=end_page or document.page,
                text=text,
                chapter=chapter,
                section=section,
                subsection=subsection,
                heading_path=heading_path,
                content_type=content_type,
                risk_level=risk_level,
                metadata={
                    "source_pages": self._source_pages(document.page, end_page or document.page),
                    "subsection": subsection,
                    "has_warning": "警告" in text,
                    "has_caution": "注意" in text,
                    "has_note": "说明" in text,
                    "is_procedure": is_procedure_text(text),
                },
            )
        )

    def _source_pages(self, start_page: int, end_page: int) -> list[int]:
        if end_page < start_page:
            return [start_page]
        return list(range(start_page, end_page + 1))


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
    if content_type == "warning":
        return "high"
    if _looks_like_warning_light_explanation(text):
        return "medium" if any(keyword in text for keyword in MEDIUM_RISK_KEYWORDS) else "low"
    if any(keyword in text for keyword in HIGH_RISK_KEYWORDS):
        return "high"
    if content_type == "caution" or any(keyword in text for keyword in MEDIUM_RISK_KEYWORDS):
        return "medium"
    return "low"


def is_procedure_text(text: str) -> bool:
    if any(term in text for term in ("操作步骤", "执行下列", "请按以下", "按以下")):
        return True
    if _has_multiple_procedure_steps(text):
        return True
    if PROCEDURE_PATTERN.search(text) and _operation_verb_count(text) >= 1:
        return True
    return _operation_verb_count(text) >= 2


def _first_meaningful_line(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line
    return text.strip()


def _is_warning_block(text: str) -> bool:
    first_line = _first_meaningful_line(text)
    if _looks_like_warning_light_explanation(first_line):
        return False
    return _has_warning_marker(text)


def _is_caution_block(text: str) -> bool:
    return _has_caution_marker(text)


def _is_note_block(text: str) -> bool:
    return _has_note_marker(text)


def _has_warning_marker(text: str) -> bool:
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if _looks_like_warning_light_explanation(line):
            return False
        return line.startswith("警告！") or line == "警告" or line.startswith("警告 ")
    return False


def _has_caution_marker(text: str) -> bool:
    first_line = _first_meaningful_line(text)
    return first_line.startswith("注意！") or first_line == "注意" or first_line.startswith("注意 ")


def _has_note_marker(text: str) -> bool:
    first_line = _first_meaningful_line(text)
    return first_line.startswith("说明！") or first_line == "说明" or first_line.startswith("说明 ")


def _looks_like_warning_light_explanation(text: str) -> bool:
    return any(term in text for term in ("警告灯", "警告图标", "警告信息"))


def _has_multiple_procedure_steps(text: str) -> bool:
    return len(
        re.findall(r"(^|\n)\s*(?:\d+\.?|\d+\s|（\d+）|[①②③④⑤⑥⑦⑧⑨⑩])", text)
    ) >= 2


def _operation_verb_count(text: str) -> int:
    return sum(1 for keyword in OPERATION_VERBS if keyword in text)
