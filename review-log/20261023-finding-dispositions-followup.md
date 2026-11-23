---
lane: L1+
follow_up_of: 568
pr: 旧#571
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ-1 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) | a2875aae | 0 | 2 | 1 | 2026-10-23T15:00+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 9a886f23ad502ce95f8831246a016089fa29a216 | 1 | 2 | 1 | 2026-10-23T16:00+09:00 |
| 方針メモ-2 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) | 9a886f23ad502ce95f8831246a016089fa29a216 | 0 | 1 | 0 | 2026-10-23T16:30+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 9bf01927d0a965b2da7add77479be4895291421a | 1 | 4 | 1 | 2026-10-23T17:10+09:00 |
| 方針メモ-3 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) | 9bf01927d0a965b2da7add77479be4895291421a | 0 | 0 | 0 | 2026-10-23T17:40+09:00 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 12f33cfffd7ff195167d8f21853824308e29fa50 | 2 | 2 | 2 | 2026-10-23T18:50+09:00 |
| 方針メモ-5 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) | 12f33cfffd7ff195167d8f21853824308e29fa50 | 0 | 0 | 0 | 2026-10-23T19:00+09:00 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 70c38bcb88a9dcd57b4ebb5bb72427c7a51f7d66 | 0 | 1 | 0 | 2026-10-23T18:20+09:00 |
| 方針メモ-4 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) + user | 70c38bcb88a9dcd57b4ebb5bb72427c7a51f7d66 | 0 | 1 | 0 | 2026-10-23T17:40+09:00 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | a0080f422f4ac7e9aa4bf7540e455da0a09bf0a1 | 0 | 3 | 0 | 2026-10-23T20:20+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| p1-1 | 方針メモ-1 | medium | no | self-inflicted | verifier | fixed | r3-5 の直し方が割れた。Opus は high・実害クラスに unverified_file を付けさせず rejected:refuted に寄せる案、Fable は述語を変えず検証役が file の不在を refuted と返す案。どちらも差し戻しは起きないので、変える場所が少ない Fable の案を採った。行き先で場合分けしない（検証役に main の意図を渡さない）点は 2 本とも同じ |
| p1-2 | 方針メモ-1 | medium | yes | self-inflicted | ledger | fixed | Opus: 最後の節だけを見ると、同じ tip の前の節の high を引き継がずに ok になる。前の節の high・実害クラスに最後の節の re-reported を要るようにした。Fable は不要とした |
| r1-1 | 独立-1 | high | yes | self-inflicted | verifier | fixed | 列挙: 設計: 変える（path の不在を欠陥が無いことの証拠にした決定）。方針メモ-2 で Opus・Fable とも、refuted の根拠を path から指摘が名指す語に移す案を推した（許可リストではなく設計変更で閉じる）。検証役は不在の file の代わりに語を Worktree で Grep し、見つかった file で判定、どこにも無いときだけ refuted。commit: 9bf01927 |
| r1-2 | 独立-1 | medium | no | self-inflicted | ledger | accepted | 引き継ぎの照合が 1 つ前の節だけを見るので、同じ sha の空の節を 2 つ足すと前の high が消える |
| r1-3 | 独立-1 | medium | no | self-inflicted | ledger | accepted | 引き継ぎの行の severity・category を見ないので、medium で引き継ぐと high 0 で通る |
| r1-4 | 独立-1 | low | no | inherited | ledger | accepted | 同じ sha を文字列の完全一致で決めるので、短い sha と 40 桁を混ぜると照合が走らない |
| r1-5 | 独立-1 | low | no | self-inflicted | test | accepted | 新しいテストの前の節が high・product の 1 形だけで、_is_serious を high だけに替える変異などが残る |
| r1-6 | 独立-1 | low | no | self-inflicted | verifier | accepted | 文書は検証役を通した unverified_file に根拠を求めるが、述語は見ていない |
| r1-7 | 独立-1 | low | no | self-inflicted | verifier | accepted | 検証役の出力の形が path:line のままで、不在の規定との優先順と worktree の外の path の扱いが無い |
| r1-8 | 独立-1 | low | no | self-inflicted | ledger | accepted | ir_count_errors の docstring が引き継ぎ漏れの invalid を挙げていない |
| r1-9 | 独立-1 | low | no | self-inflicted | verifier | fixed | finding-dispositions.md の「不在なら refuted」が、同名 file・不在自体が欠陥の例外を書いていない。r1-1 と同じ文で直した。commit: 9bf01927 |
| r1-10 | 独立-1 | low | no | self-inflicted | pr-body | fixed | PR 本文の限界の種類（未決）と、invalid の条件を新しいとした事実の誤り。invalid になる入力は減っている。commit: なし（PR 本文） |
| r1-11 | 独立-1 | advisory | no | self-inflicted | ledger | accepted | check-gate-ledger.sh の説明が、最後の節と引き継ぎの照合を書いていない |
| p2-1 | 方針メモ-2 | medium | no | self-inflicted | verifier | fixed | 名指す語が 1 つも無い指摘の扱いが割れた。Opus は unverifiable、Fable は refuted。止める側に倒れる unverifiable を採った |
| r2-1 | 独立-2 | medium | no | self-inflicted | verifier | fixed | 名指す語の無い指摘を unverifiable にし、r3-5 を依頼より狭めたのに限界を その他 と書いた。commit: 70c38bcb |
| r2-2 | 独立-2 | medium | no | self-inflicted | verifier | fixed | 列挙: 語が見つかった file を全部判定して集約するので、docs・テストに当たると unverifiable になり誤検知の差し戻しが残る。commit: 70c38bcb |
| r2-3 | 独立-2 | medium | no | self-inflicted | verifier | fixed | refuted の条件に「だけ」が 2 つあり、文字どおり読むと語が見つかった場合は refuted にならない。commit: 70c38bcb |
| r2-4 | 独立-2 | high | yes | self-inflicted | verifier | fixed | 設計: 変える（path・語の不在を欠陥が無いことの証拠にした決定）。方針メモ-3 で規則ごと外した。diff が消した・改名した file と語を根拠にした本物の high が、語が無いことで refuted になる。commit: 70c38bcb |
| r2-5 | 独立-2 | low | no | self-inflicted | verifier | fixed | 列挙: 同じ名前の file を確かめなくなり、語の書き違え 1 つで refuted になる。commit: 70c38bcb |
| r2-6 | 独立-2 | medium | no | self-inflicted | verifier | fixed | 列挙: Grep が正規表現として語を当て損ねると「無い」と数えて refuted になる。commit: 70c38bcb |
| r2-7 | 独立-2 | low | no | self-inflicted | verifier | fixed | 根拠の語に縦棒があると表が壊れる（止める側に倒れる）。commit: 70c38bcb |
| r2-8 | 独立-2 | low | no | self-inflicted | verifier | fixed | 根拠の書式が定義の中で 2 通りある。commit: 70c38bcb |
| r2-9 | 独立-2 | low | no | self-inflicted | verifier | fixed | :27 の path:line の規定と :28 の不在の refuted の優先順が無い。commit: 70c38bcb |
| r2-10 | 独立-2 | low | no | self-inflicted | changelog | accepted | 断片と PR 本文が、語が見つかった場合の refuted を書かず効果を広く言っている |
| r2-11 | 独立-2 | low | no | inherited | verifier | accepted | 述語は unverified_file・refuted の根拠が - でも通す |
| r2-12 | 独立-2 | advisory | no | self-inflicted | verifier | fixed | 不在の判定は main が渡した文の語だけで決まる。commit: 70c38bcb |
| r2-13 | 独立-2 | advisory | no | self-inflicted | changelog | accepted | 断片の Validation に検証役の文の変更の検証が無い |
| r2-14 | 独立-2 | advisory | no | self-inflicted | verifier | fixed | 語が見つかった file で refuted のときの行き先が決まっていない。commit: 70c38bcb |
| p3-1 | 方針メモ-3 | advisory | no | self-inflicted | verifier | accepted | 安全策 4 の 1 回目の発火。Opus・Fable とも撤回（不在から refuted を導く規則を外し 旧#568 の unverifiable に戻す）を推し、推奨で続行した。r3-5 の差し戻しの害は依頼より狭いとして限界に書き、ユーザーに問う。止めるなら 9bf01927 まで戻す。17:28 の返事で、撤回せず別の閉じ方（absent@）を探すことになった |
| r3-1 | 独立-3 | medium | no | self-inflicted | verifier | accepted | r3-5 の「根拠の file が無い high の誤検知の差し戻し」を直さず、依頼より狭めた。PR 本文の限界に問いを書いた。17:28 の返事で、差し戻しも直すことになった（absent@ を入れた） |
| r3-2 | 独立-3 | low | no | self-inflicted | changelog | accepted | 断片の「これまでどおり差し戻し」は、前の版（high も advisory に下げていた）から見ると逆に読める |
| r3-3 | 独立-3 | low | no | inherited | verifier | accepted | high を advisory に下げた行（検証 refuted）の根拠は - のままでよく、rejected:refuted と非対称 |
| r3-4 | 独立-3 | low | no | inherited | verifier | accepted | Step 8 の「捨てる・下げる finding は検証役が refuted のものだけ」が、§ 検証役の条件（high・実害クラスだけ）より広い |
| r3-5 | 独立-3 | advisory | no | inherited | verifier | accepted | impl-gating では high を検証役なしで advisory:out_of_scope にできる。Step 1c の場面で使われうる |
| r3-6 | 独立-3 | advisory | no | self-inflicted | pr-body | fixed | テンプレート外の記述あり（PR 本文の抜粋ファイル内の限界の行が、外した規則の経緯を書いていた）。PR 本文では変更の性質として書いた。commit: なし（PR 本文） |
| p4-1 | 方針メモ-4 | medium | no | self-inflicted | verifier | fixed | ユーザーが 17:28 に r3-5 の差し戻しも直せと指示（p3-1 の返事）。Opus・Fable とも、自由文ではなく file:line 欄と git の事実で閉じ、never だけを通し、basename の照合を必須にする案。割れたのは判定の置き場で、Opus の absent@<sha> を根拠に書き CLI が sha 固定で判定する形を採った（ledger に git を持ち込まず、後から判定が変わらない）。commit: 12f33cff |
| r4-1 | 独立-4 | high | yes | self-inflicted | absent-path | accepted | 安全策 4 の 2 回目の発火で止める。_LOCATION_RE が path に : を許すので、path:行:桁 の形は tip にある file でも never になる |
| r4-2 | 独立-4 | high | yes | self-inflicted | absent-path | accepted | 安全策 4 の 2 回目の発火で止める。basename の一覧が core.quotePath の引用符つきの非 ASCII の名前と、staged の新しい file を落とし、同じ basename の file があっても never になる |
| r4-3 | 独立-4 | medium | no | self-inflicted | absent-path | accepted | 行に書いた sha が HEAD かも、HEAD の祖先かも確かめていない |
| r4-4 | 独立-4 | medium | no | self-inflicted | absent-path | accepted | 同じ basename の file がある架空の path は差し戻しのままで、依頼より狭い。20:40 の返事で、この範囲で出すことに決まった |
| r4-5 | 独立-4 | low | no | self-inflicted | absent-path | accepted | _NEEDS_REFUTE_SERIOUS のコメント・§ 検証役・verifier の description が absent@ の例外を書いていない |
| r4-6 | 独立-4 | low | no | self-inflicted | absent-path | accepted | Step 1c の absent@ の条件とエラー文が、CLI の分類（途中の commit・同じ basename・未 commit）と食い違う |
| r4-7 | 独立-4 | low | no | self-inflicted | absent-path | accepted | basename を大文字小文字を区別して比べる |
| r4-8 | 独立-4 | low | no | self-inflicted | absent-path | accepted | 過去の節の absent@ 行も毎回分類し直すので、sha が解けなくなると直せない invalid になる |
| r4-9 | 独立-4 | low | no | self-inflicted | changelog | accepted | 断片の Summary が、同じ basename の file が無いときだけ直ったことを書いていない |
| r4-10 | 独立-4 | low | no | inherited | changelog | accepted | 前の PR の未リリースの断片が「unverified_file は検証役の refuted だけ」と書いたまま |
| r4-11 | 独立-4 | advisory | no | self-inflicted | absent-path | accepted | ledger は absent@ の形だけで通すので、Step 8 の CLI を飛ばすと push 前も見つけない |
| r4-12 | 独立-4 | advisory | no | self-inflicted | absent-path | accepted | main が file:line を書き換える形が § 限界に無い |
| p5-1 | 方針メモ-5 | advisory | no | self-inflicted | absent-path | accepted | 安全策 4 の 2 回目の発火（high を含む巡が 3 回）。規則どおり止めるの扱いで PR を出し返事を待つ。Opus・Fable とも返事の推奨は続行（r4-1 は path の文字から : を除く、r4-2 は git を -z にし ls-files --cached --others）。割れたのは r4-1 の行:桁の形を受けるか（Opus）invalid に倒すか（Fable）。返事（19:40）は「設計に戻した方が良ければ戻す、続行で閉じられそうなら続行」。main は続行とし、path を許可リストで読んで外れた形は invalid（Fable 側）、一覧は -z、basename は NFC と casefold で比べる |
| r5-1 | 独立-5 | medium | no | self-inflicted | absent-path | accepted | 依頼の原文から外れた（差し戻しを直す依頼に対し、同じ basename の file がある架空の path は差し戻しのまま。casefold・NFC・staged で残りが広がった）。Opus・Fable とも A（この範囲で出す）を推す。理由は、広げる閉じ方（不在を根拠に検証役が refuted）がこの PR で r1-1・r2-4 の high を出して外したこと。PR 本文の限界に問いを書いた。20:40 の返事で、この範囲で出すことに決まった |
| r5-2 | 独立-5 | medium | no | self-inflicted | absent-path | accepted | basename の同名判定は NFC と casefold だけで、- と _ の取り違えや全角は never に落ち、本物の high が検証役なしで advisory に下がる |
| r5-3 | 独立-5 | medium | no | self-inflicted | doc-claim | accepted | 正本・変更断片・PR 本文が path の文字を「英数字と ./@+~-」と書くが、実装の \w は _ と Unicode の文字も受け付け、行-行 とバッククォートも受ける。PR 本文は直した。commit: なし（PR 本文） |
| r5-4 | 独立-5 | low | no | self-inflicted | test-power | accepted | log -z の名前を使うケース、core.quotePath を固定するケース、repo 側の NFD の名前のケースが無い。log -z の出力に改行が残らないことは実出力で確かめた |
| r5-5 | 独立-5 | low | no | self-inflicted | absent-path | accepted | -z で生のバイトになり、UTF-8 でない名前があると UnicodeDecodeError で error になる（通す側には倒れない） |
| r5-6 | 独立-5 | low | no | self-inflicted | ledger | accepted | 位置の形の検査が CLI にだけあり、ledger は absent@ の形しか見ない |
| r5-7 | 独立-5 | low | no | inherited | absent-path | accepted | absent@ の sha が HEAD より古くても受け付け、その後に commit した file を見ない |
| r5-8 | 独立-5 | advisory | no | inherited | absent-path | accepted | rebase 後に別の clone で再開すると古い行の sha が解けず、追記専用の表で直せない |
| r5-9 | 独立-5 | advisory | no | self-inflicted | absent-path | accepted | NFC にした文字列を path の照合にも使うので、NFD のまま書いた .gitignore の file が Linux で never になりうる |
