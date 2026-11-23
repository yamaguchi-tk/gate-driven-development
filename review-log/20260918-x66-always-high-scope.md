---
lane: L1
pr: 121
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | user（AskUserQuestion。baseline の opus 判定で 旧#92/#93 の題材が category fail-open・blocking=yes になり、severity の上限だけでは往復が減らないため、実害クラスの付け方も限定するかを確認した） | - | 0 | 1 | 0 | 2026-09-18T16:20+09:00 |
| codex-1 | Codex adversarial-review（codex-companion 1.0.4, --base origin/main --scope branch, 観点: 改訂後の定義を読む全ファイルの受理集合の一致） | dabbaa7b18aca32881ea4e16b93e6421fe69f09e | 1 | 0 | 0 | 2026-09-18T17:05+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | dcb6db53d838bf7fa26d163a5ad6159ecde24585 | 0 | 3 | 0 | 2026-09-18T17:35+09:00 |
| 独立-2 | light-lane-independent-reviewer, 全差分, model: opus | a6c5026838583670cc053638b8e4ba987b306e9e | 0 | 1 | 0 | 2026-09-18T18:45+09:00 |
| 独立-3 | light-lane-independent-reviewer, 全差分, model: opus | c61f4dfe7e11dd391f851e04d6b9df25109ede63 | 0 | 1 | 0 | 2026-09-18T19:40+09:00 |
| PR後-1 | yamaguchi-tk (GitHub PR 旧#121 review, gdd-pr-review, 本体は Grok 4.6。Opus は usage limit で unavailable) | c8ceb3c254df14431f788336dcb772ba10a6a5a1 | 0 | 0 | 0 | 2026-09-18T21:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | medium | no | inherited | always-high-blocking-scope | fixed | 依頼は severity の上限だけだったが、blocking は category で決まるため、範囲外の部品の fail-open・例外には実害クラスを付けない規定も足す（ユーザーが「広げる」を選択） |
| C1 | codex-1 | high | no | self-inflicted | always-high-referrer-asymmetry | fixed | independent-review.md の出力フォーマットだけが 4 型を無条件に「severity 固定の集合」と書き、範囲外の finding も high に計上されうる。適用範囲への参照に直し、契約テストの走査対象に independent-review.md を追加した |
| D1 | 独立-1 | medium | no | self-inflicted | always-high-canonical-contradiction | fixed | reviewer-common.md の主文（常に High・Stage 2 非適用）と予約 alias の段落（blocking に一切影響しない）が無条件のまま残り、新しい適用範囲の段落と矛盾する（ユーザー指示で同じ push で修正） |
| D2 | 独立-1 | medium | no | self-inflicted | always-high-test-power | fixed | 「判定できないときは範囲内」「意図ではなく判定に届くかで決める」「範囲外は Stage 2 に戻る」の文がテストで固定されていない |
| D3 | 独立-1 | medium | no | self-inflicted | always-high-scope-enumeration | fixed | 適用範囲が限定列挙のため、どちらにも当たらない部品（利用者の製品コードの認可・入力検証など）が常時 High の固定と Stage 2 除外を失う |
| D4 | 独立-1 | low | no | self-inflicted | always-high-claim-scope | fixed | Why と断片の「旧#92 の high 6 件はすべて warn-only」は F2（block gate に届く）を含み過大。旧#93 にも過剰 block の high がある |
| D5 | 独立-1 | low | no | self-inflicted | scope-term-collision | fixed | 「範囲内／範囲外」が independent-review.md の差分スコープの用語と衝突する |
| D6 | 独立-1 | low | no | self-inflicted | fragment-affected-files | fixed | 断片の Affected Files と参照側の列挙に root CLAUDE.md と agent 定義が無い。限界の 3 点目も無い |
| D7 | 独立-1 | low | no | self-inflicted | always-high-cap-types | fixed | medium 上限の対象が fail-open・例外の 2 型だけで、範囲外の部品への guard bypass という名付けは上限を受けない |
| D8 | 独立-1 | advisory | no | self-inflicted | warn-only-output-channel | fixed | 「systemMessage だけを出す」は実際の warn-only hook（additionalContext を出す）と合わない |
| D9 | 独立-1 | advisory | no | self-inflicted | pr-body-claim | fixed | RED-GREEN の証拠が入力に無い（PR 本文に残す） |
| D10 | 独立-1 | advisory | no | inherited | hook-comment-stale | accepted | pre-push gate・nudge hook のコメントが旧い規則のまま（挙動に影響なし、L1+ の後続） |
| E1 | 独立-2 | medium | no | self-inflicted | always-high-test-power | deferred | 契約テストが語の有無しか見ず、除外リストへの追加・共有部品の文の反転・参照側の「§ 付きで常に High」を検出できない（残差方式が必要。旧#122） |
| E2 | 独立-2 | low | no | self-inflicted | always-high-cap-types | accepted | 断片の Summary・User Action Required が上限の対象を fail-open・例外の 2 型しか書いていない（正本は 4 型） |
| E3 | 独立-2 | low | no | self-inflicted | scope-term-collision | accepted | medium 上限が independent-review.md (3-d) の降格規定に当たるかが書かれていない。「範囲外」が差分スコープの語と紛れる |
| E4 | 独立-2 | low | no | self-inflicted | always-high-canonical-contradiction | accepted | 見出しの接尾辞「severity 調整の適用対象外」が無条件のまま |
| E5 | 独立-2 | low | no | self-inflicted | always-high-scope-enumeration | accepted | tests/checks からも走るが Stop hook の block に届く lint（HITL_LINT_SCRIPTS）の例が無い |
| E6 | 独立-2 | low | no | inherited | hook-comment-stale | accepted | pre-push gate のコメントが「実害クラスは常時 High」規定を引いている（挙動に影響なし） |
| E7 | 独立-2 | advisory | no | self-inflicted | lane-choice | accepted | gate の受理述語への入力が変わるので L1+ の方が妥当ではないか（レーンはユーザー指定の L1） |
| E8 | 独立-2 | advisory | no | self-inflicted | pr-body-claim | accepted | RED-GREEN の 7 件の入力と結果を PR 本文に残す |
| E9 | 独立-2 | advisory | no | self-inflicted | security-cap | accepted | Stage 2 と違い、上限に security-reviewer の除外が無い |
| E10 | 独立-2 | advisory | no | self-inflicted | test-power-definition | accepted | category 表の test-power の意味が lint・検査スクリプトの検出漏れを含まない |
| F1 | 独立-3 | medium | no | self-inflicted | always-high-scope-enumeration | deferred | block しない hook でも state の書き込み・resume 文脈の注入（PreCompact・SessionStart）の欠陥は適用範囲外になり、「resume / gate の correctness に影響」を fail-open とする category 表と読みが割れる。実害クラスとの重なりの優先順位も無い（旧#123） |
| F2 | 独立-3 | low | no | self-inflicted | always-high-scope-enumeration | accepted | 除外 (2) がパスで列挙され、tests/checks の外の共有ライブラリや利用者の security 検査の扱いが割れうる |
| F3 | 独立-3 | low | no | self-inflicted | always-high-test-power | accepted | canonical 判定の目印が検査対象の agent 定義そのもので、改名で黙って検査が外れる。governance テストと判定述語が違う |
| F4 | 独立-3 | low | no | self-inflicted | fragment-claim | accepted | 断片の User Action Required の「deferred にできる」は impl gate（product・test-power は Round 消費）には当たらない |
| F5 | 独立-3 | advisory | no | self-inflicted | always-high-referrer-asymmetry | accepted | root CLAUDE.md「指摘を直すとき」の「常時 High か実害クラス」に適用範囲の参照が無い |
| F6 | 独立-3 | advisory | no | self-inflicted | lane-choice | accepted | gate の判定件数を変えるので L1+ に近い（レーンはユーザー指定の L1） |
| F7 | 独立-3 | advisory | no | self-inflicted | style | accepted | 「severity を medium を上限にし」の助詞の重なり |
| G1 | PR後-1 | - | - | - | - | - | なし |
