# Installing Node.js 24 for xrayradar-web

This project requires Node.js 20.19.0+, 22.12.0+, or 24.0.0+.

## Quick Start: Install nvm and Node.js 24

### Step 1: Install nvm (Node Version Manager)

```bash
# Download and install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash
```

### Step 2: Reload your shell

```bash
# For bash
source ~/.bashrc

# For zsh
source ~/.zshrc
```

### Step 3: Install Node.js 24

```bash
# Install Node.js 24 (latest)
nvm install 24

# Use Node.js 24
nvm use 24

# Verify installation
node --version  # Should show v24.x.x
npm --version
```

### Step 4: Set Node.js 24 as default (optional)

```bash
# Set Node.js 24 as default for new shells
nvm alias default 24
```

## Alternative: Install Node.js 22 (LTS)

If you prefer the LTS version:

```bash
nvm install 22
nvm use 22
nvm alias default 22
```

## Alternative: System-wide Installation (Ubuntu/Debian)

If you prefer not to use nvm:

```bash
# Add NodeSource repository for Node.js 24
curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -

# Install Node.js
sudo apt-get install -y nodejs

# Verify
node --version
npm --version
```

## Troubleshooting

### nvm command not found after installation

Make sure you've reloaded your shell:
```bash
source ~/.bashrc  # or ~/.zshrc
```

Or add to your `~/.bashrc` or `~/.zshrc`:
```bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
```

### Permission issues

If you get permission errors, you may need to use `sudo` for system-wide installation, or use nvm (which installs to your home directory, no sudo needed).

## Verify Installation

After installation, verify everything works:

```bash
cd xrayradar-web
node --version  # Should be 20.19.0+, 22.12.0+, or 24.0.0+
npm install
npm test
```
