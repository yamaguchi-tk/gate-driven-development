# Accretion Prevention Decision Packet（CI に code health gate を足すかの判断）

## Context

ある導入先の repo では、巨大な god-module の解体が完了し、facade は約 300 行まで縮小された。一方で、分割先のモジュールは数千行規模であり、今後のタスクで同じ追加中心の肥大が再発する余地は残っている。

## Rejected Prior Proposal

以前の PR は、その repo の CI に code health gate を追加する提案だった。内容は実装ファイルの行数 gate、既存巨大ファイルの allowlist、CI step、単体テストを含んでいた。自動レビューでは要件適合とされていたが、repo の持ち主の「取り込まない」で CLOSED になった。

このため、同じ CI gate を再追加しない。却下理由を無視して同等の fail gate を再提案することは禁止する。この事実から読み取れる判断は「実装不備」ではなく、その repo の CI に恒久 gate を足す運用判断が採用されなかった、である。

## Options

| Option | 内容 | block | その repo の CI 変更 | 向く状況 | Tradeoff |
|---|---|---:|---:|---|---|
| 案A | その repo の CI には入れず、変更を GDD completion-check 経由で確認し、`gdd-codebase-health.py` に任せる | あり | なし | 以前の却下を最も尊重したい | GDD を通らない PR には効かない |
| 案B | warning only として構造メトリクスを PR コメントに出すだけにする | なし | あり | 可視化だけなら受け入れられる可能性がある | ノイズや運用負荷が残る |
| 案C | 分割済みファイルの行数上限だけを極小 ratchet にする | あり | あり | 対象を絞った再肥大だけ止めたい | 却下された提案に近いため、再却下リスクがある |

## Recommendation

既定の推奨は案A。理由は、以前の「取り込まない」を尊重し、その repo の CI を変更せず、既に GDD 側にある completion-check / codebase health gate を使えるため。

## Option A Boundaries

案Aは CI に恒久 gate を入れない選択なので、守れる範囲は「GDD workflow が有効な開発経路」に限られる。`gh pr create` / `gh api .../pulls` は GDD active な Bash hook で pre-PR gate を受けるが、GitHub MCP や web UI から作成された PR は Bash hook の外側にある。

このため、案Aを採用しても GitHub MCP / web UI 経由の PR は codebase health gate を通らない。真に回避不能な backstop は default branch CI だが、以前の却下により CI gate は追加しない前提で扱う。

また、案Aは作業環境で GDD active かつ plugin が有効であることを前提にする。GDD plugin が無効、または GDD workflow を通さない手動 PR では `gdd-codebase-health.py` は自動実行されない。完了時に「その repo は守られている」と表現する場合は、この前提と限界を併記する。

## Current Decision State

ユーザー選択待ち。

選択があるまで、Codex は その repo に gate / workflow / warning comment を追加しない。案B または案C を実装する場合は、ユーザーがその案を明示的に選んだ後に別 PR として扱う。
