# 🚀 Quick Start - GitHub Setup in 5 Minutes

## Step 1️⃣: Update Your Information (2 minutes)

```bash
# Quick way - use the script
python update_username.py YOUR_GITHUB_USERNAME

# Manual way - search and replace in these files:
# - README.md
# - CONTRIBUTING.md
# - GITHUB_SETUP.md
# - pyproject.toml
# - SECURITY.md

# Also update:
# - your.email@example.com → your real email
# - Your Name → your real name
```

## Step 2️⃣: Create GitHub Repository (1 minute)

1. Go to https://github.com/new
2. Repository name: `real-estate-server`
3. Description: "Real Estate Calculator API - Market analysis for Chisinau apartments"
4. Choose Public or Private
5. **Do NOT** initialize with README
6. Click "Create repository"

## Step 3️⃣: Push Your Code (1 minute)

```bash
cd /home/adrianp/personal/real-estate/server

# Initialize git (if needed)
git init

# Add all files
git add .

# Commit
git commit -m "feat: initial project setup with CI/CD pipeline"

# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/real-estate-server.git

# Push
git branch -M main
git push -u origin main
```

## Step 4️⃣: Enable GitHub Actions (30 seconds)

1. Go to your repository on GitHub
2. Click **Settings**
3. Click **Actions** → **General**
4. Select "Allow all actions and reusable workflows"
5. Click **Save**

## Step 5️⃣: Verify Everything Works (30 seconds)

1. Go to **Actions** tab
2. You should see the CI workflow running
3. Wait for it to complete (green checkmark ✅)
4. Go back to main page - badges should appear in README

## 🎉 Done! Your Project is Live!

### What You Have Now:

✅ Professional README with badges  
✅ Automated testing on every push  
✅ Code coverage tracking  
✅ Security scanning  
✅ Issue and PR templates  
✅ Comprehensive documentation  

### View Your Project:

- **Repository**: `https://github.com/YOUR_USERNAME/real-estate-server`
- **API Docs**: `http://localhost:8000/docs` (when running)
- **CI/CD Status**: Check Actions tab

---

## 📚 What's Next?

### Optional Enhancements (5-10 minutes each)

#### 🔐 Setup Codecov (better coverage tracking)
1. Go to https://codecov.io/
2. Sign in with GitHub
3. Add your repository
4. Copy the token
5. Add to GitHub: Settings → Secrets → Actions → New secret
6. Name: `CODECOV_TOKEN`, Value: [paste token]

#### 🛡️ Enable Branch Protection
1. Settings → Branches → Add rule
2. Branch name: `main`
3. Check: "Require pull request before merging"
4. Check: "Require status checks to pass"
5. Select: `test (3.11)`, `test (3.12)`, `build`
6. Save

#### 🔄 Install Pre-commit Hooks (local)
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

### Start Developing

```bash
# Create a feature branch
git checkout -b feature/my-feature

# Make changes
# ...

# Test locally
pytest --cov=app

# Commit
git commit -m "feat: add my feature"

# Push and create PR
git push origin feature/my-feature
```

---

## 🆘 Troubleshooting

### "Permission denied" when pushing
- Check you're authenticated with GitHub
- Use SSH key or personal access token
- See: https://docs.github.com/en/authentication

### CI pipeline fails
- Check Actions tab → View logs
- Most common: missing dependencies
- Fix in `pyproject.toml` and push again

### Badges not showing
- Wait 1-2 minutes after first push
- Check username in badge URLs
- Clear browser cache

---

## 📞 Need Help?

- 📖 Read GITHUB_SETUP.md for detailed instructions
- ✅ Use CHECKLIST.md to verify everything
- 📚 Check QUICK_REFERENCE.md for commands
- 🐛 Open an issue on GitHub

---

**Total time: ~5 minutes** ⏱️  
**Difficulty: Easy** 🟢  
**Result: Professional GitHub project** 🎯

