# GitHub Actions Setup Guide - **CHEAPEST & EASIEST** 🏆

## Why GitHub Actions?

✅ **100% FREE** (up to 2,000 minutes/month)  
✅ **No server management** needed  
✅ **Runs only when scheduled** (3x per week)  
✅ **Perfect for automation scripts**  
✅ **Built-in logging and monitoring**

## Step-by-Step Setup

### 1. **Create GitHub Repository**
1. Go to [GitHub.com](https://github.com)
2. Click "New Repository"
3. Name it: `gym-reservation-automation`
4. Make it **Public** (for free minutes) or **Private** (if you have GitHub Pro)
5. Click "Create Repository"

### 2. **Upload Your Code**
```bash
# In your local project directory
git init
git add .
git commit -m "Initial gym reservation automation"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/gym-reservation-automation.git
git push -u origin main
```

### 3. **Set Up Secrets** (CRITICAL STEP)
1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add these **one by one**:

| Secret Name | Value |
|-------------|-------|
| `CONDOMISOFT_USERNAME` | `santiago.sbg@gmail.com` |
| `CONDOMISOFT_PASSWORD` | `Flow!Wire103c!` |
| `EMAIL_USER` | `santiago.sbg@gmail.com` |
| `EMAIL_PASSWORD` | `tyyr pivr fatn qowx` |
| `EMAIL_TO` | `santiago.sbg@gmail.com` |

### 4. **Test the Workflow**
1. Go to **Actions** tab in your repository
2. Click on **Gym Reservation Automation**
3. Click **Run workflow** button to test manually
4. Monitor the logs to ensure everything works

### 5. **Schedule is Automatic**
- The workflow will run **Monday, Wednesday, Friday at 00:01 AM Mexico City time**
- No additional setup needed!

## 📅 **Schedule Details**

```yaml
schedule:
  # Monday, Wednesday, Friday at 00:01 AM Mexico City time (06:01 UTC)
  - cron: '1 6 * * 1,3,5'
```

## 🔍 **Monitoring**

### Check Run Status:
- Go to **Actions** tab in your repository
- See success/failure of each run
- Download logs if needed

### Email Notifications:
- You'll receive email notifications for each reservation attempt
- Success/failure details included in emails

## 💰 **Cost Breakdown**

- **GitHub Actions**: FREE (2,000 minutes/month)
- **Your usage**: ~15 minutes/month (3 runs × 5 minutes each)
- **Total cost**: **$0.00/month** 🎉

## 🚀 **Alternative: Railway (If GitHub Actions doesn't work)**

**Cost**: $5/month (after free tier)

### Railway Setup:
1. Go to [Railway.app](https://railway.app)
2. Connect your GitHub repository
3. Add environment variables
4. Deploy with one click

## 🛠️ **Troubleshooting**

### If GitHub Actions fails:
1. **Check secrets**: Ensure all 5 secrets are set correctly
2. **Check logs**: Go to Actions → failed run → view logs
3. **Test manually**: Use "Run workflow" button
4. **Check permissions**: Make sure repository has Actions enabled

### If Chrome fails:
- The workflow automatically tries Firefox as fallback
- Multi-browser support ensures high success rate

## 📊 **Success Metrics**

After setup, you should see:
- ✅ Automated runs on schedule
- ✅ Email notifications working
- ✅ Successful gym reservations
- ✅ Log artifacts for debugging

## 🎯 **Next Steps**

1. **Set up GitHub repository** (5 minutes)
2. **Configure secrets** (5 minutes)
3. **Test manually** (2 minutes)
4. **Wait for automated runs** (starts next scheduled day)

**Total setup time**: ~15 minutes  
**Monthly cost**: $0.00  
**Maintenance**: None needed!

---

## 🏆 **Why This Is The Best Option**

| Feature | GitHub Actions | Railway | Render | Heroku |
|---------|----------------|---------|---------|---------|
| **Cost** | FREE | $5/month | $7/month | $7/month |
| **Setup Time** | 15 min | 10 min | 15 min | 20 min |
| **Maintenance** | None | None | Low | Low |
| **Reliability** | High | High | Medium | Medium |
| **Logs** | Built-in | Good | Good | Good |

**Winner**: GitHub Actions! 🏆 