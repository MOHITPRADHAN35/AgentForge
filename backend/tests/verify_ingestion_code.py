import requests

BASE_URL = "http://127.0.0.1:8000"

def test_ingest_and_verify_right_side_code():
    print("\n[Step 1] Ingesting New GitHub Repo (https://github.com/tartley/colorama.git)...")
    resp = requests.post(
        f"{BASE_URL}/api/projects",
        data={
            "name": "colorama-live-test",
            "repo_type": "git",
            "git_url": "https://github.com/tartley/colorama.git"
        }
    )
    assert resp.status_code == 200, f"Failed to ingest: {resp.text}"
    project = resp.json()
    project_id = project["id"]
    print(f"-> Ingested project ID: {project_id}")
    print(f"-> Manifest file count: {project['manifest']['file_count']}")
    assert project["name"] == "colorama-live-test"

    print("\n[Step 2] Fetching file tree for the newly ingested repo...")
    files_resp = requests.get(f"{BASE_URL}/api/projects/{project_id}/files")
    assert files_resp.status_code == 200
    files = files_resp.json()["files"]
    print(f"-> Returned {len(files)} files in repo tree.")
    assert "colorama/ansi.py" in files

    print("\n[Step 3] Fetching newly ingested file content (right-side editor data)...")
    file_resp = requests.get(f"{BASE_URL}/api/projects/{project_id}/file", params={"path": "colorama/ansi.py"})
    assert file_resp.status_code == 200
    file_data = file_resp.json()
    content = file_data["content"]
    lines = content.splitlines()

    print(f"-> File path: {file_data['path']}")
    print(f"-> Line count: {len(lines)}")
    print("-> First 5 lines of code loaded into the right side editor:")
    for i, line in enumerate(lines[:5], 1):
        print(f"   Line {i}: {line}")

    print("\n[Step 4] Confirming newly ingested code replaces old demo code...")
    # It must contain colorama specific symbols
    assert "AnsiCodes" in content
    assert "code_to_chars" in content
    # It must NOT be the old buggy-commerce code
    assert "calculate_discount" not in content
    assert "PaymentProcessor" not in content
    print("-> VERIFIED: Right-side code is 100% the newly ingested repository's code!")

if __name__ == "__main__":
    test_ingest_and_verify_right_side_code()
