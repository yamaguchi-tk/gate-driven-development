---
type: patch
---

#### Summary

- `references/phase-progression.md` の batch の hotfix 退避の手順が、hotfix の worktree の作り方を `gdd-using-git-worktrees` § Hotfix Worktree と書いていたのを、実際に定めている § 実装場所の決定 に直した
- 同じファイルの root stub（`stub.md`）の雛形に `Abandoned Hotfix Attempts` の項目を足した。stub.md をこの配列の置き場所とする規定はあったが、雛形に項目が無かった

#### Affected Files

- `references/phase-progression.md`

#### User Action Required

なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run`（変えたファイルを参照するテスト）、`bash tests/validate-plugin.sh`
