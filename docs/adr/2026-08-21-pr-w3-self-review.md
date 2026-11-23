# ADR: PR-W3 — pre-push gate の新設とセルフレビュー正本の構造再設計

- Status: Accepted（2026-08-21）
- 対象タスク: `20260817-pr-w3-self-review`
- リリース: `plugins/gate-driven-development/CHANGELOG.md` § `[0.29.0]`
- **Superseded（部分）by**: `docs/adr/2026-10-03-block-guard-threat-model.md`（ADR-6 の守る範囲の線引きを、すべての block guard に広げ、意図の有無を transcript の実測で決める）
- **逐語アーカイブ（正本）**: `plugins/gate-driven-development/docs/design/2026-08-21-pr-w3-self-review-adr.md`

> 2026-10-16 追記: pre-push gate・pre-PR gate・merge gate は、今はコマンドを止めずに実行後に通知する（docs/adr/2026-10-15-merge-gate-notice-only.md・docs/adr/2026-10-16-push-pr-gate-notice-only.md）。本文の「止める」「block」は当時の挙動である。

本ファイルは repo 直下の ADR インデックスである。**個々の判断の本文・数値・実測はすべて上記の逐語アーカイブが正本**で、
ここには**転記しない**（同じ値を 2 箇所に置くと片方が黙って陳腐化するため。この規律自体が ADR-12 の成果物）。

## Context

セルフレビューが「PR を出してから外部レビュアーに指摘される」形に偏り、出す前に潰せる欠陥が毎回すり抜けていた。
`git push` 時点のガードが無く、セルフレビューの分類にも正本が無かった。

## Decisions

逐語アーカイブに ADR-1〜ADR-12 として記録した。主なものは次のとおり（詳細・根拠・却下案は各 ADR を参照）。

| ADR | 決定の要旨 |
|---|---|
| ADR-1〜ADR-9 | pre-push gate の判定順・opt-out の受理面・refspec / cwd 解決・block reason の復旧要素・テスト設計の各判断 |
| ADR-10 | AC-11 の「抽出」面は既存実装で充足しているとし、追加した薄いラッパーは撤回する |
| ADR-11 | 並行 PR 禁止リストは「所有者の実測」で失効判定し、CT-6 の測定述語を `main...HEAD` に固定する |
| **ADR-12** | **steering の記録は「面をまたいだ機械照合」と「量は機械が出す」で担保し、規約は steering 内に閉じる** |

## Consequences

- pre-push gate が `PreToolUse` の Bash matcher 3 本目として配線され、証跡なしの push が止まるようになった（当時。今は不足として実行後に通知する）
- セルフレビューの正本 `references/self-review-lanes.md` ができ、`gdd-pr-review` 3f の A〜E 型と対応づいた
- `validate-plugin.sh` の BLOCK が 4 本増えた（登録は `tests/checks/manifest.tsv` 経由）
- ADR-12 の成果物である記録規約は **branch-only** で、逐語アーカイブにのみ残る。その機械検査
  `reconcile-records.py` は ADR-12 の決定どおり出荷せず、branch 履歴からのみ取得できる

## 未処置として PR 本文へ送った論点

`--max-standard-estimated-tokens` の上限引き上げの是非、出荷 guard の `.claude/` `.gdd/` の穴、
`REJECTED_VOCAB` の pin 不在、常設の退行テスト不在ほか。**一覧と根拠は PR 本文 § Advisory Findings**。

## 運用規定からの逸脱（記録）

`references/post-completion-pr-flow.md` § Branch-Only Transfer Model は「raw steering を一時 push した branch は
**squash merge を前提にし**、merge 後に handoff branch を削除する」と定めるが、**本 PR は merge commit でマージした**。

- **理由**: 対象 repo が merge commit のみを許可している（実測: `allow_squash_merge: false` /
  `allow_rebase_merge: false`）。squash を使うには repo 設定の変更が必要で、**人間が設定を変えずに
  merge commit で進める判断をした**（2026-08-21）
- **結果として main の履歴に入るもの**: branch の 97 commit 中 **92 commit** が `.steering/` を含む。
  PR 差分は net-zero なので tip には残らないが、`git log -p` では読める
- **規定が squash を求める理由（機密残留リスク）に対する実測**: merge 対象の全 commit の追加行
  （**97,211 行**）に対し、実ホームパス / 完全形 UUID（session id）/ 12 桁数字（AWS アカウント ID）/
  秘密鍵ヘッダ を掃引し、**4 種すべて 0 件**。本 branch に限れば具体的な機密は検出されていない
- **残るコスト**: 規定に対する逸脱そのものと、main の履歴が約 10 万行ぶん重くなること
- **再発防止の選択肢（未実施）**: この repo は GDD の開発 repo であり、raw steering を一時 push する
  task branch が今後も出る。恒久対処するなら repo 設定で squash merge を有効化する
