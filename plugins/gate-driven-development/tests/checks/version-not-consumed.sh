#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

# 版数はリリースのコミットでだけ上げる。通常の PR は版数系のファイル（3 manifest・CHANGELOG.md の
# 版見出し・docs/VERSIONING.md の現状）に触れず、changelog.d/ に断片を足す。
# 正本: docs/VERSIONING.md § 版数はリリースでだけ上げる
#
# 3 manifest 間の一致は grade-evals、docs/VERSIONING.md の現行バージョンとの一致は
# test_distribution_readiness_contract が見る。本 check はそれ以外を見る。
#
# 判定は 2 層:
#   A（常時・git 不要）  manifest version が semver / CHANGELOG 先頭の released 見出しと一致 /
#                        changelog.d/ の断片の書式（scripts/release.py の parse と同じもの）
#   B（統合先 ref がある場合）manifest version を、統合先との分岐点（merge-base）と統合先の tip の版数と比べる
#       分岐点と同じ   = 通常の PR。分岐後に断片を 1 つ以上足していること（統合先が先にリリースしていても通す）。
#                        分岐点の断片を消す・書き換えるのは FAIL（足した断片と対の review-log の `amends:` で宣言した、同じパスでの書き換えだけ通す）
#       tip より大きい = リリースのコミット。断片が残っていないこと・その版数が統合先で released 済みでないこと
#       それ以外       = 後退か、統合先の版数の再利用。FAIL
#   断片として数えるのは scripts/release.py が集めるもの（changelog.d/ 直下で書式が正しいもの）だけ。
# B が実行できない環境では `SKIP-B: <理由>` を必ず出力する。
#
# SKIP-B の判定は「本リポジトリの自己申告（identity marker）」だけで行う
# （2026-09-15、sibling の review-log-present.sh で H2→H2'→H3→H4→H5 と5回
# 連続再発した設計欠陥を踏まえ、Opus へのセカンドオピニオンに基づき両
# スクリプトへ同時適用）。H2〜H4 の過去の設計はいずれも「消費者環境かどうか」
# を何らかの派生信号から逆算しており、狭めるたびに別の変異で再発した:
#   - git の失敗モード（is-inside-work-tree の成否）から逆算 → GIT_* 環境変数
#     の汚染、壊れた symlink で真の消費者環境と区別不能
#   - root が `<repo_root>/plugins/<root の名前>` というディレクトリレイアウト
#     と一致するかどうかから逆算 → root が別名の symlink（plugin cache の
#     バージョン番号ディレクトリ等）経由だと basename が一致せず真の開発
#     checkout でも SKIP-B になる fail-open。さらに逆方向にも壊れていた:
#     本物の消費者環境（別リポジトリの marketplace clone）が同じレイアウトを
#     偶然満たし「開発 checkout」と誤判定される事例が実機に複数実在した
# 代わりに、リポジトリが既に持っている固定の自己申告フィールド
# （`.claude-plugin/marketplace.json` の `name`）を読むだけにする。git 呼び
# 出しにも、ディレクトリ名の偶然の一致にも触れないため、この設計は上記の
# どの入力空間にも構造的に触れない。manifest が壊れていて `name` を読めない
# 場合は、推測せず FAIL にする。identity が確定する場合は「本リポジトリの
# 開発 checkout」と確信できるため、以後の git 呼び出しの失敗は理由を問わず
# すべて FAIL（fail-closed）にする。
#
# この方式自体も H5 として5回目の再発を起こした: `name` キー欠落・null・
# 非文字列・空文字列が `.get("name") == MARKETPLACE_NAME` を素通りして False
# （SKIP-B）に落ちていた。`name` は marketplace の主キーであり、これを欠く
# manifest はインストール不能な壊れた manifest であるため None（判定不能・
# FAIL）に倒す。H5 は H2〜H4 とは軸が異なる（開いた入力ではなく、JSON 型空間
# という列挙可能な有限集合の中の未処理分岐）ため、identity marker への転換
# 自体を覆す根拠にはならない（Opus のセカンドオピニオンで確認）。
# `repository_identity()` の受理集合は「False は manifest が存在しないか、
# 妥当な manifest が別の名前を宣言している場合だけ。その中間はすべて None」
# という1ルールに凍結し、以降 SKIP-B 判定述語そのものへの追加修正は行わない。
#
# fail-open を作らないための規則（入力の欠落と書式不正を同じ扱いにする）:
#   比較の述語を `if <両辺が semver>` で守ると、片辺が書式不正のときに述語ごと消えて
#   無言 PASS になる。そのため manifest version と ref 側 manifest version は
#   「読めない・semver でない」時点で FAIL にし、比較の手前で潰す。
#   洗う軸は「文字列としての書式」ではなく **JSON の型空間**（string / number / bool /
#   null / array / object / キー欠落 / 不正 JSON / 空ファイル / 非 UTF-8 / ファイル不在）。
#   とくに parse 失敗の sentinel に `None` を使うと `"version": null` と値が衝突し、
#   `is not None` で守った述語が自ら迂回して無言 PASS になる（2026-08-19 実測）。
#   型空間の各形は tests/test_changelog_fragments.py が固定する。
#
# PR #93 の PR 後レビュー3巡目（独立-5・独立-6に続く同クラスタの High）:
# load_dynamic_module() は exec_module() 呼び出しの SystemExit だけを守り、
# 動的ロードしたモジュールへの「呼び出し」（repository_identity() 呼び出し、
# release.load_fragments() 呼び出し等）で SystemExit が送出されると、
# fail()/die() に到達せず rc=0 で静かに成功していた（同型の fail-open が
# 呼び出し箇所ごとに再発する「開いた列挙」。independent-review.md (h) が
# 指摘する型）。Opus へのセカンドオピニオンで、個々の呼び出し箇所を
# `except BaseException` で塞ぐ対処ではなく、「判定を宣言したか」を機械的に
# 検査する構造に倒す設計を採用した: 本体を run() 関数に集約し、run() が
# 正常return しなかった（SystemExit・その他の例外を含む）場合は無条件で
# FAIL、正常return した場合だけ `VERDICT: version-not-consumed: OK|SKIP` を
# 出力する。呼び出し中の想定外の SystemExit(0) も、この方式では
# 「run() が正常return しなかった」に合流し、fail-closed になる。
# validate-plugin.sh 側にも、rc=0 なのに VERDICT 行が無い check を一律で
# FAIL にする番兵を追加した（全 BLOCK チェック共通、tests/validate-plugin.sh
# 参照）。

echo "BLOCK: version-not-consumed"
"$PYTHON_BIN" - "$ROOT" <<'PY'
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys
from collections import Counter

root = pathlib.Path(sys.argv[1])
label = "version-not-consumed"
failures: list[str] = []


def fail(message: str) -> None:
    failures.append(message)
    print(f"FAIL: {label}: {message}")


def die() -> None:
    print(f"FAIL: {label}")
    raise SystemExit(1)


def _uncommitted_new_fragments(git, base_blobs: dict[str, str], committed: list[str]) -> list[str]:
    """作業ツリーに新しく足した（untracked か、index に足しただけの）`changelog.d/*.md` のうち、
    今の作業ツリーを commit したら足した断片に数えるもの。

    `git mv` で改名したもの（index の rename）は、新しい名前を足したものとして含める。
    commit 側（merge-base の断片で元の場所に同じ中身が残っていないものと同じ中身を、その個数の分だけ外す）と
    同じ規則で、他の PR の断片の改名を外す。`committed` は merge-base..HEAD の commit で改名とみなした断片
    （`changelog.d/<name>`）で、消えた断片の分を先に取る。残りの分を、候補がパスの順に取る。
    merge-base にあるパスは、commit しても足した断片にならないので含めない。
    中身は作業ツリーで比べる（作業ツリーを `git add` して commit する前提）。
    commit 済みの断片の書き換え（` M`・`M `）・削除は含めない。ドットファイル・サブディレクトリも数えない。
    """
    status = git("status", "--porcelain", "--no-renames", "--untracked-files=all", "--", "changelog.d")
    new = []
    for line in status.stdout.splitlines():
        path = pathlib.Path(line[3:])
        if not (line.startswith("??") or line[:1] == "A"):
            continue
        if not (path.parent.name == "changelog.d" and path.suffix == ".md" and not path.name.startswith(".")):
            continue
        if f"changelog.d/{path.name}" not in base_blobs:
            new.append(f"changelog.d/{path.name}")
    if not new:
        return []
    present = [path for path in {*base_blobs, *committed, *new} if (root / path).is_file()]
    hashed = git("hash-object", "--", *present)
    work_blobs = dict(zip(present, hashed.stdout.split())) if hashed.returncode == 0 else {}
    moved = Counter(blob for path, blob in base_blobs.items() if work_blobs.get(path) != blob)
    pending = []
    for path in [*sorted(committed), *sorted(new)]:
        blob = work_blobs.get(path)
        if moved[blob] > 0:
            moved[blob] -= 1
        elif path in new:
            pending.append(path)
    return pending


def run() -> str:
    """本体。正常return した場合だけ呼び出し元が VERDICT 行を出す
    （戻り値は 'OK' か 'SKIP'）。die() の SystemExit(1)、および動的ロード
    したモジュールへの呼び出し中に想定外の例外（SystemExit を含む）が
    送出された場合は、正常return しない一点だけで「宣言なき成功」と区別
    する（呼び出し箇所を個別に except BaseException で塞ぐのではなく、
    正常return しなかった経路をすべて呼び出し元の except で一律 FAIL に
    合流させる。PR #93 の PR 後レビュー3巡目・同クラスタの High 対応）。"""

    # 動的モジュールロード（importlib）専用のブートストラップ。独立レビュー
    # 指摘（PR後-1→独立-6・high・実害あり、両方 self-inflicted）: `exec_module()`
    # を個別に `except Exception` で囲むパターンが repository_identity.py・
    # release.py の2箇所に別々に書かれ、両方とも `SystemExit`（`BaseException`
    # 派生だが `Exception` の派生ではない）を捕捉できなかった。モジュールの exec
    # 中に何らかの理由で `SystemExit` が送出されると try/except を素通りし、
    # スクリプト全体が終了コード 0 で静かに成功してしまう（release.py の場合は
    # `release` 変数が未初期化のモジュールオブジェクトのまま後続で参照され
    # `AttributeError` で不透明に落ちる別の実害もある）。Opus へのセカンド
    # オピニオン: これは受理集合が原理的に閉じない開いた入力ではなく、
    # `exec_module()` という有限で列挙可能な単一の呼び出しパターンのコピペ
    # 網羅漏れであり、ロードの唯一の入口をここに集約して1箇所だけ
    # `except BaseException` にすることで閉じる（`KeyboardInterrupt` も同様に
    # `BaseException` 派生だが、die() 自体が `SystemExit(1)` を投げてプロセスを
    # 終了させるため、ここで拾って fail() → die() しても実害はない）。
    # `BaseException` の対象を exec_module 呼び出しだけに限定し、静的ファイル
    # 読み込み（VERSIONING.md 等）には広げない（`read_text()`/`json.loads()` は
    # `SystemExit` を投げないため対象外。広げると `KeyboardInterrupt` を握り
    # 潰す逆方向の fail-open を新たに作る）。
    def load_dynamic_module(module_name: str, path: pathlib.Path):
        """path を module_name として動的ロードする。成功時は (module, None)、
        失敗時は (None, error) を返す（exec_module の例外はここでだけ
        BaseException で受ける。呼び出し側は fail()/die() を書く）。"""
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException as error:  # noqa: BLE001 - SystemExit も含めて捕捉する（上記コメント参照）
            return None, error
        return module, None

    def semver(text):
        # JSON の version は str とは限らない（null / number / bool / array / object）。
        # 非文字列は「semver として読めない」に合流させ、AttributeError で落とさない。
        if not isinstance(text, str):
            return None
        matched = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", text.strip())
        return tuple(int(part) for part in matched.groups()) if matched else None

    # parse 失敗の sentinel。JSON が取りうるどの値（null を含む）とも型で区別できる。
    # `None` を sentinel にすると `"version": null` と衝突し、後段の述語が自ら迂回する。
    UNPARSED = object()

    # --- 入力 1: manifest version ---
    manifest_version = ""
    manifest_path = root / ".claude-plugin" / "plugin.json"
    try:
        manifest_version = json.loads(manifest_path.read_text(encoding="utf-8")).get("version", "")
    except Exception as error:  # noqa: BLE001 - 読めないこと自体を FAIL として報告する
        fail(f"cannot read {manifest_path.name}: {error}")
    if not semver(manifest_version):
        fail(f"manifest version is not semver: {manifest_version!r}")
        manifest_version = ""  # 比較の手前で潰す（非文字列を後段の文字列比較へ流さない）

    # --- 入力 2: 統合先の定義 ---
    integration_ref = os.environ.get("GDD_INTEGRATION_REF", "").strip()
    declared_ref = ""
    try:
        versioning_text = (root / "docs" / "VERSIONING.md").read_text(encoding="utf-8")
    except Exception as error:  # noqa: BLE001
        versioning_text = ""
        fail(f"cannot read docs/VERSIONING.md: {error}")
    ref_match = re.search(r"^- \*\*統合先の定義\*\*: `([^`]+)`", versioning_text, re.M)
    if ref_match:
        declared_ref = ref_match.group(1)
    elif not integration_ref:
        fail("docs/VERSIONING.md is missing the canonical record line '- **統合先の定義**: `<ref>`'")

    # --- 入力 3: CHANGELOG 先頭の released 見出し ---
    try:
        changelog_text = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    except Exception as error:  # noqa: BLE001
        changelog_text = ""
        fail(f"cannot read CHANGELOG.md: {error}")
    released_headings = re.findall(r"^### \[(\d+\.\d+\.\d+)\] - ", changelog_text, re.M)

    # --- 入力 4: changelog.d/ の断片（書式の正本は scripts/release.py）---
    fragments = []
    release, release_load_error = load_dynamic_module("gdd_release", root / "scripts" / "release.py")
    if release is None:
        fail(f"cannot load scripts/release.py to parse changelog.d/: {release_load_error}")
    else:
        try:
            fragments, fragment_errors = release.load_fragments(root)
            for error in fragment_errors:
                fail(f"changelog.d/{error}")
        except Exception as error:  # noqa: BLE001
            release = None
            fail(f"cannot load scripts/release.py to parse changelog.d/: {error}")

    # --- 層 A: オフラインでも常に実効の判定 ---
    if not released_headings:
        fail("CHANGELOG.md has no released heading of the form '### [x.y.z] - YYYY-MM-DD'")
    elif manifest_version and released_headings[0] != manifest_version:
        fail(
            f"CHANGELOG.md top released heading is [{released_headings[0]}] "
            f"but the manifest version is {manifest_version}"
        )

    # --- 層 B: 統合先 ref が解決できる場合だけ実行し、できない場合は理由を必ず出す ---
    ref = integration_ref or declared_ref

    def git(*args: str):
        # review-log-present.sh の H2' 対応と揃える（受理集合の対称性 (h) 観点、
        # 2026-09-15）: GIT_DIR 等の GIT_* 環境変数が子プロセスにそのまま継承される
        # と、呼び出し元の環境次第で `git -C <root>` の判定対象が root とは別の
        # リポジトリにすり替わる（実測で GIT_DIR=/nonexistent/x.git を付けると
        # 本来 FAIL すべき入力が SKIP-B になることを確認）。GIT_* を除去する。
        env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        # 利用者の diff.relative=true では diff が cwd 相対のパスを出し、prefix 付きの集合と一致しなくなる。
        return subprocess.run(
            ["git", "-C", str(root), "-c", "diff.relative=false", *args],
            capture_output=True,
            text=True,
            errors="replace",  # ref 側が非 UTF-8 でも decode 例外で落とさず、下の parse で FAIL にする
            check=False,
            env=env,
        )

    repo_root = (root / ".." / "..").resolve()
    MARKETPLACE_NAME = "gate-driven-development"

    # repository_identity() は sibling の review-log-present.sh と共有する
    # scripts/lib/repository_identity.py に一本化した（2026-09-16。H2〜H6 の
    # fail-open がそれぞれ独立に再発する経路になっていたため、Opus への
    # セカンドオピニオンに基づき共有モジュール化した。判定ロジック本体の
    # コメント・設計根拠は同ファイル参照）。
    # このロードは SKIP-B 判定より前にあるため、SKIP-B の前提は「本リポジトリの
    # checkout には scripts/lib/repository_identity.py が同梱されている」ことに
    # 変わった（一本化前は identity 判定がインラインで、消費者環境は追加ファイル
    # なしに SKIP-B できた）。通常の marketplace 配布は scripts/ を含むため通常は
    # 崩れない前提だが、モジュール欠落・破損時はロード失敗を SKIP に倒さず FAIL
    # にする（判定不能を「無い」と誤認しない、既存の SKIP-B 設計判断と同じ方針）。
    identity_lib, identity_load_error = load_dynamic_module(
        "gdd_repository_identity_for_version_check", root / "scripts" / "lib" / "repository_identity.py"
    )
    if identity_lib is None:
        fail(f"cannot load scripts/lib/repository_identity.py: {identity_load_error}")
        die()

    prefix = ""

    def version_at(rev: str, where: str):
        """rev の manifest version を返す。読めない・semver でなければ fail() して UNPARSED を返す。"""
        shown = git("show", f"{rev}:{prefix}.claude-plugin/plugin.json")
        if shown.returncode != 0:
            fail(f"cannot read .claude-plugin/plugin.json at {where}: {shown.stderr.strip()}")
            return UNPARSED
        try:
            version = json.loads(shown.stdout).get("version", "")
        except Exception as error:  # noqa: BLE001
            fail(f"cannot parse .claude-plugin/plugin.json at {where}: {error}")
            return UNPARSED
        if not semver(version):
            fail(
                f".claude-plugin/plugin.json at {where} has a non-semver version: {version!r}. "
                "The shipping version cannot be compared against it (a malformed version must not pass)"
            )
            return UNPARSED
        return version

    def fragment_blobs(rev: str):
        """<rev> の changelog.d/ 直下にある、断片のファイル名パターンに一致するファイルの blob sha。
        サブディレクトリ・ドットファイルは除く（release.py が集めないものは追跡しない）。
        `git -C` の cwd を基点にしているので、パスは changelog.d/ 相対（ls-tree は既定で cwd 相対のパスを返す。
        root 相対にする `--full-name` は使わない）。top-level からのパスで出る `git diff --name-only` の行は、
        prefix を外してから突き合わせる。"""
        result = git("ls-tree", "-r", rev, "--", "changelog.d")
        blobs: dict[str, str] = {}
        if result.returncode != 0:
            fail(f"cannot list changelog.d/ at {rev}: {result.stderr.strip()}")
            return blobs
        for line in result.stdout.splitlines():
            meta, _, path = line.partition("\t")
            parts = meta.split()
            if len(parts) != 3 or parts[1] != "blob":
                continue
            parent, _, name = path.rpartition("/")
            if parent == "changelog.d" and release is not None and release.NAME_RE.fullmatch(name):
                blobs[path] = parts[2]
        return blobs

    def find_lost_fragments(base_blobs, head_blobs):
        """merge-base にあった断片が HEAD で消えた・書き換わったものを返す。
        同じ内容（blob）の断片が複数あっても、生き残った個数分だけ「リネーム」として見逃す。
        まず同じ場所に同じ内容で残っている分を確保し、残りだけを他所へのリネーム候補として消費する
        （先に全体を set 化すると、別の生存ファイルと blob が一致するだけで削除が素通りする）。"""
        survivors = Counter(head_blobs.values())
        unresolved = []
        for path, blob in base_blobs.items():
            if head_blobs.get(path) == blob:
                survivors[blob] -= 1
            else:
                unresolved.append((path, blob))
        lost = []
        for path, blob in sorted(unresolved):
            if survivors[blob] > 0:
                survivors[blob] -= 1
            else:
                lost.append(path)
        return sorted(lost)

    # review-log-present.sh の FRONTMATTER_RE と同じ形（test_changelog_fragment_amends.py が一致を固定する）
    FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)

    def frontmatter_values(text: str, key: str):
        """front matter の key の値の並び。front matter が読めなければ None。"""
        matched = FRONTMATTER_RE.match(text)
        if not matched:
            return None
        return [value.strip() for name, sep, value in (line.partition(":") for line in matched.group(1).splitlines())
                if sep and name.strip() == key]

    def amended_fragments(base_sha: str, added_fragments, base_blobs, head_blobs):
        """書き換えを許す、他の PR の断片（changelog.d/ 相対のパス）。
        宣言は、この branch で足した断片と対になる review-log/<slug>.md（merge-base に無いもの）の HEAD の
        front matter の `amends: <断片のファイル名>, ...` だけで読む。許すのは同じパスでの書き換え（`type:` の書き換えも
        含む。書式は層 A が見る）だけ（削除・改名は今までどおり lost に残る）。読めない宣言は fail() する。"""
        allowed = set()
        for line in added_fragments:
            slug = line.rpartition("/")[2][: -len(".md")]
            log = f"review-log/{slug}.md"
            shown = git("show", f"HEAD:{log}")
            if shown.returncode != 0 or git("cat-file", "-e", f"{base_sha}:{log}").returncode == 0:
                continue
            values = frontmatter_values(shown.stdout, "amends")
            if values is None:
                fail(f"{log}: cannot read the frontmatter ('---' / 'key: value' lines / '---') to look for amends:")
                continue
            if len(values) > 1:
                fail(f"{log}: amends: is declared {len(values)} times; write it once")
                continue
            for name in (values[0].split(",") if values else []):
                name = name.strip()
                path = f"changelog.d/{name}"
                if release is None or not release.NAME_RE.fullmatch(name) or path not in base_blobs:
                    fail(
                        f"{log}: amends: names {name!r}, which is not the file name of a fragment present at the "
                        "merge-base (write file names such as 20260911-x.md, separated by commas)"
                    )
                    continue
                if path not in head_blobs:
                    continue
                allowed.add(path)
        return allowed

    identity = identity_lib.repository_identity(repo_root, MARKETPLACE_NAME)
    skip_reason = ""
    if identity is None:
        fail(
            f"cannot parse {repo_root}/.claude-plugin/marketplace.json to confirm this is a checkout of "
            f"{MARKETPLACE_NAME}; refusing to guess"
        )
        die()
    elif not ref:
        skip_reason = "no integration ref declared"
    elif not identity:
        # review-log-present.sh の H2'/H3/H4 対応と揃える（2026-09-15、Opus/Fable への
        # セカンドオピニオンで両スクリプトへの同時適用を確認）: repo_root が本
        # リポジトリの checkout ではない（marketplace.json の name 不一致・欠落）
        # = 消費者環境（plugin cache 配置等）とみなし、git を一切呼ばずに SKIP-B
        # にする。
        skip_reason = (
            f"{repo_root} does not look like a checkout of {MARKETPLACE_NAME} "
            "(.claude-plugin/marketplace.json name mismatch or missing; plugin distributed via cache/marketplace?)"
        )
    else:
        # 本リポジトリの checkout であると確信できる以上、以後の git 呼び出しの
        # 失敗は理由を問わずすべて FAIL にする（symlink・環境変数汚染・壊れた
        # gitdir 等、どんな変異でも SKIP 側に倒れる余地を無くす）。
        inside_work_tree = git("rev-parse", "--is-inside-work-tree")
        if inside_work_tree.returncode != 0 or inside_work_tree.stdout.strip() != "true":
            fail(
                f"{repo_root} is a checkout of {MARKETPLACE_NAME} (.claude-plugin/marketplace.json name matches) "
                "but git rev-parse --is-inside-work-tree did not confirm it "
                f"(rc={inside_work_tree.returncode}, stdout={inside_work_tree.stdout.strip()!r}, "
                f"stderr={inside_work_tree.stderr.strip()!r}); refusing to guess"
            )
            die()
        elif git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").returncode != 0:
            skip_reason = f"ref '{ref}' is not resolvable locally (fetch it, or set GDD_INTEGRATION_REF)"
        elif git("merge-base", "--is-ancestor", "HEAD", f"{ref}^{{commit}}").returncode == 0:
            # HEAD が統合先に含まれている = ブランチ側の差分が存在しない（統合先そのものを検査している）。
            # 統合先には、マージ済み PR の断片が次のリリースまで残っているのが正常な状態である。
            skip_reason = f"HEAD is contained in {ref} (no branch ahead of the integration target)"
        else:
            merge_base = git("merge-base", f"{ref}^{{commit}}", "HEAD")
            if merge_base.returncode != 0:
                fail(
                    f"cannot find the merge-base of {ref} and HEAD (no common ancestor in the local history; "
                    f"if this is a shallow clone, run git fetch --unshallow): {merge_base.stderr.strip()}"
                )
                die()
            base_sha = merge_base.stdout.strip()
            if git("diff", "--quiet", base_sha, "HEAD", "--", ".").returncode == 0:
                # このブランチが分岐後に plugin ディレクトリを変えていない = 何も出荷しない。
                # 出荷物が無いのに断片を要求すると、中身の無い変更履歴を書かせることになる
                # （実測: `.github/` だけを触る PR が版数上げを要求された）。統合先の tip ではなく
                # merge-base と比べる（tip と比べると、分岐後に統合先が plugin を変えただけで
                # plugin に触れていないブランチにも断片を求めていた。PR #269）。
                skip_reason = f"plugin tree is unchanged since the merge-base with {ref} (this branch ships nothing)"
            else:
                prefix = git("rev-parse", "--show-prefix").stdout.strip()

    outcome = f"v{manifest_version}"
    if skip_reason:
        print(f"{label}: SKIP-B: {skip_reason} — layer A enforced")
        if failures:
            die()
        return "SKIP"

    base_version = version_at(base_sha, f"the merge-base with {ref} ({base_sha[:12]})")
    ref_version = version_at(ref, ref)

    # manifest_version が読めない場合は入力 1 で fail 済み。比較は 3 つとも読めるときだけ行う。
    if manifest_version and base_version is not UNPARSED and ref_version is not UNPARSED:
        head, tip = semver(manifest_version), semver(ref_version)
        if head == semver(base_version):
            # 通常の PR。統合先が分岐後にリリースしていても、統合先の取り込みは求めない。
            # 数えるのは release.py が集める断片だけ（ドットファイル・サブディレクトリは数えない）。
            added = git("diff", "--no-renames", "--name-only", "--diff-filter=A", base_sha, "HEAD", "--", "changelog.d")
            collectable = {f"{prefix}changelog.d/{fragment.path.name}" for fragment in fragments}
            base_blobs = fragment_blobs(base_sha)
            head_blobs = fragment_blobs("HEAD")
            # merge-base の断片が元の場所から消えた・書き換わったとき、同じ中身が別の名前で足されたものは、
            # 他の PR の断片の改名で、このブランチが足した断片ではない（消えた個数分だけ外す）。
            # review-log-present.sh は名前の差で足した断片を数えるので、改名先にも review-log を求める（FAIL 側のずれ）。
            moved = Counter(blob for path, blob in base_blobs.items() if head_blobs.get(path) != blob)
            added_fragments, renamed = [], []
            for line in added.stdout.splitlines():
                if line not in collectable:
                    continue
                blob = head_blobs.get(line[len(prefix):])
                if moved[blob] > 0:
                    moved[blob] -= 1
                    renamed.append(line)
                    continue
                added_fragments.append(line)
            if added.returncode != 0:
                fail(f"cannot list files added since the merge-base with {ref}: {added.stderr.strip()}")
            elif not added_fragments:
                # 足されたかは、merge-base..HEAD の commit で足され、かつ作業ツリーで書式が正しい断片で数える。新しく書いたが commit していない断片を名指しする。
                pending = _uncommitted_new_fragments(git, base_blobs, [line[len(prefix):] for line in renamed])
                hint = f" The fragment is not committed yet: {', '.join(pending)}" if pending else ""
                if renamed:
                    hint += (
                        " Not counted (same content as a fragment at the merge-base, i.e. a rename of another "
                        f"PR's fragment): {', '.join(renamed)}"
                    )
                fail(
                    f"no changelog fragment added under changelog.d/ since this branch left {ref}. "
                    "Add changelog.d/<YYYYMMDD>-<slug>.md (CHANGELOG.md § Entry Template) and leave the "
                    f"version alone (docs/VERSIONING.md § 版数はリリースでだけ上げる).{hint}"
                )
            amended = amended_fragments(base_sha, added_fragments, base_blobs, head_blobs)
            lost = [path for path in find_lost_fragments(base_blobs, head_blobs) if path not in amended]
            if lost:
                fail(
                    f"changelog fragment(s) present at the merge-base with {ref} were deleted or rewritten "
                    f"on this branch: {', '.join(lost)}. A normal PR must not remove or modify another PR's "
                    "collected fragment (renaming is fine as long as the content is unchanged). To rewrite one "
                    "on purpose, declare it in the frontmatter of the review-log paired with the fragment this "
                    "branch adds (amends: <file name>, ...); deleting and renaming stay refused"
                )
            outcome = f"v{manifest_version} unchanged on this branch; {len(added_fragments)} fragment(s) added"
        elif head < tip:
            fail(f"version {manifest_version} is lower than the version on {ref} ({ref_version})")
        elif head == tip:
            fail(
                f"version {manifest_version} was changed on this branch but is already the version on {ref}. "
                f"A release must go above {ref_version}"
            )
        else:
            if fragments:
                fail(
                    f"version {manifest_version} is greater than {ref} ({ref_version}), so this is a release "
                    f"commit, but changelog.d/ still has {len(fragments)} fragment(s). Release with "
                    "scripts/release.py --apply; a normal PR must not bump the version"
                )
            ancestor = git("merge-base", "--is-ancestor", f"{ref}^{{commit}}", "HEAD")
            if ancestor.returncode not in (0, 1):
                fail(f"cannot determine whether {ref} is merged into HEAD: {ancestor.stderr.strip()}")
            elif ancestor.returncode != 0:
                fail(
                    f"this release branch does not include the latest {ref} ({ref} is not an ancestor of "
                    f"HEAD). Re-cut the release branch from the latest {ref} before releasing "
                    "(docs/VERSIONING.md § リリース手順)"
                )
            changelog_at_ref = git("show", f"{ref}:{prefix}CHANGELOG.md")
            if changelog_at_ref.returncode != 0:
                fail(f"cannot read CHANGELOG.md at {ref}: {changelog_at_ref.stderr.strip()}")
            elif re.search(rf"^### \[{re.escape(manifest_version)}\] - ", changelog_at_ref.stdout, re.M):
                fail(f"version {manifest_version} is already released on {ref} (its CHANGELOG has a heading for it)")
            outcome = f"release v{manifest_version} over {ref} v{ref_version}"

    if failures:
        die()
    print(f"{label}: OK ({outcome})")
    return "OK"


try:
    verdict_kind = run()
    if verdict_kind not in ("OK", "SKIP"):
        # 独立レビュー指摘（独立-8・low）: run() の戻り値そのものが未検証
        # だった（現状の全 return はこの2値のみなので実害は無いが、将来
        # 新しい return を足したときに宣言と無関係な文字列が VERDICT 行に
        # そのまま出力されうる）。ここで検査し、同じ try 節内で raise する
        # ことで、下の except BaseException による fail-closed に合流させる。
        raise AssertionError(f"run() returned an undeclared verdict: {verdict_kind!r}")
except SystemExit:
    # die() が明示的に投げる SystemExit(1) と、動的ロードしたモジュールへの
    # 呼び出し中に想定外に送出される SystemExit を区別しない。「run() が
    # 正常return しなかった」という事実だけを FAIL の根拠にし、SystemExit
    # の code 値は一切読まない（PR #93 の PR 後レビュー3巡目対応、PR後-3で
    # 再指摘。code を読んで code=0 だけを 1 に変換する実装は、
    # SystemExit(256) 等の 256 の倍数が POSIX のシェル終了コードマスク
    # （`exit_code & 0xFF`）でシェル rc=0 に落ちるため fail-open だった）。
    # PR #93 マージ直前に届いた指摘（product、origin: pre-existing）: fail-
    # closed 自体は保たれるが診断メッセージが無く、直接実行時になぜ失敗した
    # か分からない。SystemExit の code 属性は一切読まず（上記 fail-open の再発防止
    # を維持する）、固定文言だけを出す。die() が通常の入力検証失敗
    # （fail() 済みの後）で送出する SystemExit(1) と、動的ロードした
    # モジュールへの呼び出し中に想定外に送出される SystemExit を区別
    # しないため、文言は「run() が正常return しなかった」という事実だけを
    # 述べ、原因を「動的モジュールロード」と断定しない（Codex レビュー
    # 指摘・medium: die() 経由の通常失敗にまで誤った原因を付加していた）。
    print(f"FAIL: {label}: run() ended via SystemExit without returning a verdict")
    sys.exit(1)
except BaseException as error:  # noqa: BLE001 - 呼び出し中の想定外の例外を含めて拾い、fail-closed にする
    print(f"FAIL: {label}: unexpected exception during check: {error!r}")
    sys.exit(1)
else:
    print(f"VERDICT: {label}: {verdict_kind}")
    sys.exit(0)
PY
