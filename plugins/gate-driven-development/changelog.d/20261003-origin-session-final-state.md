---
type: patch
---

#### Summary

- `.steering/` への書き込みを検査する hook が、ApplyPatch の `Origin Session`（write-once）を、hunk を patch の順に当てた後の値で判定するようにした。これまでは各 hunk の値の和で近似していたので、順序で決まる最終状態とずれて、次の patch を通していた
  - `*** Add File:` で値を書いた後に、`*** Update File:` でその値を消す patch（write-once の削除）
  - 値を持つファイルを move で state.md に重ねてから、`*** Add File:` で値の無い本文に置き換える patch（write-once の削除）
  - 値を複数持つファイルの move で、値の行を一部だけ消す patch（残った値で書き換え。peer turn では初回値の設定）
- peer turn の記録（承認・中止・完了など）の検査が、ApplyPatch の move で運ばれる移動元の内容も見るようにした

#### Changed

- ApplyPatch の `Origin Session` は、Codex の apply_patch と同じ順序で当てる。Add File は全文を置き換える。Delete File は消す。Update は今の値から削除行の値を除き、追加行の値を足す。move は移動先へ写してから移動元を消す
- 最後にファイルが無いか、値が無ければ、値を消したものとして扱う。既存値の無い state.md を消して作り直す書き込みは、初回書込みとして扱う
- state.md へ流れ込む hunk（Add File・Delete File・move と、`Origin Session` の行か fence 行に触れる Update）があり、値を決められないときは、既存値の有無を問わず止める（state.md に `Origin Session` が無くても止まる）。決められないのは次のとき
  - 同じ patch の前の hunk が書いた・消した・移したファイルへの Update（同じ state.md を 2 つの節で Update する patch も含む。1 つの節にまとめるか、Write で書き直す）
  - 今の値に無い値の削除行
  - fence 行（```・~~~）を足す・消す Update の hunk（fence の中の値は reader が読まない）。Add File は全文を置き換えるので、fence を含む本文も Write と同じ規則で読む
  - patch が読むファイル（移動元・Update の対象）が通常のファイルでない・読めない
- 既存値と同じ値で、state.md を消してから作り直す patch は、通るようになった
- コロンの後に何も無い `Origin Session:` の行は、値として数えない（既存値の横に足しても止めない）。コロンの後が空白だけの行は、これまでどおり空の値として数える
- peer turn の記録の検査では、move で steering のファイルへ運ばれる移動元（連鎖した move の元も含む）の今の内容も検査する。移動元が通常のファイルでないか読めなければ止める
- Write・Edit の経路の判定は変えない

#### Affected Files

- `hooks/scripts/validate-steering-write.py`
- `hooks/scripts/lib/patch_scoping.py`
- `tests/test_patch_section_scan.py`
- `tests/test_origin_session_final_state.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_origin_session_final_state.py`（hook の入口から、Add の後の削除、move と Add の重なり、move での一部の削除、値の無い行、同じ patch で消えたファイルへの Update、同じファイルの再 Update、当たらない削除行、値を隠す fence・閉じ fence の削除、FIFO・無い移動元、長い move の連鎖、fence を含む Add File（全文の規則で読む）、同じ値での作り直し、既存値の無い作り直し。peer turn の初回値と、連鎖した move で運ばれる承認の記録）
- `tests/test_origin_session_write_once_contract.py`・`tests/test_patch_section_scan.py`・`tests/test_peer_turn_write_boundary_*`（既存）
- `tests/validate-plugin.sh`
