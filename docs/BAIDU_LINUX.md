# Downloading your Baidu Netdisk dataset to Linux

**Preferred for a desktop Linux machine:** Download the official Linux client from https://wangpan.baidu.com/download and install the official .deb/.rpm package appropriate for the distribution. Sign in using the GUI; download directly to an untracked folder.

**Headless Ubuntu server:** The community-maintained BaiduPCS-Go fork provides CLI downloads but is not an official Baidu client. Verify the release and trust boundary before using account credentials: https://github.com/qjfoidnh/BaiduPCS-Go/releases .

For Linux x86-64 the v4.0.2 archive is named `BaiduPCS-Go-v4.0.2-linux-amd64.zip`. After inspecting/reviewing the release, extract to a user-owned directory and check `BaiduPCS-Go -h`. Its documented commands are `login`, `ls`, `transfer`, `config set -savedir`, and `download`.

```bash
# Within an installed BaiduPCS-Go binary's directory:
./BaiduPCS-Go login                 # follow interactive prompts
./BaiduPCS-Go ls /
./BaiduPCS-Go config set -savedir /absolute/path/duet2score/data/raw
./BaiduPCS-Go download "/MyDataset" # your own cloud directory
```

If your data starts from a shared Baidu link, first use its documented `transfer URL CODE` to save it to your own cloud account and then download that cloud folder. Do not paste BDUSS, STOKEN, browser cookies, password or QR login tokens into issues, GitHub or chat. Running untrusted CLI on a multi-user server with account cookies carries risk.

**Safer alternative when a headless server cannot authenticate:** use the official client on your own Windows/Linux desktop, then `rsync -avhP /local/duet2score-dataset/ USER@HOST:/server/path/duet2score/data/raw/`. Data stays outside Git.

After downloading:
```bash
duet2score-inventory --root data/raw --out data/manifests/inventory.json --probe
```
