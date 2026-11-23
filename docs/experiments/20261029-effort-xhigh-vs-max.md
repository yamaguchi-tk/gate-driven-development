# effort の xhigh と max の当て直し（2026-10-29）

GDD の agent の effort を max から xhigh に下げてよいかを、過去の実際の入力に当て直して確かめた記録。2 つの実験を載せる。

- remediation worker（`gdd-remediation-worker`）：xhigh のままにした（2026-10-28 に max から下げていた）
- 判断の相談役 max（`gdd-opus-advisor-max`）：max のまま残した

結論は `plugins/gate-driven-development/references/fixed-models.md` の各段落が正本で、この文書は根拠の控えである。生の材料（差分・transcript・prompt・採点役の出力）は非公開である。

## 1. remediation worker の当て直し

### 方法

- 題材：2026-10-01〜28 に max で走った remediation worker 61 本から、再現でき、その後の実装 gate の記録がある 4 件を選んだ。どれも GDD を使う別の repo の task で、以下ではタスク A〜D と呼ぶ
  - タスク A（10-01。次の gate は changes_requested。理由は依頼が決めた値に由来）
  - タスク B（10-13。次の gate は approved）
  - タスク C（10-19。次の gate は、指摘を閉じたうえで、同じ類の別の穴で changes_requested）
  - タスク D（10-28。後の gate で approved）
- 腕
  - max：当時の本番の run の差分。途中で controller から追加の指示を受けた後の commit は除いた
  - xhigh：同じ依頼で 2 回。dispatch の時点の commit から worktree を作り、steering は当時 worker が Read した範囲を transcript から戻した
- 再現の仕方：`claude -p --agent gate-driven-development:gdd-remediation-worker --effort xhigh`。headless では frontmatter の effort が効かないので `--effort` を明示し、transcript の `effort` で実際の値を確かめた。push・gh・Agent は禁じた
- 採点：3 つの差分を A〜C で伏せ、事例ごとに 1 回。採点役は Fable high（主）と Opus max（副）。観点は 解消・先回り（後の gate の指摘を先に避けたか）・害の無さ の各 0〜2 点、24 点満点

### 結果

| 腕 | Fable high の採点 | Opus max の採点 | 1 本の費用・時間 |
|---|---|---|---|
| max（当時） | 22/24（先回り 6/8） | 22/24（先回り 6/8） | $9.2〜27.3・28〜300 分 |
| xhigh 1 回目 | 19/24（先回り 4/8） | 17/24（先回り 4/8） | $3.6〜6.9・11〜25 分 |
| xhigh 2 回目 | 20/24（先回り 4/8） | 19/24（先回り 4/8） | $3.3〜6.2・10〜22 分 |

事例ごとの点（解消・先回り・害の無さ。Fable high の採点）:

| タスク | max | xhigh 1 回目 | xhigh 2 回目 |
|---|---|---|---|
| A | 2・1・2 | 1・1・2 | 2・1・2 |
| B | 2・2・2 | 2・1・2 | 2・1・2 |
| C | 2・1・2 | 2・0・2 | 2・0・2 |
| D | 2・2・2 | 2・2・2 | 2・2・2 |

- 2 つの採点役とも max が 1 位。差は主に先回りに出た
- タスク D は 3 本とも満点で、差が無い

### 偏りと限界

- 採点役は 3 件とも、max の差分を「後の gate が見た差分」と見分けていた。後の gate は max の差分だけを審査しているので、先回りの観点は max に有利に傾きうる
- タスク B の max は、差分を作る前に controller から質問への答えを受けていた。xhigh は答えを受けずに止まった
- 交絡の無い差はタスク C の 1 件だけ。max は同じ類の穴まで閉じたが、次の gate は同じ類の別の穴で changes_requested になり、往復は減らなかった
- 4 件・xhigh 2 回・max 1 回の味見で、max 自身のぶれは測っていない
- steering は当時 worker が読んだ範囲だけを戻した。タスク C の指摘のファイルは、今のファイルを当時の巡までで切って置いた

### 決めたこと

xhigh のままにする（2026-10-29 ユーザー決定）。max に戻すかを見直す条件は、remediation worker の後の gate が approved になる率が、max で走った 61 本より下がったとき。基準の率と数え方はまだ決めていない。

費用：xhigh の再現 8 本 約 $42（試走を含む）、採点 8 本 $42。

## 2. 判断の相談役 max の再検証

### 方法

- 題材：2026-10-03 の比較実験の 10 件（Fable を信号①で呼んだ PR 旧#267〜旧#319）
- 腕
  - old-max・old-xhigh：10-03 の回答
  - v0：10-03 と同じ定義で、xhigh で再実行
  - lensA：v0 に、選ぶときの基準を足した
  - lensB：v0 に、推す前の事前検死（配線・例外で guard が落ちる経路・受理集合の対称性・fail-closed）を足した
- 経過資料は、10-03 09:40 の時点の main で作り直した
- 採点：事例ごとに 5 つの回答を伏せて 1 回、0〜2 点の 20 点満点。採点役は Fable high（主。どの腕にも入っていない）と Opus max（副。10-03 と同じ）

### 結果

| 腕 | Fable high の採点 | Opus max の採点 | 混入を除いた 4 件（Fable / Opus） | 1 本の中央値 |
|---|---|---|---|---|
| old-max | 18/20 | 17/20 | 7/8 / 7/8 | $4.53・11.2 分（10-03） |
| old-xhigh | 11/20 | 11/20 | 3/8 / 4/8 | $2.22・4.5 分（10-03） |
| v0（xhigh 再実行） | 15/20 | 13/20 | 6/8 / 6/8 | $2.49・4.9 分 |
| lensA | 12/20 | 8/20 | 4/8 / 3/8 | $2.48・5.0 分 |
| lensB | 12/20 | 12/20 | 4/8 / 3/8 | $2.78・6.1 分 |

- 観点を足しても、xhigh は上がらなかった（lensA・lensB とも v0 以下）
- 同じ xhigh でも 11〜15 点とぶれる。max はぶれの上端より 3〜4 点上で、採点役を Fable に替えても 1 位のまま

### 偏りと限界

- max は 10-03 の 1 本ずつだけで、max 自身のぶれは測っていない
- 混入（事例の時点より後の repo や memory を読んだもの）：旧の 旧#267・旧#273・旧#276・旧#316・旧#319、新の 旧#276（今の repo）・旧#279・旧#316（後の memory）。除くと残りは 4 件（旧#270・旧#285・旧#293・旧#301）
- 採点は後知恵で、1 回ずつ。経過資料は作り直したもので、当時と完全には同じでない
- 定義は 10-03 の相談役の本文で、今の `gdd-opus-advisor` の本文とは違う

### 決めたこと

`gdd-opus-advisor-max` は max のまま残す。

費用：相談 30 本 $75（上限で止まった分を含む）、採点 20 本 $113。
