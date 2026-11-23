---
type: patch
---

#### Summary

未リリースの `20261004-autonomy-value-notes.md` の「steering の書き込み hook が、Write・Edit・MultiEdit で書いた後の `state.md` を見て…理由を `additionalContext` で返す」を、次のとおりに置き換える。

- 返すのは、自走上限の値と形、`Human Check Status` の evidence と行数が、書き込みの前後で変わったときだけである（書き込み前の state.md が無いときは変わったものとする）。注記の付いた記録が残っていても、それらの行に触れない書き込みには返さない（後から見つけた記録は書き換えないため）
- `State.md` のような大文字の名前の state.md も見る（advisory の lint も同じ）
- size の上限を超えた state.md への、行を消すだけの Edit でも返す
- 注記の移し先の案内は「worklog.md（事前回答を適用した承認なら、その `事前回答:` の行）」である
- ApplyPatch では、書き込み前の内容の lint の警告が、行に触れない書き込みでも利用者の端末（systemMessage）に毎回出る。警告を出すのは、自走上限か `human:` の evidence が `マージまで`・`マージ・デプロイ・QA まで` で始まるときだけである（lint の CLI も同じ。未リリースの `20261002-pre-answer-delegation.md` の「一致しないとき…WARN を出す」も、merge 値で始まらない不一致では出さない、に置き換わる）

あわせて、行の正規表現が `*` の長く続く行で後戻りを増やさないようにした。`docs/SECURITY.md` の hook の表に、steering の書き込み hook の読み取り範囲と出力を足した。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/autonomy_value.py`
- `plugins/gate-driven-development/hooks/scripts/validate-steering-write.py`
- `plugins/gate-driven-development/scripts/lint-approved-direction.py`
- `plugins/gate-driven-development/references/human-check-template.md`
- `plugins/gate-driven-development/docs/SECURITY.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_autonomy_value_notes.py` に、行が変わらない書き込み・`*` の長い行・大文字の名前・Write と MultiEdit・行を消す Edit の例外のテストを足し、形ごとの理由の語で固定した
- `tests/test_pre_answer_contract.py` の hook 入口のテストを、行に触れない書き込みでは返さない形にした
- `bash tests/validate-plugin.sh`
