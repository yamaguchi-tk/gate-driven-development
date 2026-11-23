---
type: patch
---

#### Summary

- `references/testing-anti-patterns.md` § テスト判定基準 で、クラス E のテスト（runtime が読む文書の規範文を行と動詞まで含めて見るテスト）が、同じ節の固定値 pin の規則（「文言」の pin は (a)〜(c) に当たらなければ消す）では削除対象になっていた矛盾を解消した（旧#143）。E のテストは固定値 pin に当たらないと正本の 1 か所で決めた
- **利用者の `/gdd-dev` の implementation gate と TDD の Guardrails は、runtime が読む文書の規範文を行と動詞まで含めて見るテストを、固定値 pin の規則では削除・RED 不認定にしなくなる**。語の存在・見出しの存在・最初の一致で文書を見るテストは、従来どおり消す側
- TDD の Guardrails と inline checklist は正本の「書かない・消すテスト」の全項目で判定するようになり、E 以外では従来より厳しくなる（旧文面は固定値 pin の ADR・PR の引用要件を含まず、implementation reviewer Focus 3 だけが含んでいた）

#### Changed

- `references/testing-anti-patterns.md` § 書かない・消すテスト: 「人間向け文書の文言 guard は書かない」の行に、クラス E の規範文を行と動詞まで含めて見るテストは残し、上の固定値 pin（リテラル・文言・配置の写しなどを含む）に当たらないこと、語の存在などで見るものは消すこと、節・文書を丸ごと写すものは E に含めず固定値 pin として判定することを足した（行数は不変。用語はクラス表の E の行にそろえた）。元文書（GDD を使う別の repo の `docs/testing-standard.md`）では §2.2 の「人間向け文書の文言 guard」行の例外と §2.4 の文書 guard の行でこの関係を決めていたが、旧#144 の取り込みで §2.4 が落ちていた。元文書の例外 (d) は prompt サイズ budget で別の意味を持つため、(d) としては足さない
- 参照側 3 か所（`skills/gdd-test-driven-development/SKILL.md` Guardrails、`agents/gdd-implementation-reviewer.md` Focus 3、`references/inline-review-checklists.md` § テスト品質）は、固定値 pin などの条件を別の言葉で写すのをやめ、completion reviewer Focus 6 と同じく同節の「書かない・消すテスト」を参照する形にそろえた。Focus 3 だけが「ADR・PR の引用が無い」を条件に含み、受理集合が一致していなかった

#### Added

- `tests/test_testing_standard_contract.py`: 正本のクラス E の除外の文（判別条件を含む）と、参照側 4 か所の判定行が「書かない・消すテスト」を参照し、その行に固定値 pin・文言 guard・mock の条件を写さないことを固定するテスト

#### Affected Files

- `references/testing-anti-patterns.md`
- `references/inline-review-checklists.md`
- `skills/gdd-test-driven-development/SKILL.md`
- `agents/gdd-implementation-reviewer.md`
- `tests/test_testing_standard_contract.py`

#### User Action Required

- 利用者の操作は不要

#### Known Limitations

- pressure scenario（E のテスト・語の存在で見るテスト・README の行数 pin）は、変更前後で 1 シナリオ・各 1 回だけ比べた（結果は PR 本文の Skill RED-GREEN Evidence）。除外文を「文言」の pin から固定値 pin 全体に広げた後の定義では再測定していない
- 「行と動詞まで含めて見る」に当たるか、「節・文書を丸ごと写す」に当たるかの判定は reviewer の判断に依存する
- 残す・消すの優先順位（元文書 §2.3「1 つでも残すに当たれば残す」）は取り込んでいない。(a)〜(c) に当たる語の存在のテストなどは、固定値 pin の行と除外文で判定が分かれうる
- 契約テストが止めるのは、参照側の判定行への逐語の再掲だけで、別の言葉での写しは検出しない

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
