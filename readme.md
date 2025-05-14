# Setup Guide

## 1. Install `pyenv`

If you don't have `pyenv` installed, follow these steps:

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

## 2. Create a Virtual Environment

Choose your Python version (e.g., 3.10.12):

```sh
pyenv install 3.10.12
pyenv virtualenv 3.10.12 venv-docling
pyenv local venv-docling
```

## 3. Install Dependencies

```sh
pip install -r requirements.txt
```

## 4. Configure Environment Variables

Copy `.env.example` to `.env` and fill in the required values:

```sh
cp .env.example .env
# Edit .env with your preferred editor
```