---
type: patch
---

#### Summary

- 判断の相談役 3 本（`gdd-opus-advisor`・`gdd-opus-advisor-max`・`gdd-fable-advisor`）の費用を下げた。並行の形（Opus high と Fable medium を並べる）、model、effort、選ぶときの基準、出力の欄は変えていない
- 相談役の「守ること」に、advisor ツールを呼ばない規定を足した。これまでは相談役の中で advisor（Fable 5.1）を呼ぶことが多く、1 回 約 $1.3 で、相談 1 本の費用の約半分になっていた
- 相談役の frontmatter に `omitClaudeMd: true` を足した。起動時に user・project・local の `CLAUDE.md` と memory の索引を読み込まなくなる。相談役は材料を場所で受けて、要るものは自分で Read する

#### Changed

- `agents/gdd-opus-advisor.md`・`agents/gdd-opus-advisor-max.md`・`agents/gdd-fable-advisor.md`（frontmatter の `omitClaudeMd: true`、本文の「守ること」）

#### Affected Files

- `agents/gdd-opus-advisor.md`
- `agents/gdd-opus-advisor-max.md`
- `agents/gdd-fable-advisor.md`

#### User Action Required

- 相談役を呼ぶ側の規則が、相談役に `CLAUDE.md` の内容を前提として読ませていたなら、そのファイルの場所を材料として渡す（相談役は渡された場所を読む）

#### Validation / Eval Impact

- `tests/test_advisor_agents.py`（`test_frontmatter_omits_claude_md` を追加）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
