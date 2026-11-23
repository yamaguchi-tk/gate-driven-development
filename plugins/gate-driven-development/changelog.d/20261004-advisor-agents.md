---
type: minor
---

#### Summary

判断の相談役の agent を 3 本足した。`gdd-opus-advisor`（Opus・high）、`gdd-fable-advisor`（Fable・medium）、`gdd-opus-advisor-max`（Opus・max）で、どれも read-only（Read・Grep・Glob）。model と effort は agent 定義で固定している。

- 自律モードの判断役（`references/autonomy.md` 判断の手順 1）、判断役と食い違ったときの Fable（手順 3）、事前回答の委任先（`references/human-check-template.md` § 事前回答）の起動先を、この agent に替えた。これまでは `Plan`・`general-purpose` に `model` を付けて起動していたので、effort は main から継承されていた
- dispatch model gate は、Opus の相談役を `model` 省略の起動だけ工程の model 検査から外し（`model` を明示した起動は判定する）、Fable の相談役は `model` の値によらず外す。これまでは、工程が決まっているときに手順 3 の Fable を起動すると、工程の model（opus か sonnet）に変えるよう警告していた
- plugin を更新する前から動いているセッションでは、定義が読み込まれていない。そのときは今までどおり `Plan` に `model` を付けて定義の本文を渡し、effort を継承したことを `worklog.md` の行の `model:` の欄に書く
- `gdd-opus-advisor-max` は、plugin の reference からは起動しない。利用する repo の規則が、high の推奨と食い違ったときの相談し直しを定めた場面で使う

#### Affected Files

- `plugins/gate-driven-development/agents/gdd-opus-advisor.md`
- `plugins/gate-driven-development/agents/gdd-opus-advisor-max.md`
- `plugins/gate-driven-development/agents/gdd-fable-advisor.md`
- `plugins/gate-driven-development/hooks/scripts/lib/agent_dispatch_gate.py`
- `plugins/gate-driven-development/references/autonomy.md`
- `plugins/gate-driven-development/references/human-check-template.md`
- `plugins/gate-driven-development/references/fixed-models.md`
- `plugins/gate-driven-development/README.md`
- `plugins/gate-driven-development/tests/test_advisor_agents.py`
- `plugins/gate-driven-development/tests/test_agent_dispatch_model_gate_contract.py`
- `plugins/gate-driven-development/tests/test_agent_tool_allowlist_contract.py`
- `plugins/gate-driven-development/tests/checks/agent-effort-schema.sh`

#### User Action Required

- 相談役の agent は、plugin を更新してセッションを開き直すと使える

#### Validation / Eval Impact

- `tests/test_advisor_agents.py` を足した（3 本の model・effort・本文の一致、Opus の相談役に `model` を明示した起動を判定すること、Fable の相談役は判定しないこと）
- `tests/test_agent_dispatch_model_gate_contract.py` に、相談役を model 省略で起動したときに警告を出さないことと、`general-purpose` に `model: fable` を付けた起動には警告を出すことのテストを足した
- `tests/test_agent_tool_allowlist_contract.py`・`tests/checks/agent-effort-schema.sh` の表に 3 本を足した
- `bash tests/validate-plugin.sh`
