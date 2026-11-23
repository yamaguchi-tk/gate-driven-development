---
type: minor
---

#### Summary

ユーザー引き継ぎ「requirements-template.md/lint-ac.py の退避済み archive 参照を修正」を受けて調査したところ、`references/requirements-template.md` と `scripts/lint-ac.py` が退避済みの `docs/references-archive/ac-machine-readable-schema.md` を、YAML frontmatter による機械可読 AC（optional 機能）の唯一の詳細schemaとして案内していた。X-55/X-64（現役参照と並列に案内される冗長な退避参照を削除するパターン）とは異なり単純削除は情報喪失になるため、Opus（claude-opus-5）へ2回セカンドオピニオンを依頼して検討した結果、schema 定義（`docs/references-archive/ac-machine-readable-schema.md` 105/118行目）が「strict時にid/descriptionの必須性を検査する」と書いている一方、実装（`scripts/lint-ac.py`）は`id`のみ検証し`description`は検証していないというドキュメントと実装の乖離を発見した。

実 worktree の `.steering/*/requirements.md`（695件横断）と session transcript 全体を実測したところ、YAML frontmatter による機械可読AC機能の実使用は0件（テストコード内の言及を除く）だった。この実測結果と YAGNI 原則（`CLAUDE.md`）に基づき、単純な参照修正ではなく未使用機能自体を撤去する方針とした（ユーザー承認済み、方針メモは `review-log/20260917-x65-ac-yaml-frontmatter-removal.md` 参照）。

PR 旧#96 のレビューで、当初案（req_ids が空になった場合は無条件で INFO 止まり）に HIGH の fail-open 指摘を受けた: 未移行の YAML frontmatter だけで AC を定義した requirements.md が RED Evidence の架空 AC 検査（`check_red_evidence_ac_binding` の `if defined_ac_ids:` ガード）を無言で素通りし、main では exit=1 だった入力が exit=0 になっていた（実機再現・修正済み。詳細は「Fixed」節）。

#### Removed

- `scripts/lint-ac.py`: YAML frontmatter（`acceptance_criteria`）抽出ロジック（`extract_ac_ids_from_yaml_frontmatter` 関数）と、`extract_ac_ids_from_requirements` の YAML 分岐・`source` 判別値を削除し、markdown bullet 抽出のみに単純化した。`--strict` 時の「machine-readable AC required（YAML必須）」エラー分岐を削除した（`--strict` フラグ自体と、他の意味＝WARN→ERROR昇格は維持）
- `references/requirements-template.md`: 「機械可読 schema（optional）」bullet を削除
- `references/operation-levels.md`: strict レベル詳細節および比較表から machine-readable AC / YAML frontmatter の案内を削除
- `docs/references-archive/ac-machine-readable-schema.md`: ファイルごと削除（唯一の参照元だった上記2ファイルから参照されなくなったため）
- `tests/checks/skill-body-budget.sh`: 削除したファイルの許可リストエントリを削除

#### Fixed

- `scripts/lint-ac.py`: `requirements_has_yaml_ac_frontmatter()` を追加し、`req_ids` が空でも requirements.md が未移行の YAML frontmatter（`acceptance_criteria`）を含む場合は ERROR にして `has_error = True` にする（PR 旧#96 レビュー指摘 HIGH の fail-open 修正）。「AC が本当に存在しない」（early planning）場合と区別し、後者のみ従来通り INFO のまま扱う
- `scripts/lint-ac.py`: 上記 ERROR メッセージが隣接文字列リテラルの連結時にスペース抜けで「markdownbullet」と結合表示されていた誤りを修正（独立レビュー指摘 medium）。また `requirements_has_yaml_ac_frontmatter()` の判定が単純な部分文字列一致だったため、YAML コメント化された旧フィールド（実害の無い記述）でも誤って ERROR（fail-closed 方向）になっていた問題を、行頭のキーとしての出現のみを見る正規表現判定に変更して修正（独立レビュー指摘 medium）
- `scripts/lint-ac.py`: `requirements_has_yaml_ac_frontmatter()` による素キー（`acceptance_criteria:`）検出は表記依存のため、引用符付きキー（`"acceptance_criteria":`）等の別形式では検出漏れし、`req_ids` が空集合のまま `check_red_evidence_ac_binding` の `if defined_ac_ids:` ガードに戻って架空 AC 参照が再び exit=0 で通っていた（fail-open クラスタが 2 巡連続で再発、PR 旧#96 レビュー指摘 HIGH）。個別の表記パターンを検出リストに追加するのではなく、`defined_ac_ids` が空集合でも RED Evidence の参照 AC を全て未定義として扱うよう `if defined_ac_ids:` ガード自体を撤去し、YAML の表記に依存しない形でこの fail-open クラスタを閉じた（ユーザー承認: 同じ入力空間を閉じる範囲では広い側を既定にする方針）
- `tests/test_lint_ac_id_grammar_contract.py`: `extract_ac_ids_from_requirements` の戻り値が2-tupleに変わったことに合わせて4箇所の呼び出しを更新。(1) AC未定義の requirements.md が `--strict` でも exit=0・INFO のままであること、(2) YAML frontmatterのみのrequirements.mdでRED Evidenceが架空ACを参照した場合にexit=1になること（PR 旧#96 HIGH指摘の再現・固定テスト）、(3)(4) `--strict` のWARN→ERROR昇格（未verify AC／RED Evidence AC行欠落）が両方向とも機能すること、を固定する回帰テストを追加した
- `tests/test_p0_p1_operational_hardening_contract.py`: 旧 `test_ac_machine_readable_schema_is_strict_for_high_risk_standard_tasks`（YAML必須を要求する契約）を、YAML frontmatter 撤去後の状態（案内文言の不在・schema ファイルの不在・markdown bulletのみでも strict が exit=0）を固定する契約テストに置き換えた。`lint-ac.py` 自体は移行ERRORメッセージで意図的に「YAML frontmatter」という文言を保持するため、同ファイルへの禁止語検査は撤去済み実装（抽出関数・`yaml.safe_load`・strict必須文言）の不在に絞った（PR 旧#96 レビュー指摘 MEDIUM）

#### Affected Files

- `scripts/lint-ac.py`
- `references/requirements-template.md`
- `references/operation-levels.md`
- `docs/references-archive/ac-machine-readable-schema.md`（削除）
- `tests/checks/skill-body-budget.sh`
- `tests/test_lint_ac_id_grammar_contract.py`
- `tests/test_p0_p1_operational_hardening_contract.py`

#### User Action Required

実測で実使用0件を確認済みだが、万一 YAML frontmatter（`acceptance_criteria`）だけで AC を定義した requirements.md が存在する場合は、`lint-ac.py` が ERROR（exit=1）を出すようになる。素キー（`acceptance_criteria:`）を検出できた場合は「この形式は撤去されました。markdown bullet 形式へ移行してください」の移行メッセージを出す。引用符付きキー等の別表記で検出できない場合でも、RED Evidence が参照する AC は `req_ids` が空集合である以上すべて未定義（架空 AC）として ERROR になるため、いずれの表記でも markdown bullet 形式（`- AC-1: ...`）への移行が必要になる。`--strict` の他の意味（WARN→ERROR昇格、tasklist未verify検出、RED Evidence AC ID binding検査等）や、strict運用レベルの他5要件（security reviewer常時起動・completion reviewer quick以上・Verification記録notes必須・タスクサイズ降格禁止・adr.md推奨）には影響しない。

#### Known Limitations

- ドキュメントと実装の乖離（schema定義がid/description両方の必須性を主張するが実装はidのみ検証）は、機能撤去により本PRのスコープからは消滅した。別課題として、docs/references-archive/ への現役ファイルからの参照全般（今回の2件以外に9箇所現存）を許容する基準を README に明文化し、許可リスト形式のcontract testを追加する改善は、本PRでは対応せず別PRの後続課題とする
- 削除した `docs/references-archive/ac-machine-readable-schema.md` へのパス文字列は、`docs/audits/r9-2-requirements-template-anchors.txt:318` と `docs/references-archive/requirements-template-pre-r9-2-wave1-original.md:492`（いずれも凍結済み過去スナップショット）に残存する。`broken-reference-lint`/`docs-links-valid` の対象外で実害は無いと判断し、修正せず受け入れる（独立レビュー G1、PR 旧#96）
- requirements.md で YAML frontmatter（`acceptance_criteria`）と markdown bullet が同居する部分移行時、YAML 側で定義したつもりの AC ID は markdown 側 `req_ids` に含まれないため、未verify警告からも移行ERRORからも検出されず検出力が失われる（markdown 側で定義された AC への架空 RED 参照は従来どおり ERROR になる）。PR 旧#96 レビュー指摘（MEDIUM、レビュアー自身が「後続でもよい」と明記）のため、本PRでは対応せず後続課題として受け入れる

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
