---
lane: L1+
pr: 96
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | opus (second opinion, via Agent tool, 2回) | - | 0 | 0 | 0 | 2026-09-17T12:47+0900 |
| 独立-1 | general-purpose subagent (read-only, diff-only, 経緯非共有; L1+ 追加観点 (g)(h)+security 込み) | 98c7699 | 0 | 0 | 0 | 2026-09-17T13:10+0900 |
| PR後-1 | GitHub PR reviewer（issue comment、PR 旧#96） | ba590e6 | 1 | 4 | 0 | 2026-09-17T14:00+0900 |
| 独立-2 | general-purpose subagent (read-only, diff-only, 経緯非共有; L1+ 追加観点 (g)(h)+security 込み、対象は ba590e6..460a761 の PR後-1 対応差分) | 460a761 | 0 | 2 | 0 | 2026-09-17T14:20+0900 |
| PR後-2 | GitHub PR reviewer（issue comment、PR 旧#96、head 3fad54c） | 3fad54c | 1 | 2 | 0 | 2026-09-17T16:20+0900 |
| 独立-3 | general-purpose subagent (read-only, diff-only, 経緯非共有; L1+ 追加観点 (g)(h)+security 込み、対象は 3fad54c..7dbcb12 の PR後-2 対応差分) | 7dbcb12 | 0 | 0 | 0 | 2026-09-17T17:05+0900 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 方針メモ | advisory | no | inherited | archived-reference-drift | fixed | requirements-template.md:117 と lint-ac.py:64,261 が退避済みの docs/references-archive/ac-machine-readable-schema.md を、現役でoptionalサポートされる機能（YAML frontmatter機械可読AC）の唯一の詳細schemaとして案内していた（引き継ぎ元セッションの spawn_task による指摘） |
| F2 | 方針メモ | advisory | no | inherited | unused-optional-feature-doc-impl-drift | fixed | X-55/X-64（現役参照と並列に案内される冗長な退避参照の削除）とは異なり本件は唯一の情報源であり単純削除は情報喪失になるため、Opusへ2回セカンドオピニオンを依頼。1回目でC（現状維持）案を得たが、その過程でschema定義（105,118行目）が strict時のid/description必須性を主張する一方、実装（lint-ac.py）はidのみ検証しdescriptionは検証しないというdoc/impl乖離を発見。2回目でD（機能撤去）を推奨された。.steering/*/requirements.md（695件横断）とsession transcript全体でYAML frontmatter実使用0件（テストコード内言及を除く）を実測確認し、ユーザー承認のうえYAML frontmatterによる機械可読AC機能一式（lint-ac.pyのYAML抽出・strict時YAML必須分岐、requirements-template.md/operation-levels.mdの案内、docs/references-archive/ac-machine-readable-schema.md）を撤去した。詳細な方針（7点）はPR本文に記載 |
| G1 | 独立-1 | low | no | inherited | stale-path-in-frozen-snapshot | accepted | changelogは「ac-machine-readable-schema.mdは唯一の参照元だったrequirements-template.md/lint-ac.pyの2ファイルから参照されなくなった」と述べるが、docs/audits/r9-2-requirements-template-anchors.txt:318 と docs/references-archive/requirements-template-pre-r9-2-wave1-original.md:492（いずれも過去時点の凍結スナップショット）にも同パス文字列が残存し、削除後は存在しないファイルへの参照になる。broken-reference-lint/docs-links-validはいずれも対象外でCI検出されない。過去スナップショットは凍結が仕様のため実害は無いと判断し、修正せず受け入れる |
| H1 | PR後-1 | high | yes | self-inflicted | fail-open-guard-skip | fixed | ddffc36 のYAML抽出撤去により、YAML frontmatterのみで AC を定義した requirements.md は req_ids が空集合になり、check_red_evidence_ac_binding の if defined_ac_ids: ガードが無条件でスキップされ、RED Evidence が架空ACを参照してもexit=0で通っていた（main はexit=1）。実機再現の上、requirements_has_yaml_ac_frontmatter() を追加しERROR化して修正（460a761） |
| H2 | PR後-1 | medium | no | self-inflicted | missing-regression-test | fixed | H1のfail-openを固定する回帰テストが無かった。test_yaml_only_ac_frontmatter_does_not_silently_skip_red_evidence_orphan_check を追加（460a761） |
| H3 | PR後-1 | medium | no | self-inflicted | self-conflicting-test-assertion | fixed | H1修正で追加したERRORメッセージに「YAML frontmatter」という文言を意図的に含めたため、既存契約テストの assertNotIn("YAML frontmatter", ...) と自己衝突した。撤去済み実装シンボル（extract_ac_ids_from_yaml_frontmatter・yaml.safe_load等）の不在検査に絞って修正（460a761） |
| H4 | PR後-1 | medium | no | inherited | missing-regression-test | fixed | --strict のWARN→ERROR昇格（未verify AC／RED Evidence AC行欠落）を固定する回帰テストが無かった。test_strict_promotes_unverified_ac_warn_to_error と test_strict_promotes_missing_red_evidence_ac_line_warn_to_error を追加（460a761） |
| H5 | PR後-1 | medium | no | self-inflicted | changelog-accuracy | fixed | changelog.d の User Action Required がH1のfail-open修正後の挙動（ERROR化）を反映していなかった。460a761 の内容に合わせて記述を修正 |
| I1 | 独立-2 | medium | no | self-inflicted | message-formatting-bug | fixed | H1修正で追加したERRORメッセージが隣接文字列リテラルの連結時にスペース抜けで「markdownbullet」と結合表示されていた。スペースを追加し、結合を検知する回帰テストを追加（lint-ac.py:210, test_yaml_frontmatter_migration_error_message_has_no_word_concatenation） |
| I2 | 独立-2 | medium | no | self-inflicted | over-broad-substring-match | fixed | requirements_has_yaml_ac_frontmatter() が frontmatter内の "acceptance_criteria:" を単純な部分文字列一致で判定していたため、YAMLコメント化された旧フィールド（実害の無い記述）でも誤ってERROR（fail-closed方向）になっていた。行頭のキーとしての出現のみを見る正規表現に変更し、回帰テスト test_yaml_frontmatter_detection_ignores_commented_out_field を追加（lint-ac.py:68-81） |
| J1 | PR後-2 | high | yes | self-inflicted | fail-open-guard-skip | fixed | H1修正（requirements_has_yaml_ac_frontmatter による素キー`acceptance_criteria:`検出）は表記依存のため、引用符付きキー（`"acceptance_criteria":`）等の別形式では検出されず、req_idsが空集合のままcheck_red_evidence_ac_bindingのif defined_ac_ids:ガードに戻り、架空AC参照が再びexit=0で通っていた。同クラスタのhigh指摘が2巡連続（460a761→3fad54cの間で解消したはずが別形式で再発）したため、CLAUDE.mdのL1+安全策4に基づき修正を続けずユーザーに線引きを確認（広い側=guard反転 or 狭い側=Known Limitations開示の2択）。ユーザーは広い側を選択。if defined_ac_ids:ガードそのものを撤去し、defined_ac_idsが空集合でもRED Evidence参照ACを全て未定義として扱うよう変更（YAML表記の検出パターン追加は行わない、形式非依存化）。回帰テスト test_red_evidence_orphan_check_fires_even_when_ac_id_format_is_unrecognized を追加 |
| J2 | PR後-2 | medium | no | self-inflicted | pr-body-accuracy | fixed | PR本文の方針メモ3が「実害方向のfail-openにはならない（fail-closed側の劣化に留まる）」という撤去直後（ddffc36時点）の記述のまま残り、その後のfail-open修正（460a761, 3fad54c）を反映していなかった。PR本文を実装の実態に合わせて更新 |
| J3 | PR後-2 | medium | no | inherited | detection-loss-on-partial-migration | deferred | requirements.mdでYAMLとmarkdown bulletが同居する部分移行時、YAML側で定義されたつもりのAC IDはmarkdown側req_idsに含まれないため、未verify警告からもYAML移行ERRORからも検出されず、検出力が実質的に失われる（架空RED参照はmarkdown側AC IDに対してはERRORのまま機能する）。レビュアー自身が「後続でもよい」と明記した対応（acceptance_criteriaが残っていればreq_ids非空でもWARNを出す）のため、本PRでは対応せず後続課題として受け入れる |
| K1 | 独立-3 | - | - | - | - | - | なし |
