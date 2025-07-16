# Cloud Deployment Guide for Gym Reservation System

This guide explains how to deploy your gym reservation system to the cloud for 24/7 automatic operation.

## 🏗️ Deployment Options

### 1. Railway (Recommended - Easy & Affordable)
**Cost**: ~$5/month | **Difficulty**: Easy

#### Setup Steps:
1. **Create Railway Account**: Go to [railway.app](https://railway.app) and sign up
2. **Connect GitHub**: Link your GitHub account to Railway
3. **Create New Project**: Click "New Project" → "Deploy from GitHub repo"
4. **Select Repository**: Choose your gym reservation repository
5. **Configure Environment Variables**:
   ```bash
   CONDOMISOFT_USERNAME=santiago.sbg@gmail.com
   CONDOMISOFT_PASSWORD=Flow!Wire103c!
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USER=santiago.sbg@gmail.com
   EMAIL_PASSWORD=tyyr pivr fatn qowx
   EMAIL_TO=santiago.sbg@gmail.com
   TZ=America/Mexico_City
   ```
6. **Deploy**: Railway will automatically build and deploy your app

#### Configuration File:
The `railway.json` file is already configured for Railway deployment.

---

### 2. Render (Free Tier Available)
**Cost**: Free tier available | **Difficulty**: Easy

#### Setup Steps:
1. **Create Render Account**: Go to [render.com](https://render.com) and sign up
2. **Connect GitHub**: Link your GitHub account
3. **Create New Web Service**: Click "New" → "Web Service"
4. **Select Repository**: Choose your gym reservation repository
5. **Configure Settings**:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python gym_reservation_cloud.py`
6. **Set Environment Variables**: (same as Railway above)
7. **Deploy**: Render will build and deploy automatically

#### Configuration File:
The `render.yaml` file is already configured for Render deployment.

---

### 3. DigitalOcean App Platform
**Cost**: ~$5/month | **Difficulty**: Easy

#### Setup Steps:
1. **Create DigitalOcean Account**: Go to [digitalocean.com](https://digitalocean.com)
2. **Navigate to Apps**: Go to "Apps" in the control panel
3. **Create New App**: Click "Create App"
4. **Connect GitHub**: Link your repository
5. **Configure App**:
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Run Command**: `python gym_reservation_cloud.py`
6. **Set Environment Variables**: (same as above)
7. **Deploy**: DigitalOcean will handle the deployment

---

### 4. Heroku (Simple but Limited)
**Cost**: ~$7/month | **Difficulty**: Medium

#### Setup Steps:
1. **Install Heroku CLI**: Download from [heroku.com](https://heroku.com)
2. **Login**: `heroku login`
3. **Create App**: `heroku create gym-reservation-system`
4. **Add Buildpacks**:
   ```bash
   heroku buildpacks:add --index 1 heroku/python
   heroku buildpacks:add --index 2 https://github.com/heroku/heroku-buildpack-google-chrome
   heroku buildpacks:add --index 3 https://github.com/heroku/heroku-buildpack-chromedriver
   ```
5. **Set Environment Variables**:
   ```bash
   heroku config:set CONDOMISOFT_USERNAME="santiago.sbg@gmail.com"
   heroku config:set CONDOMISOFT_PASSWORD="Flow!Wire103c!"
   heroku config:set EMAIL_HOST="smtp.gmail.com"
   heroku config:set EMAIL_PORT="587"
   heroku config:set EMAIL_USER="santiago.sbg@gmail.com"
   heroku config:set EMAIL_PASSWORD="tyyr pivr fatn qowx"
   heroku config:set EMAIL_TO="santiago.sbg@gmail.com"
   heroku config:set TZ="America/Mexico_City"
   ```
6. **Deploy**: `git push heroku main`

#### Required Files:
- `Procfile`: `worker: python gym_reservation_cloud.py`
- `runtime.txt`: `python-3.9.18`

---

### 5. AWS (Advanced)
**Cost**: ~$10-20/month | **Difficulty**: Hard

#### Options:
- **ECS Fargate**: Containerized deployment
- **EC2**: Virtual machine deployment
- **Lambda**: Serverless (requires modifications)

#### Setup (ECS Fargate):
1. **Build Docker Image**: `docker build -t gym-reservation .`
2. **Push to ECR**: Amazon Elastic Container Registry
3. **Create ECS Task Definition**: Use the Docker image
4. **Set Environment Variables**: In task definition
5. **Create ECS Service**: For continuous running
6. **Configure CloudWatch**: For logs and monitoring

---

## 🛠️ Local Testing with Docker

Before deploying to the cloud, test locally:

```bash
# Build the Docker image
docker build -t gym-reservation .

# Run with environment variables
docker run -e CONDOMISOFT_USERNAME="santiago.sbg@gmail.com" \
           -e CONDOMISOFT_PASSWORD="Flow!Wire103c!" \
           -e EMAIL_HOST="smtp.gmail.com" \
           -e EMAIL_PORT="587" \
           -e EMAIL_USER="santiago.sbg@gmail.com" \
           -e EMAIL_PASSWORD="tyyr pivr fatn qowx" \
           -e EMAIL_TO="santiago.sbg@gmail.com" \
           -e TZ="America/Mexico_City" \
           gym-reservation

# Or use docker-compose
docker-compose up
```

---

## 🔧 Configuration Files Included

- **`Dockerfile`**: Container configuration with Chrome and Python
- **`docker-compose.yml`**: Local development setup
- **`railway.json`**: Railway deployment configuration
- **`render.yaml`**: Render deployment configuration
- **`gym_reservation_cloud.py`**: Cloud-optimized version of the script

---

## 📊 Comparison Table

| Platform | Cost | Ease | Free Tier | Container Support | Scheduling |
|----------|------|------|-----------|-------------------|------------|
| Railway | $5/mo | ⭐⭐⭐⭐⭐ | No | Yes | Built-in |
| Render | Free+ | ⭐⭐⭐⭐⭐ | Yes | Yes | Built-in |
| DigitalOcean | $5/mo | ⭐⭐⭐⭐ | No | Yes | Built-in |
| Heroku | $7/mo | ⭐⭐⭐ | No | Limited | Built-in |
| AWS | $10+/mo | ⭐⭐ | Yes | Yes | CloudWatch |

---

## 🚀 Recommended Deployment Steps

### Quick Start (Railway):
1. Push code to GitHub
2. Connect Railway to GitHub
3. Set environment variables
4. Deploy!

### Environment Variables Needed:
```bash
CONDOMISOFT_USERNAME=santiago.sbg@gmail.com
CONDOMISOFT_PASSWORD=Flow!Wire103c!
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=santiago.sbg@gmail.com
EMAIL_PASSWORD=tyyr pivr fatn qowx
EMAIL_TO=santiago.sbg@gmail.com
TZ=America/Mexico_City
```

---

## 🔍 Monitoring & Troubleshooting

### Check Logs:
- **Railway**: Dashboard → Logs tab
- **Render**: Dashboard → Logs section
- **DigitalOcean**: Apps → Runtime Logs
- **Heroku**: `heroku logs --tail`

### Common Issues:
1. **Chrome/ChromeDriver**: Fixed in cloud version
2. **Memory Limits**: Increased in Docker config
3. **Timezone**: Set via TZ environment variable
4. **Email Failures**: Check Gmail app password

---

## 📧 Email Notifications

The cloud version includes enhanced email notifications that show:
- ☁️ Cloud deployment indicator
- Detailed results for both time slots
- Manual reservation link if needed
- Deployment information

---

## 🔒 Security Best Practices

1. **Never commit credentials** to GitHub
2. **Use environment variables** for all sensitive data
3. **Enable 2FA** on your cloud platform account
4. **Monitor logs** for suspicious activity
5. **Use strong passwords** for your accounts

---

## 💡 Tips for Success

1. **Start with Railway or Render** for simplicity
2. **Test locally first** using Docker
3. **Monitor email notifications** for system health
4. **Check logs regularly** for any issues
5. **Keep credentials secure** and updated

Your gym reservation system will run 24/7 in the cloud, automatically reserving your slots every Monday, Wednesday, and Friday at 00:01 AM! 