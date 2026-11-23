---
lane: L1
pr: 303
follow_up_of: 298
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | a4fc9dba771986f79b67ad780d23b772b862496f | 0 | 1 | 0 | 2026-10-03T10:40+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 7a51f8fb3b9282304ccdf0c93196263be261c798 | 0 | 1 | 0 | 2026-10-03T11:30+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | 5af396ed8a1293e3d9763ad019b23d3d39e9e7ae | 0 | 0 | 0 | 2026-10-03T12:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | test-power | fixed | glob meta を 1 文字でも含めば glob の形とみなし、`[TBD]`・`未定?`・`{TBD}` を何も出さずに合格にする。meta の語は `/` を含むときだけ受理する commit: f9f931fe |
| F2 | 独立-1 | low | no | inherited | test-power | fixed | `**未定**` のような強調の自由文を glob の形とみなす。F1 と同じく `/` を含むときだけ受理する commit: f9f931fe |
| F3 | 独立-1 | low | no | self-inflicted | test-power | fixed | 欄を読まなかったことが `--quiet` で呼ぶ hook に届かない。非 glob の語を並べた `WARN: glob field not read` を出す commit: f9f931fe |
| F4 | 独立-1 | low | no | self-inflicted | product | fixed | 単一ファイルの枝が `etc.`・`v1.2` を受理して ERROR にする。英字で始まる拡張子を求める commit: f9f931fe |
| F5 | 独立-1 | low | no | inherited | test-power | fixed | colon の形は `S-1/S-2`・`/` を glob とみなし続ける。colon の形でも glob の形でない語を 1 つずつ捨てる commit: f9f931fe |
| F6 | 独立-1 | low | no | inherited | test-power | fixed | `・`・`;`・縦棒・`／` で区切った値が 1 語になり、単一ファイル固定を検出しない。区切りの文字に足した commit: f9f931fe |
| F7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 未リリースの断片の Summary と User Action Required を置き換える注記が無く、混在した欄で ERROR・WARN が出なくなることが断片に無い commit: 7a51f8fb |
| F8 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 断片と PR 本文が受理集合を「絞った」と書くが、広がった側もある（F1・F4 の修正後の定義で書き直した） |
| F9 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 続きの箇条のテストは `_extract` だけを見て、CLI の INFO を assert していない |
| F10 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 欄を書く側の正本（requirements-template・gdd-dev 旧#10）に、欄には glob だけを書くことが無い |
| F11 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | Step 3c が続きの箇条に触れず、glob の形の定義がコードとずれる（F1・F4 の修正後の定義で書き直した） |
| F12 | 独立-1 | advisory | no | self-inflicted | product | accepted | 節が 2 つある state.md では、古い節の自由文 1 語で新しい節の glob まで捨てる |
| F13 | 独立-2 | medium | no | self-inflicted | product | fixed | 拡張子の判定が `:42` を取る前の語にかかり、`src/foo.ts:42` を glob の形とみなさない。見出しの形では ERROR が WARN に、colon の形では無言の除外になる。ユーザーの指示で直した。行番号を外した語に判定をかける commit: 95543e3a |
| F14 | 独立-2 | low | no | self-inflicted | product | accepted | 区切りの文字を見出しの形にだけ足し、colon の形は `・` などで区切った値を 1 語にする |
| F15 | 独立-2 | low | no | self-inflicted | product | accepted | `**` を is_global_glob は受けるが is_glob_shape は外し、colon の形では INFO: global glob が無言で消える |
| F16 | 独立-2 | low | no | self-inflicted | product | accepted | colon の形で `/` の無い単一ファイル（`package.json` など）を自由文の行からも拾い、偽の ERROR が増える |
| F17 | 独立-2 | low | no | inherited | product | accepted | `**S-1/S-2**` のように強調で囲んだ自由文は `/` と meta を含むので glob の形とみなされる |
| F18 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | module docstring が「colon の形は従来の読み方のまま」のままで、WARN にも触れない |
| F19 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | テストの docstring が古い glob の形の定義と INFO だけのまま |
| F20 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の同じ箇条で「WARN を出す」と「ERROR・WARN は出さない」が矛盾して読める |
| F21 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | PR 本文の限界に、混在した欄で security の WARN も出ないことが無い。PR 本文に書く commit: なし（PR 本文） |
| F22 | 独立-2 | low | no | self-inflicted | test-power | accepted | WARN が hook の systemMessage に届くテストと、colon の形の拡張子の変更を固定するテストが無い |
| F23 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の User Action Required に、`/` の無い glob（`*.ts`・`**`）の書き直し方が無い |
| F24 | 独立-2 | low | no | inherited | product | accepted | 区切りの `,` が brace 展開 `{a,b}` を分け、偽の ERROR になる |
| F25 | 独立-2 | advisory | no | self-inflicted | product | accepted | 欄ごと読まない代わりに、glob の形の語だけは検査して WARN も出す案 |
| F26 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | hook の WARN は書き込みのたびに出て、直した直後にも 1 回出ることが断片に無い |
| F27 | 独立-2 | advisory | no | self-inflicted | product | accepted | 区切りの縦棒が extglob の選択肢を分け、欄を読まなくなる（止める側） |
| F28 | 独立-3 | low | no | inherited | test-power | accepted | `src/foo.ts:42:7` や全角コロンの `：42` は glob の形とみなされず、colon の形では語が捨てられる |
| F29 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | PR 本文の変更内容に、行番号の付いた単一ファイルも ERROR になることが無い。PR 本文に書く commit: なし（PR 本文） |
| F30 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 断片の Validation に、行番号の付いた単一ファイルのテストが無い |
| F31 | 独立-3 | low | no | self-inflicted | product | accepted | colon の形で `db.internal:5432` のようなドット付きの語に `:数字` が続くと、誤って ERROR になる |
| F32 | 独立-3 | low | no | inherited | doc-claim | accepted | module docstring が「colon の形は従来の読み方のまま」と書き、実装と合わない |
