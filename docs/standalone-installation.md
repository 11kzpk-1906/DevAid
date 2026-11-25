# Install DevAid from a standalone release

This guide explains how to download and run the prebuilt DevAid CLI without installing Python, uv, or the project dependencies.

## 1. Choose the correct download

Open the [official DevAid Releases page](https://github.com/11kzpk-1906/DevAid/releases) and choose the ZIP matching your operating system and CPU architecture.

| Platform | Asset | Supported architecture |
| --- | --- | --- |
| Windows | `devaid-windows-x64.zip` | x64 |
| Linux | `devaid-linux-x64.zip` | x64 |
| macOS | `devaid-macos-arm64.zip` | Apple Silicon (ARM64) |

These are the currently published standalone targets. There is no standalone archive for Windows ARM64, Linux ARM64, or Intel macOS. Do not choose an archive just because its operating system name matches; the CPU architecture must match too.

## 2. Verify the download

For releases that include `SHA256SUMS.txt`, download that file into the same folder as the ZIP archive. Verify the archive before extracting it.

**Windows PowerShell**

```powershell
Get-FileHash .\devaid-windows-x64.zip -Algorithm SHA256
```

Compare the printed hash with the `devaid-windows-x64.zip` entry in `SHA256SUMS.txt`.

**Linux**

```bash
sha256sum --check SHA256SUMS.txt
```

**macOS**

```bash
shasum -a 256 -c SHA256SUMS.txt
```

A matching checksum confirms that the archive matches the published checksum. It is not a security certification and does not independently prove who built the file.

## 3. Extract the ZIP

- **Windows:** In File Explorer, right-click the ZIP and select **Extract All**.
- **Linux:** Use your file manager or run `unzip devaid-linux-x64.zip`.
- **macOS:** Double-click the ZIP in Finder or use `unzip devaid-macos-arm64.zip`.

Open a terminal in the extracted folder. The executable should be named `devaid.exe` on Windows and `devaid` on Linux and macOS.

## 4. Run DevAid

Start with the help and version commands to confirm that the executable starts.

**Windows PowerShell**

```powershell
.\devaid.exe --help
.\devaid.exe version
.\devaid.exe doctor .
```

**Linux**

```bash
chmod +x ./devaid
./devaid --help
./devaid version
./devaid doctor .
```

**macOS (Apple Silicon)**

```bash
chmod +x ./devaid
./devaid --help
./devaid version
./devaid doctor .
```

The `doctor .` command inspects the current directory. To inspect another project, pass its path instead of `.`.

## 5. Optional: make DevAid available from any folder

You can keep running DevAid from its extracted directory using the commands above. If you want to call it from any terminal location, add the folder containing the executable to your user PATH. The exact steps depend on your shell and operating system; make sure you add the extracted folder, not the ZIP file.

## Troubleshooting

### PowerShell says the command is not recognized

Make sure the terminal is open in the extracted folder and use ` .\devaid.exe ` (without the surrounding spaces). You can check the current folder with `Get-Location` and list its contents with `Get-ChildItem`.

### Linux or macOS says permission is denied

Run `chmod +x ./devaid` in the extracted folder, then retry `./devaid --help`.

### The executable reports an incompatible architecture or will not start

Confirm that your CPU architecture matches the release asset. The published macOS build is for Apple Silicon (ARM64), not Intel Macs. The Windows and Linux builds are x64.

### macOS blocks the downloaded executable

Only download releases from the official DevAid repository. macOS security controls may warn about downloaded software. Do not bypass a warning unless you have verified the source and understand the implications.

### I need a platform that has no standalone binary

You may be able to run DevAid from source on another platform with Python 3.11 or newer. See the [source installation instructions](../README.md#install-and-run-from-source) and the [platform support matrix](platform-support.md). Source compatibility on unlisted combinations is not guaranteed.

## Related documentation

- [Platform support matrix](platform-support.md)
- [Security diagnostics](security.md)
- [DevAid README](../README.md)
