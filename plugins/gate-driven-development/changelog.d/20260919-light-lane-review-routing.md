---
type: patch
---

#### Summary

- 軽いレーン（本リポジトリの開発手順）の review-log に、この PR で直さない指摘を表す `対応` の値を 3 つ足した。`re-reported`（前の巡で記録した指摘の再掲）、`next-pr`（次の PR で直す）、`out-of-diff`（差分の外で対応しない）。どれも `## 指摘` に行を残したまま `## 巡` の high・medium に数えず、`review-log-present.sh` の件数照合もこれらを除いて数える。`deferred`・`accepted` は今までどおり数える
- 利用者の `/gdd-dev` の挙動は変わらない（`review-log/` は本リポジトリの開発記録で、配布物の外にある）

#### Changed

- `tests/checks/review-log-present.sh`: `TAIOU_VALUES` に `re-reported`・`next-pr`・`out-of-diff` を足し、その行を `## 巡` の high・medium の照合から外した。これらの行も、severity・実害・自己起因・クラスタ・要約の値域は今までどおり検査する。`実害` が `yes` の行にこれらの値を付けると落とす（実害クラスは件数から外せない）

#### Added

- `tests/test_review_log_present.py`: 3 つの値を件数から外すこと、それを数えた宣言が落ちること、`実害=yes` の行には付けられないこと、再掲だけの巡は 0 を宣言すること、それらの行の値域検査、未知の `対応` の値が落ちることを固定した。後方互換として、main にある L1・L1+ の review-log（変更前の検査でも通らない 1 本を除く）が新しい検査でそのまま通ることを固定した
- `tests/test_light_lane_review_routing_contract.py`: 件数に入れない 3 つの値（`review-log-present.sh` の `UNCOUNTED_TAIOU_VALUES` は 3 つと一致し、それ以外を含まず、代入は 1 か所で右辺は集合リテラル 1 個だけ。`TAIOU_VALUES` も代入は 1 か所で、右辺は全体を固定する。`review-log/README.md` も `対応` の 6 値を書く）と `差分との関係` の 3 値が、root `CLAUDE.md`・独立レビューの agent 定義・`review-log-present.sh` の間でずれないこと、テンプレートの「呼び出し元の候補」の欄が指すスクリプトが実在することを固定した
- `tests/test_light_lane_review_candidates.py`: repo root の `scripts/light-lane-review-candidates.py`（配布物の外。独立レビューに渡す呼び出し元の候補を、差分から名前を抜き出して grep で列挙する）の契約を固定した。同じ差分で同じ出力、空の差分、削除だけの差分、リネーム、Markdown を読まないこと、`review-log/` を引かないこと、件数の上限と並び順、引用符つきのパス・コロンを含むパス・改行を含むパス（パスの全体が残ること）・`color.grep=always` の git config・U+2028・`\x0c`・単独の `\r` を含む行、一致の多すぎる名前は件数だけにすること

#### Affected Files

- `tests/checks/review-log-present.sh`
- `tests/test_review_log_present.py`
- `tests/test_light_lane_review_routing_contract.py`
- `tests/test_light_lane_review_candidates.py`
- plugin の外: root `CLAUDE.md`（手順 5〜7・安全策 4・全レーン共通）、root `AGENTS.md`（依頼なしに作ってよい Issue の文言）、`.claude/agents/light-lane-independent-reviewer.md`、`scripts/light-lane-review-candidates.py`、`scripts/.gitignore`（候補のスクリプトのテストが作る `__pycache__/` を無視する）、`review-log/README.md`

#### User Action Required

- なし

#### Known Limitations

- 振り分け（再掲か、② か ③ か）は検査しない。3 つの値は自己申告で、`実害=no` の行なら付けるだけで high を件数から外せ、安全策 4 の発火も避けられる。照合は main が行う（root `CLAUDE.md` 手順 6）
- `## 巡` の high・medium の意味が、この変更の前後で変わる（前は再掲や差分の外の指摘も含んでいた）。前後を比べるときは、`## 指摘` の行から数え直す
- `## 巡` の blocking は、今までどおり指摘表から導出できないので照合しない。blocking から再掲を除くことは、文書の規定だけである

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- 変異注入: `review-log-present.sh` の `UNCOUNTED_TAIOU_VALUES` に値を足す、`re-reported` を別名にする、`UNCOUNTED_TAIOU_VALUES |= …` で後から足す、代入の右辺に `| {"skip"}`・`.union(…)`・`| frozenset(…)` で足す、`TAIOU_VALUES` の受理側に値を足す・後から `|=` で足す、集合の中に単引用符の値や `*名前` の展開を足す、`TAIOU_VALUES` から `UNCOUNTED_TAIOU_VALUES` を外す、`review-log/README.md` の値を別名にする、のどれでも契約テストが落ちる
