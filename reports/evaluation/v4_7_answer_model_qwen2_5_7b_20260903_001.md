# Answer Generation Evaluation

## Run Configuration

- generated_at: 2026-09-03T14:56:36
- dataset: `data/eval/answer_eval_set.jsonl`
- case_count: 12
- semantics_version: v4.3
- retrieval_mode: hybrid
- rerank_enabled: False
- embedding_model: BAAI/bge-small-zh-v1.5
- rerank_model: N/A
- rerank_top_n: N/A
- rerank_output_top_k: N/A
- llm_model: qwen2.5:7b
- top_k: 5
- max_contexts: 5
- max_context_chars: 6000
- metadata_context_selection_enabled: True
- neighbor_expansion_enabled: False
- answer_eval_dataset_sha256: c3b06add0f3a906597a652997f824cd3c3cccc2e30eda684d6a98761ba493f8a
- answer_eval_semantics_version: v4.3
- experiment_id: v4.7-answer-model-selection
- experiment_phase: reference
- git_branch: exp/v4.7-answer-model-selection
- git_commit: 588ea481ddc35d68dc0341a61b02fa90dc06144b
- git_worktree_dirty: True
- answer_prompt_sha256: 1c2ebcf4ee6f67d84e71c6dc7f29a670d017fcbfb80528c2f105d36fe4d9cdc0
- generation_stream: False
- generation_stream_source: explicit
- generation_temperature: 0.0000
- generation_temperature_source: settings_explicit
- generation_seed: 42
- generation_seed_source: settings_explicit
- generation_think: N/A
- generation_think_source: unset
- generation_options: {'temperature': 0.0, 'seed': 42}
- generation_options_source: settings_explicit
- generation_inherited_options: ['top_k', 'top_p', 'min_p', 'repeat_penalty', 'num_predict', 'num_ctx']
- generation_inherited_options_source: ollama_model_or_service_defaults
- generation_timeout_seconds: 120
- generation_timeout_source: explicit
- ollama_base_url: http://127.0.0.1:11434
- ollama_version: 0.33.2
- ollama_version_source: api_version
- ollama_model_tag: qwen2.5:7b
- ollama_model_digest: 845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e
- ollama_model_digest_source: api_tags
- ollama_runtime_metadata_error: N/A

## Summary

| metric | value |
| --- | ---: |
| case_count | 12 |
| answer_non_empty_pass | 12 |
| internal_reference_leak_count | 0 |
| forbidden_term_failure_count | 0 |
| must_include_term_average_coverage | 0.8535 |
| expected_evidence_hit_rate | 0.3636 |
| insufficient_evidence_behavior_pass_rate | 1.0000 |
| average_elapsed_seconds | 9.0153 |

## Manual Review Status

Human semantic review has not been completed.

Deterministic checks do not establish semantic correctness, groundedness, or completeness.

## Case Details

### epb_enable_release_answer_001

**Question:** 电子驻车制动如何启用和释放？

**Answer type:** procedure

**Source case:** epb_enable_release_001

**Raw answer:**

电子驻车制动（EPB）的启用和释放方法如下：

1. **启用电子驻车制动**：
   - 您可以使用电子驻车制动器开关手动启用紧急制动功能。在车辆行驶过程中如出现紧急情况，可以拉住电子驻车制动器开关，启用紧急制动功能。释放电子驻车制动器开关后，即可解除紧急制动。

2. **释放电子驻车制动**：
   - **方法一**：启动车辆后，将变速器挂入D或R挡，踩下油门踏板也可以释放电子驻车制动。
   - **方法二**：踩下制动踏板并启动车辆，沿箭头方向按下EPB开关，释放EPB功能，红色EPB指示灯会自动熄灭。

请注意，在EPB处于释放状态时，应注意车辆周边环境，防止溜车危险。

**Final answer:**

电子驻车制动（EPB）的启用和释放方法如下： 1. **启用电子驻车制动**： - 您可以使用电子驻车制动器开关手动启用紧急制动功能。在车辆行驶过程中如出现紧急情况，可以拉住电子驻车制动器开关，启用紧急制动功能。释放电子驻车制动器开关后，即可解除紧急制动。 2. **释放电子驻车制动**： - **方法一**：启动车辆后，将变速器挂入D或R挡，踩下油门踏板也可以释放电子驻车制动。 - **方法二**：踩下制动踏板并启动车辆，沿箭头方向按下EPB开关，释放EPB功能，红色EPB指示灯会自动熄灭。 请注意，在EPB处于释放状态时，应注意车辆周边环境，防止溜车危险。

**Prompt Evidence:**

- E1; order=1; chunk_id=74a738bc-989e-5e6c-9fb2-01096b5f1921; page=158; chapter=启动和驾驶; section=电子驻车制动（EPB）; subsection=释放电子驻车制动（EPB）; heading_path=启动和驾驶 > 电子驻车制动（EPB） > 释放电子驻车制动（EPB）; content_type=note; truncated=False; original_text_chars=55; prompt_text_chars=55

释放电子驻车制动（EPB）
说明！
□启动车辆后，将变速器挂入D或R挡，踩下油门踏板也可以释放
电子驻车制动。

- E2; order=2; chunk_id=dcdde351-4cfb-5c8f-b659-66d7f8f4bc21; page=158; chapter=启动和驾驶; section=电子驻车制动（EPB）; subsection=释放电子驻车制动（EPB）; heading_path=启动和驾驶 > 电子驻车制动（EPB） > 释放电子驻车制动（EPB）; content_type=normal; truncated=False; original_text_chars=62; prompt_text_chars=62

释放电子驻车制动（EPB）
踩下制动踏板并启动车辆，沿箭头方向按下EPB开关，释放EPB功能，
红色EPB
指示灯自动熄灭。

- E3; order=3; chunk_id=bb0eb2dc-19d5-57c6-a724-b83815c49cda; page=159; chapter=启动和驾驶; section=电子驻车制动（EPB）; subsection=手动紧急制动; heading_path=启动和驾驶 > 电子驻车制动（EPB） > 手动紧急制动; content_type=normal; truncated=False; original_text_chars=70; prompt_text_chars=70

手动紧急制动
车辆行驶过程中如出现紧急情况，您可以拉住电子驻车制动器开关，
启用紧急制动功能。
释放电子驻车制动器开关后，即可解除紧急制动。

- E4; order=4; chunk_id=31c8ea68-7ffa-5e85-b2d8-c0498a4a2997; page=157; chapter=启动和驾驶; section=电子驻车制动（EPB）; subsection=N/A; heading_path=启动和驾驶 > 电子驻车制动（EPB）; content_type=normal; truncated=False; original_text_chars=27; prompt_text_chars=27

您可以使用电子驻车制动（EPB），使车辆保持静止状态。

- E5; order=5; chunk_id=cf544339-bbf7-5bf3-a971-197c7972f832; page=159; chapter=启动和驾驶; section=电子驻车制动（EPB）; subsection=熄火时解除电子驻车制动（EPB）; heading_path=启动和驾驶 > 电子驻车制动（EPB） > 熄火时解除电子驻车制动（EPB）; content_type=warning; truncated=False; original_text_chars=50; prompt_text_chars=50

熄火时解除电子驻车制动（EPB）
警告
■在EPB处于释放状态时，应注意车辆周边环境，防止溜车危险。

**Citations:**

- page=158; chapter=启动和驾驶; section=电子驻车制动（EPB）; subsection=N/A; chunk_id=74a738bc-989e-5e6c-9fb2-01096b5f1921; quote=释放电子驻车制动（EPB） 说明！
- page=158; chapter=启动和驾驶; section=电子驻车制动（EPB）; subsection=N/A; chunk_id=dcdde351-4cfb-5c8f-b659-66d7f8f4bc21; quote=释放电子驻车制动（EPB） 踩下制动踏板并启动车辆，沿箭头方向按下EPB开关，释放EPB功能， 红色EPB 指示灯自动熄灭。
- page=159; chapter=启动和驾驶; section=电子驻车制动（EPB）; subsection=N/A; chunk_id=bb0eb2dc-19d5-57c6-a724-b83815c49cda; quote=手动紧急制动 车辆行驶过程中如出现紧急情况，您可以拉住电子驻车制动器开关， 启用紧急制动功能。
- page=157; chapter=启动和驾驶; section=电子驻车制动（EPB）; subsection=N/A; chunk_id=31c8ea68-7ffa-5e85-b2d8-c0498a4a2997; quote=您可以使用电子驻车制动（EPB），使车辆保持静止状态。
- page=159; chapter=启动和驾驶; section=电子驻车制动（EPB）; subsection=N/A; chunk_id=cf544339-bbf7-5bf3-a971-197c7972f832; quote=熄火时解除电子驻车制动（EPB） 警告 ■在EPB处于释放状态时，应注意车辆周边环境，防止溜车危险。

**Deterministic checks:**

- answer_non_empty: True
- must_include_term_coverage: 0.7500
- matched_must_include_terms: EPB; 制动踏板; 按下
- missing_must_include_terms: 拉起
- forbidden_term_hits: N/A
- evidence_structure_hit: False
- expected_section_hit: True
- expected_subsection_hit: False
- insufficient_evidence_behavior: N/A
- internal_reference_leak: False

**Must include points:** 说明车辆静止时如何启用EPB; 说明手动释放EPB需要踩下制动踏板并启动车辆; 说明释放操作及指示灯变化

**Must not claim:** 不得声称手动释放EPB不需要踩下制动踏板

**Critical warning points:** N/A

**Human review:**

- Groundedness: TODO / NOT REVIEWED
- Correctness: TODO / NOT REVIEWED
- Completeness: TODO / NOT REVIEWED
- Condition Handling: TODO / NOT REVIEWED
- Safety Preservation: N/A
- Unsupported claim: TODO / NOT REVIEWED
- Critical safety omission: TODO / NOT REVIEWED
- Notes: TODO / NOT REVIEWED

**Elapsed seconds:** 13.1711

### remote_key_start_answer_001

**Question:** 如何使用遥控钥匙启动车辆？

**Answer type:** procedure

**Source case:** remote_key_start_001

**Raw answer:**

要使用遥控钥匙启动车辆，请按照以下步骤操作：

1. 将遥控钥匙放入前杯托底部。
2. 将挡位置于驻车挡（P）。
3. 将遥控钥匙放置于车内。
4. 将制动踏板踩到底。
5. 长按START/STOP按钮，车辆启动后松开按钮。

请注意，只有经过正确编码的遥控钥匙才能启动车辆。如果遥控钥匙电池电量低，系统无法检测到钥匙时，仪表显示屏上会弹出消息提示您，未检测到钥匙。此时，您可以按照上述步骤操作，将遥控钥匙放入前杯托底部，再尝试启动车辆。

**Final answer:**

要使用遥控钥匙启动车辆，请按照以下步骤操作： 1. 将遥控钥匙放入前杯托底部。
2. 将挡位置于驻车挡（P）。
3. 将遥控钥匙放置于车内。
4. 将制动踏板踩到底。
5. 长按START/STOP按钮，车辆启动后松开按钮。 请注意，只有经过正确编码的遥控钥匙才能启动车辆。如果遥控钥匙电池电量低，系统无法检测到钥匙时，仪表显示屏上会弹出消息提示您，未检测到钥匙。此时，您可以按照上述步骤操作，将遥控钥匙放入前杯托底部，再尝试启动车辆。

**Prompt Evidence:**

- E1; order=1; chunk_id=0ceca0e0-102d-5f03-b1c8-9945bd0beacb; page=143; chapter=启动和驾驶; section=通过遥控钥匙启动车辆; subsection=车辆紧急启动; heading_path=启动和驾驶 > 通过遥控钥匙启动车辆 > 车辆紧急启动; content_type=procedure; truncated=False; original_text_chars=107; prompt_text_chars=107

车辆紧急启动
遥控钥匙电池电量低，系统无法检测到钥匙时，仪表显示屏上会弹出
消息提示您，未检测到钥匙。此时，请按照以下步骤启动车辆：
1 将遥控钥匙放入前杯托底部。
2 按照前文中遥控钥匙启动车辆所述步骤启动车辆。

- E2; order=2; chunk_id=a0a38bbc-82c9-5f5c-b6b0-0b38a8326e10; page=143; chapter=启动和驾驶; section=通过遥控钥匙启动车辆; subsection=N/A; heading_path=启动和驾驶 > 通过遥控钥匙启动车辆; content_type=note; truncated=False; original_text_chars=95; prompt_text_chars=95

说明！
□只有经过正确编码的遥控钥匙才能启动车辆。
2 请将挡位置于驻车挡（P）。
3 将遥控钥匙放置于车内。
4 将制动踏板踩到底。
5 长按START/STOP按钮，车辆启动后松开按钮。

- E3; order=3; chunk_id=07e8c62e-e4e9-5314-8667-d64dafebbd18; page=40; chapter=上车和下车; section=使用遥控钥匙解锁和闭锁; subsection=遥控钥匙; heading_path=上车和下车 > 使用遥控钥匙解锁和闭锁 > 遥控钥匙; content_type=procedure; truncated=False; original_text_chars=162; prompt_text_chars=162

遥控钥匙
您的车辆配备了遥控钥匙。您可以通过遥控钥匙进行以下操作。
锁止按钮：短按锁止按钮，锁止所有车门/尾门，并启用防盗报
警。
解锁按钮：短按解锁按钮，解锁所有车门/尾门，并解除防盗报
警。
尾门按钮：短按尾门按钮，解锁尾门。长按尾门按钮，自动打开/
关闭尾门。尾门自动打开/关闭过程中，短按尾门按钮，尾门将停止
运动。

- E4; order=4; chunk_id=a3790d26-6ccf-5154-852e-40aae139fa2d; page=303; chapter=保养和维护; section=更换遥控钥匙电池; subsection=N/A; heading_path=保养和维护 > 更换遥控钥匙电池; content_type=procedure; truncated=False; original_text_chars=263; prompt_text_chars=263

如果遥控钥匙电池电量耗尽，可能会出现遥控钥匙无法正常工作的情
况，如无法正常锁止/解锁车辆，启动车辆等。请使用新电池更换。
1 拆下机械钥匙，请参见应急解锁和锁止车门（页码334）。
按住钥匙盖的边缘。
向外侧方向移动，取下钥匙盖。
3 拆下钥匙盖后，拆除遥控钥匙电池上端的盖子，插入新电池，使
“+”极端朝上。
4 更换钥匙电池后，按遥控钥匙上的任意按键，检查机械钥匙安装
区域内的工作指示灯是否点亮。
01 工作指示灯。
5 安装遥控钥匙时，按照相反的步骤进行安装。
6 操作遥控钥匙上的按键，检查并确认遥控钥匙正常工作。

- E5; order=5; chunk_id=e643bc08-a2d6-52c8-b546-2b0301f1beb2; page=142; chapter=启动和驾驶; section=通过手机APP启动车辆; subsection=通过蓝牙钥匙启动车辆; heading_path=启动和驾驶 > 通过手机APP启动车辆 > 通过蓝牙钥匙启动车辆; content_type=procedure; truncated=False; original_text_chars=72; prompt_text_chars=72

通过蓝牙钥匙启动车辆
您可以通过以下方式启动车辆：
1 打开Lynk & Co APP蓝牙钥匙。
2 在Lynk & Co APP中点击
图标。

**Citations:**

- page=143; chapter=启动和驾驶; section=通过遥控钥匙启动车辆; subsection=N/A; chunk_id=0ceca0e0-102d-5f03-b1c8-9945bd0beacb; quote=此时，请按照以下步骤启动车辆： 1 将遥控钥匙放入前杯托底部。 2 按照前文中遥控钥匙启动车辆所述步骤启动车辆。
- page=143; chapter=启动和驾驶; section=通过遥控钥匙启动车辆; subsection=N/A; chunk_id=a0a38bbc-82c9-5f5c-b6b0-0b38a8326e10; quote=□只有经过正确编码的遥控钥匙才能启动车辆。
- page=40; chapter=上车和下车; section=使用遥控钥匙解锁和闭锁; subsection=N/A; chunk_id=07e8c62e-e4e9-5314-8667-d64dafebbd18; quote=遥控钥匙 您的车辆配备了遥控钥匙。
- page=303; chapter=保养和维护; section=更换遥控钥匙电池; subsection=N/A; chunk_id=a3790d26-6ccf-5154-852e-40aae139fa2d; quote=如果遥控钥匙电池电量耗尽，可能会出现遥控钥匙无法正常工作的情 况，如无法正常锁止/解锁车辆，启动车辆等。
- page=142; chapter=启动和驾驶; section=通过手机APP启动车辆; subsection=N/A; chunk_id=e643bc08-a2d6-52c8-b546-2b0301f1beb2; quote=通过蓝牙钥匙启动车辆 您可以通过以下方式启动车辆： 1 打开Lynk & Co APP蓝牙钥匙。

**Deterministic checks:**

- answer_non_empty: True
- must_include_term_coverage: 1.0000
- matched_must_include_terms: 驻车挡; 遥控钥匙; 制动踏板; START/STOP
- missing_must_include_terms: N/A
- forbidden_term_hits: N/A
- evidence_structure_hit: True
- expected_section_hit: True
- expected_subsection_hit: N/A
- insufficient_evidence_behavior: N/A
- internal_reference_leak: False

**Must include points:** 将挡位置于驻车挡P; 将遥控钥匙放置于车内; 将制动踏板踩到底; 长按START/STOP按钮并在车辆启动后松开

**Must not claim:** 不得把蓝牙钥匙或网络远程启动步骤当作遥控钥匙启动步骤

**Critical warning points:** N/A

**Human review:**

- Groundedness: TODO / NOT REVIEWED
- Correctness: TODO / NOT REVIEWED
- Completeness: TODO / NOT REVIEWED
- Condition Handling: TODO / NOT REVIEWED
- Safety Preservation: N/A
- Unsupported claim: TODO / NOT REVIEWED
- Critical safety omission: TODO / NOT REVIEWED
- Notes: TODO / NOT REVIEWED

**Elapsed seconds:** 8.3116

### pressure_wash_warning_answer_001

**Question:** 使用高压水枪清洗车辆时有哪些注意事项？

**Answer type:** warning

**Source case:** pressure_wash_warning_001

**Raw answer:**

使用高压水枪清洗车辆时，需要注意以下事项：

1. 在清洗车辆前，请确保所有车窗和天窗均已关闭。
2. 请勿使用含酸清洁剂或强碱性肥皂、强化学性清洗剂、汽油或溶剂清洗车辆，以免损坏车辆表面。
3. 在清洗车辆底部时，避免将水枪对准车辆底部的接插件进行冲洗，以防损坏传感器。
4. 清洗传感器时，应使用较小的水流短时间冲洗，并保持至少10厘米以上的距离。
5. 在清洗车辆时，禁止将水枪对准车辆底部接插件进行冲洗。
6. 在清洗车辆外部前，请关闭所有车窗和天窗。
7. 清洗车辆后，请将车辆表面擦拭干净，避免清洁剂残留导致腐蚀。
8. 使用高压水枪时，务必严格按高压清洗器使用说明操作，特别注意工作压力和喷洗距离。喷嘴与车身表面至少保持30厘米的距离，并保持喷嘴移动，避免高压水流浸入车辆零部件内导致损坏。
9. 请勿使喷嘴直接或间接对发动机舱内进行冲洗，以免造成发动机舱内的电气元件受损或部件不能正常使用。
10. 在清洗车辆后若要立即驾车，请数次踩下制动踏板，以去除制动摩擦片上的水汽，确保制动效率。

**Final answer:**

使用高压水枪清洗车辆时，需要注意以下事项： 1. 在清洗车辆前，请确保所有车窗和天窗均已关闭。
2. 请勿使用含酸清洁剂或强碱性肥皂、强化学性清洗剂、汽油或溶剂清洗车辆，以免损坏车辆表面。
3. 在清洗车辆底部时，避免将水枪对准车辆底部的接插件进行冲洗，以防损坏传感器。
4. 清洗传感器时，应使用较小的水流短时间冲洗，并保持至少10厘米以上的距离。
5. 在清洗车辆时，禁止将水枪对准车辆底部接插件进行冲洗。
6. 在清洗车辆外部前，请关闭所有车窗和天窗。
7. 清洗车辆后，请将车辆表面擦拭干净，避免清洁剂残留导致腐蚀。
8. 使用高压水枪时，务必严格按高压清洗器使用说明操作，特别注意工作压力和喷洗距离。喷嘴与车身表面至少保持30厘米的距离，并保持喷嘴移动，避免高压水流浸入车辆零部件内导致损坏。
9. 请勿使喷嘴直接或间接对发动机舱内进行冲洗，以免造成发动机舱内的电气元件受损或部件不能正常使用。
10. 在清洗车辆后若要立即驾车，请数次踩下制动踏板，以去除制动摩擦片上的水汽，确保制动效率。

**Prompt Evidence:**

- E1; order=1; chunk_id=e02d2d11-fcdc-58ee-8f58-63557f557146; page=317; chapter=保养和维护; section=清洁车辆; subsection=高压冲洗; heading_path=保养和维护 > 清洁车辆 > 高压冲洗; content_type=warning; truncated=False; original_text_chars=352; prompt_text_chars=352

高压冲洗
警告！
■在清洗车辆后若要立即驾车，请数次踩下制动踏板，以去除制动
摩擦片上的水汽。水汽可能影响制动效率。
■洗车前，检查并确认车辆的外部开闭件已正确关闭。
■在清洗车辆时，禁止将水枪对准车辆底部接插件进行冲洗。
■避免用高压清洗机或蒸汽清洗机对传感器进行清洁，以免损坏传
感器。清洗车辆时应使用较小的水流短时间冲洗传感器表面，且
至少保持10 cm以上的距离。
■务必严格按高压清洗器使用说明清洁车辆，特别注意工作压力和
喷洗距离。如果使用压力清洗器，则喷嘴与车身的表面至少须保
持30 cm的距离。保持喷嘴移动，不要朝某个部位一直喷水，高
压水流浸入车辆零部件内可能导致损坏。
■请勿使喷嘴直接或间接对发动机舱内进行冲洗。高压水流会造成
发动机舱内的电气元件受损或造成一些部件不能正常使用。

- E2; order=2; chunk_id=77c94197-9367-5a81-9a21-710bb49aca01; page=317; chapter=保养和维护; section=清洁车辆; subsection=N/A; heading_path=保养和维护 > 清洁车辆; content_type=caution; truncated=False; original_text_chars=182; prompt_text_chars=182

注意！
■在清洗车辆外部前，请记得关闭所有车窗和天窗。
■请勿使用含酸清洁剂清洗车辆。酸液可能损坏车辆表面，影响车
辆外观。
■请勿用强碱性肥皂、强化学性清洗剂、汽油或溶剂清洗车辆，否
则可能影响车辆外观。
■在冬季道路撒盐的地区，应定期清洁车底，以防止盐累积，导致
车底和悬架加速腐蚀。
■在清洗完车辆后，请将车辆表面擦拭干净，否则残留的清洁剂会
腐蚀车辆外观。

- E3; order=3; chunk_id=2a0c6a17-3a18-5cbd-bf19-aad195e97ade; page=164; chapter=启动和驾驶; section=涉水驾驶; subsection=N/A; heading_path=启动和驾驶 > 涉水驾驶; content_type=procedure; truncated=False; original_text_chars=171; prompt_text_chars=171

涉水行驶前，应注意以下事项：
■涉水行驶前先确定水深，水位最高不得超过车身下边缘。
■应低速通过积水路段，任何情况下都不要在水中停车、倒车。
涉水驾驶之后，应在车辆安全时立即执行下列检查：
■轻踩制动踏板使制动器干燥，并检查制动器是否正常工作。
■检查喇叭是否正常工作。
■转动方向盘以检查转向助力是否正常工作。
■检查外部车灯是否正常工作。

- E4; order=4; chunk_id=4790312e-1fb3-5552-b704-9b8d8301dde7; page=305; chapter=保养和维护; section=保养和维护低压蓄电池; subsection=低压蓄电池处理的安全警告; heading_path=保养和维护 > 保养和维护低压蓄电池 > 低压蓄电池处理的安全警告; content_type=caution; truncated=False; original_text_chars=38; prompt_text_chars=38

低压蓄电池处理的安全警告
注意！
■请勿在车辆接通电源时断开车辆低压蓄电池。

- E5; order=5; chunk_id=92ca4f4b-06f1-5e82-ab29-868233b87368; page=162; chapter=启动和驾驶; section=加油; subsection=N/A; heading_path=启动和驾驶 > 加油; content_type=warning; truncated=False; original_text_chars=77; prompt_text_chars=77

警告！
如果您或其他人需接触燃油，应遵守以下规定：
■立即将皮肤上的燃油清洗干净。
■如果燃油溅入眼睛，使用清洁的水将眼睛彻底清洗，并立即寻求
医疗救助。

**Citations:**

- page=317; chapter=保养和维护; section=清洁车辆; subsection=N/A; chunk_id=e02d2d11-fcdc-58ee-8f58-63557f557146; quote=清洗车辆时应使用较小的水流短时间冲洗传感器表面，且 至少保持10 cm以上的距离。 ■务必严格按高压清洗器使用说明清洁车辆，特别注意工作压力和 喷洗距离。
- page=317; chapter=保养和维护; section=清洁车辆; subsection=N/A; chunk_id=77c94197-9367-5a81-9a21-710bb49aca01; quote=注意！ ■在清洗车辆外部前，请记得关闭所有车窗和天窗。 ■请勿使用含酸清洁剂清洗车辆。
- page=164; chapter=启动和驾驶; section=涉水驾驶; subsection=N/A; chunk_id=2a0c6a17-3a18-5cbd-bf19-aad195e97ade; quote=涉水行驶前，应注意以下事项： ■涉水行驶前先确定水深，水位最高不得超过车身下边缘。 ■应低速通过积水路段，任何情况下都不要在水中停车、倒车。 涉水驾驶之后，应在车辆安全时立即执行下列检查： ■轻踩制动踏板使制动器干燥，并检查制动器是否正常工作。 ■检查喇叭是否正常工作。 ■转动方向盘以检查转向助力是否正常工作。 ■检查外部车灯是否正常工作。
- page=305; chapter=保养和维护; section=保养和维护低压蓄电池; subsection=N/A; chunk_id=4790312e-1fb3-5552-b704-9b8d8301dde7; quote=低压蓄电池处理的安全警告 注意！ ■请勿在车辆接通电源时断开车辆低压蓄电池。
- page=162; chapter=启动和驾驶; section=加油; subsection=N/A; chunk_id=92ca4f4b-06f1-5e82-ab29-868233b87368; quote=警告！ 如果您或其他人需接触燃油，应遵守以下规定： ■立即将皮肤上的燃油清洗干净。 ■如果燃油溅入眼睛，使用清洁的水将眼睛彻底清洗，并立即寻求 医疗救助。

**Deterministic checks:**

- answer_non_empty: True
- must_include_term_coverage: 1.0000
- matched_must_include_terms: 底部接插件; 传感器; 10 cm; 30 cm; 发动机舱
- missing_must_include_terms: N/A
- forbidden_term_hits: N/A
- evidence_structure_hit: False
- expected_section_hit: True
- expected_subsection_hit: False
- insufficient_evidence_behavior: N/A
- internal_reference_leak: False

**Must include points:** 确认外部开闭件已正确关闭; 禁止对准车辆底部接插件冲洗; 避免高压清洁传感器并保持至少10厘米距离; 喷嘴与车身至少保持30厘米距离; 不得直接或间接冲洗发动机舱

**Must not claim:** 不得声称高压水枪可以直接清洗发动机舱或传感器

**Critical warning points:** 不得遗漏禁止冲洗底部接插件的要求; 不得弱化发动机舱冲洗禁令; 保留10厘米和30厘米距离条件

**Human review:**

- Groundedness: TODO / NOT REVIEWED
- Correctness: TODO / NOT REVIEWED
- Completeness: TODO / NOT REVIEWED
- Condition Handling: TODO / NOT REVIEWED
- Safety Preservation: TODO / NOT REVIEWED
- Unsupported claim: TODO / NOT REVIEWED
- Critical safety omission: TODO / NOT REVIEWED
- Notes: TODO / NOT REVIEWED

**Elapsed seconds:** 14.4527

### abs_fault_warning_answer_001

**Question:** 制动防抱死系统发生故障时应该怎么办？

**Answer type:** warning

**Source case:** abs_fault_handling_001

**Raw answer:**

当制动防抱死系统发生故障时，您需要注意以下几点：

1. 根据 Evidence E2 和 Evidence E3 的说明，防抱死制动系统存在故障时，警告灯会点亮。请留意仪表盘上的警告灯。

2. 如果警告灯点亮，建议您按照 Evidence E5 中的步骤进行检查和处理：
   - 检查仪表显示屏和中央显示屏是否有警告/指示消息。如果有，请了解这些图标的含义和相应的处理措施，可以参考指示灯和警告灯的相关内容（页码69）。
   - 如果没有警告消息，检查是否有任何系统功能下降或受限。如果有，请采取适当措施解决故障，例如打开前机舱盖、检查安全带等（页码307、99）。
   - 如果没有发现功能下降或受限的情况，请根据 Evidence E5 中列出的故障类型采取相应措施，如轮胎漏气或车辆电池电量过低等（页码340、343）。
   - 如果上述步骤都无法解决问题，请联系Lynk & Co领克中心寻求帮助。

在制动过程中，您可能会感觉到机舱传来连续“咯咯”的声音，同时感受到制动踏板传来的振动。这是防抱死制动系统工作时引起的正常现象，而不是故障。当防抱死制动系统停止工作时，制动踏板的感觉会恢复到非防抱死制动的状态。

**Final answer:**

当制动防抱死系统发生故障时，您需要注意以下几点： 1. 和 的说明，防抱死制动系统存在故障时，警告灯会点亮。请留意仪表盘上的警告灯。 2. 如果警告灯点亮，建议您按照 的步骤进行检查和处理： - 检查仪表显示屏和中央显示屏是否有警告/指示消息。如果有，请了解这些图标的含义和相应的处理措施，可以参考指示灯和警告灯的相关内容（页码69）。 - 如果没有警告消息，检查是否有任何系统功能下降或受限。如果有，请采取适当措施解决故障，例如打开前机舱盖、检查安全带等（页码307、99）。 - 如果没有发现功能下降或受限的情况，请列出的故障类型采取相应措施，如轮胎漏气或车辆电池电量过低等（页码340、343）。 - 如果上述步骤都无法解决问题，请联系Lynk & Co领克中心寻求帮助。 在制动过程中，您可能会感觉到机舱传来连续“咯咯”的声音，同时感受到制动踏板传来的振动。这是防抱死制动系统工作时引起的正常现象，而不是故障。当防抱死制动系统停止工作时，制动踏板的感觉会恢复到非防抱死制动的状态。

**Prompt Evidence:**

- E1; order=1; chunk_id=b6c3943e-cd2e-528f-883e-313f1fab8062; page=157; chapter=启动和驾驶; section=制动防抱死系统; subsection=N/A; heading_path=启动和驾驶 > 制动防抱死系统; content_type=normal; truncated=False; original_text_chars=60; prompt_text_chars=60

车辆配有制动防抱死系统，可在您施加最大制动力时，防止车轮抱
死。在大多数路况下，可改善紧急制动情况下车辆的转向控制性能。

- E2; order=2; chunk_id=b2a7d86e-8e79-5f5e-b2ea-bbc205bbc3ea; page=157; chapter=启动和驾驶; section=制动防抱死系统; subsection=功能状态说明; heading_path=启动和驾驶 > 制动防抱死系统 > 功能状态说明; content_type=normal; truncated=False; original_text_chars=27; prompt_text_chars=27

功能状态说明
防抱死制动系统存在故障时，该警告灯点亮。

- E3; order=3; chunk_id=c2be2282-a6b3-5cab-a395-9a8c26c12541; page=166; chapter=启动和驾驶; section=制动防抱死系统; subsection=功能状态说明; heading_path=启动和驾驶 > 制动防抱死系统 > 功能状态说明; content_type=normal; truncated=False; original_text_chars=27; prompt_text_chars=27

功能状态说明
防抱死制动系统存在故障时，该警告灯点亮。

- E4; order=4; chunk_id=86d51ecf-273b-5077-8ab1-61898bf44520; page=157; chapter=启动和驾驶; section=制动防抱死系统; subsection=N/A; heading_path=启动和驾驶 > 制动防抱死系统; content_type=note; truncated=False; original_text_chars=112; prompt_text_chars=112

说明！
□在制动过程中，您会感觉到机舱传来连续“咯咯”的声音，同时
感受到制动踏板传来的振动。这是防抱死制动系统工作时引起的
正常现象，而不是故障。
□当防抱死制动系统停止工作时，制动踏板的感觉会恢复到非防抱
死制动的状态。

- E5; order=5; chunk_id=192f1cda-ae12-53c0-9d70-84c79aec6967; page=329; chapter=紧急情况下; section=处理车辆故障; subsection=N/A; heading_path=紧急情况下 > 处理车辆故障; content_type=procedure; truncated=False; original_text_chars=389; prompt_text_chars=389

当您的车辆发生故障时，通常显示屏会显示故障警告指示灯图标/消
息提示，或两者同时显示。在某些情况下车辆无故障时，外部因素可
能限制系统功能，如浓雾/大雪会限制摄像头/雷达传感器，影响摄像
头/雷达功能。
1 检查仪表显示屏和中央显示屏是否有警告/指示消息。
■如果有，请了解这些图标的含义和相应的处理措施，请参见
指示灯和警告灯（页码69）。
■如果无，转至步骤2。
2 检查是否有任何系统功能下降或受限。
■如果有，采取适当措施解决故障（前机舱盖打开，请参见打
开前机舱盖（页码307）、安全带未系，请参见安全带（页
码99）等章节）。
■如果无，转至步骤3。
3 请根据下列故障采取适当措施。
■轮胎漏气，请参见补胎套装（页码340）。
■车辆电池电量过低，请参见电池电量较低（页码343）。
4 如果重复上述过程后无法解决故障，请联系Lynk & Co领克中心寻
求帮助。

**Citations:**

- page=157; chapter=启动和驾驶; section=制动防抱死系统; subsection=N/A; chunk_id=b6c3943e-cd2e-528f-883e-313f1fab8062; quote=车辆配有制动防抱死系统，可在您施加最大制动力时，防止车轮抱 死。
- page=157; chapter=启动和驾驶; section=制动防抱死系统; subsection=N/A; chunk_id=b2a7d86e-8e79-5f5e-b2ea-bbc205bbc3ea; quote=功能状态说明 防抱死制动系统存在故障时，该警告灯点亮。
- page=166; chapter=启动和驾驶; section=制动防抱死系统; subsection=N/A; chunk_id=c2be2282-a6b3-5cab-a395-9a8c26c12541; quote=功能状态说明 防抱死制动系统存在故障时，该警告灯点亮。
- page=157; chapter=启动和驾驶; section=制动防抱死系统; subsection=N/A; chunk_id=86d51ecf-273b-5077-8ab1-61898bf44520; quote=这是防抱死制动系统工作时引起的 正常现象，而不是故障。
- page=329; chapter=紧急情况下; section=处理车辆故障; subsection=N/A; chunk_id=192f1cda-ae12-53c0-9d70-84c79aec6967; quote=当您的车辆发生故障时，通常显示屏会显示故障警告指示灯图标/消 息提示，或两者同时显示。

**Deterministic checks:**

- answer_non_empty: True
- must_include_term_coverage: 0.5000
- matched_must_include_terms: Lynk & Co领克中心
- missing_must_include_terms: 安全区域停车
- forbidden_term_hits: N/A
- evidence_structure_hit: False
- expected_section_hit: True
- expected_subsection_hit: False
- insufficient_evidence_behavior: N/A
- internal_reference_leak: False

**Must include points:** 立刻在安全区域停车; 联系Lynk & Co领克中心

**Must not claim:** 不得建议用户在故障状态下继续正常驾驶

**Critical warning points:** 必须保留立即停车和联系专业人员的要求

**Human review:**

- Groundedness: TODO / NOT REVIEWED
- Correctness: TODO / NOT REVIEWED
- Completeness: TODO / NOT REVIEWED
- Condition Handling: TODO / NOT REVIEWED
- Safety Preservation: TODO / NOT REVIEWED
- Unsupported claim: TODO / NOT REVIEWED
- Critical safety omission: TODO / NOT REVIEWED
- Notes: TODO / NOT REVIEWED

**Elapsed seconds:** 14.0082

### abs_explanation_answer_001

**Question:** 制动防抱死系统有什么作用？

**Answer type:** explanation

**Source case:** abs_explanation_001

**Raw answer:**

制动防抱死系统的主要作用是在您施加最大制动力时，防止车轮抱死。这在大多数路况下，特别是在紧急制动情况下，可以改善车辆的转向控制性能。当系统正常工作时，在制动过程中您可能会感觉到机舱内有连续的“咯咯”声以及制动踏板的振动，这是正常现象。如果防抱死制动系统停止工作，制动踏板的感觉会恢复到非防抱死制动的状态。

**Final answer:**

制动防抱死系统的主要作用是在您施加最大制动力时，防止车轮抱死。这在大多数路况下，特别是在紧急制动情况下，可以改善车辆的转向控制性能。当系统正常工作时，在制动过程中您可能会感觉到机舱内有连续的“咯咯”声以及制动踏板的振动，这是正常现象。如果防抱死制动系统停止工作，制动踏板的感觉会恢复到非防抱死制动的状态。

**Prompt Evidence:**

- E1; order=1; chunk_id=b6c3943e-cd2e-528f-883e-313f1fab8062; page=157; chapter=启动和驾驶; section=制动防抱死系统; subsection=N/A; heading_path=启动和驾驶 > 制动防抱死系统; content_type=normal; truncated=False; original_text_chars=60; prompt_text_chars=60

车辆配有制动防抱死系统，可在您施加最大制动力时，防止车轮抱
死。在大多数路况下，可改善紧急制动情况下车辆的转向控制性能。

- E2; order=2; chunk_id=b2a7d86e-8e79-5f5e-b2ea-bbc205bbc3ea; page=157; chapter=启动和驾驶; section=制动防抱死系统; subsection=功能状态说明; heading_path=启动和驾驶 > 制动防抱死系统 > 功能状态说明; content_type=normal; truncated=False; original_text_chars=27; prompt_text_chars=27

功能状态说明
防抱死制动系统存在故障时，该警告灯点亮。

- E3; order=3; chunk_id=86d51ecf-273b-5077-8ab1-61898bf44520; page=157; chapter=启动和驾驶; section=制动防抱死系统; subsection=N/A; heading_path=启动和驾驶 > 制动防抱死系统; content_type=note; truncated=False; original_text_chars=112; prompt_text_chars=112

说明！
□在制动过程中，您会感觉到机舱传来连续“咯咯”的声音，同时
感受到制动踏板传来的振动。这是防抱死制动系统工作时引起的
正常现象，而不是故障。
□当防抱死制动系统停止工作时，制动踏板的感觉会恢复到非防抱
死制动的状态。

- E4; order=4; chunk_id=c2be2282-a6b3-5cab-a395-9a8c26c12541; page=166; chapter=启动和驾驶; section=制动防抱死系统; subsection=功能状态说明; heading_path=启动和驾驶 > 制动防抱死系统 > 功能状态说明; content_type=normal; truncated=False; original_text_chars=27; prompt_text_chars=27

功能状态说明
防抱死制动系统存在故障时，该警告灯点亮。

- E5; order=5; chunk_id=7ec78836-badf-5bb4-9c66-ecfe4997b4c0; page=157; chapter=启动和驾驶; section=制动防抱死系统; subsection=功能状态说明; heading_path=启动和驾驶 > 制动防抱死系统 > 功能状态说明; content_type=warning; truncated=False; original_text_chars=87; prompt_text_chars=87

功能状态说明
警告！
■防抱死制动系统存在故障时，请立刻在安全区域停车并联系Lynk
& Co领克中心。
■在崎岖、有碎石或有雪覆盖的道路上，制动距离将比在正常道路
时更长。

**Citations:**

- page=157; chapter=启动和驾驶; section=制动防抱死系统; subsection=N/A; chunk_id=b6c3943e-cd2e-528f-883e-313f1fab8062; quote=车辆配有制动防抱死系统，可在您施加最大制动力时，防止车轮抱 死。
- page=157; chapter=启动和驾驶; section=制动防抱死系统; subsection=N/A; chunk_id=b2a7d86e-8e79-5f5e-b2ea-bbc205bbc3ea; quote=功能状态说明 防抱死制动系统存在故障时，该警告灯点亮。
- page=157; chapter=启动和驾驶; section=制动防抱死系统; subsection=N/A; chunk_id=86d51ecf-273b-5077-8ab1-61898bf44520; quote=这是防抱死制动系统工作时引起的 正常现象，而不是故障。
- page=166; chapter=启动和驾驶; section=制动防抱死系统; subsection=N/A; chunk_id=c2be2282-a6b3-5cab-a395-9a8c26c12541; quote=功能状态说明 防抱死制动系统存在故障时，该警告灯点亮。
- page=157; chapter=启动和驾驶; section=制动防抱死系统; subsection=N/A; chunk_id=7ec78836-badf-5bb4-9c66-ecfe4997b4c0; quote=功能状态说明 警告！ ■防抱死制动系统存在故障时，请立刻在安全区域停车并联系Lynk & Co领克中心。 ■在崎岖、有碎石或有雪覆盖的道路上，制动距离将比在正常道路 时更长。

**Deterministic checks:**

- answer_non_empty: True
- must_include_term_coverage: 1.0000
- matched_must_include_terms: 防止车轮抱死; 转向控制性能
- missing_must_include_terms: N/A
- forbidden_term_hits: N/A
- evidence_structure_hit: True
- expected_section_hit: True
- expected_subsection_hit: N/A
- insufficient_evidence_behavior: N/A
- internal_reference_leak: False

**Must include points:** 最大制动力时防止车轮抱死; 在大多数路况下改善紧急制动时的转向控制性能

**Must not claim:** 不得声称ABS可以在所有路况下缩短制动距离

**Critical warning points:** N/A

**Human review:**

- Groundedness: TODO / NOT REVIEWED
- Correctness: TODO / NOT REVIEWED
- Completeness: TODO / NOT REVIEWED
- Condition Handling: TODO / NOT REVIEWED
- Safety Preservation: N/A
- Unsupported claim: TODO / NOT REVIEWED
- Critical safety omission: TODO / NOT REVIEWED
- Notes: TODO / NOT REVIEWED

**Elapsed seconds:** 5.0488

### autohold_explanation_answer_001

**Question:** 自动驻车 Auto Hold 的作用是什么？

**Answer type:** explanation

**Source case:** autohold_explanation_001

**Raw answer:**

自动驻车（Auto Hold）可以在正常驾驶过程中的短暂停车时提供制动，这样您就不需要一直踩制动踏板。具体来说，当车辆需要短暂停车时，您可以利用Auto Hold功能，车辆会自动施加制动，待您准备再次行驶时，只需踩下加速踏板或用力踩下制动踏板再松开，车辆即可正常行驶。

**Final answer:**

自动驻车（Auto Hold）可以在正常驾驶过程中的短暂停车时提供制动，这样您就不需要一直踩制动踏板。具体来说，当车辆需要短暂停车时，您可以利用Auto Hold功能，车辆会自动施加制动，待您准备再次行驶时，只需踩下加速踏板或用力踩下制动踏板再松开，车辆即可正常行驶。

**Prompt Evidence:**

- E1; order=1; chunk_id=3c50a072-e59a-51b2-bca0-e1815ca946ad; page=159; chapter=启动和驾驶; section=自动驻车系统; subsection=开启/关闭自动驻车; heading_path=启动和驾驶 > 自动驻车系统 > 开启/关闭自动驻车; content_type=note; truncated=False; original_text_chars=55; prompt_text_chars=55

开启/关闭自动驻车
说明！
□Auto Hold启用时，如果踩下制动踏板过轻，Auto Hold可能不激
活。

- E2; order=2; chunk_id=4495a19a-ba84-55e6-860e-89c45f1088d6; page=159; chapter=启动和驾驶; section=自动驻车系统; subsection=N/A; heading_path=启动和驾驶 > 自动驻车系统; content_type=normal; truncated=False; original_text_chars=93; prompt_text_chars=93

自动驻车（Auto Hold）可以在正常驾驶过程中的短暂停车时提供制
动，这样您就不需要一直踩制动踏板。
车辆需要起步时，您只要踩下加速踏板或用力踩下制动踏板再松开，
车辆即可正常行驶。

- E3; order=3; chunk_id=1c6557e4-776f-5363-b55f-228f6d8c0fb6; page=159; chapter=启动和驾驶; section=自动驻车系统; subsection=功能状态说明; heading_path=启动和驾驶 > 自动驻车系统 > 功能状态说明; content_type=normal; truncated=False; original_text_chars=58; prompt_text_chars=58

功能状态说明
激活自动驻车系统（Auto Hold）时，该指示灯点亮。
启用电子驻车制动（EPB）后，该警告灯长亮。

- E4; order=4; chunk_id=80ec6d19-2e74-5039-ac26-6fd1801351bf; page=159; chapter=启动和驾驶; section=自动驻车系统; subsection=N/A; heading_path=启动和驾驶 > 自动驻车系统; content_type=note; truncated=False; original_text_chars=106; prompt_text_chars=106

说明！
Auto Hold处于激活状态，且出现以下任一情况时，将自动停用
Auto Hold并启用EPB功能：
□松开驾驶员安全带。
□打开驾驶员侧车门。
□超出Auto Hold工作时间。
□挂入驻车挡（P）。

- E5; order=5; chunk_id=fce7d347-142c-5e4f-9459-49724f8d2267; page=159; chapter=启动和驾驶; section=自动驻车系统; subsection=开启/关闭自动驻车; heading_path=启动和驾驶 > 自动驻车系统 > 开启/关闭自动驻车; content_type=procedure; truncated=False; original_text_chars=78; prompt_text_chars=78

开启/关闭自动驻车
您可以通过以下步骤开启/关闭自动驻车：
1 从中央显示屏上边缘区域轻轻向下滑动，进入车辆功能界面。
2 点击
图标，开启/关闭自动驻车。

**Citations:**

- page=159; chapter=启动和驾驶; section=自动驻车系统; subsection=N/A; chunk_id=3c50a072-e59a-51b2-bca0-e1815ca946ad; quote=开启/关闭自动驻车 说明！
- page=159; chapter=启动和驾驶; section=自动驻车系统; subsection=N/A; chunk_id=4495a19a-ba84-55e6-860e-89c45f1088d6; quote=自动驻车（Auto Hold）可以在正常驾驶过程中的短暂停车时提供制 动，这样您就不需要一直踩制动踏板。
- page=159; chapter=启动和驾驶; section=自动驻车系统; subsection=N/A; chunk_id=1c6557e4-776f-5363-b55f-228f6d8c0fb6; quote=功能状态说明 激活自动驻车系统（Auto Hold）时，该指示灯点亮。
- page=159; chapter=启动和驾驶; section=自动驻车系统; subsection=N/A; chunk_id=80ec6d19-2e74-5039-ac26-6fd1801351bf; quote=Auto Hold处于激活状态，且出现以下任一情况时，将自动停用 Auto Hold并启用EPB功能： □松开驾驶员安全带。
- page=159; chapter=启动和驾驶; section=自动驻车系统; subsection=N/A; chunk_id=fce7d347-142c-5e4f-9459-49724f8d2267; quote=开启/关闭自动驻车 您可以通过以下步骤开启/关闭自动驻车： 1 从中央显示屏上边缘区域轻轻向下滑动，进入车辆功能界面。

**Deterministic checks:**

- answer_non_empty: True
- must_include_term_coverage: 1.0000
- matched_must_include_terms: Auto Hold; 短暂停车; 制动踏板; 加速踏板
- missing_must_include_terms: N/A
- forbidden_term_hits: N/A
- evidence_structure_hit: True
- expected_section_hit: True
- expected_subsection_hit: N/A
- insufficient_evidence_behavior: N/A
- internal_reference_leak: False

**Must include points:** 短暂停车时提供制动; 不需要一直踩住制动踏板; 车辆起步时可踩加速踏板或再次用力踩下并松开制动踏板

**Must not claim:** 不得声称Auto Hold可以替代驾驶员在所有场景下安全制动

**Critical warning points:** N/A

**Human review:**

- Groundedness: TODO / NOT REVIEWED
- Correctness: TODO / NOT REVIEWED
- Completeness: TODO / NOT REVIEWED
- Condition Handling: TODO / NOT REVIEWED
- Safety Preservation: N/A
- Unsupported claim: TODO / NOT REVIEWED
- Critical safety omission: TODO / NOT REVIEWED
- Notes: TODO / NOT REVIEWED

**Elapsed seconds:** 5.0312

### overspeed_condition_answer_001

**Question:** 超速报警在什么情况下触发和解除？

**Answer type:** condition

**Source case:** overspeed_alarm_001

**Raw answer:**

超速报警在以下情况下触发和解除：

1. 当车速高于您设定的超速报警车速时，系统会发出声音警告，并在仪表显示屏上弹出提示信息，提醒您减慢车速，确保安全行驶。
2. 当车速低于您设定的超速报警车速时，报警会自动解除。

请注意，超速报警功能仅提供超速提醒，但无法防止驾驶员超过设定的超速报警车速。因此，您需要主动控制车速以确保安全。

**Final answer:**

超速报警在以下情况下触发和解除： 1. 当车速高于您设定的超速报警车速时，系统会发出声音警告，并在仪表显示屏上弹出提示信息，提醒您减慢车速，确保安全行驶。
2. 当车速低于您设定的超速报警车速时，报警会自动解除。 请注意，超速报警功能仅提供超速提醒，但无法防止驾驶员超过设定的超速报警车速。因此，您需要主动控制车速以确保安全。

**Prompt Evidence:**

- E1; order=1; chunk_id=4caecc96-ba5b-51ad-ae2b-8756050ad578; page=171; chapter=驾驶辅助; section=超速报警; subsection=N/A; heading_path=驾驶辅助 > 超速报警; content_type=procedure; truncated=False; original_text_chars=175; prompt_text_chars=175

车辆配备超速报警功能，开启超速报警功能后，车速高于超速报警车
速设定值时，系统会发出声音警告，同时仪表显示屏上弹出提示信息
提醒驾驶员减慢车速，安全行驶。当车速低于超速报警车速设定值
时，报警解除。
在中央显示屏中点击
-Lynk Co-Pilot-超速报警，进入超速报警设
置界面。
01 点击开启/关闭超速报警。
02点击调节超速报警车速设定值。

- E2; order=2; chunk_id=44e38428-8ae9-51da-9c61-74f23a29077b; page=172; chapter=驾驶辅助; section=超速报警; subsection=N/A; heading_path=驾驶辅助 > 超速报警; content_type=warning; truncated=False; original_text_chars=28; prompt_text_chars=28

警告！
■超速报警无法防止驾驶员超过设定的超速报警车速。

- E3; order=3; chunk_id=3c18278f-d59c-5fd5-91ba-4839e09a011c; page=193; chapter=驾驶辅助; section=交通标志识别系统; subsection=设置限速信息识别; heading_path=驾驶辅助 > 交通标志识别系统 > 设置限速信息识别; content_type=note; truncated=False; original_text_chars=76; prompt_text_chars=76

设置限速信息识别
说明！
□限速报警功能只具备限速提醒作用，驾驶员必须主动控制车速。
□当限速报警设置为响铃方式时，则超速时报警方式为响铃且同时
闪烁。

- E4; order=4; chunk_id=34244e90-52e9-5847-b589-353ad8d29317; page=193; chapter=驾驶辅助; section=交通标志识别系统; subsection=设置限速信息识别; heading_path=驾驶辅助 > 交通标志识别系统 > 设置限速信息识别; content_type=procedure; truncated=False; original_text_chars=229; prompt_text_chars=229

设置限速信息识别
在中央显示屏中点击
-Lynk Co-Pilot-驾驶安全监测，进入驾驶安
全监测设置界面。
01 选择限速报警提醒方式（无、闪烁和响铃）。
02设置限速偏差数值。
当车速超过识别到的限速值加限速偏差值时，系统将会发出报警；直
至车速低于识别到的限速值加限速偏差值时，报警取消。
当车辆减速至低于限速值加限速偏差值5 km/h以下时，车辆再次加
速，使车速超过限速值加限速偏差值，系统才会再次发出报警，否则
将不再触发报警，直至限速值更新。

- E5; order=5; chunk_id=9843960b-73c9-5d17-9c48-04352a7b90f3; page=62; chapter=驾驶前的准备; section=胎压监测系统; subsection=胎压低报警; heading_path=驾驶前的准备 > 胎压监测系统 > 胎压低报警; content_type=normal; truncated=False; original_text_chars=115; prompt_text_chars=115

胎压低报警
当胎压低报警被激活时，对应报警轮胎开始闪烁，胎压监测系统状态
指示灯持续点亮直到报警消除，伴有声音报警，同时仪表显示屏弹出
提示信息。在冷态充气至标准胎压值后，以30 km/h以上的车速行驶
几分钟，胎压过低报警解除。

**Citations:**

- page=171; chapter=驾驶辅助; section=超速报警; subsection=N/A; chunk_id=4caecc96-ba5b-51ad-ae2b-8756050ad578; quote=车辆配备超速报警功能，开启超速报警功能后，车速高于超速报警车 速设定值时，系统会发出声音警告，同时仪表显示屏上弹出提示信息 提醒驾驶员减慢车速，安全行驶。 当车速低于超速报警车速设定值 时，报警解除。
- page=172; chapter=驾驶辅助; section=超速报警; subsection=N/A; chunk_id=44e38428-8ae9-51da-9c61-74f23a29077b; quote=警告！ ■超速报警无法防止驾驶员超过设定的超速报警车速。
- page=193; chapter=驾驶辅助; section=交通标志识别系统; subsection=N/A; chunk_id=3c18278f-d59c-5fd5-91ba-4839e09a011c; quote=□限速报警功能只具备限速提醒作用，驾驶员必须主动控制车速。 □当限速报警设置为响铃方式时，则超速时报警方式为响铃且同时 闪烁。
- page=193; chapter=驾驶辅助; section=交通标志识别系统; subsection=N/A; chunk_id=34244e90-52e9-5847-b589-353ad8d29317; quote=01 选择限速报警提醒方式（无、闪烁和响铃）。
- page=62; chapter=驾驶前的准备; section=胎压监测系统; subsection=N/A; chunk_id=9843960b-73c9-5d17-9c48-04352a7b90f3; quote=胎压低报警 当胎压低报警被激活时，对应报警轮胎开始闪烁，胎压监测系统状态 指示灯持续点亮直到报警消除，伴有声音报警，同时仪表显示屏弹出 提示信息。 在冷态充气至标准胎压值后，以30 km/h以上的车速行驶 几分钟，胎压过低报警解除。

**Deterministic checks:**

- answer_non_empty: True
- must_include_term_coverage: 0.5000
- matched_must_include_terms: 声音警告; 减慢车速
- missing_must_include_terms: 车速设定值; 报警解除
- forbidden_term_hits: N/A
- evidence_structure_hit: True
- expected_section_hit: True
- expected_subsection_hit: N/A
- insufficient_evidence_behavior: N/A
- internal_reference_leak: False

**Must include points:** 车速高于设定值时触发声音警告和提示; 车速低于设定值时解除报警

**Must not claim:** 不得混淆触发条件和解除条件

**Critical warning points:** N/A

**Human review:**

- Groundedness: TODO / NOT REVIEWED
- Correctness: TODO / NOT REVIEWED
- Completeness: TODO / NOT REVIEWED
- Condition Handling: TODO / NOT REVIEWED
- Safety Preservation: N/A
- Unsupported claim: TODO / NOT REVIEWED
- Critical safety omission: TODO / NOT REVIEWED
- Notes: TODO / NOT REVIEWED

**Elapsed seconds:** 6.7285

### remote_start_blocked_answer_001

**Question:** 哪些情况下无法远程启动发动机？

**Answer type:** condition

**Source case:** remote_start_blocked_001

**Raw answer:**

根据手册中的信息，以下情况会导致无法通过网络远程启动发动机：

- 挡位不在驻车挡（P）。
- 冷却液液位较低。
- 燃油油位较低。
- 车内有遥控钥匙。
- 网络信号丢失。
- 发动机机舱盖/车门未锁定。
- 发动机出现故障（例如出现发动机关键故障代码）。
- 车辆设置为维修模式。
- 连续两次远程启动车辆后，未手动启动车辆。

请注意检查这些条件以确保能够成功远程启动发动机。

**Final answer:**

根据手册中的信息，以下情况会导致无法通过网络远程启动发动机： - 挡位不在驻车挡（P）。
- 冷却液液位较低。
- 燃油油位较低。
- 车内有遥控钥匙。
- 网络信号丢失。
- 发动机机舱盖/车门未锁定。
- 发动机出现故障（例如出现发动机关键故障代码）。
- 车辆设置为维修模式。
- 连续两次远程启动车辆后，未手动启动车辆。 请注意检查这些条件以确保能够成功远程启动发动机。

**Prompt Evidence:**

- E1; order=1; chunk_id=5f81b96e-8136-552a-9ce1-2783904a6b53; page=143; chapter=启动和驾驶; section=通过手机APP启动车辆; subsection=通过网络远程启动发动机; heading_path=启动和驾驶 > 通过手机APP启动车辆 > 通过网络远程启动发动机; content_type=note; truncated=False; original_text_chars=161; prompt_text_chars=161

通过网络远程启动发动机
说明！
出现以下任一情况时，无法远程启动发动机：
□挡位不在驻车挡（P）。
□冷却液液位较低。
□燃油油位较低。
□车内有遥控钥匙。
□网络信号丢失。
□发动机机舱盖/车门未锁定。
□发动机出现故障（例如出现发动机关键故障代码）。
□车辆设置为维修模式。
□连续两次远程启动车辆后，未手动启动车辆。

- E2; order=2; chunk_id=20a55bcd-5480-58ae-8d7f-9a59228244fa; page=142; chapter=启动和驾驶; section=通过手机APP启动车辆; subsection=通过网络远程启动发动机; heading_path=启动和驾驶 > 通过手机APP启动车辆 > 通过网络远程启动发动机; content_type=normal; truncated=False; original_text_chars=64; prompt_text_chars=64

通过网络远程启动发动机
车辆已锁且挡位处于驻车挡（P）的情况下，登录Lynk & Co App，按
下
图标可以远程启动发动机。

- E3; order=3; chunk_id=438a348b-736a-5fe4-9567-70177cd779b9; page=142; chapter=启动和驾驶; section=通过手机APP启动车辆; subsection=N/A; heading_path=启动和驾驶 > 通过手机APP启动车辆; content_type=procedure; truncated=False; original_text_chars=94; prompt_text_chars=94

您可以通过Lynk & Co APP使用以下方式启用车辆：
■蓝牙启动：手机在车内时且处于连接状态时，可以通过蓝牙钥匙
启动车辆。
■远程启动：距离车辆较远时，可以通过网络远程启动发动机。

- E4; order=4; chunk_id=08966431-e662-58bd-b296-8130dfe538e4; page=142; chapter=启动和驾驶; section=通过手机APP启动车辆; subsection=N/A; heading_path=启动和驾驶 > 通过手机APP启动车辆; content_type=note; truncated=False; original_text_chars=86; prompt_text_chars=86

说明！
□通过蓝牙钥匙成功连接车辆后是通过蓝牙方式控制车辆。未连接
蓝牙钥匙是通过远程方式控制车辆。
□您可以在冬季寒冷条件下，远程启动发动机，提前对发动机预热
（暖机）。

- E5; order=5; chunk_id=d13c158f-d3f5-539e-b042-5828ab507c5d; page=142; chapter=启动和驾驶; section=通过手机APP启动车辆; subsection=通过蓝牙钥匙启动车辆; heading_path=启动和驾驶 > 通过手机APP启动车辆 > 通过蓝牙钥匙启动车辆; content_type=note; truncated=False; original_text_chars=147; prompt_text_chars=147

通过蓝牙钥匙启动车辆
说明！
出现以下任一情况时，无法通过蓝牙钥匙启动车辆：
□燃油油位较低。
□手机在车外或Lynk & Co APP处于关闭状态。
□发动机出现故障（例如出现发动机关键故障代码）。
□车辆位置靠近无线电塔/电视塔或发电站。
□车辆周围存在无线设备，如发射机或无线电广播设备。

**Citations:**

- page=143; chapter=启动和驾驶; section=通过手机APP启动车辆; subsection=N/A; chunk_id=5f81b96e-8136-552a-9ce1-2783904a6b53; quote=出现以下任一情况时，无法远程启动发动机： □挡位不在驻车挡（P）。
- page=142; chapter=启动和驾驶; section=通过手机APP启动车辆; subsection=N/A; chunk_id=20a55bcd-5480-58ae-8d7f-9a59228244fa; quote=通过网络远程启动发动机 车辆已锁且挡位处于驻车挡（P）的情况下，登录Lynk & Co App，按 下 图标可以远程启动发动机。
- page=142; chapter=启动和驾驶; section=通过手机APP启动车辆; subsection=N/A; chunk_id=438a348b-736a-5fe4-9567-70177cd779b9; quote=您可以通过Lynk & Co APP使用以下方式启用车辆： ■蓝牙启动：手机在车内时且处于连接状态时，可以通过蓝牙钥匙 启动车辆。 ■远程启动：距离车辆较远时，可以通过网络远程启动发动机。
- page=142; chapter=启动和驾驶; section=通过手机APP启动车辆; subsection=N/A; chunk_id=08966431-e662-58bd-b296-8130dfe538e4; quote=□您可以在冬季寒冷条件下，远程启动发动机，提前对发动机预热 （暖机）。
- page=142; chapter=启动和驾驶; section=通过手机APP启动车辆; subsection=N/A; chunk_id=d13c158f-d3f5-539e-b042-5828ab507c5d; quote=出现以下任一情况时，无法通过蓝牙钥匙启动车辆： □燃油油位较低。

**Deterministic checks:**

- answer_non_empty: True
- must_include_term_coverage: 0.8889
- matched_must_include_terms: 驻车挡; 冷却液液位较低; 燃油油位较低; 车内有遥控钥匙; 网络信号丢失; 机舱盖; 车门未锁定; 维修模式
- missing_must_include_terms: 发动机故障
- forbidden_term_hits: N/A
- evidence_structure_hit: False
- expected_section_hit: True
- expected_subsection_hit: False
- insufficient_evidence_behavior: N/A
- internal_reference_leak: False

**Must include points:** 挡位不在驻车挡时无法启动; 冷却液液位较低时无法启动; 燃油油位较低时无法启动; 车内有遥控钥匙时无法启动; 网络信号丢失时无法启动; 机舱盖或车门未锁定时无法启动; 发动机出现故障时无法启动; 车辆处于维修模式时无法启动

**Must not claim:** 不得把这些禁止条件描述成远程启动的操作步骤

**Critical warning points:** N/A

**Human review:**

- Groundedness: TODO / NOT REVIEWED
- Correctness: TODO / NOT REVIEWED
- Completeness: TODO / NOT REVIEWED
- Condition Handling: TODO / NOT REVIEWED
- Safety Preservation: N/A
- Unsupported claim: TODO / NOT REVIEWED
- Critical safety omission: TODO / NOT REVIEWED
- Notes: TODO / NOT REVIEWED

**Elapsed seconds:** 7.9395

### epb_auto_subsection_answer_001

**Question:** EPB AUTO功能开启后，车辆静止并熄火时会怎样？

**Answer type:** condition

**Source case:** epb_enable_release_001

**Raw answer:**

当EPB AUTO功能开启后，如果您在车辆处于静止状态时将车辆熄火，车辆将自动启用电子驻车制动（EPB）。请参考以下步骤：

1. 确认车辆已经处于静止状态。
2. 将挡位切换至驻车挡（P）。
3. 激活EPB电子驻车系统。
4. 短按START/STOP按钮，使车辆熄火。

此时，EPB将自动启用，以确保车辆在熄火后保持静止状态。请务必注意车辆周边环境，以防止溜车危险。

**Final answer:**

当EPB AUTO功能开启后，如果您在车辆处于静止状态时将车辆熄火，车辆将自动启用电子驻车制动（EPB）。请参考以下步骤： 1. 确认车辆已经处于静止状态。
2. 将挡位切换至驻车挡（P）。
3. 激活EPB电子驻车系统。
4. 短按START/STOP按钮，使车辆熄火。 此时，EPB将自动启用，以确保车辆在熄火后保持静止状态。请务必注意车辆周边环境，以防止溜车危险。

**Prompt Evidence:**

- E1; order=1; chunk_id=09c8e7d1-63a4-528a-9879-290353842d7f; page=158; chapter=启动和驾驶; section=电子驻车制动（EPB）; subsection=EPB AUTO功能; heading_path=启动和驾驶 > 电子驻车制动（EPB） > EPB AUTO功能; content_type=procedure; truncated=False; original_text_chars=95; prompt_text_chars=95

EPB AUTO功能开启后，如果您在车辆处于静止状态时将车辆熄火，
车辆将自动启用EPB。
在中央显示屏中点击
-车辆设置-其他进入其他设置界面。
01 点击开启/关闭EPB AUTO功能。

- E2; order=2; chunk_id=a85aeb24-8e45-51dc-bcb6-4471a943e603; page=158; chapter=启动和驾驶; section=电子驻车制动（EPB）; subsection=熄火时解除电子驻车制动（EPB）; heading_path=启动和驾驶 > 电子驻车制动（EPB） > 熄火时解除电子驻车制动（EPB）; content_type=procedure; truncated=False; original_text_chars=273; prompt_text_chars=273

熄火时解除电子驻车制动（EPB）
在一些特殊情况下（比如洗车或牵引车辆），需要在车辆熄火后，让
EPB保持释放状态，您可以通过以下任一方式实现该功能：
■在中央显示屏上关闭EPB AUTO功能。在车辆启动状态下，踩住
制动踏板，将变速器挡位切换至N挡，再按下EPB开关，将EPB切
换至释放状态，长按START/STOP按钮使车辆熄火。
■车辆熄火状态下，不踩制动踏板，长按START/STOP按钮7 秒，
待车辆完成自检后，踩住制动踏板，将变速器切换至N挡，再按
下EPB开关，将EPB切换至释放状态，长按START/STOP按钮使车
辆下电。

- E3; order=3; chunk_id=0e27168b-0251-52cb-bc66-b34b15e45968; page=144; chapter=启动和驾驶; section=车辆熄火; subsection=N/A; heading_path=启动和驾驶 > 车辆熄火; content_type=procedure; truncated=False; original_text_chars=70; prompt_text_chars=70

1 确认车辆已经处于静止状态。
2 将挡位切换至驻车挡（P）。
3 激活EPB电子驻车系统。
4 短按START/STOP按钮，使车辆熄火。

- E4; order=4; chunk_id=a485ba75-07d4-5a0d-9722-249ce1b12c75; page=157; chapter=启动和驾驶; section=电子驻车制动（EPB）; subsection=启用电子驻车制动（EPB）; heading_path=启动和驾驶 > 电子驻车制动（EPB） > 启用电子驻车制动（EPB）; content_type=normal; truncated=False; original_text_chars=73; prompt_text_chars=73

启用电子驻车制动（EPB）
当车辆处于静止状态时，沿箭头方向拉起EPB开关，启用EPB功能。启
用EPB功能后，仪表显示屏点亮红色EPB
指示灯。

- E5; order=5; chunk_id=cf544339-bbf7-5bf3-a971-197c7972f832; page=159; chapter=启动和驾驶; section=电子驻车制动（EPB）; subsection=熄火时解除电子驻车制动（EPB）; heading_path=启动和驾驶 > 电子驻车制动（EPB） > 熄火时解除电子驻车制动（EPB）; content_type=warning; truncated=False; original_text_chars=50; prompt_text_chars=50

熄火时解除电子驻车制动（EPB）
警告
■在EPB处于释放状态时，应注意车辆周边环境，防止溜车危险。

**Citations:**

- page=158; chapter=启动和驾驶; section=电子驻车制动（EPB）; subsection=N/A; chunk_id=09c8e7d1-63a4-528a-9879-290353842d7f; quote=EPB AUTO功能开启后，如果您在车辆处于静止状态时将车辆熄火， 车辆将自动启用EPB。
- page=158; chapter=启动和驾驶; section=电子驻车制动（EPB）; subsection=N/A; chunk_id=a85aeb24-8e45-51dc-bcb6-4471a943e603; quote=熄火时解除电子驻车制动（EPB） 在一些特殊情况下（比如洗车或牵引车辆），需要在车辆熄火后，让 EPB保持释放状态，您可以通过以下任一方式实现该功能： ■在中央显示屏上关闭EPB AUTO功能。
- page=144; chapter=启动和驾驶; section=车辆熄火; subsection=N/A; chunk_id=0e27168b-0251-52cb-bc66-b34b15e45968; quote=1 确认车辆已经处于静止状态。
- page=157; chapter=启动和驾驶; section=电子驻车制动（EPB）; subsection=N/A; chunk_id=a485ba75-07d4-5a0d-9722-249ce1b12c75; quote=启用电子驻车制动（EPB） 当车辆处于静止状态时，沿箭头方向拉起EPB开关，启用EPB功能。
- page=159; chapter=启动和驾驶; section=电子驻车制动（EPB）; subsection=N/A; chunk_id=cf544339-bbf7-5bf3-a971-197c7972f832; quote=熄火时解除电子驻车制动（EPB） 警告 ■在EPB处于释放状态时，应注意车辆周边环境，防止溜车危险。

**Deterministic checks:**

- answer_non_empty: True
- must_include_term_coverage: 0.7500
- matched_must_include_terms: EPB AUTO; 静止; 熄火
- missing_must_include_terms: 自动启用EPB
- forbidden_term_hits: N/A
- evidence_structure_hit: False
- expected_section_hit: True
- expected_subsection_hit: False
- insufficient_evidence_behavior: N/A
- internal_reference_leak: False

**Must include points:** 说明该结论以EPB AUTO已开启为条件; 车辆处于静止状态并熄火时自动启用EPB

**Must not claim:** 不得声称未开启EPB AUTO时也必然按相同方式自动启用

**Critical warning points:** N/A

**Human review:**

- Groundedness: TODO / NOT REVIEWED
- Correctness: TODO / NOT REVIEWED
- Completeness: TODO / NOT REVIEWED
- Condition Handling: TODO / NOT REVIEWED
- Safety Preservation: N/A
- Unsupported claim: TODO / NOT REVIEWED
- Critical safety omission: TODO / NOT REVIEWED
- Notes: TODO / NOT REVIEWED

**Elapsed seconds:** 7.7818

### epb_poweroff_release_answer_001

**Question:** 在洗车或牵引车辆等特殊情况下，车辆熄火后如何让EPB保持释放？

**Answer type:** condition

**Source case:** epb_enable_release_001

**Raw answer:**

在洗车或牵引车辆等特殊情况下，车辆熄火后，您可以通过以下任一方式让EPB保持释放状态：

1. 在车辆启动状态下，踩住制动踏板，将变速器挡位切换至N挡，再按下EPB开关，将EPB切换至释放状态，长按START/STOP按钮使车辆熄火。
2. 车辆熄火状态下，不踩制动踏板，长按START/STOP按钮7秒，待车辆完成自检后，踩住制动踏板，将变速器切换至N挡，再按下EPB开关，将EPB切换至释放状态，长按START/STOP按钮使车辆下电。

请注意，在EPB处于释放状态时，应时刻注意车辆周边环境，防止溜车危险。

**Final answer:**

在洗车或牵引车辆等特殊情况下，车辆熄火后，您可以通过以下任一方式让EPB保持释放状态： 1. 在车辆启动状态下，踩住制动踏板，将变速器挡位切换至N挡，再按下EPB开关，将EPB切换至释放状态，长按START/STOP按钮使车辆熄火。
2. 车辆熄火状态下，不踩制动踏板，长按START/STOP按钮7秒，待车辆完成自检后，踩住制动踏板，将变速器切换至N挡，再按下EPB开关，将EPB切换至释放状态，长按START/STOP按钮使车辆下电。 请注意，在EPB处于释放状态时，应时刻注意车辆周边环境，防止溜车危险。

**Prompt Evidence:**

- E1; order=1; chunk_id=a85aeb24-8e45-51dc-bcb6-4471a943e603; page=158; chapter=启动和驾驶; section=电子驻车制动（EPB）; subsection=熄火时解除电子驻车制动（EPB）; heading_path=启动和驾驶 > 电子驻车制动（EPB） > 熄火时解除电子驻车制动（EPB）; content_type=procedure; truncated=False; original_text_chars=273; prompt_text_chars=273

熄火时解除电子驻车制动（EPB）
在一些特殊情况下（比如洗车或牵引车辆），需要在车辆熄火后，让
EPB保持释放状态，您可以通过以下任一方式实现该功能：
■在中央显示屏上关闭EPB AUTO功能。在车辆启动状态下，踩住
制动踏板，将变速器挡位切换至N挡，再按下EPB开关，将EPB切
换至释放状态，长按START/STOP按钮使车辆熄火。
■车辆熄火状态下，不踩制动踏板，长按START/STOP按钮7 秒，
待车辆完成自检后，踩住制动踏板，将变速器切换至N挡，再按
下EPB开关，将EPB切换至释放状态，长按START/STOP按钮使车
辆下电。

- E2; order=2; chunk_id=8da2d761-264d-5091-be3c-ddd0742fe332; page=338; chapter=紧急情况下; section=牵引车辆; subsection=牵引方式; heading_path=紧急情况下 > 牵引车辆 > 牵引方式; content_type=procedure; truncated=False; original_text_chars=323; prompt_text_chars=323

牵引方式
01 将车辆放置在平板拖车上——推荐方式。
02车辆前轮抬起，后轮放置在小拖车上（离地）——推荐方式。
03以后轮滚动方式牵引——错误方式。
04抬起前车体/底盘部分，而非车轮——错误方式。
05抬起后车体/底盘部分，而非车轮——错误方式。
06刚性拖拽——错误方式。
车辆牵引至平板拖车前，先将变速器挂入空挡（N）并解除EPB功
能。
1 在中央显示屏中点击
-车辆设置-其他，进入其他设置界面，关
闭EPB AUTO功能。
2 踩下制动踏板，将变速器挂入空挡（N）。
3 长按点火开关，熄火车辆。
4 牵引车辆至平板拖车。
5 车辆被牵引至平板拖车后，为确保车辆驻车安全性，请将变速器
挂入驻车挡（P）并启用电子驻车制动（EPB）。

- E3; order=3; chunk_id=09c8e7d1-63a4-528a-9879-290353842d7f; page=158; chapter=启动和驾驶; section=电子驻车制动（EPB）; subsection=EPB AUTO功能; heading_path=启动和驾驶 > 电子驻车制动（EPB） > EPB AUTO功能; content_type=procedure; truncated=False; original_text_chars=95; prompt_text_chars=95

EPB AUTO功能开启后，如果您在车辆处于静止状态时将车辆熄火，
车辆将自动启用EPB。
在中央显示屏中点击
-车辆设置-其他进入其他设置界面。
01 点击开启/关闭EPB AUTO功能。

- E4; order=4; chunk_id=cdf9514a-7c8e-5d2f-9dc2-7dc6595ce82d; page=338; chapter=紧急情况下; section=牵引车辆; subsection=牵引方式; heading_path=紧急情况下 > 牵引车辆 > 牵引方式; content_type=note; truncated=False; original_text_chars=38; prompt_text_chars=38

牵引方式
说明！
□挂入空挡（N）并解除EPB仅用于车辆牵引至平板拖车过程。

- E5; order=5; chunk_id=cf544339-bbf7-5bf3-a971-197c7972f832; page=159; chapter=启动和驾驶; section=电子驻车制动（EPB）; subsection=熄火时解除电子驻车制动（EPB）; heading_path=启动和驾驶 > 电子驻车制动（EPB） > 熄火时解除电子驻车制动（EPB）; content_type=warning; truncated=False; original_text_chars=50; prompt_text_chars=50

熄火时解除电子驻车制动（EPB）
警告
■在EPB处于释放状态时，应注意车辆周边环境，防止溜车危险。

**Citations:**

- page=158; chapter=启动和驾驶; section=电子驻车制动（EPB）; subsection=N/A; chunk_id=a85aeb24-8e45-51dc-bcb6-4471a943e603; quote=熄火时解除电子驻车制动（EPB） 在一些特殊情况下（比如洗车或牵引车辆），需要在车辆熄火后，让 EPB保持释放状态，您可以通过以下任一方式实现该功能： ■在中央显示屏上关闭EPB AUTO功能。
- page=338; chapter=紧急情况下; section=牵引车辆; subsection=N/A; chunk_id=8da2d761-264d-5091-be3c-ddd0742fe332; quote=5 车辆被牵引至平板拖车后，为确保车辆驻车安全性，请将变速器 挂入驻车挡（P）并启用电子驻车制动（EPB）。
- page=158; chapter=启动和驾驶; section=电子驻车制动（EPB）; subsection=N/A; chunk_id=09c8e7d1-63a4-528a-9879-290353842d7f; quote=EPB AUTO功能开启后，如果您在车辆处于静止状态时将车辆熄火， 车辆将自动启用EPB。
- page=338; chapter=紧急情况下; section=牵引车辆; subsection=N/A; chunk_id=cdf9514a-7c8e-5d2f-9dc2-7dc6595ce82d; quote=□挂入空挡（N）并解除EPB仅用于车辆牵引至平板拖车过程。
- page=159; chapter=启动和驾驶; section=电子驻车制动（EPB）; subsection=N/A; chunk_id=cf544339-bbf7-5bf3-a971-197c7972f832; quote=熄火时解除电子驻车制动（EPB） 警告 ■在EPB处于释放状态时，应注意车辆周边环境，防止溜车危险。

**Deterministic checks:**

- answer_non_empty: True
- must_include_term_coverage: 1.0000
- matched_must_include_terms: N挡; 制动踏板; EPB开关; START/STOP
- missing_must_include_terms: N/A
- forbidden_term_hits: N/A
- evidence_structure_hit: False
- expected_section_hit: True
- expected_subsection_hit: False
- insufficient_evidence_behavior: N/A
- internal_reference_leak: False

**Must include points:** 说明该操作适用于洗车或牵引等特殊情况; 说明可关闭EPB AUTO并在车辆启动状态下完成N挡和释放操作; 说明车辆熄火状态下的另一种操作路径; 提醒EPB释放时防止车辆溜车

**Must not claim:** 不得把特殊情况下保持释放描述成一般驻车规则; 不得遗漏EPB释放后的溜车风险

**Critical warning points:** EPB处于释放状态时必须注意周边环境并防止溜车

**Human review:**

- Groundedness: TODO / NOT REVIEWED
- Correctness: TODO / NOT REVIEWED
- Completeness: TODO / NOT REVIEWED
- Condition Handling: TODO / NOT REVIEWED
- Safety Preservation: TODO / NOT REVIEWED
- Unsupported claim: TODO / NOT REVIEWED
- Critical safety omission: TODO / NOT REVIEWED
- Notes: TODO / NOT REVIEWED

**Elapsed seconds:** 9.7866

### charging_led_list_answer_001

**Question:** 充电接口 LED 指示灯不同颜色分别表示什么状态？

**Answer type:** explanation

**Source case:** charging_led_states_001

**Raw answer:**

充电接口LED指示灯的不同颜色分别表示以下状态：

- 蓝色常亮（2分钟后熄灭）：表示预约充电。
- 蓝色闪烁：表示对外放电。
- 绿色闪烁：表示充电中。
- 绿色常亮：表示充电完成。
- 绿-绿-红依次闪烁：表示充电中电子锁故障。
- 红色常亮：表示充电故障。
- 橙色常亮：表示充电预加热中。
- 橙-橙-红依次闪烁：表示充电预加热中电子锁故障。

请注意，如果充电接口插座指示灯红色报警，请拔出充电枪并锁止车辆，等待车辆休眠后再进行充电操作。若再次尝试红色指示灯还是持续点亮，请联系Lynk & Co领克中心寻求帮助。

**Final answer:**

充电接口LED指示灯的不同颜色分别表示以下状态： - 蓝色常亮（2分钟后熄灭）：表示预约充电。
- 蓝色闪烁：表示对外放电。
- 绿色闪烁：表示充电中。
- 绿色常亮：表示充电完成。
- 绿-绿-红依次闪烁：表示充电中电子锁故障。
- 红色常亮：表示充电故障。
- 橙色常亮：表示充电预加热中。
- 橙-橙-红依次闪烁：表示充电预加热中电子锁故障。 请注意，如果充电接口插座指示灯红色报警，请拔出充电枪并锁止车辆，等待车辆休眠后再进行充电操作。若再次尝试红色指示灯还是持续点亮，请联系Lynk & Co领克中心寻求帮助。

**Prompt Evidence:**

- E1; order=1; chunk_id=e4810a19-cc6a-5fdc-ac80-8c315f7050ff; page=74; chapter=仪表和灯光; section=指示灯和警告灯; subsection=指示灯图标; heading_path=仪表和灯光 > 指示灯和警告灯 > 指示灯图标; content_type=procedure; truncated=False; original_text_chars=609; prompt_text_chars=609

指示灯图标
信息/通知用黄色显示：此信息指示灯点亮，同时仪表显
示屏上出现对应文本信息。该指示灯也可能会与其他图标
一同点亮。
READY指示灯：车辆准备就绪时，该指示灯点亮。
转向指示灯：拨动转向指示灯开关时，对应的
指示灯闪烁。打开危险警告灯开关时，两侧转
向指示灯均闪烁。
近光灯指示灯：打开近光灯时，该指示灯点亮。
远光灯指示灯：打开远光灯时，该指示灯点亮。
智能远近光控制开启指示灯：打开智能远近光控制时，该
指示灯点亮。
后雾灯指示灯：打开后雾灯时，该指示灯点亮。
位置灯指示灯：打开位置灯时，该指示灯点亮。
泊车紧急制动指示灯：泊车紧急制动激活时，该指示灯点
亮。
车道辅助系统启用指示灯：车道辅助系统启用时，该指示
灯点亮。
低速行人提示音功能关闭指示灯：低速行人提示音功能关
闭时，该指示灯点亮。
自动驻车系统指示灯：激活自动驻车系统时，该指示灯点
亮。
盲点监测系统指示灯：盲点监测系统工作时，该指示灯点
亮。
车身稳定控制系统关闭指示灯：车身稳定控制系统关闭
时，该指示灯点亮。
陡坡缓降系统指示灯：陡坡缓降系统开启并未
激活时，白色指示灯点亮；激活后，绿色指示
灯点亮。
外部充电连接警告指示灯：外部充电电缆连接成功后，该
指示灯点亮。
动力电池电量低指示灯：动力电池电量不足时，该指示灯
点亮。
功率限制指示灯：车辆功率受限制时，该指示灯点亮。
燃油液位低指示灯：燃油液位低时，该指示灯点亮。

- E2; order=2; chunk_id=adaf7b26-e2fc-54d2-b885-d57a0bbb39c4; page=292; chapter=高压系统; section=车载充电设备充电; subsection=充电接口灯光指示; heading_path=高压系统 > 车载充电设备充电 > 充电接口灯光指示; content_type=normal; truncated=False; original_text_chars=184; prompt_text_chars=184

充电接口灯光指示
车辆充电输入插座配有LED指示灯，显示充电状态。
LED指示灯根据不同的充电状态显示不同的颜色。
蓝色常亮（2 分钟后熄灭）——预约充电。
蓝色闪烁——对外放电。
绿色闪烁——充电中。
绿色常亮——充电完成。
绿-绿-红依次闪烁——充电中电子锁故障。
红色常亮——充电故障。
橙色常亮——充电预加热中。
橙-橙-红依次闪烁——充电预加热中电子锁故障。

- E3; order=3; chunk_id=ab4f7f52-3ba3-58e1-98f7-122e1488f707; page=293; chapter=高压系统; section=车载充电设备充电; subsection=充电接口灯光指示; heading_path=高压系统 > 车载充电设备充电 > 充电接口灯光指示; content_type=note; truncated=False; original_text_chars=115; prompt_text_chars=115

充电接口灯光指示
说明！
□充电误操作会产生充电故障，充电接口插座指示灯红色报警，出
现此情况请拔出充电枪，并锁止车辆，等待车辆休眠后再进行充
电操作。若再次尝试红色指示灯还是持续点亮，请联系Lynk & Co
领克中心寻求帮助。

- E4; order=4; chunk_id=a6b45c33-c871-59cd-b2bd-1100c75935ca; page=289; chapter=高压系统; section=车载充电设备充电; subsection=N/A; heading_path=高压系统 > 车载充电设备充电; content_type=normal; truncated=False; original_text_chars=55; prompt_text_chars=55

车载充电设备存放在后备厢内。
充电时，仪表显示屏显示估计的剩余充电时间，充电接口插座中的
LED指示灯闪绿光。

- E5; order=5; chunk_id=dbb7a4bd-5195-5b3b-a66e-ef318e05b9c8; page=290; chapter=高压系统; section=车载充电设备充电; subsection=控制单元灯光指示; heading_path=高压系统 > 车载充电设备充电 > 控制单元灯光指示; content_type=normal; truncated=False; original_text_chars=33; prompt_text_chars=33

控制单元灯光指示
在车辆充电过程中，控制单元指示灯会显示充电状态。

**Citations:**

- page=74; chapter=仪表和灯光; section=指示灯和警告灯; subsection=N/A; chunk_id=e4810a19-cc6a-5fdc-ac80-8c315f7050ff; quote=外部充电连接警告指示灯：外部充电电缆连接成功后，该 指示灯点亮。
- page=292; chapter=高压系统; section=车载充电设备充电; subsection=N/A; chunk_id=adaf7b26-e2fc-54d2-b885-d57a0bbb39c4; quote=充电接口灯光指示 车辆充电输入插座配有LED指示灯，显示充电状态。
- page=293; chapter=高压系统; section=车载充电设备充电; subsection=N/A; chunk_id=ab4f7f52-3ba3-58e1-98f7-122e1488f707; quote=□充电误操作会产生充电故障，充电接口插座指示灯红色报警，出 现此情况请拔出充电枪，并锁止车辆，等待车辆休眠后再进行充 电操作。
- page=289; chapter=高压系统; section=车载充电设备充电; subsection=N/A; chunk_id=a6b45c33-c871-59cd-b2bd-1100c75935ca; quote=充电时，仪表显示屏显示估计的剩余充电时间，充电接口插座中的 LED指示灯闪绿光。
- page=290; chapter=高压系统; section=车载充电设备充电; subsection=N/A; chunk_id=dbb7a4bd-5195-5b3b-a66e-ef318e05b9c8; quote=控制单元灯光指示 在车辆充电过程中，控制单元指示灯会显示充电状态。

**Deterministic checks:**

- answer_non_empty: True
- must_include_term_coverage: 1.0000
- matched_must_include_terms: 蓝色常亮; 绿色闪烁; 红色常亮; 橙色常亮
- missing_must_include_terms: N/A
- forbidden_term_hits: N/A
- evidence_structure_hit: False
- expected_section_hit: True
- expected_subsection_hit: False
- insufficient_evidence_behavior: N/A
- internal_reference_leak: False

**Must include points:** 蓝色常亮表示预约充电且两分钟后熄灭; 蓝色闪烁表示对外放电; 绿色闪烁和常亮分别表示充电中和充电完成; 绿-绿-红和红色常亮表示对应故障; 橙色常亮及橙-橙-红表示充电预加热相关状态

**Must not claim:** 不得混淆充电中、充电完成、充电故障和预加热状态

**Critical warning points:** N/A

**Human review:**

- Groundedness: TODO / NOT REVIEWED
- Correctness: TODO / NOT REVIEWED
- Completeness: TODO / NOT REVIEWED
- Condition Handling: TODO / NOT REVIEWED
- Safety Preservation: N/A
- Unsupported claim: TODO / NOT REVIEWED
- Critical safety omission: TODO / NOT REVIEWED
- Notes: TODO / NOT REVIEWED

**Elapsed seconds:** 10.5276

### unsupported_voice_brake_calibration_answer_001

**Question:** 手册是否说明如何通过语音命令校准制动系统？

**Answer type:** insufficient_evidence

**Source case:** N/A

**Raw answer:**

我没有在手册中找到可靠依据说明如何通过语音命令校准制动系统。手册中提到了制动系统的故障指示灯和制动防抱死系统的工作状态说明，但没有提及通过语音命令来校准制动系统的内容。

**Final answer:**

我没有在手册中找到可靠依据说明如何通过语音命令校准制动系统。手册中提到了制动系统的故障指示灯和制动防抱死系统的工作状态说明，但没有提及通过语音命令来校准制动系统的内容。

**Prompt Evidence:**

- E1; order=1; chunk_id=e6909eee-285b-54ef-8bef-1acf8c3ecd37; page=156; chapter=启动和驾驶; section=制动系统; subsection=功能状态说明; heading_path=启动和驾驶 > 制动系统 > 功能状态说明; content_type=warning; truncated=False; original_text_chars=55; prompt_text_chars=55

功能状态说明
警告！
■仪表显示制动系统故障指示灯时，请立刻在安全区域停车并联系
Lynk & Co领克中心。

- E2; order=2; chunk_id=7ffe25ff-9b6f-55dc-aac5-47192e9cff3c; page=126; chapter=安全出行; section=语音助手; subsection=中央显示屏语音助手; heading_path=安全出行 > 语音助手 > 中央显示屏语音助手; content_type=procedure; truncated=False; original_text_chars=647; prompt_text_chars=647

中央显示屏语音助手
01 点击人物图标，唤起语音助手功能。
您还可以通过按下方向盘右侧键盘上的
按键，或者说出唤醒词，
等待系统发出提示音。
使用语音命令时，请您遵循以下几点：
■发出命令时，以常速和正常的语调说话。
■口齿清楚，避免使用俚语。
■使用语音助手时，应保持车内安静。
■系统响应过程中可以监听语音命令。
■若想要取消语音命令对话，再次按下方向盘右侧键盘上的
按
键。
■在系统响应时转动音量按钮，调节音量。
在中央显示屏中点击
-座舱体验-声音-系统音量，进入系统音量设
置界面。
01 拖动进度条来调整语音助手音量。
您可以通过在中央显示屏中点击
-我的AI助手-语音，进入语音设置
界面。
01 点击开启/关闭“允许语音唤醒”，关闭“允许语音唤醒”后，
将无法通过语音唤醒语音助手。
02点击设置“声源定位”，设置成“主驾”后，只能识别驾驶员
侧语音指令。
03点击开启/关闭“延长聆听”，开启“延长聆听”后，语音助手
执行完语音指令后，会处于激活状态等待用户输入下一个指
令。若一段时间后，未输入新指令，语音助手将会退出。
04点击开启/关闭“允许One Shot唤醒”，开启“允许One Shot
唤醒”后，无需先唤醒并等待语音助手回复，可连续说唤醒词
和语音指令。
05点击开启/关闭“免唤醒词命令”，开启“免唤醒词命令”后，
可以在不使用唤醒词或其他唤醒指令的情况下，通过语音助手
切换歌曲、拨打电话等。
06语音助手默认唤醒词是嗨，领克，您可以选择或自定义唤醒
词。

- E3; order=3; chunk_id=86d51ecf-273b-5077-8ab1-61898bf44520; page=157; chapter=启动和驾驶; section=制动防抱死系统; subsection=N/A; heading_path=启动和驾驶 > 制动防抱死系统; content_type=note; truncated=False; original_text_chars=112; prompt_text_chars=112

说明！
□在制动过程中，您会感觉到机舱传来连续“咯咯”的声音，同时
感受到制动踏板传来的振动。这是防抱死制动系统工作时引起的
正常现象，而不是故障。
□当防抱死制动系统停止工作时，制动踏板的感觉会恢复到非防抱
死制动的状态。

- E4; order=4; chunk_id=840e869c-4582-5182-85e9-8486ec5815ef; page=126; chapter=安全出行; section=语音助手; subsection=N/A; heading_path=安全出行 > 语音助手; content_type=normal; truncated=False; original_text_chars=57; prompt_text_chars=57

您可以通过语音助手对车辆功能（例如：车窗、天窗、空调等）进行
语音控制。您只需说出您的命令，系统就会帮您完成操作。

- E5; order=5; chunk_id=cac5c819-3a0d-56b6-9ea0-f88da79fc746; page=128; chapter=安全出行; section=语音助手; subsection=中央显示屏语音助手; heading_path=安全出行 > 语音助手 > 中央显示屏语音助手; content_type=note; truncated=False; original_text_chars=190; prompt_text_chars=190

中央显示屏语音助手
说明！
□使用语音助手时请确保车辆网络良好。
□开启车窗、天窗时，风噪可能会干扰语音控制功能正常工作。
□当语音系统检测到用户对话中有含有唤醒词或与唤醒词相近的发
音时，语音系统也可能被激活并发出提示音。
车载12 V电源
通过12 V电源插座，可以给电子设备（例如：音乐播放器、车载冰箱
和移动手机）充电。
前排扶手箱12 V电源插座
后备厢12 V电源插座

**Citations:**

- page=156; chapter=启动和驾驶; section=制动系统; subsection=N/A; chunk_id=e6909eee-285b-54ef-8bef-1acf8c3ecd37; quote=功能状态说明 警告！ ■仪表显示制动系统故障指示灯时，请立刻在安全区域停车并联系 Lynk & Co领克中心。
- page=126; chapter=安全出行; section=语音助手; subsection=N/A; chunk_id=7ffe25ff-9b6f-55dc-aac5-47192e9cff3c; quote=■使用语音助手时，应保持车内安静。 ■系统响应过程中可以监听语音命令。 ■若想要取消语音命令对话，再次按下方向盘右侧键盘上的 按 键。 ■在系统响应时转动音量按钮，调节音量。
- page=157; chapter=启动和驾驶; section=制动防抱死系统; subsection=N/A; chunk_id=86d51ecf-273b-5077-8ab1-61898bf44520; quote=这是防抱死制动系统工作时引起的 正常现象，而不是故障。
- page=126; chapter=安全出行; section=语音助手; subsection=N/A; chunk_id=840e869c-4582-5182-85e9-8486ec5815ef; quote=您可以通过语音助手对车辆功能（例如：车窗、天窗、空调等）进行 语音控制。
- page=128; chapter=安全出行; section=语音助手; subsection=N/A; chunk_id=cac5c819-3a0d-56b6-9ea0-f88da79fc746; quote=中央显示屏语音助手 说明！

**Deterministic checks:**

- answer_non_empty: True
- must_include_term_coverage: N/A
- matched_must_include_terms: N/A
- missing_must_include_terms: N/A
- forbidden_term_hits: N/A
- evidence_structure_hit: N/A
- expected_section_hit: N/A
- expected_subsection_hit: N/A
- insufficient_evidence_behavior: True
- internal_reference_leak: False

**Must include points:** N/A

**Must not claim:** 不得编造通过语音命令校准制动系统的步骤

**Critical warning points:** N/A

**Human review:**

- Groundedness: TODO / NOT REVIEWED
- Correctness: TODO / NOT REVIEWED
- Completeness: TODO / NOT REVIEWED
- Condition Handling: TODO / NOT REVIEWED
- Safety Preservation: N/A
- Unsupported claim: TODO / NOT REVIEWED
- Critical safety omission: TODO / NOT REVIEWED
- Notes: TODO / NOT REVIEWED

**Elapsed seconds:** 5.3959