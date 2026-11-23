---
type: minor
---

#### Summary

human check の承認の後に本人が会話で許可したことを、human check を表示し直さずに適用する（`references/human-check-template.md` § 事前回答 の 5）。これまでは承認済みの自走上限を会話で変える経路が無く、表示し直すまで止まっていた。発話ごとに、明示したものだけを適用する。

- 「マージも自律的にして良い」「CI が通ったらマージして」など、エージェントにマージさせる指示・許可：自走上限をマージの値に上げ、`references/post-merge-qa.md` の自走のマージに入る。誰がマージするか読めない発話は上げず、マージの時点で今までどおり Merge Approval を問う
- 「マージしたら次に進んで」など：後続 Stage の着手の合図を先に受けたものとして扱う。新しい steering の human check は表示する
- 「Fable に相談しながら自律的に進めて」など：`事前回答:` 行を書き、以後の human check を委任先に相談して進める

あわせて、自走上限の値には表の値だけを書き、注記を付けないことを § 自走上限の置換値に明記した（注記つきの値は `references/post-merge-qa.md` 手順 2 の完全一致に当たらず、自走のマージに入れなかった）。

#### Changed

- `references/human-check-template.md` § 事前回答 に 5（承認後の引き上げ）を足した。`worklog.md` に `自走上限の引き上げ:` 行を書き、`Human Check Status` の evidence と `Approved Direction` の `自走上限` を 1 回の書き込みで新しい値に書き換える
- `references/human-check-template.md` § 自走上限の置換値 に、値は表の値だけを書くことを足した
- `references/post-merge-qa.md` の対象に、承認の後に会話で引き上げたときを足した

#### Affected Files

- `references/human-check-template.md`
- `references/post-merge-qa.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- Skill RED-GREEN Evidence（PR 本文）
