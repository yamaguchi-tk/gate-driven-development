#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

# 軽いレーンの指摘記録（review-log/）を強制する。`changelog.d/` に断片を足すのに
# 対応する `review-log/<同じファイル名>` が無い、または書式が不正なら FAIL。
# 正本: 書式は repo root の `review-log/README.md`、運用は root `CLAUDE.md` の軽いレーンの手順 6
#
# 対象は「このブランチが統合先との merge-base 以降に足した断片」だけ（release.py が
# 集める断片名パターンと同じ集合）。このチェック導入前から changelog.d/ にある断片は
# 対象外（遡及しない。導入時の限界として開示済み）。
#
# fail-closed と SKIP-B の使い分け:
#   統合先 ref が解決できない場合は FAIL にする（sibling の version-not-consumed.sh
#   の SKIP-B とは異なる判断）。本チェックには ref なしに「このブランチが新規に
#   足した断片」を特定する層が無く、ref が解決できないのに SKIP すると
#   「判定できないときに通ってしまう」fail-open になるため、fail-closed を優先する。
#
#   一方 repo root（`$ROOT/../..`）が本リポジトリの開発 checkout でない場合は
#   SKIP-B にする（2026-09-14、Codex レビューの指摘）。ONBOARDING.md の手順3
#   「Plugin の自己検証を走らせる」は plugin 配布先（消費者環境）でも
#   validate-plugin.sh の実行を明記しており、plugin cache 配置等では repo root
#   が本リポジトリでないことが実際にありうる。この場合に FAIL で die() すると、
#   review-log/ という本リポジトリ固有の開発運用チェックのせいで
#   validate-plugin.sh 全体（他の全 BLOCK チェック）まで誤 block してしまう
#   （実害）。
#
#   SKIP-B の判定は「本リポジトリの自己申告（identity marker）」だけで行う
#   （2026-09-15、Codex レビューで同じ型の指摘が続いた後、Opus へのセカンド
#   オピニオンで設計転換）。それまでの修正は、いずれも「消費者環境かどうか」を何らか
#   の派生信号から逆算する設計で、狭めるたびに別の変異で再発した:
#     - 1 つ目の案: `git rev-parse --is-inside-work-tree` の成否から逆算 → GIT_* 環境
#       変数の汚染、壊れた symlink で真の消費者環境と区別不能
#     - 2 つ目の案（壊れた symlink への対応）: ROOT が `<repo_root>/plugins/<ROOT の名前>` というディレクトリ
#       レイアウトと一致するかどうかから逆算 → ROOT が別名の symlink（例:
#       plugin cache のバージョン番号ディレクトリ）経由だと、真の開発 checkout
#       でも basename が一致せず SKIP-B になる fail-open（実機で再現）。
#       さらに逆方向にも壊れていた: 本物の消費者環境（別リポジトリを marketplace
#       clone したもの）が `<repo_root>/plugins/<name>` と同じレイアウトを偶然
#       満たし、「開発 checkout」と誤判定されて SKIP-B が発動しない事例が実機に
#       実在した（Opus のセカンドオピニオンで発見・実機検証）
#   git の失敗モードも、ディレクトリ名の偶然の一致も、どちらも「別の原因でも
#   同じ値になる」入力を含むため、狭めるたびに再発する。代わりに、リポジトリが
#   既に持っている固定の自己申告フィールド（`.claude-plugin/marketplace.json`
#   の `name`）を読むだけにする。本リポジトリなら値は `gate-driven-development`
#   で固定であり、他リポジトリの clone・別 plugin の marketplace ではこの値が
#   異なるか、そもそも manifest 自体が存在しない。推論をやめて宣言を読むことで、
#   それまでの案の入力空間（git 呼び出し・basename）のどれにも構造的に触れなくなる。
#   manifest が壊れていて `name` を読めない場合は、推測せず FAIL にする
#   （判定不能を「無い」と誤認しない）。この方式自体も、2 つ目の案の直後にさらに
#   再発を起こした: `name` キー欠落・null・非文字列・空文字列（`{}` 等）
#   が `.get("name") == MARKETPLACE_NAME` の等価比較を素通りして False（SKIP-B）
#   に落ちていた。`name` は marketplace の主キーであり、これを欠く manifest は
#   「別の marketplace の宣言」ではなくインストール不能な壊れた manifest である
#   ため、None（判定不能・FAIL）に倒す。ディレクトリ・壊れた symlink・symlink
#   loop（`is_file()` は False を返すが「宣言が無い」わけではない）も同様に
#   None にする。この再発はそれまでの案とは軸が異なる（消費者環境かどうかを派生信号から
#   逆算する開いた入力ではなく、`name` フィールドの JSON 型空間という列挙可能
#   な有限集合の中の未処理分岐）ため、identity marker への転換自体を覆す根拠
#   にはならない（Opus のセカンドオピニオンで確認）。
#
#   本チェックのスコープでは、`repository_identity()` の受理集合を「False は
#   manifest が存在しないか、妥当な manifest が別の名前を宣言している場合
#   だけ。その中間はすべて None」という1ルールに凍結していたが、その後、親
#   `.claude-plugin` 自体の異常でこの1ルールにも未処理分岐が見つかった。
#   個別ケースの列挙ではなく「False を返せるのは対象が本当に存在しないと
#   `FileNotFoundError` で確認できた場合だけ、それ以外の OSError は全て
#   None」という既定の反転で閉じた（詳細は `repository_identity()` の
#   docstring 参照）。以降 SKIP-B 判定述語そのものへの追加修正は行わない
#   （新しい指摘が出た場合も、判定ロジックの調整ではなくユーザーへ方針を
#   差し戻す）。原理的に閉じない残差として次の2点を受け入れる: (1) 「本
#   リポジトリ自体を marketplace として clone した消費者環境」は、開発
#   checkout とバイト単位で同一なためどんな内容マーカーでも区別できない。
#   (2) `name` の前後空白・大小文字違いは意図的に締めていない（`strip()`
#   した非空文字列であることだけを要求し、比較は厳密一致）。`.claude-plugin`
#   ディレクトリ自体が不在、または実在するが `marketplace.json` を持たない
#   場合（実機に複数実在する単体 plugin リポジトリのレイアウト）は、引き
#   続き意図的に SKIP-B のまま締めていない。限界として PR 本文に開示する。
#
#   PR #93 の PR 後レビュー（独立レビューに続いて同じクラスタで出た High）:
#   load_dynamic_module() は exec_module() 呼び出しの SystemExit だけを守り、
#   動的ロードしたモジュールへの「呼び出し」（repository_identity() 呼び出し、
#   release.NAME_RE.fullmatch() 呼び出し等）で SystemExit が送出されると、
#   fail()/die() に到達せず rc=0 で静かに成功していた（同型の fail-open が
#   呼び出し箇所ごとに再発する「開いた列挙」。independent-review.md (h) が
#   指摘する型）。Opus へのセカンドオピニオンで、個々の呼び出し箇所を
#   `except BaseException` で塞ぐ対処ではなく、「判定を宣言したか」を機械的に
#   検査する構造に倒す設計を採用した: 本体を run() 関数に集約し、run() が
#   正常return しなかった（SystemExit・その他の例外を含む）場合は無条件で
#   FAIL、正常return した場合だけ `VERDICT: review-log-present: OK|SKIP` を
#   出力する。呼び出し中の想定外の SystemExit(0) も、この方式では
#   「run() が正常return しなかった」に合流し、fail-closed になる。
#   validate-plugin.sh 側にも、rc=0 なのに VERDICT 行が無い check を一律で
#   FAIL にする番兵を追加した（全 BLOCK チェック共通、tests/validate-plugin.sh
#   参照）。

echo "BLOCK: review-log-present"
"$PYTHON_BIN" - "$ROOT" <<'PY'
import importlib.util
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

root = Path(sys.argv[1])
label = "review-log-present"
MARKETPLACE_NAME = "gate-driven-development"
failures: list[str] = []


def fail(message: str) -> None:
    failures.append(message)
    print(f"FAIL: {label}: {message}")


def die() -> None:
    print(f"FAIL: {label}")
    raise SystemExit(1)


def run() -> str:
    """本体。正常return した場合だけ呼び出し元が VERDICT 行を出す
    （戻り値は 'OK' か 'SKIP'）。die() の SystemExit(1)、および動的ロード
    したモジュールへの呼び出し中に想定外の例外（SystemExit を含む）が
    送出された場合は、正常return しない一点だけで「宣言なき成功」と区別
    する（呼び出し箇所を個別に except BaseException で塞ぐのではなく、
    正常return しなかった経路をすべて呼び出し元の except で一律 FAIL に
    合流させる。PR #93 の PR 後レビューで同じクラスタに出た High への対応）。"""

    # --- 入力 1: repo root（ROOT は plugin dir） ---
    repo_root = (root / ".." / "..").resolve()
    if not repo_root.is_dir():
        fail(f"cannot resolve repo root from ROOT/../.. ({repo_root})")
        die()

    def git(*args: str):
        # Codex レビュー指摘（high・fail-open、実測で再現）: 子プロセスに
        # GIT_DIR 等の GIT_* 環境変数がそのまま継承されると、呼び出し元の環境次第で
        # `git -C <repo_root>` の判定対象が repo_root とは別のリポジトリにすり替わる
        # （例: GIT_DIR=/nonexistent/x.git を付けると is-inside-work-tree が偽の
        # 成功/失敗を返す）。判定用の全 git 呼び出しから GIT_* を除去し、-C で
        # 明示した repo_root だけを見るようにする。
        env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        return subprocess.run(
            ["git", "-C", str(repo_root), *args],
            capture_output=True,
            text=True,
            errors="replace",
            check=False,
            env=env,
        )

    # 動的モジュールロード（importlib）専用のブートストラップ。独立レビュー
    # 指摘（high・実害あり、両方 self-inflicted）: `exec_module()`
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
    def load_dynamic_module(module_name: str, path: Path):
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

    # repository_identity() は sibling の version-not-consumed.sh と共有する
    # scripts/lib/repository_identity.py に一本化した（2026-09-16。一連の
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
        "gdd_repository_identity_for_review_log", root / "scripts" / "lib" / "repository_identity.py"
    )
    if identity_lib is None:
        fail(f"cannot load scripts/lib/repository_identity.py: {identity_load_error}")
        die()

    identity = identity_lib.repository_identity(repo_root, MARKETPLACE_NAME)
    if identity is None:
        fail(
            f"cannot parse {repo_root}/.claude-plugin/marketplace.json to confirm this is a checkout of "
            f"{MARKETPLACE_NAME}; refusing to guess"
        )
        die()
    if not identity:
        # 独立レビュー指摘（low）: sibling の version-not-consumed.sh
        # は SKIP 返却前に `if failures: die()` を通すが、ここには無かった
        # （現状は到達前の fail() がすべて直後に die() するため到達不能だが、
        # 対称性のため揃える）。
        if failures:
            die()
        print(
            f"{label}: SKIP-B: {repo_root} does not look like a checkout of {MARKETPLACE_NAME} "
            "(.claude-plugin/marketplace.json name mismatch or missing; plugin distributed via cache/marketplace?) "
            "— cannot determine which changelog.d/ fragments this branch added"
        )
        return "SKIP"

    # 本リポジトリの checkout であると確信できる以上、以後の git 呼び出しの失敗は
    # 理由を問わずすべて FAIL にする（symlink・環境変数汚染・壊れた gitdir 等、
    # どんな変異でも SKIP 側に倒れる余地を無くす）。
    inside_work_tree = git("rev-parse", "--is-inside-work-tree")
    if inside_work_tree.returncode != 0 or inside_work_tree.stdout.strip() != "true":
        fail(
            f"{repo_root} is a checkout of {MARKETPLACE_NAME} (.claude-plugin/marketplace.json name matches) "
            "but git rev-parse --is-inside-work-tree did not confirm it "
            f"(rc={inside_work_tree.returncode}, stdout={inside_work_tree.stdout.strip()!r}, "
            f"stderr={inside_work_tree.stderr.strip()!r}); refusing to guess"
        )
        die()

    # --- 入力 2: release.py（changelog.d/ 断片名パターンの正本） ---
    release, release_load_error = load_dynamic_module("gdd_release_for_review_log", root / "scripts" / "release.py")
    if release is None:
        fail(f"cannot load scripts/release.py to parse changelog.d/: {release_load_error}")

    # --- 入力 3: 統合先の定義（version-not-consumed.sh と同じ正本） ---
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
    ref = integration_ref or declared_ref
    if not ref:
        fail("no integration ref declared (docs/VERSIONING.md § 統合先の定義 missing and GDD_INTEGRATION_REF unset)")

    if failures or release is None:
        die()

    if git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").returncode != 0:
        fail(f"ref '{ref}' is not resolvable locally (fetch it, or set GDD_INTEGRATION_REF)")
        die()

    merge_base = git("merge-base", f"{ref}^{{commit}}", "HEAD")
    if merge_base.returncode != 0:
        fail(f"cannot find the merge-base of {ref} and HEAD: {merge_base.stderr.strip()}")
        die()
    base_sha = merge_base.stdout.strip()

    try:
        plugin_prefix = root.resolve().relative_to(repo_root).as_posix()
    except ValueError as error:
        fail(f"cannot resolve ROOT ({root}) relative to repo root ({repo_root}): {error}")
        die()

    changelog_dir = f"{plugin_prefix}/changelog.d" if plugin_prefix else "changelog.d"

    # merge-base 時点の断片名集合（committed tree のみを見る。この時点ではまだ
    # 「このブランチが足した断片」ではないため working tree の状態は無関係）。
    base_tree = git("ls-tree", "--name-only", f"{base_sha}:{changelog_dir}")
    base_names = set()
    if base_tree.returncode == 0:
        for line in base_tree.stdout.splitlines():
            name = line.strip()
            if name and release.NAME_RE.fullmatch(name):
                base_names.add(name)

    # 現在の断片名集合は working tree を直接見る（HEAD や git diff ではなく）。
    # 「変更 → validate-plugin.sh で検証 → コミット」という通常の運用では、この
    # チェックはコミット前に走るため、merge-base..HEAD の git diff だけでは
    # 未コミット・staged の新規断片を検出できない（実測で再現、Codex 指摘）。
    # release.py の load_fragments はパース失敗時にその断片を黙って除外する
    # （fail-open の懸念）ため使わず、load_fragments と同じ受理集合（ディレクトリ
    # 直下・NAME_RE 一致）だけをファイル名で判定する。
    current_names = set()
    changelog_path = repo_root / changelog_dir
    if changelog_path.is_dir():
        for entry in changelog_path.iterdir():
            if entry.is_file() and release.NAME_RE.fullmatch(entry.name):
                current_names.add(entry.name)

    added_names = sorted(current_names - base_names)

    if not added_names:
        print(f"{label}: OK (no changelog fragment added since the merge-base with {ref})")
        return "OK"

    # --- 断片ごとに対の review-log/<name> を検査する ---
    JUN_HEADER = ("巡", "reviewer", "sha", "high", "medium", "blocking", "at")
    FINDING_HEADER = ("id", "巡", "severity", "実害", "自己起因", "クラスタ", "対応", "要約")
    SEVERITY_VALUES = {"high", "medium", "low", "advisory"}
    JITSUGAI_VALUES = {"yes", "no"}
    JIKOKIIN_VALUES = {"self-inflicted", "inherited"}
    # root CLAUDE.md 手順 6 の、この PR で直さない指摘の値。行は残し、`## 巡` の
    # high・medium には数えない: `re-reported`（既に Issue・accepted・次の PR に回した
    # 指摘の再報告）、`next-pr`（② 話題だけ関連。次の PR で直す）、`out-of-diff`（③ 差分の
    # 外で実データに該当なし）。振り分けは main が行い、この検査は確かめない（自己申告。
    # 限界として changelog に開示）。ただし 実害=yes の行には付けられない。`deferred`・`accepted` は今までどおり数える。
    UNCOUNTED_TAIOU_VALUES = {"re-reported", "next-pr", "out-of-diff"}
    TAIOU_VALUES = {"fixed", "deferred", "accepted"} | UNCOUNTED_TAIOU_VALUES
    FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
    SEPARATOR_RE = re.compile(r"\|?[\s:|-]+\|?")
    NON_NEGATIVE_INT_RE = re.compile(r"[0-9]+")
    # review-log の書式の正本が定める巡ラベルの値域（`方針メモ` / `codex-N` / `独立-N` / `PR後-N`）。
    # `方針メモ-N` は、root CLAUDE.md L1+ 安全策1 に基づく差し戻し後の再方針メモを
    # 記録できるよう追加で許可する（2026-09-16、Opus へのセカンドオピニオンに基づく
    # 安全策4 の機械化に合わせた拡張）。`方針メモ` 単独の重複禁止はそのまま維持し、
    # `方針メモ-1`・`方針メモ-2` は別ラベルとして複数回使える。
    POLICY_MEMO_JUN_RE = re.compile(r"^方針メモ(?:-[0-9]+)?$")
    JUN_LABEL_RE = re.compile(r"^(?:方針メモ(?:-[0-9]+)?|codex-[0-9]+|独立-[0-9]+|PR後-[0-9]+)$")

    def split_row(line: str) -> list[str]:
        return [cell.strip() for cell in line.strip().strip("|").split("|")]

    def parse_frontmatter(name: str, text: str):
        matched = FRONTMATTER_RE.match(text)
        if not matched:
            fail(f"review-log/{name}: must start with the frontmatter '---' / 'key: value' lines / '---'")
            return None
        fields: dict[str, str] = {}
        for line in matched.group(1).splitlines():
            if not line.strip():
                continue
            key, sep, value = line.partition(":")
            if not sep:
                fail(f"review-log/{name}: frontmatter line is not 'key: value': {line!r}")
                continue
            fields[key.strip()] = value.strip()
        return fields, matched.end()

    ALLOWED_HEADINGS = ("## 巡", "## 指摘")

    def split_sections(name: str, body: str):
        """review-log の body を「空行 / `## 巡` / `## 指摘` の見出しと、その配下の
        行」だけのホワイトリストで走査する。この2つ以外の見出し・説明文・コード
        フェンス等、どんな形であれ検査対象外の領域を作れないようにする。

        Codex レビュー指摘（high・fail-open、実測で再現、fence-parsing/隠し
        領域クラスタの再発）: 直前の修正（見出しから次の `## ` 見出しまたは
        EOF までを検査範囲にする）は、`## 巡` の正しい表の直後に `## メモ` のような
        未知の見出しを置けば、その下が無条件で検査範囲の外になった。Opus への
        セカンドオピニオンで、必要なのは終端判定の精度を上げることではなく、body が
        受理する文法そのものを『空行・`## 巡` 表・`## 指摘` 表』の3種類だけに狭める
        ことだと判断した（done-guard・#83 と同じ『開いた入力』クラスの例。
        軸は『パーサーを良くする』ではなく『受理する文法を狭める』）。この設計では
        `## 巡`/`## 指摘` 以外の見出しはただの非空行として扱われ、後続の
        parse_table_rows がテーブル外の行として機械的に FAIL にするため、フェンスの
        内外を見分けるロジック自体が不要になった。
        """
        sections: dict[str, list[str]] = {}
        current: str | None = None
        for line in body.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped in ALLOWED_HEADINGS:
                if stripped in sections:
                    fail(f"review-log/{name}: '{stripped}' appears more than once")
                    return None
                sections[stripped] = []
                current = stripped
                continue
            if current is None:
                fail(
                    f"review-log/{name}: review-log body must contain only blank lines and the "
                    f"'## 巡'/'## 指摘' sections; found content before any of them: {stripped!r}"
                )
                return None
            sections[current].append(line)
        missing = [heading for heading in ALLOWED_HEADINGS if heading not in sections]
        if missing:
            fail(f"review-log/{name}: missing required section(s) {missing}")
            return None
        return sections

    def parse_table_rows(name: str, heading: str, lines: list[str], expected_header: tuple[str, ...]):
        if not lines:
            fail(f"review-log/{name}: '{heading}' has no table")
            return None
        header_cells = split_row(lines[0])
        if header_cells != list(expected_header):
            fail(
                f"review-log/{name}: '{heading}' table header must be "
                f"{' | '.join(expected_header)} (got {' | '.join(header_cells)})"
            )
            return None
        if len(lines) < 2 or not SEPARATOR_RE.fullmatch(lines[1].strip()):
            fail(f"review-log/{name}: '{heading}' table is missing the separator row")
            return None
        rows = []
        for line in lines[2:]:
            stripped = line.strip()
            if not stripped.startswith("|"):
                fail(
                    f"review-log/{name}: '{heading}' section has a non-table line "
                    f"(hidden data?): {stripped!r}"
                )
                continue
            cells = split_row(line)
            if len(cells) != len(expected_header):
                fail(
                    f"review-log/{name}: '{heading}' table row has {len(cells)} column(s), "
                    f"expected {len(expected_header)}: {stripped!r}"
                )
            else:
                rows.append(cells)
        if not rows:
            fail(f"review-log/{name}: '{heading}' table has no data row")
            return None
        return rows

    def validate_format(name: str, text: str) -> None:
        parsed = parse_frontmatter(name, text)
        if parsed is None:
            return
        fields, body_start = parsed
        if fields.get("lane") not in ("L1", "L1+"):
            fail(f"review-log/{name}: frontmatter 'lane' must be L1 or L1+ (got {fields.get('lane')!r})")
        if "pr" not in fields:
            fail(f"review-log/{name}: frontmatter is missing the 'pr' key (value may be empty until the PR exists)")

        body = text[body_start:]
        sections = split_sections(name, body)
        if sections is None:
            return
        jun_rows = parse_table_rows(name, "## 巡", sections["## 巡"], JUN_HEADER)
        finding_rows = parse_table_rows(name, "## 指摘", sections["## 指摘"], FINDING_HEADER)
        if jun_rows is None or finding_rows is None:
            return

        jun_label_counts = Counter(row[0] for row in jun_rows)
        duplicated_jun = sorted(label for label, count in jun_label_counts.items() if count > 1)
        if duplicated_jun:
            fail(f"review-log/{name}: '## 巡' has duplicated 巡 label(s) {duplicated_jun}")

        for row in jun_rows:
            jun_label, reviewer, sha, high, medium, blocking, at = row
            # Codex レビュー指摘（P2）: 巡ラベルが任意文字列を受理しており、書式の正本が
            # 定める値域（方針メモ / codex-N / 独立-N / PR後-N）外のラベルが通っていた。
            if not JUN_LABEL_RE.fullmatch(jun_label):
                fail(
                    f"review-log/{name}: '## 巡' has an invalid 巡 label {jun_label!r} "
                    "(must be 方針メモ/方針メモ-N / codex-N / 独立-N / PR後-N)"
                )
            # Codex レビュー指摘（P1・再レビュー）: reviewer/sha/at が空でも
            # 通っていた。これらが欠けるとレビュー元・対象差分・時系列を分析できず
            # review-log の記録として成立しない。sha='-' は「まだコミットが無い」ことを
            # 表す方針メモ巡（差し戻し後の再方針メモ `方針メモ-N` を含む）だけの
            # 例外として、正本に合わせて明示的に許可する。
            if not reviewer:
                fail(f"review-log/{name}: '## 巡' row {jun_label!r} has an empty reviewer")
            if not sha:
                fail(f"review-log/{name}: '## 巡' row {jun_label!r} has an empty sha")
            elif sha == "-" and not POLICY_MEMO_JUN_RE.fullmatch(jun_label):
                fail(
                    f"review-log/{name}: '## 巡' row {jun_label!r} has sha='-' "
                    "(only 方針メモ/方針メモ-N may omit sha with '-', since it precedes any commit)"
                )
            if not at:
                fail(f"review-log/{name}: '## 巡' row {jun_label!r} has an empty at")
            for column_name, value in (("high", high), ("medium", medium), ("blocking", blocking)):
                if not NON_NEGATIVE_INT_RE.fullmatch(value):
                    fail(
                        f"review-log/{name}: '## 巡' row {jun_label!r} has a non-numeric "
                        f"{column_name} value {value!r} (must be a non-negative integer)"
                    )

        jun_labels = set(jun_label_counts)
        finding_jun_labels = {row[1] for row in finding_rows}
        missing = jun_labels - finding_jun_labels
        if missing:
            fail(
                f"review-log/{name}: 巡 {sorted(missing)} has no row in '## 指摘' "
                "(0 件でも 要約=なし の行を1本置く。未記録と0件を区別する)"
            )
        extra = finding_jun_labels - jun_labels
        if extra:
            fail(f"review-log/{name}: '## 指摘' references undeclared 巡 {sorted(extra)} (not present in '## 巡')")

        seen_ids: set[str] = set()
        severity_counts_by_jun: dict[str, Counter[str]] = {}
        real_finding_jun_labels: set[str] = set()
        invalid_severity_jun_labels: set[str] = set()
        nashi_counts_by_jun: Counter[str] = Counter()
        for row in finding_rows:
            finding_id, jun, severity, jitsugai, jikokiin, cluster, taiou, summary = row
            if not finding_id:
                fail(f"review-log/{name}: '## 指摘' has a row with an empty id")
            elif finding_id in seen_ids:
                fail(f"review-log/{name}: '## 指摘' id '{finding_id}' is duplicated")
            else:
                seen_ids.add(finding_id)
            if not summary:
                # Codex レビュー指摘（P1・再レビュー）: 要約が空でも通っていた。
                # 要約が無いと指摘内容を分析できない。0件は明示的に「なし」と書く
                # 既存規律（未記録と0件の区別）と同じ理由で、空文字列は許可しない。
                fail(f"review-log/{name}: '## 指摘' id '{finding_id}' has an empty 要約")
            if summary == "なし":
                # 0件の巡を表す「なし」行は、分類列をすべて '-' にする（実在する指摘が
                # 無いので分類しようがない）。
                if any(value != "-" for value in (severity, jitsugai, jikokiin, taiou)):
                    fail(f"review-log/{name}: '## 指摘' id '{finding_id}' has 要約=なし but other columns are not all '-'")
                nashi_counts_by_jun[jun] += 1
            else:
                real_finding_jun_labels.add(jun)
                # Codex レビュー指摘（P2）: 値域に '-' を無条件で含めていたため、要約が
                # 「なし」ではない実在する指摘行でも分類列をすべて '-' にできた。
                # 「なし」行以外は固定語彙を必須にし、'-' を許可しない。
                if severity not in SEVERITY_VALUES:
                    fail(f"review-log/{name}: '## 指摘' id '{finding_id}' has an invalid severity {severity!r} (allowed: {', '.join(sorted(SEVERITY_VALUES))})")
                    invalid_severity_jun_labels.add(jun)
                elif taiou not in UNCOUNTED_TAIOU_VALUES:
                    severity_counts_by_jun.setdefault(jun, Counter())[severity] += 1
                if jitsugai not in JITSUGAI_VALUES:
                    fail(f"review-log/{name}: '## 指摘' id '{finding_id}' has an invalid 実害 {jitsugai!r} (allowed: {', '.join(sorted(JITSUGAI_VALUES))})")
                elif jitsugai == "yes" and taiou in UNCOUNTED_TAIOU_VALUES:
                    # 実害クラスは再掲・次の PR・差分の外にできない（root CLAUDE.md 手順 6）。
                    # 付けると巡の high から外れ、安全策 4 の数え方も素通りする
                    fail(f"review-log/{name}: '## 指摘' id '{finding_id}' has 実害=yes but 対応 {taiou!r} leaves it out of the count")
                if jikokiin not in JIKOKIIN_VALUES:
                    fail(f"review-log/{name}: '## 指摘' id '{finding_id}' has an invalid 自己起因 {jikokiin!r} (allowed: {', '.join(sorted(JIKOKIIN_VALUES))})")
                if taiou not in TAIOU_VALUES:
                    fail(f"review-log/{name}: '## 指摘' id '{finding_id}' has an invalid 対応 {taiou!r} (allowed: {', '.join(sorted(TAIOU_VALUES))})")
                # Codex レビュー指摘（P1・再レビュー）: クラスタが空でも通って
                # いた。同一根本原因のクラスタ化が
                # できなくなるため、実指摘行では必須にする（「なし」行は '-' のまま）。
                if not cluster:
                    fail(f"review-log/{name}: '## 指摘' id '{finding_id}' has an empty クラスタ")
                elif cluster == "-":
                    # 独立レビュー指摘（2026-09-16）: severity/実害/自己起因/
                    # 対応の4列は「なし」行以外で '-' を明示的に拒否している（P2 の
                    # ノイズ防止のため）のに、クラスタ列だけ '-' を素通りさせていた。
                    # クラスタは同一根本原因の指摘をまとめる分類ラベルであり、
                    # プレースホルダーの '-' では分類にならないため拒否する。
                    #
                    # 独立レビュー指摘（medium）: 他4列は固定語彙の
                    # ホワイトリスト（`*_VALUES`）で検査しているのに対し、この分岐は
                    # プレースホルダー '-' だけを拒否するブラックリスト判定であり、
                    # 受理集合は他4列と揃っていない（`n/a`・`--`・空白等は依然通る）。
                    # クラスタ名は自由記述の分類ラベルであり列挙値ではないため、
                    # ホワイトリスト化は本PRのスコープ外とし、既知のプレースホルダー
                    # '-' のみを拒否する限界として開示する（他の変異は後続課題）。
                    fail(f"review-log/{name}: '## 指摘' id '{finding_id}' has a クラスタ of '-' (use a real cluster label)")

        # Codex レビュー指摘（P2・再レビュー）: 同じ巡に実指摘行と「なし」行が
        # 両方あっても検出されなかった。「なし」は0件を示す排他的なプレースホルダー
        # なので、実指摘がある巡に「なし」行が混在していたら FAIL にする。また
        # 0件の巡（なし行のみ）で「なし」行が複数本あると集計が曖昧になるため、
        # ちょうど1本であることも要求する。
        mixed_jun_labels = sorted(real_finding_jun_labels & set(nashi_counts_by_jun))
        if mixed_jun_labels:
            fail(
                f"review-log/{name}: 巡 {mixed_jun_labels} has both a real finding row and a "
                "要約=なし row ('なし' is an exclusive placeholder for 0 findings)"
            )
        for jun_label, count in sorted(nashi_counts_by_jun.items()):
            if jun_label not in real_finding_jun_labels and count > 1:
                fail(f"review-log/{name}: 巡 {jun_label!r} has {count} 要約=なし rows (must be exactly 1)")

        # Codex レビュー指摘（P1・実害あり）: 巡の high/medium/blocking 件数が指摘表の
        # 実際の内容と無関係に自己申告できた（例: high=99 なのに指摘行は1件だけでも
        # 通る、high=1 なのに「なし」行だけでも通る）。「なし」行のみの巡は 0 件のはず
        # なので high/medium/blocking をすべて 0 に限定し、実在する指摘がある巡は
        # high/medium 件数を対応する severity の指摘行数と照合する。blocking は
        # severity の値域に存在せず指摘表から導出できないため対応関係を検証できない
        # （書式の正本にも blocking 専用の列は定義されていない。非負整数であることの
        # 検証に留める。この限界は changelog に開示済み）。severity 自体が無効な行を
        # 含む巡は、その無効値エラーを別途 fail 済みなので件数照合はスキップする
        # （無効値による見せかけの件数不一致でノイズを増やさない）。
        for row in jun_rows:
            jun_label, _reviewer, _sha, high, medium, blocking, _at = row
            if jun_label in invalid_severity_jun_labels:
                continue
            if jun_label not in real_finding_jun_labels:
                if (high, medium, blocking) != ("0", "0", "0"):
                    fail(
                        f"review-log/{name}: '## 巡' row {jun_label!r} has no real finding row "
                        f"(only 要約=なし) in '## 指摘' but declares high/medium/blocking = "
                        f"{high}/{medium}/{blocking} (must be 0/0/0)"
                    )
                continue
            counts = severity_counts_by_jun.get(jun_label, Counter())
            expected_high = str(counts.get("high", 0))
            if high != expected_high:
                fail(
                    f"review-log/{name}: '## 巡' row {jun_label!r} declares high={high} but "
                    f"'## 指摘' has {expected_high} high row(s) for this 巡"
                )
            expected_medium = str(counts.get("medium", 0))
            if medium != expected_medium:
                fail(
                    f"review-log/{name}: '## 巡' row {jun_label!r} declares medium={medium} but "
                    f"'## 指摘' has {expected_medium} medium row(s) for this 巡"
                )

        # root CLAUDE.md L1+ 安全策4「同じ種類（クラスタ）の high・blocking が
        # 2回続いたら、修正を続けずにユーザーへ線引きを戻す」の機械化を
        # 2026-09-16 に試みたが、独立レビューの巡ごとに
        # high 指摘が続き、そのたびに検知ロジック自身の受理集合・状態遷移
        # （クラスタ名の自由文字列照合、方針メモによる保留・クリア・再登録の
        # 順序関係）に新しい穴が見つかった。クラスタ名は検査対象である当人が
        # 自由文で書く自己申告値であり、個別の異常値（空文字・'-'・大小文字
        # 違い等）を塞ぐ都度、別の変異（表記を変える・別ラベルを使う等）で
        # 回避できてしまう構造だった。Opus（claude-opus-5）へのセカンド
        # オピニオンで「この受理集合は原理的に閉じない。block 化の代償
        # （保留・クリア・再登録の複雑な状態機械）がそれらの指摘の火種
        # そのもので、回避が自明な検査に block の強度を持たせても得るものが
        # ない」との判断を受け、ユーザー承認のもとこの安全策4の機械化を撤回
        # した。安全策4自体は root CLAUDE.md の
        # 散文の規定のまま残り、機械化は後続課題とする。

    for name in added_names:
        # review-log も working tree から直接読む（git show HEAD: ではなく）。
        # 断片自身と同じ理由で、未コミットの review-log を検出する必要がある。
        review_log_path = repo_root / "review-log" / name
        if not review_log_path.is_file():
            fail(
                f"review-log/{name} is missing for changelog.d/{name} (added since the merge-base with {ref}). "
                "Create it in the format described in review-log/README.md"
            )
            continue
        try:
            content = review_log_path.read_text(encoding="utf-8")
        except Exception as error:  # noqa: BLE001
            fail(f"cannot read review-log/{name}: {error}")
            continue
        validate_format(name, content)

    if failures:
        die()
    print(f"{label}: OK ({len(added_names)} fragment(s) checked)")
    return "OK"


try:
    verdict_kind = run()
    if verdict_kind not in ("OK", "SKIP"):
        # 独立レビュー指摘（low）: run() の戻り値そのものが未検証
        # だった（現状の全 return はこの2値のみなので実害は無いが、将来
        # 新しい return を足したときに宣言と無関係な文字列が VERDICT 行に
        # そのまま出力されうる）。ここで検査し、同じ try 節内で raise する
        # ことで、下の except BaseException による fail-closed に合流させる。
        raise AssertionError(f"run() returned an undeclared verdict: {verdict_kind!r}")
except SystemExit:
    # die() が明示的に投げる SystemExit(1) と、動的ロードしたモジュールへの
    # 呼び出し中に想定外に送出される SystemExit を区別しない。「run() が
    # 正常return しなかった」という事実だけを FAIL の根拠にし、SystemExit
    # の code 値は一切読まない（PR #93 の PR 後レビューへの対応で、同じ点を
    # 再指摘された。code を読んで code=0 だけを 1 に変換する実装は、
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
