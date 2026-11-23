---
type: patch
---

#### Summary

自律モードの判断役を選ぶ `GDD Autonomy Advisor` の行の扱いを、止まる側に揃えた。

- 大文字小文字を問わず `Autonomy Advisor` を含む行が、`GDD Autonomy Advisor: opus` か `GDD Autonomy Advisor: fable` のどちらとも一致しないとき（`- ` の箇条書き、小文字、全角コロンなど）は、判定できないものとして人間に止まる。これまでは `GDD Autonomy Advisor:` で始まらない行を「行が無い」と扱い、黙って `opus` で進めていた
- `GDD Autonomy Advisor: fable` で判断役を起動できなかったとき、worklog の `自律判断:` の行は `Fable: 呼べない` と書く
- Codex・Cursor では `fable` の判断役を起動できない。共有の `.gdd-config.md` に `fable` を書くと、それらのセッションは自律で決めてよい停止でも人間に止まる
- 既定を `opus` にしている根拠として、近い実測（`CHANGELOG.md` v0.44.0 の設計成果物の欠陥検出）の数値と、判断役そのものの比較は無いことを書いた

#### Changed

- `references/autonomy.md` の § 宣言、§ 判断の手順 5、§ 限界

#### Affected Files

- `plugins/gate-driven-development/references/autonomy.md`

#### User Action Required

- `.gdd-config.md` に `GDD Autonomy Advisor` の行を書いたプロジェクトは、行が `GDD Autonomy Advisor: opus` か `GDD Autonomy Advisor: fable` と一致するかを確かめる（一致しなければ自律モードの判断点で止まる）

#### Validation / Eval Impact

- 文書だけの変更。表記の揺れた行・起動の失敗・Codex での利用・既定の根拠の 5 問を、変更前後の文書で main 役に答えさせた（結果は PR 本文の Skill RED-GREEN Evidence）
