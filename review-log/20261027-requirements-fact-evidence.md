---
lane: L1+
pr: 594
amends: 20261027-amendment-evidence-propagation.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) | 641f99a9 | 0 | 0 | 0 | 2026-10-27 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 0f81fe4b | 3 | 6 | 3 | 2026-10-27 |
| 方針メモ-1 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) | 0f81fe4b | 0 | 0 | 0 | 2026-10-27 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | d0c87026 | 3 | 1 | 3 | 2026-10-28 |
| 方針メモ-2 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) + user | d0c87026 | 0 | 0 | 0 | 2026-10-28 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 394c8051 | 0 | 0 | 0 | 2026-10-28 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M-1 | 方針メモ | advisory | no | self-inflicted | 閉じ方 | accepted | 2 本とも案 A（AC に 根拠・計測 の欄、lint で有無だけ）を推した。割れた点: 範囲は Opus が AC と承認ポイント、Fable が AC だけ。承認ポイントの番号つき項目は実データ 218 本で項目の形が多い（`N. **` が主）ので、項目ごとに欄の有無だけを見る形で広い側を採った。lint-existing-code-reading.py は 2 本とも撤去。Opus は同じ PR、Fable は別 PR。この PR の範囲を保つため別 PR にした |
| F1-1 | 独立-1 | high | yes | self-inflicted | 欄の検査の範囲 | fixed | 列挙: 設計: 変える（認識した件数で通すかを決めず、AC の定義か承認ポイントの番号つき項目が 0 件なら止める。check_treatments の処置 0 件と同じ倒し方）。方針メモ-1 で (a) にした。`3a.`・`3-1.` も 1 項目、見出しの `（…）` の付記は承認ポイントとして読む。10 月の requirements 57 本で新しい ERROR は 4 本（HCQ の参照だけ 2・テンプレート外の最小の書式 1・見出しの付記 1〔付記を受けたので今は止まらない〕）。commit: eeed27e0 |
| F1-2 | 独立-1 | high | yes | self-inflicted | 欄の検査の範囲 | fixed | 設計: 変える（欄名を本文のどこかで探さず、箇条の先頭か ` / ` の直後に限る。処置の欄も同じ helper で数える）。commit: b10c97e2 |
| F1-3 | 独立-1 | high | yes | self-inflicted | 欄の検査の範囲 | fixed | 設計: 変える（意味を狭めた値を使い回さず、design の起動を `design` に改名し、`other` は exit 2）。commit: b10c97e2 |
| F1-4 | 独立-1 | medium | no | self-inflicted | 依頼のずれ | accepted | ユーザーが次の PR で撤去すると決めた（2026-10-28）。依頼は lint-existing-code-reading.py の扱いを相談に含めると求めた。相談の結論は 2 本とも撤去で、撤去は別のファイル群（検査 9 か所）に広がるので次の PR にした（手順 6 の (c)）。推奨のとおり次の PR で撤去する |
| F1-5 | 独立-1 | medium | no | self-inflicted | 依頼のずれ | accepted | ユーザーが AC と承認ポイントの範囲と決めた（2026-10-28）。依頼の「requirements が書くコード・データの事実」を AC と承認ポイントの項目に限った。依頼が節で読むか項目で読むかの 2 通りに読める（手順 6 の (b)）。Opus は AC と承認ポイント、Fable は AC だけを推した。推奨は AC と承認ポイントのまま |
| F1-6 | 独立-1 | medium | no | self-inflicted | 依頼のずれ | fixed | 計測の欄の説明を「どの母集団で」に戻した（テンプレート・断片・ERROR の文）。commit: b10c97e2, d0c87026 |
| F1-7 | 独立-1 | medium | no | self-inflicted | 予算 | fixed | standard runtime profile の token を、同じテンプレートの説明文を縮めて main（旧#593 の後）に重ねた状態で 45497/45497 にした。commit: eeed27e0 |
| F1-8 | 独立-1 | medium | no | self-inflicted | 断片 | fixed | 旧#592 の断片の `--entry` の値の説明を新しい意味に書き換え、front matter に amends を書いた。commit: b10c97e2 |
| F1-9 | 独立-1 | medium | no | self-inflicted | テスト | accepted | 承認ポイントの節を `###` で閉じる分岐を通るテストが無い。① の blocking でない medium |
| F1-10 | 独立-1 | low | no | self-inflicted | 依頼のずれ | accepted | ユーザーが残すと決めた（2026-10-28）。依頼の `根拠:` の値（`file:line`・コマンドと値・`未測（理由）`）に `なし（理由）` を足した。欄を AC ごとに置いたので、既存の事実を前提にしない AC に要る（手順 6 の (b)）。推奨は残す |
| F1-11 | 独立-1 | low | no | self-inflicted | reviewer | accepted | planning reviewer の新しい文が design の Round にも効く。① の low |
| F1-12 | 独立-1 | low | no | self-inflicted | 再入の範囲 | accepted | 欄の書き足しを「変えた節」に数えない規定が、1 枚と再入の範囲を決める箇所に無い。① の low |
| F1-13 | 独立-1 | low | no | self-inflicted | テンプレート | accepted | テンプレートの AC の例と HCQ の説明が欄の規定に追いついていない。① の low。token の予算が 0 なので足さない |
| F1-14 | 独立-1 | low | no | self-inflicted | 欄の検査の範囲 | accepted | 太字の欄名は F1-2 の修正で受けるようになった。方向性の除外が `**方向性**` の文字列に頼る点は残る。① の low |
| F1-15 | 独立-1 | low | no | self-inflicted | テンプレート | accepted | 承認ポイントの `根拠:` と HITL の「根拠」の意味が違う。① の low |
| F1-16 | 独立-1 | low | no | self-inflicted | 重複検査 | accepted | `根拠:` の backtick のパスが重複検査の WARN を招くことがある（warn だけ）。① の low |
| F1-17 | 独立-1 | low | no | self-inflicted | 数値の照合 | accepted | 定義行に書いた欄の数値が AC の数値の照合に混ざる（warn だけ）。① の low |
| F1-18 | 独立-1 | low | no | self-inflicted | テスト | accepted | `--entry requirements` が処置を見ないことを固定するテストが無い。① の low |
| F1-19 | 独立-1 | low | no | self-inflicted | テスト | accepted | 欄ごとのテストの assert が、どちらの欄の報告かを区別していない。① の low |
| F1-20 | 独立-1 | low | no | self-inflicted | 断片 | fixed | テストのコメントを design の起動だけの意味に直した。commit: b10c97e2 |
| F1-21 | 独立-1 | low | no | self-inflicted | PR 本文 | fixed | PR 本文に、2026-10-27 の steering で数えたことを書く。commit: なし（PR 本文） |
| F1-22 | 独立-1 | advisory | no | self-inflicted | 断片 | fixed | 断片を「テンプレートに欄を足し、brainstorming の手順 9 を寄せた」と分けた。commit: b10c97e2 |
| F1-23 | 独立-1 | advisory | no | self-inflicted | PR 本文 | accepted | マージ後に測る指標・母集団・期間を PR 本文に書く |
| F1-24 | 独立-1 | advisory | no | self-inflicted | PR 本文 | accepted | 349 本が ERROR の内訳を PR 本文に書かない（実データの全期間は古い書式が多く、今の gate の誤 block の材料にならない。10 月の 57 本の内訳を書く） |
| P1-1 | 方針メモ-1 | advisory | no | self-inflicted | 閉じ方 | accepted | 方針メモ-1: Opus は承認ポイントの字下げなしの行を番号つき項目だけに限る許可リスト、Fable は 0 件 ERROR を推した。10 月の 57 本で許可リストは正当な行を 4 本で止め、混在の書式は 0 本だったので、0 件 ERROR にし、`3a.`・`3-1.` と見出しの付記を受けた。HCQ を参照するだけの本は 2 本とも案 ii（承認ポイントに項目を書かせる）。処置の欄も同じ helper で数えるのは Fable の案 |
| F2-1 | 独立-2 | high | yes | self-inflicted | 欄の検査の範囲 | accepted | 列挙: 設計: 変えない（項目の境界は行の形で決める。字下げなしの非項目行を ERROR にする案は字下げした `  2.` を閉じず、正当な 1/57 本を止める）。(b) 承認ポイントの項目を列挙外の形（`**2. x**`・`2．`・字下げした `  2.`・`3.1.`・`3A.`・`- **x**:`）で書くと前の項目の続きになり、前の項目の `根拠:` で通る。入力者: 2026-10 の requirements 57 本で 0 本。PR 本文の限界の先頭に書く |
| F2-2 | 独立-2 | high | yes | self-inflicted | 欄の検査の範囲 | accepted | 列挙: 設計: 変えない（テンプレートは方向性だけの承認ポイントを認める）。(b) 方向性だけを書き判断を Human Check Questions に置いた本が 0 件の検査を通る。入力者: 57 本で 0 本（方向性だけの本も 0）。PR 本文の限界の先頭に書く |
| F2-3 | 独立-2 | high | yes | self-inflicted | 欄の検査の範囲 | fixed | 設計: 変える（方向性の除外を行のどこかの文字列で決めず、項目の先頭のカテゴリの位置に限る）。57 本の方向性の項目 52 件はすべてこの形で、新しい ERROR は 0。commit: d97f9624 |
| F2-4 | 独立-2 | medium | no | self-inflicted | 欄の位置 | accepted | 欄の位置の規則が処置の形の正本・skill・ERROR の文に無い。① の blocking でない medium |
| F2-5 | 独立-2 | medium | no | self-inflicted | 依頼のずれ | re-reported | F1-5 の再掲 |
| F2-6 | 独立-2 | medium | no | self-inflicted | 依頼のずれ | re-reported | F1-4 の再掲 |
| F2-7 | 独立-2 | low | no | self-inflicted | 断片 | accepted | 旧#592 の断片が別の断片のファイル名を指す。① の low |
| F2-8 | 独立-2 | low | no | self-inflicted | テスト | accepted | テストの needle が緩い。① の low |
| F2-9 | 独立-2 | low | no | self-inflicted | PR 本文 | fixed | PR 本文の挙動の変化に、見出しの付記と `3a.`・`3-1.` を書く。commit: なし（PR 本文） |
| F2-10 | 独立-2 | advisory | no | self-inflicted | テンプレート | accepted | テンプレートの「節の存在と決まった欄の有無だけ」が件数の検査を含まない |
| P2-1 | 方針メモ-2 | advisory | no | self-inflicted | 閉じ方 | accepted | 安全策 4 の 1 回目の発火（クラスタ「欄の検査の範囲」の high を含む巡が 2 回）。Opus・Fable とも続行（3 だけ構造で閉じ、1・2 は (b)）を推した。割れた点なし。Fable は撤回の案（承認ポイントの欄の検査を外す）を選択肢に名前を分けて置くよう求めた。推奨で進めた。ユーザーの返事（2026-10-28）: 「安全策 4 は続行でよい」 |
| F3-1 | 独立-3 | low | no | self-inflicted | 欄の検査の範囲 | accepted | 方向性の除外の正規表現が前方一致で、`**方向性の変更範囲**` も除く。① の low |
| F3-2 | 独立-3 | low | no | self-inflicted | 欄の検査の範囲 | accepted | docstring の方向性の除外の書き方が前の挙動のまま。① の low |
| F3-3 | 独立-3 | low | no | self-inflicted | 欄の検査の範囲 | re-reported | F2-1 の再掲（項目の境界を列挙で決めている。方向性の項目の後ろでは検査されない形を含む） |
| F3-4 | 独立-3 | medium | no | self-inflicted | 欄の検査の範囲 | re-reported | F1-5 の再掲 |
| F3-5 | 独立-3 | medium | no | self-inflicted | 欄の検査の範囲 | re-reported | F1-4 の再掲 |
| F3-6 | 独立-3 | low | no | self-inflicted | 欄の検査の範囲 | re-reported | F1-10 の再掲（AC ごとの欄 1 つへの読み替えを含む） |
| F3-7 | 独立-3 | advisory | no | self-inflicted | 欄の検査の範囲 | accepted | 断片の「方向性を除く」が位置の限定を書いていない |
