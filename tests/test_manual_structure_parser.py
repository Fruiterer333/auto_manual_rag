from app.data.parsers.manual_structure_parser import (
    ManualStructureParser,
    detect_content_type,
    detect_risk_level,
    is_procedure_text,
)
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


def test_exact_section_title_is_primary_heading_signal() -> None:
    parser = ManualStructureParser(skip_toc_pages_enabled=False)
    blocks = parser.parse(
        [
            _document(
                "\n".join(
                    [
                        "充电安全警告",
                        "警告！",
                        "■充电前请检查充电电缆。",
                    ]
                )
            )
        ]
    )

    assert len(blocks) == 1
    assert blocks[0].section == "充电安全警告"
    assert blocks[0].subsection is None
    assert blocks[0].content_type == "warning"


def test_non_whitelist_heading_becomes_subsection_not_section() -> None:
    parser = ManualStructureParser(skip_toc_pages_enabled=False)
    blocks = parser.parse(
        [
            _document(
                "\n".join(
                    [
                        "安全系统",
                        "系紧安全带",
                        "缓慢拉出安全带，将锁舌插入锁扣中。",
                    ]
                )
            )
        ]
    )

    assert len(blocks) == 1
    assert blocks[0].section == "安全系统"
    assert blocks[0].subsection == "系紧安全带"
    assert blocks[0].heading_path == ["安全系统", "系紧安全带"]
    assert blocks[0].text.startswith("系紧安全带\n")
    assert not blocks[0].text.startswith("安全系统\n")


def test_flush_buffer_does_not_duplicate_existing_subsection_prefix() -> None:
    parser = ManualStructureParser(skip_toc_pages_enabled=False)
    blocks: list[ManualBlock] = []

    parser._flush_buffer(
        blocks,
        ["系紧安全带", "缓慢拉出安全带，将锁舌插入锁扣中。"],
        _document("系紧安全带\n缓慢拉出安全带，将锁舌插入锁扣中。"),
        None,
        "使用安全带",
        "系紧安全带",
    )

    assert len(blocks) == 1
    assert blocks[0].text.startswith("系紧安全带\n")
    assert blocks[0].text.count("系紧安全带") == 1


def test_subsection_note_block_keeps_note_classification_from_raw_text() -> None:
    parser = ManualStructureParser(skip_toc_pages_enabled=False)
    blocks = parser.parse(
        [
            _document(
                "\n".join(
                    [
                        "电子驻车制动（EPB）",
                        "释放电子驻车制动（EPB）",
                        "说明！",
                        "车辆启动后，踩下制动踏板可释放EPB。",
                    ]
                )
            )
        ]
    )

    assert len(blocks) == 1
    assert blocks[0].subsection == "释放电子驻车制动（EPB）"
    assert blocks[0].text.startswith("释放电子驻车制动（EPB）\n说明！")
    assert blocks[0].content_type == "note"
    assert blocks[0].metadata["has_note"] is True


def test_subsection_warning_block_keeps_warning_classification_from_raw_text() -> None:
    parser = ManualStructureParser(skip_toc_pages_enabled=False)
    blocks = parser.parse(
        [
            _document(
                "\n".join(
                    [
                        "清洁车辆",
                        "高压冲洗",
                        "警告！",
                        "■在清洗车辆时，禁止将水枪对准车辆底部接插件进行冲洗。",
                    ]
                )
            )
        ]
    )

    assert len(blocks) == 1
    assert blocks[0].subsection == "高压冲洗"
    assert blocks[0].text.startswith("高压冲洗\n警告！")
    assert blocks[0].content_type == "warning"
    assert blocks[0].risk_level == "high"
    assert blocks[0].metadata["has_warning"] is True


def test_section_hint_in_body_sentence_is_not_heading() -> None:
    parser = ManualStructureParser(skip_toc_pages_enabled=False)
    blocks = parser.parse(
        [
            _document(
                "\n".join(
                    [
                        "安全带",
                        "如果安全带无法正常使用，请联系Lynk & Co领克中心。",
                        "安全带未系警告灯图标会在组合仪表上显示。",
                    ]
                )
            )
        ]
    )

    assert len(blocks) == 1
    assert blocks[0].section == "安全带"
    assert blocks[0].subsection is None
    assert "如果安全带无法正常使用" in blocks[0].text
    assert "警告灯图标" in blocks[0].text


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
    assert blocks[0].section is None
    assert blocks[0].subsection == "高压冲洗"
    assert blocks[0].content_type == "warning"
    assert "雨刮片" not in blocks[0].text
    assert "外部开闭件" in blocks[0].text
    assert "底部接插件" in blocks[0].text
    assert blocks[1].subsection == "雨刮片"
    assert blocks[1].text == "雨刮片\n首先将雨刮片置于维修位置，然后清洁雨刮片。"
    assert blocks[2].subsection == "轮辋"
    assert blocks[2].text == "轮辋\n请使用软刷清洁轮辋并用水枪冲洗。"


def test_adjacent_epb_and_autohold_sections_do_not_share_section() -> None:
    parser = ManualStructureParser(skip_toc_pages_enabled=False)
    blocks = parser.parse(
        [
            _document(
                "\n".join(
                    [
                        "手动紧急制动",
                        "车辆行驶过程中如出现紧急情况，您可以拉住电子驻车制动器开关。",
                        "自动驻车系统",
                        "自动驻车（Auto Hold）可以在正常驾驶过程中的短暂停车时提供制动。",
                    ]
                )
            )
        ]
    )

    assert [(block.section, block.subsection, block.text) for block in blocks] == [
        (None, "手动紧急制动", "手动紧急制动\n车辆行驶过程中如出现紧急情况，您可以拉住电子驻车制动器开关。"),
        ("自动驻车系统", None, "自动驻车（Auto Hold）可以在正常驾驶过程中的短暂停车时提供制动。"),
    ]


def test_front_hood_open_and_close_sections_do_not_inherit_wrong_section() -> None:
    parser = ManualStructureParser(skip_toc_pages_enabled=False)
    blocks = parser.parse(
        [
            _document(
                "\n".join(
                    [
                        "打开前机舱盖",
                        "打开前机舱盖前，确保前机舱盖打开区域无障碍物。",
                        "关闭前机舱盖",
                        "1 缓慢降低前机舱盖，直至前机舱盖接触到闩锁。",
                    ]
                )
            )
        ]
    )

    assert [(block.section, block.subsection, block.text) for block in blocks] == [
        ("打开前机舱盖", None, "打开前机舱盖前，确保前机舱盖打开区域无障碍物。"),
        ("关闭前机舱盖", None, "1 缓慢降低前机舱盖，直至前机舱盖接触到闩锁。"),
    ]


def test_new_section_resets_previous_subsection() -> None:
    parser = ManualStructureParser(skip_toc_pages_enabled=False)
    blocks = parser.parse(
        [
            _document(
                "\n".join(
                    [
                        "清洁车辆",
                        "高压冲洗",
                        "使用高压水枪清洗车辆时，请遵照设备操作说明。",
                        "更换雨刮片",
                        "首先将雨刮片置于维修位置。",
                    ]
                )
            )
        ]
    )

    assert [(block.section, block.subsection) for block in blocks] == [
        ("清洁车辆", "高压冲洗"),
        ("更换雨刮片", None),
    ]


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
    assert blocks[0].section is None
    assert blocks[0].subsection == "释放电子驻车制动（EPB）"
    assert blocks[0].text.startswith("释放电子驻车制动（EPB）\n")
    assert "红色EPB\n指示灯自动熄灭。" in blocks[0].text


def test_section_heading_at_page_end_applies_to_next_page_body() -> None:
    parser = ManualStructureParser(skip_toc_pages_enabled=False)
    blocks = parser.parse(
        [
            _document("打开前机舱盖", page=10),
            _document("11\n打开前机舱盖前，请确保前机舱盖打开区域无障碍物。", page=11),
        ]
    )

    assert len(blocks) == 1
    assert blocks[0].start_page == 11
    assert blocks[0].section == "打开前机舱盖"
    assert blocks[0].subsection is None
    assert blocks[0].text == "打开前机舱盖前，请确保前机舱盖打开区域无障碍物。"


def test_section_metadata_can_continue_across_page_in_same_block() -> None:
    parser = ManualStructureParser(skip_toc_pages_enabled=False)
    blocks = parser.parse(
        [
            _document("清洁车辆\n高压冲洗\n使用高压水枪清洗车辆时，请遵照设备操作说明。", page=20),
            _document("21\n请勿使喷头过于靠近软材料。", page=21),
        ]
    )

    assert len(blocks) == 1
    assert blocks[0].section == "清洁车辆"
    assert blocks[0].subsection == "高压冲洗"
    assert blocks[0].start_page == 20
    assert blocks[0].end_page == 21
    assert "21" not in blocks[0].text


def test_warning_marker_at_page_end_merges_with_next_page_body() -> None:
    parser = ManualStructureParser(skip_toc_pages_enabled=False)
    blocks = parser.parse(
        [
            _document("充电安全警告\n警告！", page=30),
            _document("31\n请勿让儿童进行充电作业。\n■充电前请检查充电电缆。", page=31),
        ]
    )

    assert len(blocks) == 1
    assert blocks[0].start_page == 30
    assert blocks[0].end_page == 31
    assert blocks[0].section == "充电安全警告"
    assert blocks[0].content_type == "warning"
    assert blocks[0].text.startswith("警告！\n请勿让儿童")
    assert "31" not in blocks[0].text


def test_caution_marker_at_page_end_merges_with_next_page_bullets() -> None:
    parser = ManualStructureParser(skip_toc_pages_enabled=False)
    blocks = parser.parse(
        [
            _document("高压冲洗\n注意！", page=40),
            _document("41\n■请勿单手关闭前机舱盖。\n■请勿让前机舱盖自由落下。", page=41),
        ]
    )

    assert len(blocks) == 1
    assert blocks[0].content_type == "caution"
    assert blocks[0].section is None
    assert blocks[0].subsection == "高压冲洗"
    assert blocks[0].text.startswith("高压冲洗\n注意！")
    assert "■请勿单手" in blocks[0].text


def test_warning_marker_does_not_swallow_next_page_section_heading() -> None:
    parser = ManualStructureParser(skip_toc_pages_enabled=False)
    blocks = parser.parse(
        [
            _document("高压冲洗\n警告！", page=50),
            _document("雨刮片\n首先将雨刮片置于维修位置。", page=51),
        ]
    )

    assert len(blocks) == 1
    assert blocks[0].section is None
    assert blocks[0].subsection == "雨刮片"
    assert blocks[0].text == "雨刮片\n首先将雨刮片置于维修位置。"


def test_parser_skips_page_numbers_and_toc_noise_lines() -> None:
    parser = ManualStructureParser(skip_toc_pages_enabled=False)
    blocks = parser.parse(
        [
            _document(
                "\n".join(
                    [
                        "88",
                        "使用危险警告灯............................89",
                        "使用危险警告灯",
                        "车辆遇到交通事故或其他紧急情况时，按下危险警告灯按键。",
                    ]
                )
            )
        ]
    )

    assert len(blocks) == 1
    assert blocks[0].section == "使用危险警告灯"
    assert "88" not in blocks[0].text
    assert "............................89" not in blocks[0].text


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
        subsection="手动启用",
        heading_path=["启动和驾驶", "启用电子驻车制动（EPB）", "手动启用"],
        content_type="procedure",
        risk_level="low",
        metadata={"source_pages": [10], "subsection": "手动启用"},
    )

    chunks = ManualStructureSplitter(chunk_size=120, chunk_overlap=20).split_blocks([block])

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.chapter == "启动和驾驶"
    assert chunk.section == "启用电子驻车制动（EPB）"
    assert chunk.subsection == "手动启用"
    assert chunk.content_type == "procedure"
    assert chunk.risk_level == "low"
    assert chunk.metadata["start_page"] == 10
    assert chunk.metadata["end_page"] == 10
    assert chunk.metadata["heading_path"] == ["启动和驾驶", "启用电子驻车制动（EPB）", "手动启用"]
    assert chunk.metadata["subsection"] == "手动启用"
    assert chunk.metadata["split_strategy"] == "manual_structure"


def test_content_type_avoids_warning_light_false_positive() -> None:
    text = "制动系统故障警告灯：制动系统故障时，黄色警告灯点亮。"

    assert detect_content_type(text) == "normal"
    assert detect_risk_level(text, detect_content_type(text)) == "medium"


def test_content_type_detects_alert_blocks_and_procedure_rules() -> None:
    assert detect_content_type("警告！\n■请勿让儿童进行充电作业。") == "warning"
    assert detect_risk_level("警告！\n■请勿让儿童进行充电作业。", "warning") == "high"
    assert detect_content_type("注意！\n■请勿单手关闭前机舱盖。") == "caution"
    assert detect_risk_level("注意！\n■请勿单手关闭前机舱盖。", "caution") == "medium"
    assert detect_content_type("1 打开车门。\n2 关闭车门。") == "procedure"


def test_single_operation_verb_plain_text_is_not_procedure() -> None:
    text = "车辆配备电动助力转向系统，可以在驾驶员转动方向盘时提供助力。"

    assert is_procedure_text(text) is False
    assert detect_content_type(text) == "normal"
    assert detect_risk_level(text, "normal") == "low"
