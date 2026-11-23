---
type: patch
---

#### Summary

pytest の全量は CI（`plugin-lint`、旧#157）が PR と main への push ごとに回すようになった。それに合わせて、`CONTRIBUTING.md` の必須チェックと `.github/copilot-instructions.md` の PR の前提を、「全量は CI、手元では関係するテストと `validate-plugin.sh`」に揃えた。root `CLAUDE.md` の軽いレーンの手順 3・4・6・7 は 旧#161 で変えていて、CONTRIBUTING の文面だけが取り残されていた（手順 3 が「CONTRIBUTING の項 1 は実行しない」と注記して埋めていたずれを、なくす。追随したので、この注記は外した）。

#### Changed

- `CONTRIBUTING.md` 必須チェック項 1: 見出しを「pytest の全量が通る（CI が回す。手元では関係するテスト）」にし、CI が全量を回すこと、手元で回すのは変更に関係するテストと項 2 の `validate-plugin.sh` であること、マージ前に PR の check で `gdd-plugin` が success かを確かめること（private repo では branch protection の required check を設定できず、CI が赤でもマージは止まらない）、手元で全量を回すのは release 前（項 0）、hooks を local に入れる前、CI が使えないときだけであることを書いた。全量を手元で回すときの手順（`-n auto` など）は残した
- `CONTRIBUTING.md` の「skill を追加する」の手順 6 と「既存テスト」の一覧: 全量のコマンドをそのまま並べていた箇所を、「関係するテストを回す。全量は CI」に揃えた。新規の skill は名前を参照するテストがまだ無いので、手順 6 に、skill 数を固定するテスト（`test_superpowers_differentiation_contract.py`）と skills 本文の語彙を検査するテスト（`test_finding_category_vocabulary_contract.py`）も入れる指示を足した。「hook を追加する」には、関係するテストと、local に入れる前の全量の手順を足した
- `CONTRIBUTING.md` 項 1 の構成: 「契約は `tests/test_*.py` で固定する。full suite が落ちる場合（CI が赤のときを含む）は契約破れを先に直す」の一般規定を、「以下は全量を手元で回すときの手順」の見出しの外（項 1 の先頭側）へ出した（見出しの内側にあった「round ごとの検証は契約テストのみでよい」の重複した 1 文は削った。同じ指示は項 1 の先頭側にある）。手元で全量を回すときだけの話に読めないようにするため
- `references/gdd-self-development.md` の「テストの階層」: 「フルスイートは completion-check と pre-PR の 2 回だけ」を、「フルスイートは CI が PR ごとに回す。手元では completion-check と pre-PR でも対応する契約テストだけを回す」に直し、「CI は PR を作った後の push（と main への push）で走るので、フルの結果は PR 作成後に `gdd-plugin` の success で確かめる」を足した。項 1 が指す正本が、項 1 の新しい規定と逆のことを言っていたため
- root `CLAUDE.md` の軽いレーンの手順 3: 「CONTRIBUTING の項 1 は実行しない（文面の追随は次の PR）」の注記を外し、「CONTRIBUTING の項 1 も同じ分担を書いている」に直した。追随済みなので、注記が事実と食い違うため。あわせて、ローカルで全量を回してよい場合に「release 前」「hooks を local に入れる前」を足した（`references/gdd-self-development.md` の規定と、列挙を揃えるため）
- `.github/copilot-instructions.md` の「PR の前提」: 全量と `validate-plugin.sh` が「通っている前提か」を PR 内の実行結果で見る指示を、「CI の `gdd-plugin` が success か、PR 本文に run の URL や結果があるか」を見る指示に変えた（全量をローカルで回した結果は求めない）

#### Affected Files

- `plugins/gate-driven-development/CONTRIBUTING.md`
- `plugins/gate-driven-development/references/gdd-self-development.md`
- `.github/copilot-instructions.md`
- `CLAUDE.md`

#### User Action Required

- 利用者の操作は不要

#### Known Limitations

- release 前の全量（`CONTRIBUTING.md` 項 0 と `docs/VERSIONING.md` のリリース手順 6〈140 行目〉）は、release 時の確認なので変えていない。手元で全量を回す前提のまま残る（`docs/VERSIONING.md` の 47 行目は v1.0 昇格基準の「CI 安定」で、手元で全量を回す前提の記述ではないので対象外）
- 「関係するテスト」の選び方は、CONTRIBUTING には要点（変更したファイルの名前を、拡張子を除いて参照するテストと、足した・変えたテスト）だけを書いた。grep のかけ方と共有部品を変えたときの範囲の詳細は root `CLAUDE.md` の手順 3 にあり、plugin の文書を自己完結させる設計判断として、CONTRIBUTING からは root `CLAUDE.md` を指さない（CONTRIBUTING の「Root CLAUDE.md 独立性」は README・commands・skills・agents・scripts に適用される規則で、CONTRIBUTING 自身は対象外だが、同じ趣旨に合わせた）。`references/gdd-self-development.md` の round 単位の選び方（`tests/test_<対象>_contract.py`、不明なら `-k`）は別の目安で、統一していない。名前の参照で絞るので、間接的な依存は取りこぼす（CI が拾う）
- CI の結果を確かめるのは手順であり、仕組みでは強制されない（branch protection を設定できない）

#### Validation / Eval Impact

- Affected Files の 4 ファイルの文言だけの変更で、判定ロジック・hook・テストは変えていない
- 関係するテスト: `grep -rlE 'CONTRIBUTING|copilot-instructions|gdd-self-development|CLAUDE|changelog' plugins/gate-driven-development/tests/ --include='test_*.py'` の結果を回す
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- 全量は CI（`gdd-plugin`）が回す
