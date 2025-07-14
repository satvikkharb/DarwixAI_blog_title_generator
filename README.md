# Blog Title Generator API

A Django REST API service that leverages OpenAI GPT and HuggingFace models to generate engaging, SEO-friendly blog titles. The service combines multiple AI models for diverse title suggestions and includes content analysis features.

#### Note: For Diarization, please go inside the diarization-whisper directory, was facing some memory issue problem in my linux, that's why not able to integrate that with django application (space issue for installing a module - pyannote.audio)

## 📋 Table of Contents

- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Development](#-development)
- [Contributing](#-contributing)

## ✨ Features

- **Multiple AI Models**
  - OpenAI GPT-4 Turbo for creative titles
  - HuggingFace BART-CNN for content-focused titles
- **Content Analysis**
  - Keyword extraction
  - Content summarization
- **Caching System**
  - 24-hour cache duration for faster responses
- **Admin Interface**
  - Monitor and manage title requests
  - View content and generated titles
- **Error Handling**
  - Comprehensive logging
  - Graceful fallback options
- **API Documentation**
  - Clear endpoint documentation
  - Request/response examples

## 🔧 Prerequisites

- Python 3.8+
- Django 4.2+
- OpenAI API key
- HuggingFace API key (optional)

## 🚀 Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repository-url>
   cd blog_title_generator
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   
   # Linux/Mac
   source venv/bin/activate
   
   # Windows
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create .env file in the project root:**
   ```bash
   # Django Settings
   DJANGO_SECRET_KEY="your-secret-key"
   DEBUG=True
   ALLOWED_HOSTS=127.0.0.1,localhost

   # API Keys
   OPENAI_API_KEY="your-openai-api-key"
   HUGGINGFACE_API_KEY="your-huggingface-api-key"
   ```

5. **Run database migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create a superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

## 💻 Usage

1. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

2. **Make API requests:**
   ```bash
   POST http://localhost:8000/api/suggest-titles/
   Content-Type: application/json

   {
       "content": "Your blog post content here (minimum 50 characters)",
       "include_analysis": true
   }
   ```

3. **Example Response:**
   ```json
   {
       "id": 1,
       "suggestions": [
           "The Future of AI: A Deep Dive",
           "Understanding Machine Learning in 2025",
           "AI Revolution: What You Need to Know"
       ],
       "analysis": {
           "keywords": ["artificial", "intelligence", "machine", "learning", "technology"],
           "summary": "A brief summary of your content..."
       }
   }
   ```

## 📘 API Documentation

### Title Generation Endpoint

**URL:** `/api/suggest-titles/`  
**Method:** `POST`

**Request Body:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| content | string | Yes | Blog post content (minimum 50 characters) |
| include_analysis | boolean | No | Includes keyword extraction and content summary (default: false) |

**Success Response:**

- **Code:** 200 OK
  ```json
  {
      "id": 1,
      "suggestions": ["Title 1", "Title 2", "Title 3"],
      "analysis": {
          "keywords": ["keyword1", "keyword2", "keyword3"],
          "summary": "Content summary..."
      }
  }
  ```

**Error Response:**

- **Code:** 400 Bad Request  
  Content missing or too short

- **Code:** 500 Internal Server Error  
  Service unavailable or processing error

## 🗂️ Project Structure

```
blog_title_generator/
├── title_suggestion/
│   ├── services/
│   │   ├── openai_service.py
│   │   ├── huggingface_service.py
│   │   ├── text_utils.py
│   │   └── cache_service.py
│   ├── models.py
│   ├── views.py
│   └── urls.py
└── blog_title_generator/
    ├── settings.py
    └── urls.py
```

## 🧪 Development

### Running Tests

```bash
python manage.py test
```

### Logging
- Logs are stored in `debug.log`
- Configure logging in `settings.py`

### Admin Interface
- Access at `/admin/`
- Monitor title generation requests
- View generated titles and content

### Error Handling
The application includes comprehensive error handling:
- Input validation
- API service errors
- Model loading errors
- Request/response logging

### Cache System
Title suggestions are cached to improve performance:
- 24-hour cache duration
- Content-based cache keys
- Separate caching for each AI service

## 👥 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 🙏 Acknowledgements

- [OpenAI](https://openai.com) for their powerful GPT models
- [HuggingFace](https://huggingface.co) for their transformer models

---

Made with ❤️ by Om Sharma