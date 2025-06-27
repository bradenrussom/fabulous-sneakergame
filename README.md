# MVP Health Care Document Processor

A web application that automatically applies all 71 MVP Health Care corporate standards to Word documents.

## 🚀 Live Demo

Visit the deployed application: `https://your-app-name.onrender.com`

## ✨ Features

- **71 Corporate Rules**: Automatically applies time formatting, terminology, branding, and more
- **Web Interface**: Easy drag-and-drop file upload
- **Instant Processing**: Fast document correction and download
- **Analysis Mode**: Preview potential corrections before processing
- **Mobile Friendly**: Responsive design works on all devices

## 📋 Rules Applied

### Time Formatting
- Removes unnecessary `:00` minutes
- Standardizes AM/PM to lowercase `am`/`pm`
- Adds proper spacing and en dashes for time ranges

### Number Formatting
- Spells out numbers 1-9 (with smart exclusions)
- Adds commas to numbers 1,000+

### MVP Branding & Terminology
- Adds ® and ℠ symbols to trademarks
- Corrects "healthcare" to "health care"
- Updates "telehealth" to "virtual care"
- Standardizes "login" to "sign in"
- Fixes MVP-specific terminology

### State Abbreviations
- Removes periods from NY, VT, CT
- Ensures proper capitalization

### Punctuation & Style
- Replaces `&` with "and"
- Removes double spaces
- Standardizes punctuation

## 🛠️ Local Development

### Prerequisites
- Python 3.11+
- pip

### Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/mvp-document-processor.git
cd mvp-document-processor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

Visit `http://localhost:5000` to use the application.

## 🚀 Deployment to Render.com

### Method 1: Automatic Deployment (Recommended)

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Deploy on Render**:
   - Go to [render.com](https://render.com)
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Use these settings:
     - **Name**: `mvp-document-processor`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app`
   - Click "Create Web Service"

3. **Wait for deployment** (usually 2-3 minutes)

4. **Get your URL**: `https://mvp-document-processor.onrender.com`

### Method 2: Using render.yaml

1. The included `render.yaml` file will automatically configure deployment
2. Just connect your repo and Render will use the configuration

## 🔧 Environment Variables

The application uses these environment variables:

- `SECRET_KEY`: Flask secret key (auto-generated on Render)
- `PORT`: Port to run on (auto-set by hosting platform)

## 📁 Project Structure

```
mvp-document-processor/
├── app.py                 # Main Flask application
├── templates/
│   └── index.html        # Web interface
├── requirements.txt      # Python dependencies
├── render.yaml          # Render deployment config
├── Procfile             # Heroku deployment config
├── runtime.txt          # Python version specification
├── gunicorn.conf.py     # Gunicorn configuration
├── .gitignore           # Git ignore file
└── README.md            # This file
```

## 🎯 Usage

1. **Upload Document**: Drag and drop or click to select a `.docx` file
2. **Analyze** (Optional): Preview what corrections will be made
3. **Process**: Apply all corrections and download the fixed document
4. **Download**: Get your corrected document with timestamp

## 🔒 Security Features

- File type validation (only `.docx` files accepted)
- File size limits (16MB maximum)
- Temporary file cleanup
- No data persistence (files are processed and discarded)

## 📊 Technical Details

- **Backend**: Python Flask
- **Document Processing**: python-docx library
- **Web Server**: Gunicorn
- **Frontend**: Vanilla JavaScript with modern CSS
- **Deployment**: Render.com (free tier available)

## 🚀 Alternative Deployment Platforms

### Heroku
```bash
# Install Heroku CLI, then:
heroku create mvp-document-processor
git push heroku main
```

### Railway
1. Connect GitHub repo at [railway.app](https://railway.app)
2. Auto-deploys from your repository

### DigitalOcean App Platform
1. Create new app from GitHub repo
2. Uses automatic Python detection

## 🐛 Troubleshooting

### Common Issues

**"Application Error" on Render**:
- Check the logs in Render dashboard
- Ensure all files are committed to GitHub
- Verify `requirements.txt` is correct

**Upload not working**:
- Check file size (must be under 16MB)
- Ensure file is `.docx` format
- Try a different browser

**Processing fails**:
- Document may be corrupted
- Try re-saving the document in Word
- Check if document has special formatting

### Support

For issues with the MVP corporate rules or document processing logic, refer to the original Python files:
- `mvp_master_rules.yaml` - Complete rule definitions
- `working_document_processor.py` - Core processing logic

## 📝 License

This project is for MVP Health Care internal use.

## 🔄 Updates

The application automatically updates when you push changes to your GitHub repository (if using Render.com auto-deploy).

To update:
```bash
git add .
git commit -m "Update description"
git push origin main
```

Render will automatically redeploy your changes.

---

**Ready to deploy!** 🎉

Follow the deployment steps above and you'll have your MVP Document Processor running on the web in minutes.