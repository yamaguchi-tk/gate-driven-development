---
type: patch
---

#### Summary

- `.steering/` への書き込みを検査する hook が、ApplyPatch の patch を Codex の apply_patch と同じ規則で読むようにした。これまでは関数ごとに patch を読み直していて、規則が Codex と食い違っていた。そのため、次の patch が `Origin Session` の write-once の検査や、ほかの検査を素通りしていた
  - `*** End of File` の後ろに、同じファイルの `@@` の hunk が続く patch
  - `*** Update File:` などの header の前に空白がある patch（`*** Begin Patch` の直後や、Add File の中）
  - header の path の前に `\u2028` などの改行に似た文字がある patch
  - 同じ値の `Origin Session` を書き直してから、同じ patch でファイルを消す patch
  - `*** Add File:` で既存の state.md を、`Origin Session` の無い本文で置き換える patch
- 同じ値の `Origin Session` を持つ state.md を、同じ patch で消してから同じ値で作り直す patch は、止めるようになった

#### Changed

- patch を 1 つの規則で走査し、ファイルごとの追加行・削除行、対象の path、move の移動元、ファイルの削除を、すべてその結果から決める
- 行は `\n` だけで割る（行末の `\r` は落とす）
- fence は、ApplyPatch の hunk（`*** Add/Update File:` の 1 つ）ごとと、ファイルごとの両方で判定する（どちらかで fence の外なら検査する）
- `Origin Session` は、書込み後に残りうる値の和で判定する（追加行の値、move 元の値、ファイルを消す・move で移す patch の空値）。`*** Add File:` は全文の置き換えとして読み、追加行に `Origin Session` が無ければ削除として扱う
- steering の target を拾えない書き込みでも、`.steering` を含み、LF・CRLF 以外の改行に似た文字を含むなら、通さずに止める（`\n` 以外で行を割る harness では header になる）
- `*** End of File` で、そのファイルの区切りを閉じない
- header は、Update File の中では行末の空白だけを落として判定する（先頭に空白のある行は context 行）。それ以外の場所では、前後の空白を落として判定する
- ファイルの中の `+++`・`---` で始まる行は、`++`・`--` で始まる内容として扱う
- `*** Move to:` は Update File の中でだけ move として扱う。1 つの Update File の中の `*** Move to:` は全部移動先にする。Update File の外の `*** Move to:` も、対象の path として拾う
- `*** End Patch` の後ろの行は、次の header までどのファイルにも属さない。後ろにある header は、対象の path として拾う

#### Affected Files

- `hooks/scripts/lib/patch_scoping.py`
- `hooks/scripts/validate-steering-write.py`
- `tests/test_patch_section_scan.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_patch_section_scan.py`（hook の入口から、`*** End of File` の後ろの書き換え・削除、header の前の空白、`*** End of File` の後ろの fence、path の前の改行に似た文字、move をまたぐ fence、書き直してから消す patch、Add File での置き換え、同じ path への move、行の中の改行に似た文字の後ろの header、同じファイルの hunk をまたぐ fence。既存値の無い state.md で消して作り直す・move を重ねる patch の単体テスト。走査の結果を関数ごとに見るテスト）
- `tests/test_origin_session_write_once_contract.py`（既存の move のテスト）
- `tests/validate-plugin.sh`
