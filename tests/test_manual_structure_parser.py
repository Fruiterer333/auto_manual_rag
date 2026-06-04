from app.data.parsers.manual_structure_parser import ManualStructureParser
from app.data.schemas.models import Document, ManualBlock
from app.data.splitters.manual_structure_splitter import ManualStructureSplitter


def _document(text: str, page: int = 1) -> Document:
    return Document(
        doc_id=f"doc-{page}",
        source_file="manual.pdf",
        page=page,
        text=text,
    )


def test_heading_transition_updates_section_and_flushes_previous_block() -> None:
    parser = ManualStructureParser(skip_toc_pages_enabled=False)
    blocks = parser.parse(
        [
            _document(
                "\n".join(
                    [
                        "使用超车灯",
                        "超车时，您可将拨杆朝向自身方向拉动然后松开。",
                        "使用危险警告灯",
                        "危险警告灯按键",
                        "车辆遇到交通事故或其他紧急情况时，按下危险警告灯按键，启用危险警告灯。",
                    ]
                )
            )
        ]
    )

    assert [(block.section, block.text) for block in blocks] == [
        ("使用超车灯", "超车时，您可将拨杆朝向自身方向拉动然后松开。"),
        (
            "使用危险警告灯",
            "危险警告灯按键\n车辆遇到交通事故或其他紧急情况时，按下危险警告灯按键，启用危险警告灯。",
        ),
    ]


def test_warning_block_stops_at_new_heading_and_preserves_bullets() -> None:
    parser = ManualStructureParser(skip_toc_pages_enabled=False)
    blocks = parser.parse(
        [
            _document(
                "\n".join(
                    [
                        "高压冲洗",
                        "警告！",
                        "■洗车前，检查并确认车辆的外部开闭件已正确关闭。",
                        "■在清洗车辆时，禁止将水枪对准车辆底部接插件进行冲洗。",
                        "雨刮片",
                        "首先将雨刮片置于维修位置，然后清洁雨刮片。",
                        "轮辋",
                        "请使用软刷清洁轮辋并用水枪冲洗。",
                    ]
                )
            )
        ]
    )

    assert len(blocks) == 3
    assert blocks[0].section == "高压冲洗"
    assert blocks[0].content_type == "warning"
    assert "雨刮片" not in blocks[0].text
    assert "外部开闭件" in blocks[0].text
    assert "底部接插件" in blocks[0].text
    assert blocks[1].section == "雨刮片"
    assert blocks[1].text == "首先将雨刮片置于维修位置，然后清洁雨刮片。"
    assert blocks[2].section == "轮辋"
    assert blocks[2].text == "请使用软刷清洁轮辋并用水枪冲洗。"


def test_body_sentence_and_explanatory_label_are_not_sections() -> None:
    parser = ManualStructureParser(skip_toc_pages_enabled=False)
    blocks = parser.parse(
        [
            _document(
                "\n".join(
                    [
                        "使用安全带",
                        "松开已系上的安全带，安全带未系警告灯图标",
                        "如果安全带无法正常使用，请联系Lynk & Co领克中心。",
                    ]
                )
            )
        ]
    )

    assert len(blocks) == 1
    assert blocks[0].section == "使用安全带"
    assert "警告灯图标" in blocks[0].text


def test_mixed_alphanumeric_line_fragment_is_not_section() -> None:
    parser = ManualStructureParser(skip_toc_pages_enabled=False)
    blocks = parser.parse(
        [
            _document(
                "\n".join(
                    [
                        "释放电子驻车制动（EPB）",
                        "踩下制动踏板并启动车辆，沿箭头方向按下EPB开关，释放EPB功能，",
                        "红色EPB",
                        "指示灯自动熄灭。",
                    ]
                )
            )
        ]
    )

    assert len(blocks) == 1
    assert blocks[0].section == "释放电子驻车制动（EPB）"
    assert "红色EPB\n指示灯自动熄灭。" in blocks[0].text


def test_parser_handles_missing_section_without_crashing() -> None:
    parser = ManualStructureParser(skip_toc_pages_enabled=False)
    blocks = parser.parse([_document("普通说明文本。\n请按照手册要求操作。")])

    assert len(blocks) == 1
    assert blocks[0].section is None
    assert blocks[0].text == "普通说明文本。\n请按照手册要求操作。"


def test_splitter_preserves_required_chunk_metadata_fields() -> None:
    block = ManualBlock(
        block_id="block-1",
        source_file="manual.pdf",
        start_page=10,
        end_page=10,
        text="当车辆处于静止状态时，沿箭头方向拉起EPB开关，启用EPB功能。",
        chapter="启动和驾驶",
        section="启用电子驻车制动（EPB）",
        heading_path=["启动和驾驶", "启用电子驻车制动（EPB）"],
        content_type="procedure",
        risk_level="low",
        metadata={"source_pages": [10]},
    )

    chunks = ManualStructureSplitter(chunk_size=120, chunk_overlap=20).split_blocks([block])

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.chapter == "启动和驾驶"
    assert chunk.section == "启用电子驻车制动（EPB）"
    assert chunk.content_type == "procedure"
    assert chunk.risk_level == "low"
    assert chunk.metadata["start_page"] == 10
    assert chunk.metadata["end_page"] == 10
    assert chunk.metadata["heading_path"] == ["启动和驾驶", "启用电子驻车制动（EPB）"]
    assert chunk.metadata["split_strategy"] == "manual_structure"
