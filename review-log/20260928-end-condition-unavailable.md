---
lane: L1
pr: 旧#192
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | a00b81c0b38845155476876c8956b7ec3ec05ebb | 0 | 0 | 0 | 2026-09-28T13:45+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| U1 | 独立-1 | low | no | self-inflicted | unavailable-exception-scope | next-pr | `CLAUDE.md:88` の足した句が「PR 本文に」を限定せず、「Claude Code 以外で読むとき」が方針メモに書かせる `memory 照合: unavailable`（:120）まで PR 本文に書くと読める。「これ」が括弧の外の「巡の sha と結果」を指すことも読み取りにくい。「…が PR 本文に書かせる `unavailable` の行は、巡の sha と結果とは別に書く」にし、テストの句も揃える。近道の規定で次の PR |
| U2 | 独立-1 | low | no | self-inflicted | test-power | next-pr | テストのコメントは「同じ文に書く」と言うが、assert は終了条件の箇条の 1 行に句があるかだけを見る。括弧の外（行末）へ移しても通る。括弧の中で隣接することを固定するか、コメントを「同じ行」に直す。近道の規定で次の PR |
| U3 | 独立-1 | advisory | no | inherited | step7-body-list-incomplete | next-pr | 経路: 差分の `CLAUDE.md:88`（PR 本文に書く `unavailable` の行を名指し）→ 同じく PR 本文の中身を列挙する手順 7（:96）。:96 の列挙に `unavailable` の行が無い（列挙はもとから網羅的ではない）。PR 本文の advisory に載せ、次の PR |
