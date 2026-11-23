# VERSIONING（バージョニング戦略）

> **対象**: GDD plugin の maintainer・リリース担当・CHANGELOG レビュワー
> **目的**: v0.x → v1.0 の昇格基準、Breaking Change の分類、SemVer 適用ルールを明文化する
> **上位正本**: `CHANGELOG.md` § Policy（個別エントリの記載ルール）
> **この文書の位置付け**: 「次のバージョンをどう付けるか」で迷わないようにするための判断基準

---

## 現状

- **現行バージョン**: v0.44.0（`.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json`）
- この行・3 manifest の `version`・`CHANGELOG.md` の版の節は、リリースのコミットでだけ変わる（§ 版数はリリースでだけ上げる）
- **配布**: GitHub の marketplace で配布
- **利用者**: 複数の導入先での利用を想定

---

## バージョン体系の基本方針

SemVer（MAJOR.MINOR.PATCH）を採用する。ただし v0.x の間は以下の扱いとする:

| セグメント | v0.x の扱い | v1.0 以降の扱い |
|-----------|------------|---------------|
| MAJOR | 常に 0（実験段階） | Breaking Change で bump |
| MINOR | 新機能・Breaking Change 両方で bump | 後方互換の新機能で bump |
| PATCH | バグ修正・ドキュメント修正で bump | バグ修正のみで bump |

**理由**: v0.x は「契約が流動的であることを宣言するゾーン」。利用者は v0.x 間の upgrade で Breaking Change が入りうることを前提とする。

---

## v0.x → v1.0 の昇格基準

以下を**全て**満たしたら v1.0 にする:

### 機能的成熟度

- [ ] **standard / quick / express / trivial** の全 sizing が 1 か月以上安定稼働
- [ ] **4 reviewer agent** の責務境界が確定し、`references/reviewer-selection.md` の Responsibility Matrix で変更が 1 か月以上発生していない
- [ ] **state machine** の field 定義（`state.md` / `tasklist.md`）が 2 か月以上変更されていない
- [ ] **hook 8 種類**（UserPromptSubmit / UserPromptExpansion / SessionStart / PreCompact / Stop / StopFailure / Notification / PreToolUse）の契約が固まっている

### 品質・安定性

- [ ] `tests/validate-plugin.sh` の全 BLOCK が CI 安定（flaky test なし）
- [ ] `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto` の full suite が CI 安定（flaky test なし）
- [ ] `evals/evals.json` のトリガー精度が gate ごとに閾値を満たす（`scripts/grade_evals.py` の合格基準）
- [ ] **Reviewer Loop Escape Hatch** / **Scope Drift Guard** / **Autonomous Continuation** の実戦テスト済み（複数の導入先の運用で機能していることを確認）
- [ ] CRITICAL バグの新規発生が 1 か月ゼロ

### 文書・運用

- [ ] `docs/` の 4 ファイル（ONBOARDING / TROUBLESHOOTING / PROJECT_CLAUDE_MD_TEMPLATE / SECURITY）が最新
- [ ] `CONTRIBUTING.md` が最新
- [ ] `CHANGELOG.md` に v1.0 までの migration guide が書かれている
- [ ] 利用者向けの upgrade 手順が `docs/` 配下に用意されている

### 利用実績

- [ ] 最低 3 つの導入先が 1 か月以上継続利用
- [ ] `gdd-metrics` の baseline KPI（`docs/METRICS_BASELINE.md`）を満たす導入先が 2 つ以上

---

## Breaking Change の分類

v0.x の間も、以下の変更は **Breaking Contract Change** として CHANGELOG に明記し、利用者への通知 + migration guide 提供を必須にする:

### 契約レベル（最重要）

| 変更 | 影響 | 必須対応 |
|------|------|---------|
| `references/self-contained-contract.md` の契約変更 | 利用者の plugin 呼び出し方法が変わる | migration guide + 暫定互換期間 |
| `references/state-machine.md` の field 削除・rename | 既存 `.steering/` が壊れる | 自動 migration script or 手動 migration 手順 |
| `Resume From` / `Next Action` の意味変更 | 再開時の routing が変わる | 新旧の違いを CHANGELOG で明示 |
| reviewer set（agent 数）の変更 | reviewer selection が変わる | Responsibility Matrix の更新 |
| gate 順序の変更（phase-progression） | workflow が変わる | 進行中 steering の扱いを明記 |

### スキーマレベル

| 変更 | 影響 | 必須対応 |
|------|------|---------|
| `evals/evals.json` schema 変更 | eval 実行が落ちる | schema migration + CI 更新 |
| `plugin.json` 必須フィールド追加 | Claude Code / Cursor / Codex が plugin を認識しない | `install-*-links.sh` 更新 + `scripts/sync-plugin-tooling.py --check` |
| hook 入出力フォーマット変更 | session-start / stop hook が壊れる | hook version 互換性 check |

### 利用者体験レベル

| 変更 | 影響 | 必須対応 |
|------|------|---------|
| 既定の stop 条件・block 条件の変更 | 自走継続が止まる / 止まらない | CHANGELOG の Migration 欄に説明 |
| `/gdd-dev` 引数の rename・削除 | 既存スクリプト・エイリアスが壊れる | 旧引数の alias 維持 or error message |
| required external prerequisite 追加（例: Python 3.11+ を必須化） | 実行環境が満たせなくなる | prerequisite のバージョン要件を明記 |

---

## Non-breaking な変更の例

以下は PATCH / MINOR で入れてよい:

- 新 skill / 新 reference の追加（既存を壊さない）
- hook エラーメッセージの文言改善
- documentation のみの追加・修正（`docs/` / `README.md` 等）
- 新 BLOCK の `validate-plugin.sh` への追加（既存の構成を failing にしないなら）
- `learned-patterns.md` / `worklog.md` 等の optional artifact の schema 追加

---

## リリース手順

リリース手順の正本は本節。`CONTRIBUTING.md` § リリース手順 は本節への案内だけを持つ。

### 版数はリリースでだけ上げる

通常の PR は、版数系のファイル（3 manifest の `version`・`CHANGELOG.md` の版の節・本文書 § 現状 の「現行バージョン」）に触れず、`changelog.d/<YYYYMMDD>-<slug>.md` に変更断片を 1 つ足す（書式: `CHANGELOG.md` § Entry Template）。PR ごとに版数を上げると、1 本マージされるたびに残りの PR がこれらのファイルで衝突し、衝突を解消すると先頭 commit が変わるので回帰テストと独立レビューをやり直すことになる（2026-09-12 に数えた直近 3 日では、main を取り込むときの衝突解消 10 回のうち 7 回が、これらのファイルとその版数を固定したテストだけの衝突だった）。

断片の `type`（`patch` / `minor` / `breaking`）は § バージョン判定フローチャート で決める。リリースでは、断片の `type` の最大値（breaking > minor > patch）で版数を上げる。v0.x の breaking は MINOR を上げる（§ バージョン体系の基本方針）。

- **統合先の定義**: `origin/main`（`GDD_INTEGRATION_REF` で上書き可）

検査は `tests/checks/version-not-consumed.sh`（BLOCK）が行う。3 manifest 間の一致は `grade-evals`、本文書の「現行バージョン」との一致は `test_distribution_readiness_contract.py` が見る。

| 層 | 実行条件 | 判定 |
|---|---|---|
| A（常時） | git 不要 | manifest の `version` が semver の文字列であること（`null` / 数値 / 真偽値 / 配列 / オブジェクト / キー欠落 / 不正 JSON / 空ファイル / 非 UTF-8 / ファイル不在は FAIL）/ `CHANGELOG.md` 先頭の released 見出しが manifest version と一致すること / `changelog.d/` の断片の書式 |
| B（統合先 ref がある場合） | `$ROOT` が git work tree 内・ref が解決できる・HEAD が統合先に含まれない・統合先との分岐点（merge-base）から HEAD までに plugin の配下が変わっている（分岐点が求まらないときは FAIL） | ブランチが統合先との分岐点（merge-base）から manifest version を変えていなければ、通常の PR として、分岐後に断片を 1 つ以上足していることを要求する（数えるのは `scripts/release.py` が集める `changelog.d/` 直下の断片だけ。統合先が分岐後にリリースしていても、統合先の取り込みは求めない）。分岐点にあった断片を消す・書き換えるのも FAIL にする。ただし、この branch で足した断片と対になる `review-log/<slug>.md`（repo root。分岐点に無いもの）の HEAD の front matter に `amends: <断片のファイル名>, ...` で宣言した断片の、同じパスでの書き換えだけは通す（`type:` の書き換えも通す。書式は層 A が見る。読めない宣言は FAIL）。変えていれば、統合先の版数より大きいときだけリリースのコミットとして、断片が残っていないことと、その版数が統合先の `CHANGELOG.md` に released 見出しとして無いことを要求する。統合先の版数以下なら FAIL |

B が実行できない環境では、その旨を `SKIP-B: <理由>` として出力し、A の判定だけで終わる。統合先には、マージ済み PR の断片が次のリリースまで残っているのが正常な状態である。上の判定の分岐と、HEAD 側 manifest の型違いの扱いは `tests/test_changelog_fragments.py` が固定する（統合先側 manifest の型違いは `null` と不正 JSON の 2 形だけ）。`amends:` の例外は `tests/test_changelog_fragment_amends.py` が固定する。

### MINOR / PATCH リリース

リリースは maintainer の明示の指示があるときだけ行う。

1. 最新の main からリリース用のブランチを切る
2. `python3 scripts/release.py` を実行する（dry-run。何も書かない）。表示された次の版数・集める断片・`CHANGELOG.md` に入る節を確かめる
3. `python3 scripts/release.py --apply` を実行する。3 manifest（`.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json`）の `version`、本文書 § 現状 の「現行バージョン」、`CHANGELOG.md` の新しい版の節をまとめて更新し、断片を削除する。断片が 0 件なら何もしない
4. `CHANGELOG.md` が 1200 行以上なら、同じコミットで回転する（`CHANGELOG.md` § Archive）
5. `python3 scripts/sync-plugin-tooling.py --check` で marketplace / plugin metadata の派生差分が無いことを確認
6. `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto` 全 contract test OK
7. `bash tests/validate-plugin.sh` 全 BLOCK OK
8. **Superpowers Benchmark Summary** を確認する。changed GDD primitive が含まれる場合は 比較資料を release evidence に含める。primitive 変更が無い場合は release note に `Superpowers Benchmark Summary: not_applicable (no changed GDD primitive)` と書く
9. commit と tag 作成（例: `v0.6.1`）。スクリプトは commit も tag も行わない
10. リリースのブランチを main に入れる前に別の PR がマージされて断片が増えたら、最新の main から切り直して 2 からやり直す（`--apply` を重ねると版数が 2 回上がる）

### v1.0.0 リリース

MINOR / PATCH の手順に加えて:

1. v1.0 昇格基準チェックリスト（本文書）を完全に埋める
2. `CHANGELOG.md` に v0.x → v1.0 の累積 migration guide を追記
3. `docs/` 配下の全ファイルが v1.0 前提であることを再確認
4. `README.md` の「experimental / beta」表記を削除
5. tag `v1.0.0` 作成

### Breaking Change リリース（v0.x 内で）

MINOR / PATCH の手順に加えて:

1. `type: breaking` の断片の `#### Breaking Contract Changes` と `#### User Action Required` に、破壊的変更と利用者向けの対応手順が書かれていることを確かめる
2. 可能なら旧挙動の **暫定互換期間**（例: 1 リリース期間）を設ける
3. リリースノートなどで事前周知

---

## バージョン判定フローチャート

PR ではこのフローで断片の `type` を決める（PATCH → `patch`、MINOR → `minor`、Breaking 明記 → `breaking`）。

```
変更の種類は？
├─ ドキュメントのみ → PATCH bump
├─ バグ修正（既存挙動の不具合） → PATCH bump
├─ 新機能追加（既存を壊さない） → MINOR bump
├─ 新機能追加（既存を壊す） → v0.x なら MINOR bump + Breaking 明記 / v1.x なら MAJOR bump
└─ 契約レベル変更 → 「Breaking Change の分類」を確認
    ├─ 契約レベル / スキーマレベル → Breaking 明記 + migration guide
    └─ 利用者体験レベル → CHANGELOG User Action Required に記載
```

---

## よくある判断の迷い

### Q: skill を新規追加した場合、MINOR bump？

**A**: MINOR bump。新 skill が既存フローを壊さない限り non-breaking。ただし `gdd-using-skills` の mapping 更新、`evals/evals.json` のケース追加は忘れない。

### Q: `state.md` に optional field を追加した

**A**: PATCH または MINOR bump。既存 `.steering/` が壊れない（fallback = 空文字）なら non-breaking。routing source に影響するなら MINOR + CHANGELOG に追記。

### Q: `learned-patterns.md` の schema が変わった

**A**: optional artifact なので non-breaking。PATCH bump。ただし migration path（旧形式の自動変換 or 無視）を明記。

### Q: reviewer agent の判断ロジックを変えた（false positive 削減）

**A**: non-breaking であれば PATCH bump。ただし `evals/evals.json` の expected score が変わる場合は MINOR bump。

### Q: 既存の agent の定義の model・effort を変えた

**A**: PATCH bump。変えた model に合わせて、既にある dispatch gate の固定 model の表・その警告・reference を直しただけのときも PATCH。新しい機能を足していないので、MINOR にしない。agent や仕組みを新しく足すなら MINOR。

### Q: hook の exit code が変わった

**A**: Breaking Change（hook 契約変更）。MINOR bump + Breaking 明記。fail-closed の挙動が変わるケースが多いので、利用者に影響大。

---

## モデル世代監査（定常運用）

**トリガー: メジャーモデルが更新されたとき**（例: Opus 4.x → Opus 5）。バージョン bump とは独立した保守イベントとして扱う。

**なぜ定常化するか**: この plugin は AI エージェント向けの指示文書であり、
「どのモデルに向けて書かれているか」が品質を直接左右する。旧モデル向けに書いた補正・過剰規定は、
モデル世代が上がっても自動では消えず堆積する。1 回蒸留して終わりにすると同じ状態に戻る。

### 手順

1. **実行時ロードの実測**（主観的な読み直しをしない）
   - `scripts/lint-runtime-budget.py` で runtime profile のトークン量を測る
   - 過去セッションの transcript から `references/*.md` の実行時 Read 頻度を集計する
2. **実測に基づく処分**: 4 値ルーブリック（keep / rewrite-to-intent / delete / relocate）を節単位で適用
3. **replay eval で検証**: 蒸留の前後で過去 task の gate 判定を比較する
   （`scripts/run-gdd-scenario-evals.py`。判定基準は改善計画 §10.7 U-9）

### ベースライン（2026-07-16 実測。次回はこれと比較する）

- 注入は **top 8 ファイルに約 77%** が集中（総注入 143 万行、首位 `state-machine.md` 24.2 万行）
- **Read ゼロが 10/66 ファイル**
- 1 セッション平均およそ 2,100 行の注入。compaction 後の再 Read で同一ファイルが繰り返し注入される

### 判断の原則

- **静的な参照数を代理指標にしない**。実測で、10 skill から引用されるファイルの実行時ロードがほぼゼロだった例がある
  （引用されること と 実行時に読まれること は別）
- 全ファイルを均等に磨かない。hot-core に集中し、残りは触らない（YAGNI）
- 削除・蒸留は eval で同等性を示してから行う

---

## 参考

- 変更履歴: `CHANGELOG.md`
- 個別エントリのフォーマット: `CHANGELOG.md` § Entry Template
- リリース前チェック: `CONTRIBUTING.md` § 必須チェック
- SemVer 仕様: https://semver.org/lang/ja/
