---
type: patch
---

#### Summary

- 指摘の行き先（`review-findings.md`）の検査が通してしまっていた形を閉じた。今回の Round の IG 節が無い、`absent@` の sha が古い、短い sha と長い sha が一致しない、同じ sha の 3 つ目以降の節で引き継ぎが落ちる、などである

#### Changed

- IG 節の見出しを `## IG<k> | task: <task> | sha: <HEAD の sha> | round: <Gate Rounds。無ければ 0> | findings: <N>` にした。`scripts/check-finding-dispositions.py` は `--task <Current Task>` が要る引数になる。どの task も、`tasklist.md` の Current Task にあり、その task を含む最後の IG 節の sha が HEAD で round がその task の `Gate Rounds` でなければ invalid にする（同じ HEAD のまま再 gate して今回の節を書き落とした形も止める）
- CLI は、どの IG 節の `absent@` の行も、その節の sha で git で分類する。sha が解けない節の行は invalid にする。`absent@` の sha は節の sha と同じでなければならない
- sha は、短い方が長い方の先頭と一致すれば同じとみなす（IR 節と `Independent Review` 行、IG 節と HEAD）
- 同じ sha の IR 節が 3 つ以上あるとき、前の節すべての high・実害クラスを、最後の節の `re-reported` が引き継ぐことを求める（re-reported を元の id まで辿って比べる）
- IR 節の `re-reported` の行は参照先より軽くできない（IG 節では、一部を直した後に軽くした再報告を止めない）。`rejected:duplicate` は、`rejected:refuted`・検証 `refuted`・根拠 `absent@` の行を参照できない
- IG の high・実害クラスの `advisory:out_of_scope` は、節の task がどれも前の IG 節にある（再入の）ときだけにした
- 検証が `refuted` の行は、行き先によらず根拠に `path:line` が要る。`absent@` の行の `file:line` の形は述語が見る（`check-gate-ledger.sh` の `findings` 行も見るようになった）

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/finding_dispositions.py`
- `plugins/gate-driven-development/scripts/check-finding-dispositions.py`
- `plugins/gate-driven-development/references/finding-dispositions.md`
- `plugins/gate-driven-development/skills/gdd-implementation-gating/SKILL.md`
- `plugins/gate-driven-development/tests/test_finding_dispositions.py`

#### User Action Required

- impl-gating Step 8 の検査は `check-finding-dispositions.py --steering <Steering Dir> --task <Current Task> --base <default-branch>` で回す（`--task` が無いと引数の誤りで exit 2）

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_finding_dispositions.py -q`
