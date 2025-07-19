
<div align="center">


# AI-Powered Résumé & Job Application Automation Tool

## Modular Architecture Roadmap (In Progress)

```
project_root/
│
├── job_search/         # Fetching/filtering job postings (pluggable sources)
├── documents/          # Résumé & cover letter generation (AI/OpenAI logic)
├── applications/       # Application sending, logging, manual apply
├── profiles/           # User profile/config management
├── cli/                # CLI entrypoint and scripts
├── utils/              # Helper functions
├── tests/              # Unit and integration tests
│
├── requirements.txt
├── dev-requirements.txt
├── README.md
└── .env.example
```

- **PEP8, type hints, docstrings**
- **Dependency injection** for all external services
- **Pydantic** for config/profile schema validation
- **Logging**: log-to-file and log-to-console
- **Error handling**: try/except with meaningful messages, retries for network
- **Separation of concerns**: no CLI logic in business modules
- **Unit tests**: pytest, with mocks for external dependencies

---

## 🚀 Quick Start

The system now offers **two interfaces** for your convenience:

### 🌐 Web UI (Recommended)
Modern, intuitive web interface with real-time updates:
```bash
python launcher.py --web
```

### 💻 CLI Interface
Command-line interface for power users:
```bash
python launcher.py --cli
```

### 📋 Interactive Menu
Choose your preferred interface:
```bash
python launcher.py
```

For detailed instructions, see [USER_GUIDE.md](USER_GUIDE.md).

---

# AIHawk: the first Jobs Applier AI Agent


AIHawk's core architecture remains **open source**, allowing developers to inspect and extend the codebase. However, due to copyright considerations, we have removed all third‑party provider plugins from this repository.

For a fully integrated experience, including managed provider connections: check out **[laboro.co](https://laboro.co/)** an AI‑driven job board where the agent **automatically applies to jobs** for you.


---


AIHawk has been featured by major media outlets for revolutionizing how job seekers interact with the job market:

[**Business Insider**](https://www.businessinsider.com/aihawk-applies-jobs-for-you-linkedin-risks-inaccuracies-mistakes-2024-11)
[**TechCrunch**](https://techcrunch.com/2024/10/10/a-reporter-used-ai-to-apply-to-2843-jobs/)
[**Semafor**](https://www.semafor.com/article/09/12/2024/linkedins-have-nots-and-have-bots)
[**Dev.by**](https://devby.io/news/ya-razoslal-rezume-na-2843-vakansii-po-17-v-chas-kak-ii-boty-vytesnyaut-ludei-iz-protsessa-naima.amp)
[**Wired**](https://www.wired.it/article/aihawk-come-automatizzare-ricerca-lavoro/)
[**The Verge**](https://www.theverge.com/2024/10/10/24266898/ai-is-enabling-job-seekers-to-think-like-spammers)
[**Vanity Fair**](https://www.vanityfair.it/article/intelligenza-artificiale-candidature-di-lavoro)
[**404 Media**](https://www.404media.co/i-applied-to-2-843-roles-the-rise-of-ai-powered-job-application-bots/)

