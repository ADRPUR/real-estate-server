# GitHub Setup Instructions

This document provides step-by-step instructions for setting up the project on GitHub with CI/CD, test coverage, and automated workflows.

## 📋 Prerequisites

- GitHub account
- Git installed locally
- Repository created on GitHub

## 🚀 Initial Setup

### 1. Create GitHub Repository

```bash
# On GitHub, create a new repository named "real-estate-server"
# Choose public or private as needed
# Do NOT initialize with README (we have one)
```

### 2. Initialize Local Repository

```bash
cd /home/adrianp/personal/real-estate/server

# Initialize git if not already done
git init

# Add all files
git add .

# Initial commit
git commit -m "feat: initial commit with complete project setup"

# Add remote
git remote add origin https://github.com/ADRPUR/real-estate-server.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## 🔧 GitHub Configuration

### 1. Update README Badge URLs

Edit `README.md` and replace `ADRPUR` with your GitHub username:

```markdown
[![CI/CD Pipeline](https://github.com/ADRPUR/real-estate-server/actions/workflows/ci.yml/badge.svg)](https://github.com/ADRPUR/real-estate-server/actions/workflows/ci.yml)
```

### 2. Setup Codecov (Optional but Recommended)

1. Go to https://codecov.io/
2. Sign in with GitHub
3. Add your repository
4. Copy the Codecov token
5. Add it as a GitHub secret:
   - Go to Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `CODECOV_TOKEN`
   - Value: Your Codecov token

### 3. Enable GitHub Actions

- Go to repository Settings → Actions → General
- Under "Actions permissions", select "Allow all actions and reusable workflows"
- Click "Save"

### 4. Branch Protection (Recommended)

Protect the `main` branch:

1. Go to Settings → Branches
2. Click "Add rule"
3. Branch name pattern: `main`
4. Enable:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - Select status checks: `test (3.11)`, `test (3.12)`, `build`
5. Save changes

## 📊 Test Coverage Badge

### Option 1: Using Codecov (Recommended)

The CI pipeline automatically uploads coverage to Codecov. The badge URL is:

```markdown
[![codecov](https://codecov.io/gh/ADRPUR/real-estate-server/branch/main/graph/badge.svg)](https://codecov.io/gh/ADRPUR/real-estate-server)
```

### Option 2: Using Local Badge (Manual)

Generate and commit the badge manually:

```bash
# Run tests and generate badge
./generate_coverage.py

# Commit the badge
git add coverage.svg
git commit -m "docs: update coverage badge"
git push
```

Then update README to use the local badge:

```markdown
![Coverage](./coverage.svg)
```

### Option 3: GitHub Actions Artifact

The CI pipeline generates a coverage badge as an artifact. You can:

1. Download it from the Actions tab
2. Commit it to the repository
3. Reference it in README

## 🔄 Automated Workflows

### CI/CD Pipeline (`ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

**Jobs:**
1. **Test Suite**: Runs tests on Python 3.11 & 3.12
   - Linting with Ruff
   - Type checking with MyPy
   - Tests with coverage
   - Upload coverage to Codecov

2. **Build Check**: Validates package can be built

3. **Security Scan**: Runs Bandit security checks

### Release Workflow (`release.yml`)

**Trigger:** Push a version tag (e.g., `v0.1.0`)

```bash
# Create a release
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

This automatically:
- Builds the package
- Creates a GitHub release
- Attaches distribution files

## 📝 Pre-commit Hooks (Optional)

Setup pre-commit hooks for automatic checks before each commit:

```bash
# Install pre-commit
pip install pre-commit

# Install the hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

This will automatically:
- Format code with Ruff
- Check for common issues
- Run type checking
- Run tests before commit

## 🏷️ Creating Releases

### Semantic Versioning

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.1.0): New features, backward compatible
- **PATCH** (0.0.1): Bug fixes

### Release Process

1. Update `CHANGELOG.md` with changes
2. Update version in `pyproject.toml`
3. Commit changes:
   ```bash
   git add CHANGELOG.md pyproject.toml
   git commit -m "chore: prepare release v0.1.0"
   git push
   ```
4. Create and push tag:
   ```bash
   git tag -a v0.1.0 -m "Release version 0.1.0"
   git push origin v0.1.0
   ```
5. GitHub Actions will automatically create the release

## 📈 Viewing Results

### CI/CD Status

- View workflow runs: `Actions` tab
- Check test results and logs
- Download artifacts (coverage reports, builds)

### Coverage Reports

- **Codecov**: https://codecov.io/gh/ADRPUR/real-estate-server
- **Local HTML**: Open `htmlcov/index.html` after running tests

### Badges

All badges should appear in README:
- CI/CD status (green = passing)
- Code coverage percentage
- Python version
- License

## 🔐 Security

### Secrets Management

Never commit:
- `.env` files
- API keys
- Credentials
- Tokens

Use GitHub Secrets for sensitive data in workflows.

### Dependabot (Recommended)

Enable Dependabot for automatic dependency updates:

1. Go to Settings → Security → Code security and analysis
2. Enable "Dependabot alerts"
3. Enable "Dependabot security updates"

Create `.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
```

## 📚 Next Steps

1. ✅ Push code to GitHub
2. ✅ Update README with your username
3. ✅ Setup Codecov (optional)
4. ✅ Enable GitHub Actions
5. ✅ Configure branch protection
6. ✅ Setup pre-commit hooks (optional)
7. ✅ Create first release tag

## 🆘 Troubleshooting

### CI Fails on First Run

- Check GitHub Actions are enabled
- Ensure all dependencies are in `pyproject.toml`
- Review workflow logs for specific errors

### Coverage Badge Not Updating

- Ensure Codecov token is set correctly
- Check that tests are running successfully
- Wait a few minutes for Codecov to process

### Tests Fail in CI but Pass Locally

- Check Python version differences
- Ensure all dependencies are specified
- Review environment-specific settings

## 📞 Support

- Open an issue: https://github.com/ADRPUR/real-estate-server/issues
- Discussions: https://github.com/ADRPUR/real-estate-server/discussions

---

**Remember to replace `ADRPUR` with your actual GitHub username in all files!**

