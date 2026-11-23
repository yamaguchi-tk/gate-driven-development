# ADR アーカイブ: PR-W3（セルフレビューの構造再設計）

- 対象タスク: `20260817-pr-w3-self-review`
- リリース: `CHANGELOG.md` § `### [0.29.0]`
- 内容: pre-push gate の新設、セルフレビュー正本 `references/self-review-lanes.md` の新設、
  `validate-plugin.sh` への BLOCK 4 本追加、および **記録規約（ADR-12）**

> 2026-10-16 追記: pre-push gate・pre-PR gate・merge gate は、今はコマンドを止めずに実行後に通知する（docs/adr/2026-10-15-merge-gate-notice-only.md・docs/adr/2026-10-16-push-pr-gate-notice-only.md）。本文の「止める」「block」は当時の挙動である。

`.steering/` は feature branch 上でのみ追跡し、merge 時に本ファイルへ蒸留して `main` には含めない運用のため、
**GDD の steering から逐語でアーカイブした**（再要約による転記誤りを避けるため意図的にコピーのみ）。（2026-10-16: 3 つの gate が今も止めると読める現在形の記述だけを直した。ほかは逐語のまま）
本文中の `design.md` / `requirements.md` / `tasklist.md` / `worklog.md` / `handoff/impl-gate.md` への参照は
branch 上の `.steering/20260817-pr-w3-self-review/` を指しており、アーカイブ対象外のため解決しない。
結論の正本は `CHANGELOG.md` の 0.29.0 エントリと、各 lint / contract test の実装そのもの。

**ADR-12 の付随成果物について**: 記録規約の正本 `record-discipline.md` は下に逐語で収録した。
その機械検査 `reconcile-records.py`（196 行）は ADR-12 の決定どおり**出荷しない**方針だったため
branch の `.steering/20260817-pr-w3-self-review/reconcile-records.py` にのみ存在する。
必要なら branch 履歴から取得できる。

---

# ADR: PR-W3 セルフレビューの構造再設計

design-gating で確定した重要判断と却下した代替案を残す。詳細な設計本文は `design.md` を正本とする。

## ADR-1: pre-push gate を新規 hook ファイルとして新設する

### Context

`git push` を止める既存機構は無い。追記先の候補は `hooks/scripts/gdd_stop_hook.py`（1569 行、健全性方針の 1500 行超過）と `hooks/scripts/run-pre-pr-gate-hook.sh`（636 行、`pr create` 早期 exit の最適化あり、既存 54 test）。dialectic counter から「新 hook を作らず既存 pre-PR gate の Bash matcher に push を足せば、コマンド解析の重複が消える」という代替案が出た。

### Decision

`hooks/scripts/run-pre-push-gate-hook.sh` を新規に作り、`hooks/hooks.json` の Bash matcher に 3 本目として配線する。

### Why

- 636 行の hook に refspec 解決・cwd 解決・opt-out 受理面の解析を足すと 900 行規模になり、健全性方針の上限に近づく
- rollback が「hooks.json から 1 行削除」で済む。既存 hook に同居させると rollback がコード revert になり、`pr create` gate と push gate が同時に壊れる単一障害点になる
- `hooks-wiring-lint` が `run-*.sh` の配線を全数検証するため、新 hook の配線漏れは自動検出される

### Consequences

- nested shell 展開ロジックが `run-pre-pr-gate-hook.sh` の inline python と新 `hooks/scripts/lib/push_command_parse.py` の 2 箇所に存在する。統合は Planned Follow-up Stage の S-6 で行う
- 新 python module は `run-*.sh` 命名でないため配線 lint の対象外。未参照化を検出する単体テストを別に置く

## ADR-2: steering resolver を和集合にする

### Context

requirements AC-25 は「`lib/detect-steering.sh` の `gdd_detect_active_steering` を使い、pre-PR gate 内部の done 限定 resolver は使わない」と規定していた。実測すると、同関数は registry 経路では `Resume From ∈ {done, cancelled}` のみを除外し、fallback 経路では `Resume From` / `Next Action` の 6 条件すべてを除外するという非対称な実装だった。Post-Completion PR Flow の push は `Next Action=done` 確定後に走るため、fallback 経路に落ちた環境では最頻の push が解決不能として素通りする。

### Decision

`gdd_pre_push_resolve_steering` を `hooks/scripts/lib/self-review-evidence.sh` に新設し、(1) `gdd_detect_active_steering`（非 done 系）を先に呼び、(2) 解決できない場合だけ `Resume From == done || Next Action == done` の候補を独立実装で拾う和集合にする。`blocked` は両経路で「gate 対象」に統一する。`gdd_detect_active_steering` 本体は変更しない。

### Why

- AC-25（非 done で発火）と AC-1（active GDD 中の証跡なし push を止める）の両方を満たすには、done 系も解決対象に含める必要がある
- 既存関数を変更すると他 hook の挙動が変わる。呼び出し側で補完する方が影響範囲が小さい

### Consequences

- resolver は hook プロセス自身が対象 root へ `cd` してから呼ぶ必要がある（同関数は戻り値ではなくグローバル変数で結果を返すため、サブシェルでは伝播しない）
- registry binding を登録した fixture でのテストが必須になった。binding なしの fixture だけでは fallback 経路しか検証できない

## ADR-3: 代理指標であることを設計に織り込み、空洞化率を観測指標にする

### Context

hook が機械検証できるのは「証跡の sha が push 対象 ref の tip と一致すること」と書式だけで、`rounds` / `lanes` / `dry` は AI の自由記述である。dialectic counter から「gate を通す最短経路がレビューではなく文字列記入になる」「`rounds: 1` + `dry: yes` + `lanes` 全 0 が最も安く最も優秀に見える証跡になる」という空洞化シナリオが提示された。

### Decision

統制は縮小せず（AC-5 / AC-6 / AC-24 は承認済み）、代わりに次を設計に入れる。

- `Pre-Push Self Review` にも `consecutive_clean` を持たせ、`dry: yes` かつ `consecutive_clean < 2` を自己矛盾として block する（当時）
- `grounding: not_applicable` は理由 token を必須にする
- `dry` の severity 判定に「false positive 実績のある項目を 1 段階降格する」既存規定を適用しない
- 空洞化率（`rounds:1` かつ `dry:yes` かつ `lanes` 全 0 の証跡比率）を効果測定に加え、dogfood の第一観測指標にする
- block reason に「記録先 / 不足 key / 緊急時の逃げ道」の 3 要素を固定文言で必ず含め、肯定側 assertion でテストする

### Why

- 検証不能な述語を block 条件から外す案は AC の削除を伴い、要件修正の手続きが必要になる
- block reason に復旧手段が無いと、deny を受け取った AI の最短行動が「不足 key を書き足して再 push」になり、gate が書式修復の訓練として学習される
- 否定側（禁止語が出ない）だけの検査は、最も無内容な出力が最高得点になる構造で、本 PR が導入する分類の「常に成功する検証は検証していないのと同じ」に自分で抵触する

### Consequences

- 空洞化率が高止まりした場合、統制の縮小を別タスクで再検討する必要がある
- Honest Limitations に「機械検証できる述語は sha 一致と書式のみ」を明記した

## ADR-4: 逃げ道は広げず、承認済みの受理面に合わせて狭める

### Context

requirements の Route / Ownership Matrix は PR 作成 gate の flag 欄を「同上」（pre-push gate と同じ）と書いていたが、AC-4 の受理面は `git` token の直前という pre-push 固有の定義で、`gh pr create` には適用できない。また実測で、`GDD_HOOK_STATE_DIR` の差し替え、設定ファイルの env 追記、hook 定義の直接編集、push を包むラッパーという 4 つの無記録バイパスが AI の権限内にあることが分かった。

### Decision

- PR 作成 gate の逃げ道は kill-switch と「証跡を書く」の 2 つに確定する。環境変数による opt-out は pre-push gate 限定のまま広げない
- 上記 4 経路に session_id 書き換えと別 checkout からの push を加えた 6 項目を「opt-out 等価物」として skill 契約の禁止対象に追加する
- opt-out ログのパスは AC-4 の記述どおり環境変数 override を残す（テスト隔離に必要）。差し替え可能である事実は Honest Limitations に明記する

### Why

- 逃げ道を広げる方向の変更は承認済み policy の実質的な緩和になる。狭める側での確定なら安全側で、AC-4 の定義とも一致する
- ログ先を固定パスにすると、テストが実際の HOME を汚す構造になり別の問題を生む。禁止と明示の組み合わせで扱う方が単純

### Consequences

- プラグイン更新時点で走っている GDD タスクは、証跡を書くまで PR 作成が止まる（当時。今は不足として実行後に通知する）。CHANGELOG に User Action Required として記載する
- 環境変数によるログ差し替えは検出できない。これは受容する残余リスク

## ADR-5: `git push` 検出面は「一覧の完全性」ではなく「未知は両解釈」で閉じる

### Context

T-1 の impl-gate が 2 回連続で `changes_requested` になり、2 回目は 1 回目（F-1）と同一 root cause クラスの fail-open が 4 形（G-1 `--shallow-file` 欠落 / G-2 `#` によるトークン破棄 / G-3 long option の `-c` 誤爆 / G-4 行継続）で再発した。Implementation Gating Reviewer Bounce Log の escape hatch も発動した。

共通の構造は「`is_git_push` の検出面が、実 bash / 実 git が受理する書式集合の**部分集合**になっている」ことで、個別要因はいずれもその実例だった。1 回目の修正は「global flag 読み飛ばしの欠落」という**症状**を identifier にして横展開検索したため、同じクラスの他の 4 形を取り逃がしていた。

### Decision

- **未知の `-` 始まり token は arity 不明として「引数を取らない / 分離引数を 1 つ取る」の両方を subcommand 候補にする**。これにより `GIT_GLOBAL_FLAGS_WITH_ARGUMENT` の完全性は fail-open の原因にならない。一覧は `git -C push` を過検出しないための精度確保にのみ使う
- 一覧の正しさは実 git に問い合わせて検証する（`git <flag> <arg> version` の出力で arity を判定）。`git --help` の synopsis のような二次情報を正本にしない
- 字句層は bash のセマンティクスに合わせる: `#` をコメント扱いしない、`\` + 改行（行継続）は**バックスラッシュのエスケープを数えて**除去し token を残さない、生の改行は独立した区切り token（`NEWLINE_TOKEN`）にする
- 検出面は**差分テスト**で機械的に固定する。実 bash に書式を実行させ、PATH 先頭の stub `git` が受け取った argv を実測する。判定は片方向で、過検出は受容する。**固定できるのは差分テストの CORPUS に列挙した書式集合に対してのみ**であり、任意の shell 入力に対する無条件の包含関係ではない（保証範囲の限定は ADR-6 を参照）
- 上記に伴い design.md § opt-out 受理面の機械定義 item 2 から「改行 token は連続列の中でスキップしてよい」を削除する。行継続が token を残さなくなったため不要になり、残すと改行を跨いだ別コマンドへ opt-out が波及する

### Why

- flag や書式を 1 件ずつ足す修正は「一覧の完全性」に賭ける設計であり、git のバージョン差と将来の option 追加で必ず破れる。破れ方が fail-open（無記録の gate 素通り）なので、賭けの対象にしてよい性質ではない
- 過検出は「git を起動しないコマンドが block される」（当時）誤爆コストで済み、operator が気付ける。検出漏れは無記録で通るため気付けない。非対称なので fail-closed 側に倒す
- grep による横展開検索は「症状」でしか検索できず、同一クラスの別形を取り逃がすことが実測で確認された。差分テストは「検出すべき入力集合」を体系的に列挙する検索手段として機能する

### Consequences

- `echo Run git push origin main >> notes.md` のような文書編集コマンドも GDD active 中は block されうる（当時）。Honest Limitations に明記した
- テストは実 bash / 実 git を要求する（不在時は skip）。CI に両方が無い環境では差分テストが実行されない
- 既存 `run-pre-pr-gate-hook.sh` の inline python には同一クラスの fail-open が 4 形とも残っている。design.md § コマンド解析ロジックの再利用方針 の確定（既存 hook を触らない / 統合は S-6）に従い本 PR では修正せず、S-6 の申し送りとして記録した
- mutation テストの期待値を module の定数から読むと集合削除 mutation を検出できない（同語反復）ため、テスト側に literal で置く方針を採った。定数とテストの二重管理は `test_module_set_matches_expected_flags` で同期を強制する

## ADR-6: `git push` 検出面の保証範囲を「実測で固定した書式集合」に限定する

### Context

T-1 の impl-gate 3 回目（Attempt 3）で 2 件が blocking として残った。

- **G-9**: `_lex` の行継続除去がバックスラッシュのエスケープを数えず、行末が偶数個の `\` のときに 2 行を癒着させる。実 bash は次行の `git push` を実行するが module は `(False, -1)` を返す（fail-open）。派生で `GDD_SKIP_PRE_PUSH_GATE=1 env \\`+改行+`git push` の代入列が別コマンドの git に直結し、ADR-5 / G-8 で閉じたはずの opt-out 過大受理が別形で復活する
- **G-10**: 検出面の不変条件「実 bash / 実 git が push として実行する書式 ⊆ `is_git_push` が True」が module docstring / design.md / ADR-5 / tasklist Carry Forward の 4 箇所で**無条件**に主張され「差分テストで機械的に固定している」と書かれていた。実体は固定 15 ケースへの片方向 assert であり property ではないため、この命題は成立しない。列挙外の未検出書式（herestring / パイプ経由 shell / ANSI-C quoting / 変数展開・コマンド置換）が実測された

Bounce Log は同一 identifier（検出面の fail-open）で 3 回目に到達しており、`gdd-systematic-debugging` の route hint は `human_recheck_required` だった。人間に出した論点は 1 点、「検出面の不変条件をどこまで保証するか」。

### Decision

- **保証範囲を「差分テストの `RealShellDifferentialTests.CORPUS` に実測で固定した書式集合」に限定する**。無条件の包含関係は主張しない。4 箇所の主張をこの限定命題に書き改め、未検出が実測済みの書式を design.md § Honest Limitations に列挙する
- **G-9 はバグとして修正する**（保証範囲の限定とは独立）。行末の連続バックスラッシュが**奇数個のときだけ**行継続として除去する。偶数個なら全部リテラルとして残し、改行は区切り token にする
- **property / fuzz 差分テストへの拡張は採用しない**。この gate の守備範囲は「うっかりスキップの防止」であり、シェル書式を意図的に選んだ迂回は escape hatch（`GDD_SKIP_PRE_PUSH_GATE=1`）と同じ「意図的」側に分類して防護対象外とする
- 同一クラスの追加指摘が今後出た場合は、本決定の範囲内で **Honest Limitations への追記**として処理してよい（`human_recheck_required` への再エスカレーションを要しない）

### Why

- **根拠**: 2026-08-17 の human recheck 承認（state.md § Approved Direction）。人間が Option A（保証範囲の限定 + G-9 のバグ修正）を明示的に選択した
- 偽の命題を根拠として残すと、S-6 の「既存 `run-pre-pr-gate-hook.sh` の inline python 統合」と T-2〜T-4 の受理面設計が成立しない前提の上に積み上がる。G-7 で同型の偽コメントを Medium として閉じた前例と整合させる
- 無条件保証を目指すと字句層に bash のクォート・展開規則を再実装することになり、費用が守備範囲に見合わない。一方で「意図せず gate を通り抜ける」形（行継続の数え漏れのような字句層のバグ）は守備範囲の内側なので、そこは直す。この線引きが escape hatch の設計思想（意図的な迂回は記録して許す）と一貫する
- 保証範囲を明示すれば、限界は「隠れた欠陥」ではなく「宣言された仕様」になり、後続の判断が正しい前提に乗る

### Consequences

- `CORPUS` が保証範囲の**正本**になる。検出面を変える変更では CORPUS を先に増やすこと（module docstring / テスト docstring に明記）
- G-9 修正により CORPUS に偶数バックスラッシュ 3 形を追加した。行継続まわりの mutation 5 件は survivor 0
- design.md § Honest Limitations が長くなるが、gate が「何を防がないか」を operator が読める形になった
- 行継続の除去はクォート状態を見ないため、シングルクォート内の `\` + 改行も除去する乖離が残る。実測範囲では fail-open にならないため受容し、Honest Limitations に明記した
- 既存 `run-pre-pr-gate-hook.sh` の inline python に残る同一クラスの fail-open は、S-6 での統合時に本 ADR の保証範囲定義を引き継ぐ

### Addendum（2026-09-29）— pre-PR gate・merge gate の行継続は空白 + 改行に置き換えてから字句解析する

- pre-PR gate の inline python と merge gate（`gh_command_parse._tokenize_checked`）は、shlex の前に、行継続（エスケープされていない `\` + 改行）を空白 + 改行に置き換える。shlex（posix）は行継続を次の語の先頭の改行にするので、置き換えないと `&& \` + 改行 + `gh` の `gh` が改行つきの token になる。実データ（transcript の Bash コマンドのうち gh と create/new/pulls/graphql/merge を含む 19,840 件）で main が見落としていた `\` + 改行 + `gh pr create` 28 件・`gh pr merge` 47 件は、すべてこの形だった
- 改行を残す理由: 2 つの gate はコメントを shlex（pre-PR の top-level）か語頭の `#` の除去（merge gate と、pre-PR の `bash -c`・`eval` の本体）で扱う。行継続を消して前後をつなぐと、`\` で終わるコメントが次の行を飲み込む（bash ではコメントの中の `\` + 改行は行継続にならない）。改行を残せば、コメントは今までどおり行末で終わる。token の後で改行を落とす方式は、引用符の中の改行・空の値と区別できず、値の位置がずれるか、字下げ付きの行継続が改行だけの token として残った
- 語の途中（前後がどちらも語の文字。エスケープした区切り文字 `a\ ` も語の文字）の行継続は置き換えない。bash は `1\` + 改行 + `23` を 123 と読むので、2 語に割ると別の PR 番号として読む。残した分は 1 つの token の中の改行になり、PR を特定できない側に倒れる
- pre-push gate（本 ADR の `_strip_line_continuations`）と受理する入力が違うところ: 語の途中の行継続は、pre-push gate はつなぎ、2 つの gate はつながない（`g\` + 改行 + `h pr create` は見落とす）。二重引用符の中の行継続は、bash と pre-push gate は取り除き、2 つの gate は空白 + 改行にする（区切りの隣）か、`\` + 改行のまま残す（語の途中）。gh の語と PR 番号の判定には効かないが、PR 本文の機密検査は、行継続で折った秘密（`-----BEGIN PRIVATE \` + 改行 + `KEY-----`）に当たらない（main も同じ）。行継続が続く形は 1 まとまりで判定する。heredoc の導入行が行継続で終わる形（`cat <<'EOF' && \` + 改行 + `gh …`）は、heredoc の本文の除去が物理行の単位なので、次の行の gh を見落とす（main も同じ）

### Addendum（2026-10-13）— 字句解析の芯を共有し、ADR-5 の字句層の決定を bash の読みに置き換える

- pre-push gate・root-branch guard・merge gate・pre-PR gate は、字句解析の芯（`hooks/scripts/lib/shell_lexer.py`）を共有する。ADR-5 の「`#` をコメント扱いしない」は、「語頭の `#` から行末までをコメントとして落とし、語の途中・引用符の中・`$(…)`・バッククォート・`${…}` の中の `#` は残す」に置き換える。引用の文脈はスタックで追い、二重引用符の中の置換・展開の中の `"` は外の引用を閉じない
- 置き換えた理由: 行ごとの字句解析は引用符を行をまたいで追わず、複数行の commit メッセージの閉じ側の行で ` && git push … ` を引用符の中と読み、実データで push を 44 件見落としていた。芯は引用符を行をまたいで追い、引用符の外の改行だけを区切り token にする
- ADR-5 の「行継続はバックスラッシュのエスケープを数えて除去する」は保つ。ただし除去するのは引用符の外と二重引用符の中だけで、単引用符・`$'…'` の中では残す（ADR-6 の Consequences の「シングルクォート内の `\` + 改行も除去する乖離」は解消した。`$'…'` の中は bash の読みに合わせ、zsh とは割れる）
- 引用符が末尾まで閉じない入力（bash は手前の行を実行し、zsh は何も実行しない）は縮退として扱い、pre-push の検出は芯の読みと行ごとの読み（行継続だけを処理し、`#` は落とさない）の和にする。opt-out・cd・refspec は検出した側の読みで決める
- 保証範囲は ADR-6 のとおり CORPUS に限る。CORPUS には、引用の中の置換・展開の 3 形、複数行の commit メッセージの後の push、引用した heredoc の行末の `\`、コメント行の後の push、`2>&1` を足した

## ADR-7: 述語の正本は「実装済み・承認済みの層」に寄せ、回帰ガードの変異は方向・型・対象レイヤの 3 軸で起こす

> 初版（T-9 / 2026-08-18）は「方向 × 型」の **2 軸**として決定した。T-10 impl-gate Attempt 1 の H-1 を受けて **対象レイヤ**を第 3 の軸として追加している。以下の Context / Decision / Why / Consequences は初版のままで、追補は末尾の § Addendum（T-10 / 2026-08-18）— 対象レイヤ軸の追加 が正本。

### Context

T-9 impl-gate Attempt 1 で 2 つの構造的な問題が出た。

1. 証跡 sha の値ドメインという**同じ述語**の正本が 2 箇所に分かれていた。`lib/self-review-evidence.sh` は 7〜40 桁の hex を valid とし（T-5 で approved 済み）、`run-pre-push-gate-hook.sh` は 40 桁完全一致でしか通さない。結果、書式検証を通った 12 桁の証跡が恒久 `sha-mismatch` になり、block reason に桁数要件が無いため復旧経路が無かった（AC-3 の「証跡 sha を更新すれば通る」が成立しない）。
2. gate 独立 mutation が、explicit ref から解決した `TIP_SHA` を直後に `$HEAD_SHA` で上書きする変異を **31 test 全 PASS のまま** 通した。T-8 Attempt 2 で採った「変異は fail-open 方向と誤爆方向の**両方向**から起こす」規則は適用されていたが、変異集合は依然すべて**分岐の変異**（条件を偽にする / 分岐を削る）で構成されていた。

### Decision

- **同じ述語の正本が複数層に現れたら、実装済み・承認済みの層に寄せる**。T-9 では `lib` 側（7〜40 桁）を正本とし、hook 側で比較前に `git rev-parse --quiet --verify "<sha>^{commit}"` により full sha へ正規化する。解決不能・曖昧 prefix は空文字に落ちて block（当時。fail-closed の向きは不変）。逆向き（lib を 40 桁必須へ狭める）は approved 済み task の Files に触るため採らない
- **mutation の生成規則を「方向 × 型」の 2 軸に拡張する**。方向 = fail-open / 誤爆。型 = **分岐型**（条件・分岐そのものを壊す）と**値置換型**（正しく解決した中間結果を、別の解決済み変数や定数で上書きする = resolve-then-discard）
- **値置換型には「差のある fixture」をセットで用意する**。代替値と解決結果が一致する fixture（tip == HEAD、active root == process cwd）しか無いと、この型は原理的に観測できない

### Why

- 述語の二重化は「片方だけが緩い / 厳しい」形で必ず非対称を生む。どちらかを正本と決めずに両方に書くと、修正のたびに別の箇所で再発する。承認済み・実装済みの層を正本にすれば、正本を動かす判断が approved scope の変更として可視化される
- 分岐型だけの変異集合は「その分岐が存在するか」しか問えない。gate が守る述語の多くは**値の正しさ**（どの ref の tip か / どの root を基準にしたか / どの sha を記録したか）なので、値を差し替える型を持たないと中心 claim に穴が空いたまま緑になる
- 実測: 本規則を T-9 remediation に適用したところ、gate が挙げていない survivor を 2 件（`PROJECT_ROOT` ← `PROCESS_CWD` = AC-17 面 / `HEAD_SHA` ← 定数 `unknown` = AC-19 のログ `head` 面）自力検出できた。方向の拡張だけでは検出できなかった面である

### Consequences

- 短縮 sha の証跡が通るようになる。恒久 block による復旧不能経路は消えた。桁数契約の正本が `lib` 側であることは design.md § Honest Limitations に明記した
- 正規化のため `git rev-parse` の呼び出しが 1 回増える（block 判定に到達した push のみ。python3 起動数は不変で design 115 行の制約に影響しない）
- 「回帰ガードの判別力不足」は T-4 / T-5 / T-7 / T-8 / T-9 と 5 タスク連続していたクラスで、本 ADR は方向拡張（T-8）に続く 2 段目の構造対策にあたる。**T-22 のレーン定義へ「方向 × 型」の 2 軸と差のある fixture の規律を反映する**
- 値置換型は変異数がおおむね倍になる。実行コストは増えるが、変異の適用はアンカー出現数 assert + ディスク再読込 assert + `bash -n` で機械確認する既存手順に乗せられる

### Addendum（T-10 / 2026-08-18）— 対象レイヤを第 3 の軸として追加

#### 追加の Context

T-10（`hooks.json` への配線）の impl-gate Attempt 1 で H-1 が出た。gate 独立の**配線 mutation** 6 形 + 対照で **KILLED 1 / SURVIVOR 5**。KILLED はエントリの完全削除のみで、matcher `Bash`→`Skill` / `Bash`→`bash`（大小文字）/ event `PreToolUse`→`SessionStart` / `timeout` 10→1 / `description` の `eight`→`seven` はすべて生存した。B / C / D はいずれも「script は存在し `hooks-wiring-lint` 上は wired だが、`Bash` tool 呼び出しで一度も起動しない」状態 = **AC-1 / AC-25 が本番で無言のまま fail-open する形**を作る。

原因は 2 つとも「見る場所が無い」ことにあった。(1) `tests/checks/hooks-wiring-lint.sh` は `hooks.json` の全 event / 全 matcher を平坦走査して `run-*.sh` の出現有無しか見ないため、event 名・matcher 値・timeout を一切 assert しない (2) 既存 38 contract test は `hooks.json` を一度も開かない。

そして T-10 自身は、この lint に配線面の判別力があるという（実測で偽の）前提に立って `Mutation` 欄に「設定のみの diff で新規ロジックがないため新規 mutation は不要（YAGNI）」と書いていた。

#### 追加の Decision

- **mutation の生成規則を「方向 × 型 × 対象レイヤ」の 3 軸へ拡張する**。対象レイヤ = **コード**（実装ロジック）/ **設定・配線**（`hooks.json` / manifest / 登録表など、実行されるコードを選ぶメタデータ）
- **設定・配線レイヤの標準変異 4 形**を規定する:
  1. 登録先の key / matcher / event を**隣の妥当な値**へ差し替える（`Bash`→`Skill`、`PreToolUse`→`SessionStart`）
  2. 表記ゆれを入れる（大小文字、区切り、別名）
  3. 数値パラメータ（`timeout` 等）を**下限割れ**させる
  4. 自己記述メタデータ（本数・列挙・説明中の数値）を実体からずらす
- **「diff が設定ファイルのみだから mutation 不要」という判断を禁止する**。config-only の diff では「その config が効いていることを assert するテスト」が唯一の判別面であり、mutation を省く理由がむしろ最も薄い
- 設定・配線レイヤの回帰ガードは、**設定ファイルを実際に開いて構造で assert する**テストとして書く。名前の grep や出現有無の走査は「wired」の証明にならない
- 自己記述メタデータの検査では、**期待値を設定ファイル自身から機械導出**し、テスト側に literal の数値を置かない（同じ数値が 2 箇所に生まれると、片方だけ直る形の不整合が再発する）

#### 追加の Why

- 既存の 2 軸（方向・型）はどちらも *実装ロジックを変異させる* ことを暗黙の前提にしている。したがって **diff が設定・配線ファイルのみのタスクでは変異集合が空になり、2 軸は自動的に無力化される**。これは軸の中身の不足ではなく、軸そのものの不足だった
- 配線は「実行されるかどうか」を決める層なので、ここが黙って外れると**下の全レイヤのテストが緑のまま gate が発火しなくなる**。判別力の欠落として最も影響範囲が広い
- 実測: 本規則を T-10 remediation に適用したところ、gate の 5 survivor に加えて gate が挙げていない 1 形（`Bash` entry 自体の matcher 差し替え）を自力で起票でき、**配線 mutation 8 形すべてで KILLED 7 / 7・対照のみ SURVIVOR** を実測した。方向・型の拡張だけでは検出できなかった面である

#### 追加の Consequences

- `tests/test_pre_push_gate_contract.py` に `PrePushGateWiringContractTests`（3 test）を追加した。既存の 38 test はすべて hook script の直接呼び出しで、`hooks.json` の配線面はこの 3 test が唯一の担保になる
- `hooks-wiring-lint` の役割は「エントリの完全消失の検出」に限定されることを明示した。これを配線面の担保として引用してはならない（T-10 の tasklist 記述はこの誤りを含んでいたため訂正済み）
- 「回帰ガードの判別力不足」は T-4 / T-5 / T-7 / T-8 / T-9 / T-10 と **6 タスク連続**。本追補は方向拡張（T-8）・型拡張（T-9）に続く **3 段目**の構造対策にあたる。**T-22 のレーン定義へは 3 軸すべてを反映する**
- 設定・配線レイヤの変異は隔離コピー上で行い、変異前後の**正規化 JSON が異なること**を `applied` として assert する（コードレイヤのアンカー出現数 assert に相当する機械確認）。無変異の対照を 1 形入れて harness が無条件 KILLED を返していないことを毎回裏取りする

---

## ADR-8: 実装タスクが先取りした contract surface は後続テストタスクへ「重複追加」せず、task 側を吸収・整理する

- 日付: 2026-08-18
- 起票: `gdd-design-gating`（route `design_detail_only` / `gdd-test-driven-development` からの差し戻しを受けて）
- 対象: T-11（廃止）/ T-12〜T-14（`Depends on` 付け替え + Step 0 追加）/ `design.md` § テスト方針

### Context

`tests/test_pre_push_gate_contract.py` は T-8（step 1〜6）→ T-9（step 7〜14）→ T-10 remediation（配線面）と積み上げられ、現在 41 test。tasklist の当初計画では、この後に T-11〜T-14 が観点別の契約テストを追記する予定だった。

T-11（AC-1 primary / AC-2 primary / AC-7 / AC-20 primary / CT-1）の RED 準備で `gdd-test-driven-development` が Contract Surface Coverage を照合したところ、draft の残り 5 test がいずれも既存 41 test の近似重複であることが判明した。scratchpad の隔離コピーで実装を一切変えずに probe 実行した結果 **5/5 が即 GREEN**（RED 不成立）。さらに `hooks/scripts/run-pre-push-gate-hook.sh:195-197` の

```
case "$TASK_SIZE" in trivial | "quick (express)" | "quick (standard)" | standard) ;; *) TASK_SIZE="standard" ;; esac
```

により、文字列 `standard` と `quick (standard)` は**同一 case アーム**にあり、片方だけを狙ったテストは mutation 上の差別化能力を持たないことも確認された。

原因は「実装タスクも自身の RED / mutation 証跡を立てるために同じ contract test ファイルへ書く」という構造で、T-9 の remediation（steps 7〜14 の追加とガード強化）が T-11 の割当 surface を先に飽和させた（over-delivery）。design.md の hook 判定順の仕様自体は正しく、誤っていたのは tasklist 側の「T-11 が何を新規に書くべきか」という task 詳細だった。

### Decision

1. **T-11 を廃止（superseded）し、T-8 / T-9 / T-10 remediation に吸収する。** テストの水増し追加は行わない
2. **AC の意味・境界値・許容値は一切変更しない。** 変更するのは primary owner 表記だけ:
   - `AC-1 primary: T-11 → T-9`（**2026-08-18 の planning reviewer 事後レビュー M-1 で T-8 から再訂正**。当初は T-8 へ移したが、T-8 自身の Attempt 記録が「AC-1 は step 10 の責務なので本タスクの Contract Surface から意図的に除外した」と明記しており、missing-evidence block のコードと契約テスト `test_step10_missing_pre_push_self_review_field_blocks_missing_evidence` を実際に持ち込んだのは T-9。「surface を最初に固定したタスク」規則に従い T-9 が正しい）/ `AC-2 primary: T-11 → T-8` / `AC-20 primary: T-9`（T-11 から移管）
   - `AC-7` は元から `primary: T-27`、`CT-1` は T-8 が引き続き carry するため変更なし
   - **同規則の水平展開（2026-08-18 / planning reviewer M-2）**: 同じ論拠は T-13 / T-14 の未着手 AC にも当てはまる。両タスクの Step 0 が **全面飽和**と断定した AC は primary を実装タスクへ移す — `AC-3 primary: T-14 → T-9`（`test_step11_*` 3 件）/ `AC-16 primary: T-13 → T-9`（`test_step8_*` と cross-ref tip の対）/ `AC-19 primary: T-14 → T-9`（`unresolved-steering` ログの 2 件と `test_logged_head_field_..._ac19`。GDD 外副作用ゼロ面は T-8 が carry）。一方 **Step 0 に未充足 surface が残る AC は後続タスクが primary を保持する** — `AC-17`（T-13: コマンド内 `cd` 経路 / `--work-tree` 形）/ `AC-18`（T-14: allow-list token 検査）/ `AC-25`（T-14: `Next Action: done` の配線層）。判定基準は「その primary owner が当該 AC の判別力を新規に 1 つ以上増やすか」であり、増やさない primary は T-11 と同型の空所有になる
3. **T-12 / T-13 / T-14 の `Depends on` を `T-11` → `T-10` へ付け替える**（T-10 は impl-gate Attempt 2 = `approved` で完了済みのため、3 タスクはいずれも即着手可）。`Stage Output Contract` の `Consumes` も「T-11 の fixture helper」から「T-8 / T-9 / T-10 remediation の fixture helper（再定義禁止）」へ是正
4. **上書き事故ガードの件数正本を T-11 § Verification から T-12 § Verification へ移設する。** 数値は引き続き 1 箇所のみに置き、本 ADR を含む他の文書は**参照だけ**を持つ（2026-08-18 / planning reviewer M-3 で、移設後も 4 箇所に併存していたため参照へ統一）
5. **T-12〜T-14 に `Step 0: Contract Surface Coverage 事前照合` を必須ステップとして追加する。** 照合の単位は「入力値」ではなく「分岐」とし、同一 case アーム内の値違いは新規 surface に数えない。全観点が飽和していた場合は重複追加せず `superseded` として design gate へ戻す
6. `design.md` § テスト方針 に「契約テストの所有と RED 成立条件」節を追加し、上記を設計の正本として固定する

### Why

- **AC カバレッジに穴が開かないことを機械確認した。** tasklist の全タスクから `Covers AC` / `Covers Critical Trace` を横断集計した結果、T-11 を除いても AC-1〜AC-25・CT-1〜CT-6 のいずれもカバレッジ 0 にならない:
  - `AC-1`: T-1 / T-8 / T-10（いずれも完了）
  - `AC-2`: T-8（完了）
  - `AC-7`: T-15 / T-16 / T-27（primary は T-27）
  - `AC-20`: T-9（完了）
  - `CT-1`: T-8（完了）
  - 他の 20 AC・5 CT は T-11 を参照していないため影響なし
- **実測で飽和を裏取りした。** design gate 側でも `python3 -m pytest tests/test_pre_push_gate_contract.py -q` を再実行し **41 passed, 29 subtests passed** を確認したうえで、T-11 の 4 AC + CT-1 に対応する既存テスト（`test_step7_next_action_non_done_..._ac25` / `test_step10_missing_pre_push_self_review_field_blocks_missing_evidence` / `test_full_flow_registry_bound_..._passes` / `test_step8_cross_ref_push_passes_..._ac16` / `test_step9_quick_express_does_not_require_dry_passes` / `test_step9_quick_standard_requires_dry_blocks_when_dry_no` / `test_step9_task_size_case_and_unknown_values_normalize_to_standard_ac20` / `test_step9_trivial_bypasses_unconditionally_..._ac20` / `test_no_active_steering_anywhere_exits_silently_ct1` / `test_active_marker_false_treated_as_non_active` / `test_non_active_repo_git_dir_push_is_not_blocked_ct1`）を個別に確認した。**AC-20 の Task Size 分岐についての正確な実測（2026-08-18 / planning reviewer M-6 で訂正）**: 4 値のうち専用テストを持つのは 3 値のみで、リテラル `standard` に**専用テストは無い** — `trivial` = `test_step9_trivial_bypasses_unconditionally_regardless_of_evidence_state_ac20`（3 subTest）/ `quick (express)` = `test_step9_quick_express_does_not_require_dry_passes` / `quick (standard)` = `test_step9_quick_standard_requires_dry_blocks_when_dry_no`。`standard` は `test_step9_task_size_case_and_unknown_values_normalize_to_standard_ac20`（`  STANDARD  ` / `banana` の 2 subTest がいずれも `standard` へ正規化され `Task Size: standard` を reason に含めて block）が代表として固定し、加えて `task_size="standard"` fixture を使う block / pass 系テスト 16 本（2026-08-18 実測）が同アームの挙動を毎回通過させている。**結論（T-11 廃止の妥当性）は維持する** — 4 値は `case` の別アームとして全て観測されており、T-11 draft が足そうとした `standard` 単独テストは同一アーム内の値違いに過ぎず mutation 上の判別力を増やさない（本 ADR § Decision 5 の「照合の単位は分岐」に該当）。誤っていたのは「4 値すべてが**別々の**テストで固定されている」という記述だけである
- **重複テストを足す方が有害。** 判別力を増やさないテストは実行時間と読解コストだけを増やし、「テストがあるから守られている」という誤った安心を作る。GDD の mutation 規律（ADR-7 の 3 軸）とも整合しない
- **`human_recheck_required` に昇格しない根拠**: AC の根本追加 / 削除 / 意味変更・境界値変更に該当しない（primary owner 表記の移管のみ）。`Approved Direction` の方向性、final output owner / delivery path / prompt-output contract / masking enforcement / rollout order、technology stack / access method / credential backend のいずれも変わらない。`references/rollback-patterns.md` § design_detail_only の適用条件を満たす

### Consequences

- 既存 41 test は 1 つも削除・変更していない。production コードも無変更
- T-12 が Current Task へ昇格し、`Next Action=gdd-test-driven-development` で即着手できる
- **T-12〜T-14 も同じ飽和リスクを持つため、design gate が実測して「実際に RED が立つ surface」を各タスクに明記した**（Step 0 配下）。これにより T-11 と同型の差し戻しの再発を防ぐ:
  - T-12: `GDD_SKIP_PRE_PUSH_GATE=1 git rev-parse HEAD && git push ...`（代入列はコマンド先頭だが push が別セグメント）の非受理、および opt-out 肯定側の `env` 形 / `/usr/bin/git` 絶対パス形 / 行継続形。draft 6 test のうち 5 test は既存テストで飽和済み
  - T-13: AC-17 の優先順第 2 位「コマンド内 `cd`」経由の候補 root 解決、および `--work-tree` を伴う形。refspec 面（`--all` / `--mirror` / 複数 refspec / 未解決 explicit ref / cross-ref tip 照合）は飽和済み
  - T-14: **`Next Action: done` fixture でも block されること**（design.md § steering resolver の設計 § テスト追加（必須）および § テスト方針 が二重に必須指定）。既存 41 test の steering fixture は `next_action` が `gdd-implementation-gating` / `gdd-design-gating` のみで `done` を 1 件も含まない（`grep -n '"done"' tests/test_pre_push_gate_contract.py` が 0 件）。**精度の注記**: `gdd_pre_push_resolve_steering` の union 分岐（`Resume From == done || Next Action == done`）自体は lib 単体テスト `tests/test_self_review_evidence.sh` の T6-2 / T6-3 で固定済みなので、空いているのは **hook がその lib 結果を受けて実際に block へ落とす配線**の層。post-completion PR flow（`Next Action=done` 確定後の push）は実運用で最頻の経路であり、ここが fail-open すると AC-1 の中心価値が経路依存で失われる。次いで AC-18 の allow-list 文法による token 単位検査（既存は 3 要素の存在と slug / 絶対パスの非混入までで、token 単位の許可文法照合は未実装）。resolver 面のうち `Resume From: blocked` / multiple / registry binding と block reason 3 要素は飽和済み
- **副次的な bookkeeping 是正**: Completed Tasks 配下にありながら `Execution Status: in_progress` のままだった T-10 を `completed` に是正した
- 本 ADR は ADR-7（回帰ガードの変異は方向・型・対象レイヤの 3 軸）の運用面の続き。ADR-7 が「変異をどう起こすか」を定めたのに対し、本 ADR は「その変異で既に守られている surface に、後続タスクがテストを重ねない」ための task 分割側の規律を定める

### Addendum（2026-08-18 / planning reviewer 事後レビュー反映）

ADR-8 は `gdd-design-gating` の 2 回の subagent 実行がいずれも reviewer 待ちで return したため、controller の verification で承認していた（state.md § Design Review Status）。その後 `gdd-planning-reviewer` が事後レビューを完走し **High 2 / Medium 7** を指摘。reviewer 自身が「`design_detail_only` で閉じてよい（`human_recheck_required` / `planning_rework_required` への昇格は不要）」と判定しており、**AC の追加・削除・意味変更は行っていない**。反映内容は次のとおり。

| ID | 指摘 | 反映先 |
|---|---|---|
| H-1 | T-12〜T-14 の Step 1 code block が旧 draft のままで Step 0（飽和済みは書くな）と矛盾。literal 実行すると T-11 の失敗モード（即 GREEN）を再現する | tasklist.md T-12 / T-13 / T-14 § Steps 1 を **Step 0 で未充足と確定した surface のぶんだけ**に差し替え。飽和済み draft は削除 |
| H-2 | T-11 廃止で helper の所有者が消え draft が実行不能（`self._decision` を 11 箇所で使用するが実ファイルに不在 / `self._optout_state_dir` はどのバージョンにも不在 / `_write_steering(..., sha=)` は T-11 draft 版シグネチャで実在の T-9 版は `TypeError`） | (a) `_decision` を **T-12 § Produces** へ移管（T-12 が定義し T-13 / T-14 が消費）(b) opt-out ログ経路を `extra_env={"GDD_HOOK_STATE_DIR": ...}` 形へ書き換え (c) `_write_steering` の実シグネチャ（`sha` キーワード無し・`evidence=` に完成行を渡す）の申し送りを **T-13 / T-14 の `Consumes` へ複製**（T-9 impl-gate M-3 の「申し送りが 1 エントリにしか無い」再発の是正） |
| M-1 | AC-1 primary の三つ巴矛盾（ADR-8 は T-8 / T-8 の Attempt は「意図的に除外」/ テスト docstring は T-14） | 本 ADR § Decision 2 で `AC-1 primary: T-9` に確定。`tests/test_pre_push_gate_contract.py` の該当 docstring も同時訂正 |
| M-2 | 「primary = surface を最初に固定したタスク」規則が AC-3 / AC-16 / AC-19 に未適用 | 適用して `AC-3 → T-9` / `AC-16 → T-9` / `AC-19 → T-9`。保持する AC（AC-17 / AC-18 / AC-25）の根拠も § Decision 2 に明記 |
| M-3 | 「唯一の正本 41」が 4 箇所に併存 | 正本を tasklist.md T-12 § Verification の 1 箇所に固定し、T-11 § Verification / L-17 / T-10 gate 記録 / design.md § テスト方針 / 本 ADR の計 5 箇所を**参照**へ書き換え |
| M-4 | T-13 / T-14 の `Produces` が Step 0 と矛盾 | T-12 と同型（「Step 0 の照合で未充足と確定した surface のみ」）に是正 |
| M-5 | design.md の opt-out 否定側 5 形のうち commit message 形 / `--` 以降形が Step 0 のどちらの表にも無い | 実測のうえ **hook レベルで独立 surface にならない根拠**（いずれも `has_optout == False` 分岐に落ち、opt-out 無しの通常 push を扱う既存 block 系テスト群が飽和させている）を design.md § テスト方針 と T-12 Step 0 に記録 |
| M-6 | ADR-8 の Why「4 値すべてが別々のテストで固定されている」が実測とずれる | § Why を実測に訂正（`standard` に専用テストは無く正規化テスト + 16 本の standard fixture が代表）。結論は維持 |
| M-7 | design.md が必須指定する「`push_command_parse.py` を contract test から直接 import する単体テスト 1 本」に所有タスクが無い | `tests/test_push_command_parse.py`（T-1 作成済み・97 test・冒頭 docstring に本要件を明記）が意図を充足するとして **design.md 側を訂正**。重複 import テストを契約テストへ足すのは ADR-8 が禁じた水増しに当たるため新規 owner は割り当てない |

**AC カバレッジへの影響**: なし。reviewer が AC-1〜25 が各 1 個の primary を持つこと・CT-1〜6 の充足を独立検証済み。既存 41 test は 1 つも削除・変更していない（M-1 の docstring 訂正のみ）。production コードも無変更。

---

## ADR-9: T-16（pre-PR gate dry gate テスト追記）は T-15 の統合 RED サイクルで全面飽和のため superseded とし、AC-6 primary を T-21 へ移管する

- 日付: 2026-08-18
- 起票: `gdd-test-driven-development`（T-16 の Step 0 自力再実行の結果）
- 対象: T-16（廃止）/ T-19・T-21（`AC:` へ AC-6 追記）/ tasklist.md Current Task（T-17 昇格）

### Context

T-16 の担当は `tests/test_pre_pr_gate_contract.py` への dry gate ケース追記（AC-5 の block/pass 双方向、AC-6 の round/lane 書式検証、AC-7 の express 免除側）。ただし T-15 の RED 準備時点で「T-15 単独では RED が観測できない」構造問題が判明し、T-15/T-16 は 1 RED サイクルへ統合され、T-16 が書く予定だった 4 test（block-without-evidence / block-when-dry-not-reached / pass-with-dry-yes / unknown-case-normalization）と `_write_steering` の `task_size` / `pre_pr_self_review` kwarg 拡張が T-15 の Current Task 内に先取り実装された（54→58 test）。続く T-15 impl-gate Attempt 1 の remediation で、M-1（block reason の 3 要素肯定側 assert）・L-27（Task Size 正規化の回帰ガード）・L-28（`trivial` 免除の回帰ガード）も同ファイルへ追記された（58→60 test）。

T-16 の Carry Forward はこれらを「hypothesis として扱い、Step 0 を自力で再実行せよ」と明記していたため、`gdd-test-driven-development` が改訂 4 段の Step 0（写像元 2 つ = AC-5/AC-6/AC-7 本文 + design.md § テスト方針、単位は分岐）を実行した。

### 実測（Step 0・4 段）

1. **Current Task の AC / Planned RED を確認**: AC-5（primary は既に T-15 へ移管済み）/ AC-6（primary: T-16 表記だが Completion Testability Matrix は Evidence を `validate-steering-write.py` の deny fixture と定義しており本ファイルの対象外）/ AC-7（primary は T-27）
2. **AC 本文（requirements.md）を直接読み、受理/拒否条件を分岐へ分解**:
   - Task Size 正規化（`tr`+`sed`）→ 免除アーム（`trivial` / `quick (express)`）と通常アーム（それ以外すべて。同一 case アームのため入力値差は新規 surface に数えない）
   - 通常アーム: 証跡 invalid（`GDD_SR_VALID != true`）→ `missing-evidence` ／証跡 valid かつ `dry != yes` → `dry-not-reached` ／証跡 valid かつ `dry == yes` → pass
   - 免除アーム: 証跡なしで無条件 pass
   - block reason の 3 要素（記録先・不足 key・逃げ道）× 2 reason code（AC-5 の block reason 品質要件）
3. **design.md § テスト方針 / § Route・Ownership Matrix / § 証跡フィールドの書式 を突合**: pre-PR gate 固有の追加次元なし（sha 一致検査は AC-5 に無い。kill-switch は既存の別経路で本 file の対象外）
4. **既存 test との突き合わせ（単位は分岐）**: 上記すべての分岐が既存 60 test で個別に固定済み — `test_standard_task_size_blocks_without_pre_pr_self_review_evidence_ac5` / `test_standard_task_size_blocks_when_dry_not_reached_ac5` / `test_standard_task_size_passes_with_dry_yes_evidence_ac5` / `test_task_size_unknown_case_and_whitespace_values_require_dry_ac5` / `test_exempt_task_sizes_skip_dry_gate_without_evidence_ac7` / `test_dry_gate_block_reasons_carry_recovery_elements_and_leak_nothing`。`dry-consecutive-clean-contradiction`（`gdd_parse_self_review_field` 内部の自己矛盾判定）は pre-PR hook レベルでは `missing-evidence` と同一分岐に集約され、design.md「hook 層と lib 層で二重に同じ入力を並べない」のとおり `tests/test_self_review_evidence.sh` が lib 単体で既に固定している

`python3 -m pytest tests/test_pre_pr_gate_contract.py -q` を独立実行し **60 passed, 11 subtests passed** を確認。T-16 draft 3 test（`class DryGateTests(PrePrGateContractTests)` 形）を実行しても既存 6 test 群と同一分岐しか踏まないため即 GREEN（RED 不成立）になる（継承クラス形自体も design.md ADR-8 addendum が禁じるパターン）。

結果: **未充足 surface 0 件。全面飽和**。

### Decision

1. **T-16 を廃止（superseded）とし、テストの水増しは行わない。** Contract Surface は T-15（Current Task 内の先取り実装）と T-15 impl-gate remediation に吸収済み
2. **AC の意味・境界値・許容値は変更しない。primary owner 表記のみ変更**:
   - `AC-5 primary`: 既に T-15（変更なし。T-16 Carry Forward の既存記載を確認したのみ）
   - **`AC-6 primary: T-16 → T-21`**。Completion Testability Matrix（requirements.md）が AC-6 の Evidence を「`validate-steering-write.py` の deny fixture」と定義しており、T-16 の対象ファイル（`tests/test_pre_pr_gate_contract.py`）はそもそも AC-6 を固定する場所ではなかった（T-16 Carry Forward が「primary 表記は据え置くが実際の証跡は T-19/T-21」と既に記録していた保留事項）。T-16 廃止に伴いこの保留を解消する。T-21 の `test_edit_to_malformed_value_denies_even_with_prior_valid_line`（`rounds` のみで `consecutive_clean`/`dry`/`lanes` が欠落した Edit を deny）が AC-6 の「round/lane 検出数の欠落を書式検証で検出できる」を実際に固定する
   - `AC-7`: primary は元から T-27（変更なし）。T-16 が Covers していた express 免除側の実測は T-15 remediation の `test_exempt_task_sizes_skip_dry_gate_without_evidence_ac7` が引き続き担う
3. `T-19`（実装）/ `T-21`（primary の契約テスト）の `AC:` 行に `AC-6` を追記する
4. `Pending Tasks` の先頭 `T-17` を `Current Task` へ昇格する（`Depends on: T-15` は充足済み）

### AC カバレッジ確認（横断集計）

tasklist 全体を `AC-1`〜`AC-25` / `CT-1`〜`CT-6` で横断 grep した結果、いずれも 1 件以上のタスクが言及しており、T-16 を除いてもカバレッジ 0 になる AC/CT はない。T-16 が primary 指定先だった AC は **AC-6 のみ**（AC-5 primary は既に T-15、AC-7 primary は既に T-27）で、上記 Decision 2 で解消した。他の AC/CT に primary owner の穴は生じない。

### Why

- AC-6 の primary を放置すると、廃止された T-16 が唯一の primary owner のまま残り、ADR-8 の T-11 と同型の「新規に何も固定しない primary owner」の空所有が発生する
- 重複テストを足す方が有害（ADR-8 と同じ理由）。T-16 の draft 3 test はいずれも既存 6 test 群と同一分岐を狙っており、追加しても判別力は増えない
- **`human_recheck_required` に昇格しない根拠**: AC の追加・削除・意味変更に該当しない（primary owner 表記の移管のみ）。`Approved Direction` の方向性、final output owner / delivery path / prompt-output contract / masking enforcement / rollout order、technology stack / access method / credential backend のいずれも変わらない。`references/rollback-patterns.md` § design_detail_only の適用条件を満たす

### Consequences

- 既存 60 test は 1 つも削除・変更していない。production コードも無変更
- T-17 が Current Task へ昇格し、`Next Action=gdd-test-driven-development` で即着手できる
- T-19 / T-21 の `AC:` 行に AC-6 を追記した（primary は T-21）

---

## ADR-10: AC-11 の「抽出」面は既存 `gdd_extract_doc_field` で充足しているとし、T-20 が追加した薄いラッパーは撤回する

- 日時: 2026-08-18
- 起票: `gdd-systematic-debugging`（impl-gate T-20 Attempt 1 = `changes_requested` の remediation）
- route: `design_detail_only`（`design.md` 変更点 6 の訂正を伴うため。AC は無変更）

### Context

T-20 は `hooks/scripts/lib/detect-steering.sh` に `gdd_extract_self_review_evidence_field`（`gdd_extract_doc_field` へ引数そのままで委譲する 7 行の薄いラッパー）を追加した。狙いは「pre-push / pre-PR の両 gate が同じ抽出規約を使っていることをコード上で確認できるようにする」ことだった。

impl-gate Attempt 1 の実測:

| 観点 | 実測 |
| --- | --- |
| 呼び出し元 | repo 全域（`.steering` 除く）で**定義行 1 件のみ** = 0 caller |
| 両 gate の実経路 | `run-pre-push-gate-hook.sh` / `run-pre-pr-gate-hook.sh` → `gdd_parse_self_review_field`（`lib/self-review-evidence.sh`）→ 同関数内で `gdd_extract_doc_field` を**直接**呼ぶ |
| 関数を丸ごと削除した隔離コピー | `pytest tests/ -q` **1015 passed, 1 skipped, 968 subtests**（baseline 完全一致）/ `validate-plugin.sh` exit 0 / `test_self_review_evidence.sh` pass = **判別力ゼロを機械証明** |
| planned verification `wrapper_equals_canonical` | 「委譲していること」ではなく「1 fixture で同値を返すこと」しか見ておらず、**委譲を捨てた独自 sed 実装が SURVIVOR**（ops-blocking M-2）。しかもその独自実装は backtick + markdown list 形で canonical と挙動が割れる（canonical は値を返すが空文字を返す）|

### Decision

1. **`gdd_extract_self_review_evidence_field` を削除する**（`detect-steering.sh` は追加前の 374 行へ復帰）。
2. **`design.md` 変更点 6 を訂正する** — 当該行の種別を「変更（関数追加）」から「**無変更**」へ改め、AC-11 の「抽出」面は既存 `gdd_extract_doc_field` が担うことを明記する。
3. **AC-11 は無変更**。AC-11 の本文が要求しているのは「`hooks/scripts/lib/detect-steering.sh` が両 hook 向けに値を抽出できる」という **capability** であり、特定のラッパー関数の存在ではない。既存 `gdd_extract_doc_field` は `detect-steering.sh` に定義され、両 hook が唯一の入口 `gdd_parse_self_review_field` 経由で実利用しているため、AC-11 は削除後も文言どおり充足する。
4. **T-20 の Verification を「委譲の観測」へ差し替える**（M-2 の解消）。旧 `wrapper_equals_canonical` を撤去し、(b) `gdd_extract_doc_field` を番兵 stub で空返しにしたとき `gdd_parse_self_review_field` が「field 行なし」と判定するか（= 委譲の直接観測）、(c) backtick + markdown list 形での抽出値、(d) 両 hook からの入口呼び出し数（`grep -cw`）、(e) 撤回した wrapper が復活していないこと、を機械検査する。
5. **T-21 の `Depends on` から `T-20` を除去する**（T-21 が Consume するのは `validate-steering-write.py` と `gdd_parse_self_review_field` のみで、T-20 の追加物に依存していなかった）。

### 却下した代替案: (a) ラッパーを配線して実体を与える

impl-gate が推奨した「`self-review-evidence.sh` の `gdd_extract_doc_field` 呼び出しをラッパー経由へ置換する」案は採らない。理由:

- **主張された保証を回復しない**。「片方の gate が独自抽出を始めたら差分に現れる」という当初の狙いは、配線後も成立しない。独自抽出を始める gate は `gdd_parse_self_review_field` ごとバイパスするため、その 1 段下にあるラッパーには何の差分も出ない。配線は「dead code でなくなる」だけで、保証の実体は増えない。
- **単一点を 2 つにする**。抽出規約の単一点は T-19 remediation で `gdd_parse_self_review_field` に一元化したばかりで、そこへ振る舞い不変の pass-through をもう 1 段挟むのは DRY ではなく重複の追加になる。
- **同型の再演になる**。「宣言だけで機構を伴わない保証」は T-19 gate の `delegates_to_shipped_parser`（docstring の言及だけで常に充足）と同じクラスで、ADR-8 § Consequences が禁じた「守られているという誤った安心」を production コード側で作る。
- (a) を採っても M-2 は別途「委譲の観測」へ差し替える必要があり、その検査は**ラッパーが無くても書ける**（実際、本 ADR の Decision 4 がそれ）。ラッパーは検査の前提条件ではない。

### Why

- **AC-11 は capability を要求しており、実装形（ラッパー関数の存在）は要求していない**。要求文を実装形として読んだことが、呼び出し元 0 件の追加物を生んだ。
- 判別力ゼロの production コードは、判別力ゼロのテストと同じ害を持つ（ADR-8 § Consequences）。読む側は「共通経路がある」と誤読し、実際の共通経路（`gdd_parse_self_review_field`）から注意を逸らす。
- 検査は「同値であること」ではなく「委譲していること」を見なければ、規約差し替えを検出できない。M-2 の SURVIVOR は 1 fixture の同値検査の構造的限界を実測で示した。

### `human_recheck_required` に昇格しない根拠

- AC の追加 / 削除 / 意味変更に該当しない（AC-11 は無変更で、充足経路の記述を実装の実体へ合わせただけ）
- `Approved Direction` の方向性、final output owner / delivery path / prompt-output contract / masking enforcement / rollout order、technology stack / access method / credential backend のいずれも変わらない
- `Human Recheck Boundary`（AC-1〜25 の意味変更 / CT 変更 / escape hatch 受理面の拡張 / block reason の allow-list 拡張 / PR-W1 非スコープファイルへの接触）のいずれにも抵触しない
- Scope Drift Counter: **+0**（`references/rollback-patterns.md` § design_detail_only の Counter マトリクス「naming / comment only（振る舞い不変）」相当。削除対象は呼び出し元 0 件で実行経路に乗っておらず、production の振る舞いは前後で完全に同一）
- `scripts/lint-approved-direction.py` = **glob pattern 未宣言**（Approved Direction が散文のため exit=2 / `INFO: no Approved Direction patterns found`）。単一ファイル固定 glob の ERROR は非該当

### Consequences

- `hooks/scripts/lib/detect-steering.sh` は本 PR で **無変更**（374 行）。T-20 は production 成果物を持たないタスクになり、成果物は「AC-11 の抽出面が既存経路で成立していることを固定した検査」になる
- 撤回した wrapper の復活は Verification (e) `dead_wrapper_files=0` が検出する（変異 N4 で KILL を実測）
- M-2（ops-blocking）は Verification の差し替えで解消。SURVIVOR だった独自 sed 実装への変異（N1）が `delegates_to_detect_steering=False` で KILL されることを実測した
- AC-11 のテスト所有は T-21（primary）のまま。抽出面の回帰を実際に固定しているのは既存 `tests/test_self_review_evidence.sh`（`gdd_parse_self_review_field` 経由で `gdd_extract_doc_field` を実行する 40 件超の parse テスト）= **カバレッジの穴なし**。**2026-08-18 訂正（impl-gate T-20 Attempt 2 の実測）**: 本行は当初 `tests/test_steering_detection_contract.py` も抽出面を固定すると併記していたが、gate 独立の変異実測でこれは**誤り**だった — `gdd_extract_doc_field` の backtick 正規化削除（N2）でも定数返し（N5）でも `test_steering_detection_contract.py` は **5 passed で素通り**する一方、`test_self_review_evidence.sh` は N2 で **1 FAIL** / N5 で **57 FAIL** を出す。抽出面の retention は `test_self_review_evidence.sh` 単独が担っている。結論（カバレッジの穴なし）は変わらないが、根拠は 1 suite に絞る
- 本 ADR は ADR-8（判別力を増やさないテストを重ねない）/ ADR-9（T-16 廃止）と同じ系列。ADR-8 が test 側、本 ADR が **production コード側**で同じ規律を適用した事例になる
- **design-gating 再審査での追補（2026-08-18 / `gdd-planning-reviewer` M-A・M-B）**: 変更点 6 の種別訂正は 2 箇所へ波及するため同時に是正した。(1) `design.md` § Requirements Trace の AC-11 行を `変更点 5, 6, 8` → **`変更点 2, 5, 8`** へ更新（「抽出」面を本 PR で成立させている実体は変更点 2 の `gdd_parse_self_review_field` であり、無変更の変更点 6 を実装箇所として辿らせない）。(2) `tasklist.md` T-20 § Contract Surface Coverage の 3 項目（no-op / validation / user-visible）の根拠を「薄いラッパー」前提から「**production 追加物を持たない**」へ書き改め、撤回済みの関数を現存物として記述した状態を解消した

## ADR-11: 並行 PR 禁止リストは「所有者の実測」で失効判定し、CT-6 の測定述語を `main...HEAD` に固定する

- **Status**: Accepted（2026-08-19。ユーザー承認済み）
- **Context**:
  - 2026-08-17 の requirements 策定時、並行 worktree PR-W1（`20260816-pr-w1-dialogue-ux`）が 36 ファイルを同時変更していたため、§ 非スコープ に 15 ファイル（glob 含む）の禁止リストを置き、CT-6 で「最終 diff に禁止リストのファイルが含まれない」を受入条件にした。禁止理由は **merge 時の conflict 回避と所有者の一意化**であり、ファイル自体の不可触性ではない
  - T-22（`b7dee77`）が `tests/checks/skill-body-budget.sh` の `required_files` に新設レーン正本 `references/self-review-lanes.md` を 1 行登録した。**変更内容は妥当**（新規正本の実在を fail-closed に守る）だが、当時の禁止リストに載っていた
  - T-22 gate はこれを見逃した。記録された scope guard が `git diff --name-only HEAD`（未コミット差分）で、CT-6 が要求する `main...HEAD`（PR 差分）ではなかったため。**測った述語と書いた述語のずれ**（分類5）
  - T-29 impl-gate が `main...HEAD` で実測して M-3 として検出。`adr.md` が「PR-W1 非スコープファイルへの接触」を Human Recheck Boundary に置いているため、gate の裁量では受容できなかった
- **Decision**:
  1. 禁止リストを **live / 失効の 2 段**に分け、失効判定を **(a) 当該ファイルを変更中の open PR・未マージ branch・未コミット worktree 変更がゼロ** かつ **(b) `git merge-tree --write-tree main HEAD` で当該ファイルが無競合**、の AND でファイル単位に行う。判定は実測コマンドの結果を伴って記録する
  2. 2026-08-19 の実測により 14 ファイルを失効させ、`tests/test_p0_p1_operational_hardening_contract.py` の 1 件を **live のまま残す**（所有者が PR-W1 から open PR 旧#5 へ移っただけで前提は生きている）。**禁止集合は空にしない**
  3. CT-6 の証明手順を requirements 本文に固定する。`git rev-parse main origin/main` で基準の同期を確認したうえで `git diff --name-only main...HEAD` を用い、`git diff --name-only HEAD` / `git diff main`（two-dot）/ `git show <commit> --stat` での代用を**明示的に不許可**とする
  4. T-22 が入れた 1 行は revert しない（内容妥当・無競合・所有者不在）
- **Rejected Alternatives**:
  - **(a) 当該 1 行を revert し、`required_files` 登録を別 PR へ切る**: CT-6 は形式上満たせるが、本 PR が新設する `references/self-review-lanes.md` の実在を守る検査だけが別 PR に取り残され、マージ直後に「正本が消えても検知されない窓」が開く。禁止の理由（並行所有）が既に消えているのに形式だけ守る選択で、コストに見合わない
  - **(b) 禁止リストを丸ごと削除する**: PR 旧#5 が実際に所有中のファイルが 1 件あり、実測に反する。またリスト自体を消すと同種の衝突が次回に無防備になる
  - **(c) open PR が触る全ファイルを禁止集合へ拡張する**: 実測すると 3 manifest / `CHANGELOG.md`（PR 旧#5）と `tests/checks/manifest.tsv` / `tests/test_validate_plugin_check_inventory.py`（PR 旧#9）が本 PR の差分と重複しており、AC-15 / AC-21 が本 PR による変更を要求するため **AC と直接矛盾**する。既知重複として merge 時に解消する扱いに留める
  - **(d) 述語を明記せず「PR 差分で見ること」とだけ書く**: T-22 の見逃しは自然文の解釈幅から生じた。コマンドを書かなければ同じ代用が再発する
- **Consequences**:
  - CT-6 の**判定は緩まない**。対象集合は 15 → 1 に縮小する一方、述語は代用形 3 つを不許可にして強化され、失効ファイルを触る場合は無競合の実証が追加要求になる
  - AC-1〜AC-25 の本文・意味は無変更。実装差分・hook 挙動・テストへの影響はゼロで、tasklist の再生成も不要
  - `T-30` Step 5 の grep 対象と Expected を live 集合へ更新する必要がある（本改訂で実施）
  - 将来の解除は同じ 2 条件の実測表を残すことを義務とする。「merge されたから」だけを根拠にした緩和は本 ADR では許可していない
  - `Scope Drift Counter` は **+0 / 対象外**（`references/rollback-patterns.md` § Counter マトリクスの +1 契機は `design_detail_only` route の選択であり、本件は該当しない）。既存値は継続

---

## ADR-12: steering の記録は「面をまたいだ機械照合」と「量は機械が出す」で担保し、規約は steering 内に閉じる

- **Status**: Accepted（2026-08-21 / T-30 Attempt 8 後の Architecture Gate / route `design_detail_only`）
- **Context**:
  - T-30 は Attempt 4〜8 の 5 ラウンドで「**記録が実体と合わない**」を **14 件**発生させた。全数分類は
    `record-discipline.md` § なぜ作ったか の表が正本（**内訳をここに転記しない** — 転記は規約 3 が禁じており、
    実際 Attempt 9 の M-1 で正本を直したあとも本行が旧値のまま残る事故が起きた。Attempt 10 gate の M-1）。
  - Attempt 8 の reviewer は「`implementation_fix_only` の継続判断そのものは `state-machine.md` の判定式 5 項
    すべて No で正当」としつつ、「**同一 root cause が Attempt 4 以降 5 ラウンド連続で再発**しており
    Architecture Gate に形式的には該当する」ことを判断材料として明示した。
  - Attempt 6 以降の 3 ラウンドは**すべて production 差分 0**で、出荷面は全項目 green のまま。
    すなわち止まっていないのは**記録の生産プロセスだけ**である。
- **Decision**:
  1. **面をまたいだ機械照合を導入する**。1 Attempt の記録先は 4 面（tasklist gate entry / tasklist remediation
     entry / worklog Error Log 行 / handoff 逐条節）と定め、**Attempt 番号の集合が 4 面で一致する**ことを
     `reconcile-records.py` が検査する。
  2. **様式を機械で固定する**。Error Log の `Attempt` 列は分数形式で始まること、逐条見出しは
     `## <TASK> Attempt N` に統一することを同スクリプトが検査する。
  3. **機械化できる量は散文に literal で書かない**。面の員数・様式・宣言 3 集合はスクリプトの出力が正本。
     それ以外の量は導出コマンドと出力を同じブロックに併記し、**転記は禁止**する。
  4. **規約と検査は `.steering/` に閉じる**。出荷 check にはしない。
- **Rejected Alternatives**:
  - **(a) GDD の出荷 check にする**: 他プロジェクトの steering にも効く点は魅力だが、`manifest.tsv` 登録・
    inventory test 更新・`references/` 残枠 6 行という制約に入り、hard cap 超過中の task で scope を大きく
    広げることになる。**効果の実証はまだ 1 steering 分しかない**ため、出荷は実績を積んでからでよい。
  - **(b) 記録先の面そのものを減らす（DRY）**: 最も根本的だが、4 面の存在は `state-machine.md` /
    `bounce-log-schema.md` の出荷契約が定めるもので、契約変更とその検証が必要になる。本 PR の scope 外。
  - **(c) 記録面の審査を打ち切り advisory として出荷する**: 出荷物は green なので成立するが、
    「点の訂正で閉じたことにする」型そのもので、本 PR が塞ごうとしている規律と正面から衝突する。
  - **(d) `human_recheck_required` へ正式昇格する**: Tasklist Reset Policy により 30 task 分の全セクションが
    初期化される。今回の blocker は 5 項すべて No の procedural / evidence only で、要件も方向性も
    変わっていないため、リセットに見合う判断の変更が無い。
- **Consequences**:
  - **担保範囲と、担保していない範囲の境界は `record-discipline.md` § 機械検査している範囲 / していない範囲 が正本**。
    check の本数も検出できない形も**そこにしか書かない**（本 ADR に写すと Attempt 10 gate の M-2 のように陳腐化する）。
    Bounce Log の計上漏れは **convention only で機械検査していない**（`reconcile-records.py` は `state.md` を読まない）。
  - **判別力は実測済み**（注入した形と結果は `record-discipline.md` § 判別力（mutation で実測）が正本。
    **件数をここに書かない**）。注入後の復元一致も毎回確認している。
  - 逐条見出しのレベルを正規化した（**本文は無変更**。段階と件数は `record-discipline.md` § 適用時に行った正規化
    が正本。当初「3 件」と書いたが、実際は小見出しの降格を伴う 2 段階だった — Attempt 10 gate の M-2）。
    正規化しないと既存記録で規約 5 と「本文が空でない」の検査が常に fail する。
  - 出荷物への影響は **0**。`plugins/` 配下に差分は無く、`manifest.tsv` にも登録しない。
  - **`Scope Drift Counter` は +1**（`state.md` に **1** として新設した）。`references/state-machine.md` は
    「`gdd-systematic-debugging` が `design_detail_only` を**選択するたびに** +1 する」「+1 の正本タイミングは
    `Route In Progress=design_detail_only` の**書込みが永続化完了した瞬間**」と定めており、本 ADR は
    その route 選択そのものである。**当初この Consequences は `rollback-patterns.md` の Counter マトリクスの
    「method-only / naming・comment only」行を根拠に +0 と書いたが、それは同マトリクスが
    「詳細な counter 定義は `state-machine.md` 参照」と委譲している側の記述で、+1 契機の定義ではなかった。
    ADR-11 の同項（+1 契機 = `design_detail_only` route の選択）とも食い違っていた。Attempt 9 gate の H-1
    で指摘され、`state-machine.md` に合わせて訂正した。**
  - **`Scope Drift Counter` フィールドは本 steering に存在しなかった**ため新設した。値 1 の根拠は
    `worklog.md` § Error Log の route 列に `design_detail_only` を持つ行が本件以前 0 であること。
    `references/phase-progression.md` § Scope Drift Guard の発動条件 1（Counter が 3 を超えた）は
    フィールド不在の間ずっと判定不能だったが、これで機械判定できる。閾値 3 には未到達。

---

# 記録規約アーカイブ: `record-discipline.md`（ADR-12 の成果物・逐語）

# 記録規約（本 steering 専用）

**位置づけ**: T-30 Attempt 8 で発動した Architecture Gate の成果物。`gdd-implementation-gating` /
`gdd-systematic-debugging` が本 steering に記録を書くときの規約と、その機械検査の正本。
**出荷しない**（`plugins/` 配下ではなく `.steering/` に置く。`manifest.tsv` にも登録しない）。

## なぜ作ったか

**母集合**: Attempt 4〜8 の 5 ラウンドで gate が起票した blocking finding（High + Medium）の全件。
**導出**: `handoff/impl-gate.md` の § `T-30 Attempt 4`〜`Attempt 8` の Findings 節を読み、
`worklog.md` § Error Log の gate 行（No 42 / 44 / 46 / 48 / 50）の件数と突き合わせる。
内訳は Attempt 4 = 4（M-1〜M-4）/ Attempt 5 = 3（R-1〜R-3）/ Attempt 6 = 1（M-1）/
Attempt 7 = 4（M-1〜M-4）/ Attempt 8 = 2（M-1・M-2）。

**全数分類**（各 finding をちょうど 1 型へ割り当てる。重複計上も未分類も無い）:

| 型 | 件数 | 割り当てた finding |
|---|---|---|
| **A. 量を人手で書く**（母集合未記載・再現不能・転記・正本の置き方） | 6 | A4-M3（「引用 1 件のみ」実測 2）/ A4-M4（件数の正本を、この検査が自ら走査除外している文書へ寄せた）/ A5-R1（導出コマンドが別集合を測る）/ A5-R3（`.gitignore` アンカー化の前提が実測で偽）/ A7-M4（「残る 2 箇所」が母集合により変わる）/ A8-M1（「追加行 23,459 行」が再現不能） |
| **C. 記録の欠落・置き場違い** | 4 | A4-M1（worklog 未更新のまま「更新した」と宣言）/ A7-M1（Bounce Log 未計上）/ A7-M2（逐条節の不在）/ A8-M2（Attempt 7 の bounce 未計上。**counter が散文にしか無い E 的側面も持つが、主たる欠陥は計上漏れなので C へ 1 回だけ計上する**） |
| **B. 宣言が実体に追随しない**（同一 commit 内の片側更新） | 2 | A4-M2（`.gitignore` が Map に無い）/ A6-M1（Map の責務セルがアンカー形のまま） |
| **E. 様式ドリフト** | 1 | A7-M3（`Fix Attempts` が単独数字） |
| **D. 記述と実行の乖離** | 1 | A5-R2（宣言 3 集合の C 述語） |

**合計 = 6 + 4 + 2 + 1 + 1 = 14**（母集合の件数と一致）。

**構造的な原因は 2 つ**:

1. **記録先が 4 面あるのに、面をまたいだ機械照合が無かった**。Attempt 4〜7 で入れた員数照合は
   tasklist と worklog の 2 面しか見ておらず、逐条節の不在（C 型）と Bounce Log の未計上（C 型）は
   **照合の射程外**で起きた。
2. **面ごとに様式が割れていた**。実測すると逐条見出しは Attempt 1〜3 が `#`、4〜8 が `##` で、
   同じ記録なのに grep 一つで件数が 5 とも 8 とも変わった。**照合が空回りする形**である。

対照として、**唯一構造的に直した箇所**（出荷 check が自分で件数を出力し、散文はそれを指すだけに
した `tests/checks/bounded-claim-evidence.sh`）は、その後 A 型の再発が **0** だった。この対比を
そのまま設計指針にする。

## 規約

1. **機械化できる量は機械が出し、散文は指すだけにする**。面の員数・様式・宣言 3 集合の 3 種は
   `reconcile-records.py` の出力が正本。**これらの件数を散文に literal で書かない**。
2. **それ以外の量を散文に書くときは、同じブロックに導出コマンドと出力を併記する**。
   母集合を書けないなら量を書かない。
3. **転記を禁止する**。reviewer の報告や他 Attempt の記録にある数値を、**自分で母集合を取り直さずに
   写さない**（A 型 4 件のうち 1 件はこれが原因だった）。
4. **1 Attempt につき 4 面すべてに記録する** — (i) `tasklist.md` の gate entry、(ii) 同 remediation entry、
   (iii) `worklog.md` § Error Log の行（gate 用と remediation 用の 2 行）、(iv) `handoff/impl-gate.md` の逐条節。
   Bounce Log（`state.md`）は Attempt ごとではなく identifier ごとの counter なので員数照合の対象外だが、
   **bounce が立った Attempt は identifier 行の `bounce_count` / `bounced_at` フィールド自体を更新する**
   （散文の sub-bullet だけに書かない。正本は出荷 reference の `bounce-log-schema.md`）。
5. **様式を固定する** — Error Log の `Attempt` 列は**分数形式で始める**（出荷契約
   `skills/gdd-systematic-debugging/SKILL.md`）。逐条見出しは `## <TASK> Attempt N` に統一する。
6. **時点記録と live 宣言を区別して書く**。過去 Attempt の記述を残す場合は「本行は時点記録であって
   現構造の宣言ではない」と明示する（B 型の再生産経路を塞ぐ）。

## 機械検査している範囲 / していない範囲

`reconcile-records.py` が検査するのは **規約 1・4・5 と宣言 3 集合**だけである。

- **検査している（6 種）**: **外部アンカー**（`git log` の commit subject に現れる Attempt 番号が
  4 面すべてに存在する）/ 逐条節の本文が空でない / 面の員数（Attempt 番号の集合が 4 面で一致）/
  Error Log の Attempt 列の分数形式 / 逐条見出しのレベル統一 / 宣言 3 集合 A ≡ B ≡ C と
  「Map のどの行にも無い touched path」
- **外部アンカーが要る理由（実測）**: 面の**相互一致**しか見ないと、「4 面から一様に Attempt を
  落とす」「T-30 の記録を 4 面から全削除する」形が**空集合どうしの一致で素通りする**（rc=0）。
  steering 内の値をアンカーにしてもアンカーごと消えるため、**steering の外**（git）から導く。
- **検査していない（convention only）**: 規約 2（導出コマンドの併記）/ 規約 3（転記禁止）/
  規約 6（時点記録と live 宣言の区別）/ **Bounce Log の計上漏れ**（`reconcile-records.py` は
  `state.md` を一切読まない）。
  これらは**機械化していないので、守られている保証は無い**。守るのは書き手の責任であり、
  検出は reviewer の実測に依存する。**この節は「どこまで機械が担保しているか」の宣言であって、
  担保範囲の外については主張しない**。

## 実行

worktree root から:

```
python3 .steering/20260817-pr-w3-self-review/reconcile-records.py
```

exit code 0 = すべて一致 / 1 = いずれかが不一致。**gate と remediation の両方で、記録を書いた直後に実行する**。

## 判別力（mutation で実測）

無条件に通る照合でないことを、退行を注入して確認した。注入は毎回復元し、`git status --short`
と 3 ファイルの byte 一致で復元を確かめている。

**主張どおりに検出できた形（kill / rc=1）**:

| 注入 | 狙う check |
|---|---|
| handoff の Attempt 6 節の見出しレベルを下げる | 面の員数 |
| worklog の Attempt 列を単独数字にする | 様式（分数形式） |
| handoff の Attempt 4 見出しを H1 にする | 様式（見出しレベル） |
| File Structure Map から `.gitignore` 行を削除 | 宣言 3 集合 |
| tasklist の remediation 見出しを破壊 | 面の員数 |
| **T-30 の記録を 4 面から全削除** | **外部アンカー** |
| **Attempt 8 を 4 面から一様に削除** | **外部アンカー** |
| **逐条節の本文を削除し見出しだけ残す** | **本文が空でない** |
| `BASE` を存在しない rev にする（git 失敗） | fail-closed（例外で停止） |
| `## Current Task` 見出しを削除 | fail-closed（例外で停止） |
| `worklog.md` を空にする | 複数 |

baseline は rc=0。**下 3 つの太字は Attempt 9 reviewer が見つけた空洞化**で、当初の実装では
いずれも rc=0（SURVIVOR）だった。外部アンカーと本文の非空判定を足して閉じた。

**検出できない形（既知・記録）**:

| 形 | 理由 |
|---|---|
| 同じ見出しを重複して増やす | 集合で比較しており dedup される。水増しの実害は低い |
| code fence の中に `## <TASK> Attempt N` を書く | fence を区別しない。ただし**多く数える**方向なので fail-closed 側 |
| 空白を含む path 名 | `git` 出力を空白分割している。現 repo に該当なし |
| **内容ゼロの節で 4 面を埋める**（本文 10 行 + 見出しだけ） | 本文の**中身**は判定しない。行数の閾値はいくつにしても回避できるので、閾値を上げずに**検出できない形として宣言する**（Attempt 10 gate の N2 で実測） |
| **Bounce Log（`state.md`）の計上漏れ・様式** | `reconcile-records.py` は `state.md` を一切読まない（`grep "state.md" reconcile-records.py` = 0 hit）。規約 4 後段は **convention only** |
| 他 task（T-1〜T-29）の Bounce Log 行の様式 | 本 steering の Bounce Log は 31 行あり、`- <id> \| bounced_at: <ISO> \| bounce_count: <N>` に準拠するのは **T-30 の 4 本 + 1 本**。残りは完了済み task の時点記録で本 PR の owner 外のため触っていない（導出: `grep -cE '^- .*\\| bounce_count: '` と `grep -cE '^- .*\\| bounced_at: [0-9T:Z-]+ \\| bounce_count: [0-9]+$'`） |

**閉じた空洞化（記録）**: 「**commit subject に `Attempt N` を書かずに steering を commit する**」形は、当初の
git アンカー（過去の subject に現れた番号のみを要求する片側包含）では素通りした（Attempt 10 gate の N1）。
**steering を触った直近 commit の subject 自体が Attempt を名乗ること**を要求する check を足して閉じた
（実測: subject を変えて steering を commit すると rc=1）。Architecture Gate のように Attempt 番号を持たない
commit は subject に `Architecture Gate` を含めることで明示的に免除する。

## 適用時に行った正規化（記録）

見出しレベルのみを 2 段階で正規化した（**本文は一切変更していない**）。導出:
`git diff <base> -- handoff/impl-gate.md | grep -c '^+## '` 等で毎回数え直せる。

1. **逐条見出し**: Attempt 1〜3 だけ `#` だったため `##` へ。
2. **その小見出し**: 1 の結果、Attempt 1〜3 の小見出し（`##`）が逐条見出しと同レベルに
   なり、「逐条節の本文」が構文上 0 行になった。**この不整合は本検査自身が検出した**ため、
   当該範囲の小見出しを `###` へ降格して Attempt 4〜8 と揃えた。

正規化しないと規約 5 の検査と「本文が空でない」検査が既存記録で常に fail する。
