# ADR: planning reviewer に AC 閉包チェックを入れ、安全境界の述語は専用の finding を作らず既存の規則に委ねる（X-35）

- **日付**: 2026-09-11
- **状態**: 採用（開示して受容した既知の穴あり）
- **対象タスク**: `20260910-ac-closure-check`（X-35）
- **リリース**: `plugins/gate-driven-development/CHANGELOG.md` `[0.41.12]`（PR 旧#64、merge commit `c21e92c`）
- **関連**: `plugins/gate-driven-development/agents/gdd-planning-reviewer.md` § AC 閉包チェック（AC Closure Check）/ `plugins/gate-driven-development/tests/test_planning_reviewer_ac_closure_contract.py`

## Context

2026-09-10、GDD 自身の修正 3 本（X-28 = PR 旧#63 / X-34 = `env -S` / done guard Check 2 の Verification 文法）のレビューループが収束しなかった。原因は、完了条件が曖昧なことではなく「開いている」ことにある。文言は具体的でも、あらゆる入力について成り立つことを求める述語はテストで証明できず、reviewer は探せば次の反例を見つけられる。

- X-28 AC-18「任意の shell コマンド文字列から chdir の意図を検出する」→ impl-gate 22 巡・人間確認 10 回・約 38 時間
- 典型は「閉じた列挙 + それを包む開いた見出し」。X-34 AC-3 は下位の (a)〜(d) を列挙していたが、見出し「既存の誤爆面を増やさない」が design review の BL-1 の根拠になった

入口（requirements-gating）でこの形を止める規則が planning reviewer に無かった。一方で、閉じるだけでは実害のある穴を黙って出荷しうる（X-34 の IG-1 は本物の fail-open だった）ため、閉じられない述語の開示を対にする必要があった。

## Decision

1. `gdd-planning-reviewer` の Additional Design-Quality Checks に「AC 閉包チェック」を置く
   - 発火語（日本語 18 語 + 英語 8 語の閉じたリスト）を含む AC に、閉じ方 (a) 有限の入力集合（列挙）か、(b) 実行できる計測コマンドと合否基準を、同じ AC に添えさせる
   - 閉じた列挙を包む見出し・末尾句が列挙より広い範囲を主張する形も、開いた述語として扱う
   - 閉じられない述語は AC から外し、`Honest Limitations` へ開示させる（以下「退避」）
2. 閉じ方も開示も無い開いた述語は `Open Predicate in AC` とし、requirements phase では Medium（blocking）、design phase では **Low** とする
3. 安全境界（破壊的操作・秘匿、および `gdd-requirements-gating` の Fail-closed Default / Untrusted Input Boundary Check の対象）・ユーザーが明示した完了条件・不可逆操作の述語は、退避を使わず既存の規則（同 Check・Mission の blocking 接地条件・完了条件の「非スコープか Open Questions に理由付き」）に従わせる。**この節は安全境界専用の finding を持たない**
4. 閉じた例は fail-closed で書く（X-28: 検出対象の構文パターンを列挙し、列挙外の入力は block すると同じ AC に明記する）
5. 契約テストは逐語の needle を節の中に閉じ込めて固定する。検知する変異は閉じた集合に限る（節・参照文の削除 / needle 内の語の変更 / 表の行と完結した文の後ろへの追加 / 文中の needle の述部の後ろへの追加 / 発火語 1 語の削除 / 親節の外への移動 / advisory の復帰）

## Why

- 開いた述語を入口で閉じさせると、reviewer が反例を探す範囲が AC の列挙に閉じ、反例探しのループを入口で断てる
- design phase を Low にしたのは、`gdd-design-gating` が high と medium の全解消を approved 条件にしており、advisory を区別しないため。design phase の AC は承認済みで、閉じ直すには amendment が要る。Medium のままだと design gate を止め、減らしたい巡回を増やす（PR 旧#64 レビュー P2）
- 安全境界の述語を丸ごと `Honest Limitations` へ移すと、既存の fail-closed 契約を弱める（PR 旧#64 レビュー P1）。これを退避からの除外 1 文で防ぎ、判定は既存の規則に委ねた
- 専用の finding を持たないのは、次の Rejected Alternatives のとおり、新しい規則を既存の gate 規則の上に重ねるたびに、その交差から隣の穴が出続けたため

## Rejected Alternatives

- **design phase も Medium・advisory にする**: `gdd-design-gating` に advisory を非 blocking とする契約が無く、実際には design gate を止める
- **`gdd-design-gating/SKILL.md` に advisory の非 blocking 扱いを書く**: `skills/*/SKILL.md` は standard runtime 予算の残りが 132 tokens で、並行する W-29 と衝突する
- **安全境界専用の finding `Unapproved Safety Predicate Removal` High（とその細則）**: マージ前に、実装文脈を持たない独立レビュー（diff-only）を 5 回回した。細則（確認できる部分を AC に残す・残余の併記・列挙と計測の区別）を、1 本の閉じた規則（外した部分を承認ポイントに載せる）にまで縮めても、既存の Fail-closed Check・再入レビュー規則（`references/requirements-gating-steps.md`）・完了条件の非スコープ規則（`skills/gdd-requirements-gating/SKILL.md`）との交差から、隣の穴が 4 回続けて見つかった。規則の正本が範囲外の skills / references 側にあり、PR 旧#64 の中では閉じ切れない
- **`references/requirements-template.md` にも規則を書く**: references の行数予算（残り 20 行）を W-29 と取り合っていた
- **契約テストで「どんな変異でも検知する」**: 境界判定の穴は、直すたびに隣の型が見つかる開いた目標で、X-35 が止めたい型そのもの。PR 旧#64 のレビューで求められた集合で閉じた

## Consequences

- requirements phase で開いた述語の AC が差し戻され、X-28 型の開いた完了条件が impl-gate まで持ち越されにくくなる。効果は requirements-gating を通るタスクで観測する（PR 旧#64 では測れない）
- **既知の穴（開示して受容。マージ前の独立レビュー 5 回目 旧#1 High・旧#2 Medium）**
  - 閉じ方 (a)（列挙）や見出しの縮小で安全境界の述語を狭め、残りをどこにも書かない AC を、この節は拾わない。X-35 は AC を閉じる方向の圧力を持つため、安全境界の AC を黙って狭める圧力にもなりうる
  - 退避からの除外に反して `Honest Limitations` へ移した AC を拾う指摘も無い。委譲先の Fail-closed Check が扱うのは 3 項目（未設定時のデフォルト / untrusted input の区切り / injection のトリガー文字列）だけで、Mission の blocking 接地条件は指摘を生む規則ではない
- `quick (express)` と `trivial` は requirements-gating を通らないため、この節は走らない
- インストール済みプラグインは main チェックアウトへの symlink なので、pull した時点で稼働中の全 GDD セッションの planning reviewer にこの観点が加わる
- 後続タスク・再検討条件
  - 安全境界の述語と X-35 の閉じ方の相互作用を、`skills/gdd-requirements-gating/SKILL.md`（Fail-closed Check・完了条件の規則）と `references/requirements-gating-steps.md`（再入レビュー規則）と一緒に設計する。W-29 のマージ後に予定している「レビュー対象の閉集合化」「完了条件の置き換え」と同じ領域
  - `gdd-design-gating` が advisory を区別しない（planning reviewer の Mission が出す advisory も design phase では効かない）
  - `plugins/gate-driven-development/CHANGELOG.md` が回転トリガー（1200 行）を超えた（main で 1225 行）。並行 PR のマージ後に回転する
  - 壁時計の閾値を持つテスト（`test_root_branch_guard_contract.py` の 2 本、`test_merge_gate_followup_findings.py` の 1 本）が、`-n auto` の並列負荷下で閾値を超えて落ちる（単独の直列実行では通る）。並列を既定にする X-36 に影響する
- プロセスの学び: 同じクラスタで独立レビューの blocking が続いたとき、「何回目で直すのを止め、人間が閉じ方を選ぶか」を事前に合意しておくと、修正ループを止められた（独立レビュー 3・4・5 回目で停止し、人間が 1 本の規則への縮約 → 仕組みの撤去 → 開示して手動マージ、の順に選んだ）

## Source

- Derived from `.steering/20260910-ac-closure-check/`（branch-only。requirements.md の Correction Log、handoff の independent_review 1〜5 回目と impl-gate の記録）
- Related PR: 旧#64（merge commit `c21e92c`）
