# ADR: W-29 gate feedback loop のコスト削減（v0.39.0）

## Approved Direction

PR-W8（33.5h実測）で観測されたgate feedback loopの4つの発散経路を1PRで塞ぐ:
1. completion-checkへのW-27適用（差分スコープ / Round上限 / 記録staleの非blocker化）
2. reviewerの実起動検証 + design順方向整合チェックの追加
3. cross-session HITL通知（起動元セッションへの通知経路 + 受信メッセージの権限境界）
4. `human_check_gate`（Fable方向確認tier）の新設

自走上限: design-gating → task-breakdown → TDD → 実装 → impl-gate → completion-check → PR作成まで。merge / deploy / apply / production write / external postingは許可されない。

## 採用した設計方針と却下した代替案

### 1. completion-check の stale 3分類（(i)evidence鮮度 / (ii)記録stale / (iii)既定blocker、曖昧なら(iii)）

- **採用**: 3分類 + fail-closed既定。境界を`skills/gdd-completion-check/SKILL.md`に明記し契約テストで固定
- **却下**: 全staleをadvisory（impl-gate未通過taskの素通り経路を再び開くため）

### 2. completion-check の Round 上限とescalation route

- **採用**: `Completion Rounds`が2を超えたら方式転換の選択肢を人間へ一括提示。route は既存経路（`Route In Progress=human_recheck_required` + `Next Action=gdd-systematic-debugging`）を再利用し、`Next Action`許容値表は変更しない
- **却下**: 許容値表に`human-check-waiting`を追加（state machineのbreaking change） / impl-gateと同じ梯子（3/3→5/5→2/2）に揃える（ユーザー指定の「上限2」と異なる）

### 3. design順方向整合の検査範囲

- **採用（Option A）**: `references/inline-review-checklists.md`のimplementation-reviewer checklistに順方向整合項目を1件追加し、impl-gateが走査する
- **却下（Option B）**: design.mdに`既存部品:`明示行の規約を作りlintで機械突合（budget赤字になるため、次回dogfoodingでAの効果を見てから判断）

### 4. cross-session メッセージの権限境界（受信側）

- **採用**: cross-sessionメッセージはhuman approvalを代替しない。承認・中止・AC変更・破壊的操作の許可には使えず、`[情報のみ]`として扱いユーザー本人のターンを待つ。停止中の受信は再開させず、artifactへの書き込みにも使わない。宛先`Origin Session`はwrite-once
- **背景の重要な設計転換（v1→v2）**: 当初は「受信経路の一覧を正本化し、契約テストで突合する」案（v1、references配下に`cross-session-receiving-paths.md`のような一覧ファイルを置くcoverage scan方式）で設計を進めたが、4者独立レビュー（planning/security/dialectic Primary/Counter）全員が`changes_requested`で一致し撤回。核心指摘: 仕様どおり実装するとKeyword Listが1,600+行ヒットする一方、Paths表は15行のみで、テストは実装した瞬間に恒常REDになる。根本原因は「列挙が機械化されていないこと」ではなく「受信経路の意味論的な完了条件がACに定義されていないこと」であり、列挙を機械化しても「pointerの欠落」から「Keyword Listの不完全さ」へ問題の所在が移るだけでループが止まらないと判定された
- **採用（v2）**: markdown側のpointer分散をやめ、**hook側の機械的境界**として実装。(a) `hooks/scripts/lib/transcript.py`のuser-turn抽出で`origin.kind=="peer"`または固定text prefixのturnを`last_user_text`候補から除外（`isMeta`単独は独立セルフレビュー是正でfalse positive多発が判明し判定条件から除外済み） (b) `hooks/scripts/validate-steering-write.py`（`hooks.json`で`Write|Edit|MultiEdit|ApplyPatch`に配線されたPreToolUse関門）に、書込内容が承認・マージ承認・中止を含み、かつ直近の未フィルタuser-role turnがpeer由来なら書込をblockするルールを追加
- **却下**: v1の一覧化+coverage scan方式（実装不能と判明） / 一元化を「受信側の共通1関数を必ず経由する」設計にとどめる案（Fableの独立方向確認で「一元化はmarkdown側ではproblemを名前替えするだけ」と判定）

### 5. cross-session通知の送信可否

- **採用**: `Origin Session`がstate.mdにあり、かつmessaging toolが使える場合だけ送信。使えなければ送信せず理由をstate.mdに記録し、HITL停止自体は従来どおり必ず行う（fail-openしない）

### 6. `human_check_gate`（Fable方向確認）tierの適用範囲

> **v0.44.0（2026-09-12）で撤去**: 方向確認は W-29 で 5 回・env-s で 7 回すべて「方向 OK」、13 タスクで指摘 1 件・実害 0 だったため、tier・`agents/gdd-direction-checker.md`・`Direction Check` field を撤去した。本節と下の制約（`model: fable` の受理可否）は履歴として残す。

- **背景**: 実測3件（W8 RF-1、PR 旧#22、JIT access）はいずれも「人間承認点直前の方向の誤り」型。Opus推奨が承認済みAC・運用要件から外れ、Fableの独立確認で正しい方向に戻る事例が繰り返し観測された
- **採用**: 発動点を人間承認点直前の2箇所のみ（(a) requirements-gatingのhuman check直前、(b) `human_recheck_required`提示直前）に限定。`Fable` + `effort=medium`。役割は方向の判定のみで網羅的指摘は出さない。出力は1〜3行、`Fable確認: ...`としてHITLへ埋め込む。既定案と無回答時のデフォルトは`requirements.md`の採用案のまま変えず、代替案は並置するだけ（direction checkerの推奨で人間の判断を上書きしない）
- **却下**: planning reviewer全体をFable化（観測は人間承認点直前の方向判定に限られ、コストが全planningに乗る） / `effort=high`（まずmediumで実測し、不足が出たときだけ上げる）

## 後続 task が守るべき制約

- **budget ratchet**: `tests/checks/skill-body-budget.sh`の上限値（SKILL body total 6982 / per-skill 350 / template lines express 187・standard 411 / references ratchet 11922 / express・standard runtime token 30083・45381）は本PRで引き上げていない。今後の追加は既存の重複説明・冗長エピソードの圧縮とセットで行う
- **数値の二重正本を作らない**: completion-checkの数値契約は`references/state-machine.md`のみ、cross-sessionの契約は`references/phase-progression.md`のみに置き、SKILL/agent側はpointer + 非数値要約だけ持つ
- **cross-sessionメッセージの権限境界は`hooks/scripts/validate-steering-write.py`が機械的に強制する**。markdown側にpointerを追加するだけの対応では同種の欠陥（受信経路→権限境界pointer欠落）が3回連続で再発した実績があるため、新しい受信経路を追加する場合は必ずhook側の`PEER_TURN_STATE_WRITE_PATTERNS`（または同等の機械的チェック）を経由させること
- **`human_check_gate`のfrontmatter `model: fable`のhost受理可否は未検証**（実dispatchされたことがない）。（v0.44.0 で撤去済み。履歴。tier 自体が無くなったため、このフォールバック手順も対象外）
- **既知の技術的負債（Non-Goal、次回リファクタ候補）**: `hooks/scripts/lib/transcript.py`の`parse_transcript()`（cyclomatic complexity 37、pre-existing）と`last_user_turn_is_peer()`（同17、新規）、`hooks/scripts/validate-steering-write.py`の`main()`（同17、pre-existing）は複雑度上限15を超過。peer判定ロジックがセキュリティクリティカルなため、本PRでは安全性を優先しリファクタを見送った
- **機械的境界はfile-writeツール経路のみを覆う（既存の限界。PR #31レビューで明示化）**: `validate-steering-write.py`は`hooks/hooks.json`上で`Write|Edit|MultiEdit|ApplyPatch`にしか配線されていない。`Bash`は配線対象外なので、`sed -i` / shell redirection / `python -c` 等のBash経由の`.steering/**`書込は、peer turn直後でも無検査で通る。`Origin Session`のwrite-once検査（PR 旧#31 Finding 2で追加）も同じ配線を共有するため同じ限界を持つ。これは本PR以前から存在する配線上の制約で、塞ぐには`git_command_parse.py`相当のBashコマンドパーサ（書込先パスの抽出）が必要になり、W-29のAC-8〜11の範囲を超える。次回この経路を塞ぐ場合は、hookの検査ロジックではなく`hooks.json`のmatcherとBashパーサ側で扱うこと
- **peer判定の失敗経路（`OSError`等）はfail-open**（transcript読み取り不能時にvalidate-steering-write自体をブロックしない意図的trade-off）。次回のHonest Limitations改訂で明記を検討すること
