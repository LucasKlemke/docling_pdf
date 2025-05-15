# Setup Guide

Follow these steps to set up the project from scratch:

## 1. Clone the Repository

Clone this repository to your local machine:

```sh
git clone https://github.com/yourusername/docling_pdf.git
cd docling_pdf
```

## 2. Install `pyenv` (Recommended)

Ensure you have `pyenv` to manage Python versions.

### macOS (with Homebrew)

```sh
brew update
brew install pyenv
```

### Ubuntu

```sh
curl https://pyenv.run | bash
```

Add the following to your `~/.bashrc` or `~/.zshrc`:

```sh
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv virtualenv-init -)"
```

Restart your terminal or run `source ~/.bashrc` (or `source ~/.zshrc`).

## 3. Set Up Python Environment

Install the required Python version and create a virtual environment:

```sh
pyenv install 3.10.12
pyenv virtualenv 3.10.12 venv-docling
pyenv local venv-docling
```

## 4. Install Project Dependencies

Install all required Python packages:

```sh
pip install -r requirements.txt
```

## 5. Configure Environment Variables

Copy the example environment file and edit it with your credentials:

```sh
cp .env.example .env
# Edit .env with your preferred editor
```

## 6. Update Book URLs

Edit the `books` array in `create_db.py` to add or update the book URLs as needed.

## 7. Create the Local Database

Generate the local database by running:

```sh
python create_db.py
```

## 8. Migrate Database to Supabase

After creating the local database, migrate it to Supabase:

```sh
python migrate_db.py
```

---

**You're all set!**  
Refer to the project documentation or code comments for further usage instructions.