# TEAM ROLLOUT（チーム外展開キット）

> **対象**: GDD をチーム外へ試験展開するテックリード / 導入担当
> **目的**: 最初に読む 1 枚として、導入判断・初回実行・安全境界・成功指標をまとめる
> **詳細手順**: `docs/ONBOARDING.md`、`references/operation-levels.md`、`docs/METRICS_BASELINE.md`

---

## 使う / 使わない

| 使う | 使わない |
|---|---|
| 要件整理から PR 作成までを AI に一貫実行させたい | artifact 不要の短い相談だけしたい |
| HITL で scope / AC / 技術スタック / 自走上限を承認したい | 完全な探索 prototype で、状態管理が不要 |
| 中断・再開・post-merge follow-up の混線を避けたい | 1 行 typo など、ceremony の方が重い |
| superpowers と併用しつつ formal workflow を GDD に寄せたい | superpowers の standalone skill だけで十分 |

---

## 30 分導入

1. 試験用 clone を用意する。本番相当 repo でいきなり始めない。
2. plugin を配置し、`bash tests/validate-plugin.sh` を実行する。
3. `docs/PROJECT_CLAUDE_MD_TEMPLATE.md` から安全境界を導入先の CLAUDE.md に入れる。
4. `/gdd-dev README に導入セクションを 1 つ追加したい` を実行する。
5. human check で止まったら HITL の `30秒判断` と `判断ポイント` を先に読む。
6. `OK` 後、設計・TDD・実装・レビュー・PR 作成までの自走が意図通りか観察する。
7. `/gdd-dev 再開` と `gdd-status` を試し、worktree / resume が迷わず現在地を出すか確認する。

---

## 運用レベル

初回は `standard` を既定にする。導入抵抗が強いチームは `light` で始め、レビュー品質や中断復帰が安定したら `standard` に上げる。品質・監査が強いチームは `strict` を選ぶ。

| レベル | 使いどころ | 注意 |
|---|---|---|
| light | 初回 trial / 小規模チーム | gate を軽くするため、metrics で drift を見る |
| standard | 通常導入 | まずこの水準で展開判断する |
| strict | security / infra / production 影響あり | HITL と reviewer gate が重くなる |

詳細は `references/operation-levels.md` を参照する。

---

## HITL の読み方

HITL は全文レビューの場ではない。まず先頭の `30秒判断（まず見るところ）` と `判断ポイント`（簡易版は冒頭の行と `判断ポイント`）だけで、以下を確認する。

- 何を作るか: scope / AC / 完了条件の変換
- どう作るか: 技術スタック / access method / credential boundary
- どこまで任せるか: OK 後の自走上限
- 何は許可しないか: merge / deploy / terraform apply / AWS write / DB write / Docker push
- どこで戻ってくるか: 人間に戻す条件、まだ確認できないこと

非エンジニアの承認者には、詳細表より先に「OK で何が増えるか」「OK でも何が増えないか」を説明する。

---

## worktree / resume

チーム外展開で最も壊れると困るのは、再開時に別 task を見てしまう混線である。導入時は次を必ず確認する。

- `Worktree Identity Tuple` が path / steering / state task / branch を照合する
- 汚染や複数 non-terminal steering がある場合は auto-resume しない
- Codex compact 503 は workflow failure ではなく host interruption として resume する
- PR マージ後の追加実装は元 worktree を再利用せず、latest default branch から新しい worktree を作る
- post-merge follow-up では Origin PR / Origin Branch / Origin Merge Commit / Base Branch / Base Commit を残す

この確認に失敗したら、展開は進めず `docs/TROUBLESHOOTING.md` と `references/phase-progression.md` を見る。

---

## superpowers 共存

superpowers と併用してよい。ただし active GDD 中は `GDD Workflow Lock` として扱い、GDD remains the state owner。superpowers は `superpowers advisory only` であり、No direct superpowers workflow handoff を守る。

- `/gdd-dev` で入った formal workflow は GDD primary
- active GDD の自然文 follow-up は state.md / tasklist.md / worklog.md に戻す
- Codex goal continuation と SessionStart の reboot task が食い違う場合は、reboot task を採用せず Task Binding / PR / branch / worktree / state Task ID で解決する
- `superpowers:executing-plans` は standalone written-plan executor として参考にし、GDD中の実行主体にしない
- repo-local Project Skill（例: `example-prod-eval`）は検証手段・実行手段であり、workflow owner ではない。結果は GDD artifact / GDD route / worklog に戻す
- `superpowers の指示に従い` / `gdd-dev 相当` といった owner を曖昧にする言い方は active GDD 中に使わない
- GDD 外の単発探索・prototype・artifact 不要の相談では superpowers を使ってよい

詳細は `docs/SUPERPOWERS_COEXISTENCE.md` と `references/superpowers-overlap.md` を参照する。

---

## 成功指標

初回 1 週間は、機能数ではなく workflow の安定性を見る。

| 指標 | 目安 | 見る理由 |
|---|---|---|
| human check 到達 | Day 1 に到達 | HITL で判断できる入口がある |
| resume 成功率 | 80% 以上 | 中断・再開が混線していない |
| worktree 汚染警告 | 0 件が理想 | state / branch / steering が混ざっていない |
| HITL 差し戻し率 | 30% 以下 | 承認点が理解できている |
| superpowers 混入率 | active GDD 中は 0 件 | workflow owner が二重化していない |
| PR 前 reviewer 指摘 | high / medium を PR 前に処理 | 人間レビュー前に品質を上げている |

継続判断は `docs/METRICS_BASELINE.md` のチーム外展開 readiness を使う。

---

## 撤退条件

次のいずれかが出たら展開一時停止にする。

- resume が別 task / 古い branch / stale steering を候補にする
- HITL の `OK` で merge / deploy / apply まで許可されたと誤解される
- active GDD 中に superpowers workflow へ直接 handoff して state.md / tasklist.md / worklog.md が更新されない
- worktree 汚染警告が解消されないまま実装に進む
- 代表タスクで 2 回連続、承認者が「思ったものと違う」と判断する

撤退時は GDD を無理に続けず、対象 worktree と `.steering/` の状態を記録し、`docs/TROUBLESHOOTING.md` の混線・再開系を確認する。

---

## 最小リンク集

- 初回 30 分: `docs/ONBOARDING.md`
- 導入判断: `docs/TEAM_ROLLOUT.md`
- 運用レベル: `references/operation-levels.md`
- 成功指標: `docs/METRICS_BASELINE.md`
- superpowers 共存: `docs/SUPERPOWERS_COEXISTENCE.md`
- プロジェクト設定: `docs/PROJECT_CLAUDE_MD_TEMPLATE.md`
