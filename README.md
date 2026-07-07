### <img src="logo_transparent.png" width="35" align="center" alt="MaMoW Icon" />  MaMoW

MaMoW is a CLI tool designed to parse Markdown test cases into structured Excel files. This utility streamlines the process for QA engineers to convert human-readable test case specifications into standardized spreadsheet formats.

## 📋 Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Python 3.9+** (Check with `python3 --version` or `python --version`)
- **Git** (Check with `git --version`)
- **pip** (Python package installer)

## 🚀 Getting Started

### 1. Clone the Repository

Clone the project from the very beginning using the following command:

```bash
git clone https://github.com/hanifrazin/MaMoW.git
cd MaMoW
```

### 2. Install the CLI Command

MaMoW provides two ways to run the tool:

| Method | Command | Best for |
|--------|---------|---------|
| **Global CLI** (recommended) | `mamow -i <input>` | After installation, use from anywhere |
| **Direct Python** | `python src/main.py -i <input>` | Quick testing, no install needed |

The installation scripts below make the `mamow` command available globally. They handle everything — including virtual environment creation and dependency installation — automatically on the first run.

---

#### 🍎 macOS & 🐧 Linux

**Option A — Quick Install (Recommended):**

Run the installation script from the project root. This copies a launcher into `/usr/local/bin`:

```bash
chmod +x src/executable_scripts/install.sh
./src/executable_scripts/install.sh
```

**Option B — Manual PATH Setup (no sudo needed):**

If you don't have sudo access, add the scripts folder to your shell profile instead:

```bash
echo 'export PATH="$PATH:'"$(pwd)"'/src/executable_scripts"' >> ~/.zshrc
source ~/.zshrc
```

> **How it works:** The `mamow` bash script resolves its real path, creates a `.venv` virtual environment with all dependencies on first run, then executes `src/main.py` with your arguments.

---

#### 🪟 Windows

Run the installation batch script in **Command Prompt** (or PowerShell). This adds the `src\executable_scripts` folder to your user `PATH`:

```cmd
.\src\executable_scripts\install.bat
```

After installation, **restart your terminal** for the PATH changes to take effect.

> **How it works:** The `mamow.bat` script creates a `.venv` and installs dependencies on first run. It also attempts to build a standalone `mamow.exe` via PyInstaller for faster subsequent launches. If PyInstaller is not available, it falls back gracefully to running via Python.

---

> **💡 First-run behavior:** When you run `mamow` for the first time (on any platform), it will automatically:
> 1. Create a Python virtual environment (`.venv/`) in the project root
> 2. Install all required dependencies (`pydantic`, `openpyxl`, `rich`)
> 3. Execute your command — no manual `pip install` needed

## 📖 How to Use

The MaMoW CLI provides a straightforward way to process Markdown files. You can run the CLI natively using the `mamow` command, or via the Python entry script `src/main.py`.

**Using the `mamow` executable (Recommended):**

```bash
mamow -i <input_path> [-o <output_path>] [-c <config_path>] [--merge | --single]
```

**Using Python:**

```bash
python src/main.py -i <input_path> [-o <output_path>] [-c <config_path>] [--merge | --single]
```

### Arguments:

| Option | Description | Default |
|--------|-------------|---------|
| `-i`, `--input` **(Required)** | Path to input Markdown file (`.md`) or a directory containing `.md` files | — |
| `-o`, `--output` | Path to output Excel file (`.xlsx`) or directory | Value from `config.json` |
| `-c`, `--config` | Path to configuration file | `config.json` |
| `--merge` | Merge **all** `.md` files in a directory into a **single** `.xlsx` file | off |
| `--single` | Export **each** `.md` file in a directory to **separate** `.xlsx` files | off |
| `-h`, `--help` | Show help message with all options and examples | — |

### Processing Modes

When the input is a **directory**, MaMoW supports three modes:

| Mode | Flag | Behavior |
|------|------|----------|
| **Batch** *(default)* | *(no flag)* | Processes each `.md` file individually → separate `.xlsx` files |
| **Merge** | `--merge` | Combines all `.md` files into one `.xlsx` file |
| **Single** | `--single` | Exports each `.md` file to its own `.xlsx` file with conflict-safe naming |

> **Note:** `--merge` and `--single` cannot be used together. If the input is a single file, both flags are ignored.

### Output Naming Convention

When the output path is a **directory**, MaMoW auto-generates filenames as follows:

| Mode | Output Filename Pattern | Example |
|------|------------------------|---------|
| **Single file** | `{filename}.xlsx` | `login.xlsx` |
| **Batch** *(directory)* | `{filename}.xlsx` per file | `login.xlsx`, `register.xlsx` |
| **Merge** *(directory)* | `{input_folder}_merge.xlsx` | `data_merge.xlsx` |
| **Single** *(directory)* | `{filename}_single.xlsx` (appends `_1`, `_2`, … on conflict) | `login_single.xlsx` |

### Auto-created Result Subfolder

When the input is a **directory**, MaMoW automatically creates a `result_<input_folder_name>` subfolder inside the output directory to keep your exports organized. For example:

```bash
mamow -i samples/data/ -o samples/output/ --merge
```
→ Exports to `samples/output/result_data/data_merge.xlsx`

This prevents output clutter and keeps results from different input directories separated.

### Examples:

**1. Process a single Markdown file:**

```bash
mamow -i samples/data/login.md -o samples/output/login.xlsx
```

**2. Batch process all files in a directory (default mode):**

```bash
mamow -i samples/data/ -o samples/output/
```
→ Each `.md` file becomes its own `.xlsx` inside `samples/output/result_data/`

**3. Merge all files in a directory into a single Excel workbook:**

```bash
mamow -i samples/data/ -o samples/output/data.xlsx --merge
```
→ All test cases combined into `samples/output/result_data/data_merge.xlsx`

**4. Export each file separately using `--single` mode:**

```bash
mamow -i samples/data/ -o samples/output/ --single
```
→ Each `.md` → separate .xlsx (e.g., `login_single.xlsx`, `login-2_single.xlsx`) inside `samples/output/result_data/`

**5. Run using fallback default paths (as defined in `config.json`):**

```bash
mamow -i login.md
```
→ Looks for `samples/input/login.md` and outputs to `samples/output/`

**6. View the help menu:**

```bash
mamow -h
```

## 🛠 Troubleshooting

Here are some common issues you might encounter and how to fix them:

### 1. "Command not found: python3" or "python3 is not recognized"

- **Solution:** Ensure Python is added to your system's PATH during installation. On Windows, you might need to use `python` instead of `python3`.

### 2. Virtual environment activation fails (`source venv/bin/activate`)

- **Solution (macOS/Linux):** Ensure you created the venv with the exact name `venv`. Check your current directory is the project root.
- **Solution (Windows):** If you receive a script execution policy error in PowerShell, run `Set-ExecutionPolicy Unrestricted -Scope CurrentUser` as an Administrator, or use Command Prompt to run `venv\Scripts\activate.bat`.

### 3. `ModuleNotFoundError: No module named 'pydantic'` (or openpyxl)

- **Solution:** This means the dependencies are not installed or your virtual environment is not active. Make sure you activate the virtual environment (`source venv/bin/activate`) and run `pip install -r requirements.txt` again.

### 4. `Error: Input path '...' does not exist` when running the CLI

- **Solution:** Verify the path to your Markdown file is correct relative to your current terminal working directory. You can also provide an absolute path to the file.

### 5. `mamow` command not found or does not execute

If you try to run `mamow` and get an error, ensure you have run the installation script first (`install.sh` for Mac/Linux, `install.bat` for Windows). If issues persist, follow these manual fixes:

**🍎 macOS & 🐧 Linux:**

* **Issue A: Permission Denied**
  The scripts need execution permissions.
  **Fix:** Run the following command from the project root:

  ```bash
  chmod +x src/executable_scripts/mamow
  chmod +x src/executable_scripts/install.sh
  ```
* **Issue B: Command not found (`mamow: command not found`)**
  The `install.sh` might have failed to write to `/usr/local/bin` due to permission issues or restricted environments.
  **Fix 1 (Manual Symlink):**

  ```bash
  sudo ln -s "$(pwd)/src/executable_scripts/mamow" /usr/local/bin/mamow
  ```

  **Fix 2 (Add to PATH):** Add the folder to your `~/.zshrc` or `~/.bashrc`.
  ```bash
  echo 'export PATH="$PATH:'"$(pwd)"'/src/executable_scripts"' >> ~/.zshrc
  source ~/.zshrc
  ```

**🪟 Windows:**

If you ran `install.bat` but `mamow` still isn't recognized in PowerShell or Command Prompt:

* **Issue: PATH environment variable didn't refresh**
  **Fix:** Restart your PowerShell or Command Prompt window. The PATH changes applied by `install.bat` take effect in new terminal sessions.
* **Issue: Script Execution Disabled (PowerShell)**
  **Fix:** Open PowerShell as Administrator and run:

  ```powershell
  Set-ExecutionPolicy Unrestricted -Scope CurrentUser
  ```
* **Alternative for Git Bash Users:**
  If you prefer Git Bash instead of PowerShell, Git Bash reads the bash `mamow` file instead of `mamow.bat`. You can alias it by running:

  ```bash
  echo "alias mamow='bash $(pwd)/src/executable_scripts/mamow'" >> ~/.bash_profile
  source ~/.bash_profile
  ```
