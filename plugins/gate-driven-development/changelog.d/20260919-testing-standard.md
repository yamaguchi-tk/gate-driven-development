---
type: minor
---

#### Summary

- テストを書く・残す・消すときの判定基準を `references/testing-anti-patterns.md` § テスト判定基準 に置いた。判定軸は「消したら、どのクラスの、現実にありうるどの不具合を見逃すかを 1 文で言えるか」で、言えないテストは書かず、既存なら消す。基準は GDD を使う別の repo の `docs/testing-standard.md`（fix コミット 2,280 件と本番障害 8 件の分析）から、repo 固有の事例を除いて取り込んだ
- **利用者の `/gdd-dev` のテストの書き方と判定が変わる**。TDD（RED）、implementation gate、completion check、design gate のテスト方針が、この基準で判定する。completion reviewer は境界値・エラーパスなどの一覧を網羅の要件として扱わなくなり、クラスと見逃す不具合を 1 文で言える gap だけを報告する。逆に、例外条件の無い固定値 pin、人間向け文書の文言 guard、mock しか検証しないテストは Medium で削除を求める
- 本番ファイルの SHA 固定は原則として消す。残すのは、(1) runtime・hook・resolver が実行時に読む規範文書か、セキュリティ境界の実装が対象 (2) わざと壊して試し、その pin でしか検出できない改変があると確かめてある (3) 更新は「新しいハッシュ＋理由」を履歴に 1 件足す方式で、ハッシュの値だけを差し替えられない、の 3 つをすべて満たすものだけ。(3) を満たしていない既存の pin は、変更の多いファイルを対象から外したうえでこの方式に移す
- 対象 repo に固有の基準（`docs/testing-standard.md`、`AGENTS.md` / `CLAUDE.md` のテストの節）があれば、そちらを正とする

#### Changed

- `references/testing-anti-patterns.md`: 冒頭に § テスト判定基準（repo 固有基準の優先、判定軸、バグクラス A〜H、テストのダブルで置き換えた継ぎ目ごとに実物を通すテストを 1 本置くこと、書かない・消すテスト〔live file の SHA 凍結を残す 3 条件を含む〕、新しいテストの受入条件〔変異注入で検出力を実測〕）を追加した。行数を増やさないため、末尾の重複節（Quick Reference / Red Flags / TDD がこれらを防ぐ理由 / Bottom Line）を削り、Anti-Pattern 5（テストを後付けの task として扱う）を Core Principle の 1 文に畳んだ。旧 Anti-Pattern 6 は 5 に番号を詰めた。superpowers v5.0.7 の testing-anti-patterns から取り込んだ本文の構成が変わるため、superpowers 側の更新への追従は節単位では行えなくなる
- `skills/gdd-test-driven-development/SKILL.md` Guardrails: mock の Iron Laws の行を、§ テスト判定基準で RED を判定する行に置き換えた（行数は不変）
- `agents/gdd-implementation-reviewer.md` Focus 3: 退行注入に加えて、各テストを § テスト判定基準で判定し、基準を満たさないテストは Medium で削除を求め、ダブルで置き換えた継ぎ目に実物を通すテストが無ければクラス A の gap として報告する
- `agents/gdd-completion-reviewer.md` Focus 6: 報告する gap を「クラスと見逃す不具合を 1 文で言えるもの」に限り、既存の観点一覧を網羅の要件から gap を探す手がかりに変えた。「書かない・消すテスト」に当たるテストを削除候補として見る逆向きの観点を足した
- `agents/gdd-planning-reviewer.md` Design phase・`skills/gdd-design-gating/SKILL.md` Step 5 のテスト方針・`references/inline-review-checklists.md` § テスト品質: § テスト判定基準を参照させた

#### Added

- `tests/test_testing_standard_contract.py`: 正本の規範文（repo 固有基準の探索先、判定軸、クラス A〜H、固定値 pin の例外、SHA 凍結を残す 3 条件、受入条件）と、参照側 6 ファイルの該当行の § 参照・判定の動詞を固定する契約テスト

#### Affected Files

- `references/testing-anti-patterns.md`
- `references/inline-review-checklists.md`
- `skills/gdd-test-driven-development/SKILL.md`
- `skills/gdd-design-gating/SKILL.md`
- `agents/gdd-implementation-reviewer.md`
- `agents/gdd-completion-reviewer.md`
- `agents/gdd-planning-reviewer.md`
- `tests/test_testing_standard_contract.py`

#### User Action Required

- 利用者の操作は不要。repo 固有のテスト基準を使いたい場合は、`docs/testing-standard.md` か、`AGENTS.md` / `CLAUDE.md` のテストの節に書く

#### Known Limitations

- 「1 文で言えるか」の判定は reviewer の判断に依存する。機械的な検査は持たない
- repo 固有の基準の探索先は 3 つに固定しており、それ以外の場所（`docs/testing.md` など）に置いた基準は読まれない
- 既存のテストを遡って削除する手順は持たない。削除を求めるのは、差分に入ったテストだけである

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- 変異注入 10 件（参照の削除、Focus 6 の網羅要求への巻き戻し、判定軸の弱化、クラス行の削除、TDD の不合格の動詞の弱化、探索先の閉包の削除、逆向き観点の削除、SHA 固定の 3 条件を「どれか」に緩める、履歴方式への移行を外す、ハッシュの値の差し替えを許す）をすべて検出
- Skill RED-GREEN Evidence（PR 本文）: 同じ pressure scenario に対する completion reviewer / implementation reviewer の判定を、変更前後で比べた
