---
type: patch
---

#### Summary

- `.steering/` への書き込みを検査する hook が、ApplyPatch の `Origin Session`（write-once）を、patch を当てた後の値を推定せずに判定するようにした。これまでは hunk を順に当てた後の値を推定していたが、推定と Codex の実際の当て方のずれ（緩い照合・fence・同じファイルの別の綴り・move の連鎖）が開いた入力として残っていた

#### Changed

- state.md を `*** Move to:` の移動先にする ApplyPatch は、移動元を読まずに、ターンによらず止める（移動元の値・連鎖した move・巨大な移動元を追わない）。peer turn の記録（承認・中止・完了など）の検査も、この patch では移動元を読まない
- それ以外の state.md に届く ApplyPatch（Update・Delete・Add と、state.md を移動元にする move）は、patch の本文か今の state.md に、バッククォートを除いて `Origin Session` の語があれば、ターンによらず止める
  - 値の行に触れない patch・同じ値の書き直しでも、state.md に語（fence の中の記入例を含む）があれば止める
  - 初回の値も ApplyPatch では書けない。Write・Edit で書く
- 語の無い state.md への、語の無い patch（state.md を移動先にしないもの）は、これまでどおり通す
- Write・Edit・MultiEdit の判定と、state.md 以外への move での peer turn の記録の検査は変えない
- 未リリースの断片 `20261002-patch-section-parser.md`・`20261003-origin-session-final-state.md` に書いた ApplyPatch の `Origin Session` の判定（値の和・hunk を順に当てた値で判定する、値を決められない patch を止める、同じ値の書き直しや作り直しを通す）は、この変更で置き換わる

#### Affected Files

- `hooks/scripts/validate-steering-write.py`
- `hooks/scripts/lib/patch_scoping.py`
- `references/phase-progression.md`
- `references/state-field-tiers.md`
- `tests/test_origin_session_final_state.py`
- `tests/test_origin_session_write_once_contract.py`
- `tests/test_patch_section_scan.py`
- `tests/test_peer_turn_write_boundary_e2e_contract.py`

#### User Action Required

- Codex など、Edit・Write の無い runtime で、`Origin Session` の語がある state.md を更新するときと、state.md を移動先にする move（steering のディレクトリの移し替えなど）では、ApplyPatch が止まり、降格もしない。shell で書かずに、ユーザーに頼む（`Origin Session` の値がある state.md は、これまで実データで見つかっていない）

#### Validation / Eval Impact

- `tests/test_origin_session_final_state.py`（hook の入口から、既存値のある state.md への ApplyPatch、通常のターンの初回の値、field 名の途中のバッククォート、既存の記入例の fence を開く patch、別のファイルの fence の後ろの値、state.md を移動先にする move〔FIFO の移動元を読まない・綴りの違う連鎖・Update の外の Move to・peer turn〕を止めること。語の無い patch を通すこと）
- `tests/test_origin_session_write_once_contract.py`・`tests/test_patch_section_scan.py`・`tests/test_peer_turn_write_boundary_e2e_contract.py`（既存値のある state.md への patch と、state.md を移動先にする move を通していた期待値を、止める側に直した）
- `tests/validate-plugin.sh`
