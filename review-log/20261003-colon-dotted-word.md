---
lane: L1
pr: 311
follow_up_of: 303
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | c92ce9bd8a53ea3fbe69d5d00081a344d4620624 | 1 | 1 | 1 | 2026-10-03T14:10+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 134ded2a9e26b7bd0990609cfa878391d1d023be | 0 | 3 | 0 | 2026-10-03T15:00+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | f7c5de381ba35f4cf2f7b78bb7e4c09d1e270771 | 0 | 1 | 0 | 2026-10-03T16:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | colon の形で `/` の無い単一ファイルを 5 つの拡張子のときしか拾わず、`自走範囲: package.json, src/bar/**` が何も出さずに exit 0 になる。拡張子の絞り込みを `自走範囲` 以外の行だけにかけ、テストで固定した commit: 7013c693 |
| F2 | 独立-1 | medium | no | self-inflicted | test-power | fixed | `/` を含む語を今までどおり拾うことを固定するテストが無い。stderr を見て、`src/main.go`・`**/auth/**` の ERROR・WARN を確かめるテストを足した commit: dad0d480 |
| F3 | 独立-1 | low | no | self-inflicted | test-power | fixed | 5 つの拡張子のうち `.ts` しか検査していない。`戻し条件` の行で 5 つの拡張子と `cookie.tsx` を検査するテストにした commit: dad0d480 |
| F4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 「製品名を拾わない」が実装より広く、残る誤検知（`Node.js`・`requirements.md`・URL）を書いていない。コメント・断片を狭め、PR 本文の限界に書く commit: 134ded2a |
| F5 | 独立-1 | low | no | inherited | product | fixed | 箇条で始まる colon の形の節が、次の箇条や見出しで終わらず、後ろの行の `SKILL.md` などを ERROR にする。同じ字下げ以下の次の箇条と見出しで閉じる commit: 7013c693 |
| F6 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 断片の Summary が、検出を狭めたことを書いていない（F1 の修正で `自走範囲` の行は狭めなくなった） |
| F7 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 未リリースの `20261002-approved-direction-glob-extract` の「colon の形の読み方は変えていない」が、リリースで同じ版の節に並ぶ |
| F8 | 独立-2 | medium | no | self-inflicted | product | fixed | 箇条の `Approved Direction` と同じ字下げに `- 方向性:`・`- 自走範囲:` を並べると節が閉じ、`src/foo.ts` を拾わない（main は ERROR）。ユーザーの指示（退行を直す）で直した。英語の欄名の兄弟の箇条だけで閉じる commit: 034f64dc |
| F9 | 独立-2 | medium | no | self-inflicted | product | fixed | `自走範囲:` の値を次の行の箇条に書くと、`/` の無い単一ファイルを拾わない（main は ERROR）。ユーザーの指示（退行を直す）で直した。続きの行も自走範囲として読む commit: 034f64dc |
| F10 | 独立-2 | medium | no | self-inflicted | doc-claim | fixed | 箇条でない節も見出しで閉じるのに、断片・PR 本文・docstring が箇条の節だけを書いている commit: 034f64dc |
| F11 | 独立-2 | low | no | self-inflicted | test-power | fixed | 見出しで節を閉じる規則をどのテストも検出しない。兄弟の箇条を挟まずに見出しが来るテストを足した commit: 145ecb07 |
| F12 | 独立-2 | low | no | self-inflicted | product | fixed | `自走範囲外:`・`自走範囲の補足:` の行も自走範囲の行になる。欄名の一致で判定する commit: 034f64dc |
| F13 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | `自走範囲` の行では host:port・ホスト名・`Node.js` が ERROR のまま残ることが限界に無い（PR 本文に書く） |
| F14 | 独立-3 | medium | no | self-inflicted | product | accepted | `自走範囲:` の下に入れ子で置く `明示的に除外する範囲: package-lock.json` も自走範囲の続きの行として読み、ERROR にする |
| F15 | 独立-3 | low | no | self-inflicted | product | accepted | 平らな箇条の形では `事前スキャン対象 glob:` の行まで読み、`/` を含む単一ファイルを ERROR にする |
| F16 | 独立-3 | low | no | self-inflicted | test-power | accepted | `自走範囲（S-1）: main.go`・`自走範囲 = main.go` は自走範囲の行にならず、`main.go` を拾わない（main は ERROR） |
| F17 | 独立-3 | low | no | self-inflicted | product | accepted | 親の階層（浅い字下げ）の日本語の欄名の箇条で節が閉じず、後ろの行を読む |
| F18 | 独立-3 | low | no | self-inflicted | product | accepted | 「英語の欄名」の照合が `-`・バッククォート・小文字の欄名や欄名の無い箇条を認めず、そこで節が閉じない |
| F19 | 独立-3 | low | no | inherited | test-power | accepted | 箇条でない英語の欄名の行は字下げを問わず節を閉じ、除外の tuple が効いていない（この PR より前から） |
| F20 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | docstring・断片・PR 本文の「top-level field」「続きの行」の記述が実装と合わない |
| F21 | 独立-3 | low | no | self-inflicted | test-power | accepted | 箇条でない節を英語の欄名の行で閉じる分岐、節の始まりでの自走範囲のリセット、全角コロンをテストが固定していない |
| F22 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 既存テストの docstring・名前（`_and_heading`）が、変えた節の終わり方に追いついていない |
| F23 | 独立-3 | advisory | no | inherited | bookkeeping | accepted | この lint を § 常時 High の適用範囲外（advisory の lint）とした判定。Step 3c が exit code を route に使うので、適用範囲内とするなら F16 は fail-open になる |
| F24 | 独立-3 | advisory | no | inherited | test-power | accepted | `COLON_SLASHLESS_FILE_RE` が大文字小文字を区別し、`SETUP.PY` を拾わない |
