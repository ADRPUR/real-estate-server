# ✅ GitHub Push Checklist

Use this checklist before pushing your project to GitHub.

## 📝 Pre-Push Checklist

### 1. Personal Information
- [ ] Replace `ADRPUR` in README.md
- [ ] Replace `ADRPUR` in GITHUB_SETUP.md  
- [ ] Replace `ADRPUR` in pyproject.toml
- [ ] Replace `apurice@gmail.com` in pyproject.toml
- [ ] Replace `Adrian` in pyproject.toml
- [ ] Replace `apurice@gmail.com` in CONTRIBUTING.md
- [ ] Replace contact emails in SECURITY.md

### 2. Repository Setup
- [ ] Create repository on GitHub: `real-estate-server`
- [ ] Choose visibility (public/private)
- [ ] Do NOT initialize with README (we have one)

### 3. Local Git Setup
```bash
# Check these commands are ready
cd /home/adrianp/personal/real-estate/server
git init
git add .
git commit -m "feat: initial project setup"
git remote add origin https://github.com/ADRPUR/real-estate-server.git
git branch -M main
git push -u origin main
```

- [ ] Git repository initialized
- [ ] All files added
- [ ] Initial commit created
- [ ] Remote added
- [ ] Pushed to GitHub

### 4. GitHub Configuration

#### Actions
- [ ] Go to Settings → Actions → General
- [ ] Enable "Allow all actions and reusable workflows"
- [ ] Save changes

#### Secrets (if using Codecov)
- [ ] Sign up at https://codecov.io/
- [ ] Add repository to Codecov
- [ ] Copy Codecov token
- [ ] Add secret: Settings → Secrets → Actions → New secret
- [ ] Name: `CODECOV_TOKEN`, Value: [your token]

#### Branch Protection
- [ ] Go to Settings → Branches
- [ ] Add rule for `main` branch
- [ ] Enable "Require pull request before merging"
- [ ] Enable "Require status checks to pass"
- [ ] Select status checks: `test (3.11)`, `test (3.12)`, `build`
- [ ] Save

### 5. Verify CI/CD

- [ ] Go to Actions tab on GitHub
- [ ] Verify CI pipeline runs successfully
- [ ] Check all jobs pass (test, build, security)
- [ ] Review logs if any failures

### 6. Documentation

- [ ] README badges display correctly
- [ ] All links work (test a few)
- [ ] API documentation accessible at /docs
- [ ] Coverage badge appears (after first test run)

### 7. Test Coverage

```bash
# Generate initial coverage
./generate_coverage.py

# Commit badge
git add coverage.svg
git commit -m "docs: add initial coverage badge"
git push
```

- [ ] Coverage tests run successfully
- [ ] Badge generated
- [ ] Badge committed and pushed

### 8. Optional Enhancements

#### Pre-commit Hooks
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```
- [ ] Pre-commit installed
- [ ] Hooks installed
- [ ] Initial run successful

#### Dependabot
- [ ] Go to Settings → Security
- [ ] Enable Dependabot alerts
- [ ] Enable Dependabot security updates
- [ ] Create `.github/dependabot.yml` (optional)

#### GitHub Pages (if needed)
- [ ] Settings → Pages
- [ ] Select source: GitHub Actions or branch
- [ ] Configure custom domain (optional)

### 9. First Release (Optional)

```bash
# Tag version
git tag -a v0.1.0 -m "Initial release"
git push origin v0.1.0
```

- [ ] Version tagged
- [ ] Tag pushed
- [ ] Release created automatically
- [ ] Release notes reviewed

### 10. Post-Push Verification

- [ ] Repository visible on GitHub
- [ ] README displays correctly with badges
- [ ] CI/CD pipeline runs
- [ ] All checks pass (green)
- [ ] Issues and PR templates work
- [ ] Documentation is accessible

## 🔍 Final Checks

### README Badges Status
- [ ] 🟢 CI/CD Pipeline: Passing
- [ ] 🟢 Code Coverage: Shows percentage
- [ ] 🟢 Python Version: 3.11+
- [ ] 🟢 FastAPI: Version shown
- [ ] 🟢 License: MIT displayed
- [ ] 🟢 Code Style: Ruff shown

### Repository Settings
- [ ] Description set: "Real Estate Calculator API - Market analysis for Chisinau apartments"
- [ ] Topics added: `real-estate`, `fastapi`, `web-scraping`, `moldova`, `api`
- [ ] Website URL set (if you have one)
- [ ] License: MIT shown

### Files Present
- [ ] README.md
- [ ] CONTRIBUTING.md
- [ ] CHANGELOG.md
- [ ] LICENSE
- [ ] SECURITY.md
- [ ] .gitignore
- [ ] .github/workflows/ci.yml
- [ ] .github/workflows/release.yml
- [ ] .github/PULL_REQUEST_TEMPLATE.md
- [ ] .github/ISSUE_TEMPLATE/bug_report.yml
- [ ] .github/ISSUE_TEMPLATE/feature_request.yml

## 🎯 Quick Commands Reference

### View Files Status
```bash
git status
```

### View Recent Commits
```bash
git log --oneline -5
```

### Check Remote
```bash
git remote -v
```

### View GitHub Actions Locally
```bash
# Install act (optional)
brew install act  # macOS
# or follow https://github.com/nektos/act

# Run CI locally
act
```

## 📞 Troubleshooting

### Push Rejected
- Check remote URL: `git remote -v`
- Verify authentication (SSH key or token)
- Try: `git pull --rebase origin main` then push

### CI Pipeline Fails
- Check workflow file syntax
- Review logs in Actions tab
- Verify all dependencies in pyproject.toml
- Check Python version compatibility

### Badges Not Showing
- Verify GitHub username in URLs
- Check branch name (main vs master)
- Wait a few minutes for cache refresh
- Clear browser cache

### Coverage Not Uploading
- Verify CODECOV_TOKEN secret
- Check Codecov project settings
- Review CI logs for upload errors

## ✨ Success Criteria

Your project is ready when:
- ✅ All files pushed to GitHub
- ✅ CI/CD pipeline passes
- ✅ Badges display correctly
- ✅ Documentation is clear
- ✅ Tests run successfully
- ✅ Coverage badge shows percentage
- ✅ Issues and PRs work
- ✅ Branch protection active

## 🎉 You're Done!

If all items are checked, your project is professionally set up on GitHub!

Next steps:
1. Share the repository
2. Add contributors
3. Start accepting issues and PRs
4. Continue development with confidence

---

**Need help?** Check GITHUB_SETUP.md for detailed instructions.

