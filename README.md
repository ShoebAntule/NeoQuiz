
# NeoQuiz Project

## Overview
NeoQuiz is a Django-based online quiz application with AI-powered multiple-choice question generation using OpenAI and Azure APIs. This project includes teacher and student modules, email notifications, and more.

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Git
- Virtualenv (recommended)
- An OpenAI API key (or Azure/DeepSeek API keys if using those providers)
- Gmail account credentials for email notifications (or configure your own SMTP server)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/ShoebAntule/NeoQuiz.git
   cd NeoQuiz
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file in the project root with the following variables:**
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   AZURE_API_KEY=your_azure_api_key_here
   DEEPSEEK_API_KEY=your_deepseek_api_key_here
   EMAIL_HOST_USER=your_email@example.com
   EMAIL_HOST_PASSWORD=your_email_password
   EMAIL_RECEIVING_USER=recipient_email@example.com
   ```

5. **Apply database migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser (admin) account**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   Open your browser and go to `http://127.0.0.1:8000/`

### Notes
- The project uses environment variables to securely manage API keys and email credentials.
- The `.env` file is included in `.gitignore` to prevent accidental commits of secrets.
- If you have committed secrets previously, make sure to clean your Git history before pushing to GitHub.

### Additional Tools
- To clean Git history of secrets, consider using [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/) or `git filter-repo`.

## Contact
For any issues or questions, please contact the project maintainer.  +91 8779030806
