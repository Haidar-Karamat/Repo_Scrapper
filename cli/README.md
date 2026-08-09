# 📦 Repo Scrapper API & AI CLI

[![PyPI Version](https://img.shields.io/pypi/v/repo-scrapper-cli.svg)](https://pypi.org/project/repo-scrapper-cli/)
[![Build & Deploy Status](https://github.com/Haidar-Karamat/Repo_Scrapper/actions/workflows/ci-cd.yaml/badge.svg)](https://github.com/Haidar-Karamat/Repo_Scrapper/actions)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-AKS-0078D4?logo=kubernetes&logoColor=white)](https://azure.microsoft.com/en-us/products/kubernetes-service)
[![Azure ACR](https://img.shields.io/badge/Registry-Azure_ACR-0089D6?logo=microsoftazure&logoColor=white)](https://azure.microsoft.com/en-us/products/container-registry)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi)](https://fastapi.tiangolo.com/)
[![IaC Terraform](https://img.shields.io/badge/IaC-Terraform-7B42BC?logo=terraform&logoColor=white)](https://www.terraform.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An automated, AI-powered GitHub repository search and scraping platform. Features a **Grok AI-driven FastAPI backend** deployed on **Azure Kubernetes Service (AKS)** via **Terraform** & **GitHub Actions CI/CD**, alongside an interactive **PyPI CLI tool (`repo-scrapper-cli`)**.

---

## 🏛️ End-to-End System Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        PyPI Package Client                             │
│                    pip install repo-scrapper-cli                       │
└───────────────────────────────────┬────────────────────────────────────┘
                                     │
                  ┌──────────────────┴──────────────────┐
                  │                                      │
        [ Primary Hybrid Route ]                [ Offline Fallback Route ]
        FastAPI Backend (AKS)                   Direct GitHub REST API
                  │                                      │
    ┌─────────────┴─────────────┐            ┌───────────┴───────────┐
    │ Grok AI Dual-Key Rotator  │            │   Rule-Based Engine    │
    │ (Key 1 ➔ Key 2 Failover)  │            │   Regex Extractor      │
    └─────────────┬─────────────┘            └───────────┬───────────┘
                  │                                       │
                  └──────────────────┬────────────────────┘
                                     │
                                     ▼
                       ┌──────────────────────────┐
                       │   GitHub Search REST API │
                       └──────────────────────────┘
```

---

## 💻 1. For End Users: CLI Quickstart (PyPI)

If you just want to use the tool to find repositories, you don't need to download the source code — just install it via pip.

**Install the CLI tool:**

```bash
pip install repo-scrapper-cli
```

**Run a search query:**

```bash
repo-scrapper "top 3 python microservices with docker" --limit 3
```

**Connect to a custom backend URL:**

```bash
repo-scrapper "react templates" --url "http://your-aks-cluster-ip:8000"
```

---

## 🛠️ 2. For Developers: Local Backend Setup

If you want to run the AI-powered FastAPI backend locally, follow these steps.

**Step 1: Clone the repository**

```bash
git clone https://github.com/Haidar-Karamat/Repo_Scrapper.git
cd Repo_Scrapper
```

**Step 2: Set up a virtual environment**

```bash
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / Mac
python3 -m venv venv
source venv/bin/activate
```

**Step 3: Install dependencies**

```bash
cd server
pip install -r requirements.txt
```

**Step 4: Configure environment variables**

Create a `.env` file inside the `server/` directory:

```env
# Grok AI API Keys (Optional, fallback works without it)
GROK_API_KEY_1=your_first_key_here
GROK_API_KEY_2=your_second_key_here

# GitHub Token (Increases rate limit to 5000 req/hr)
GITHUB_TOKEN=ghp_your_github_token_here
```

**Step 5: Run the FastAPI server**

```bash
uvicorn app.main:app --reload --port 8000
```

API documentation will be available at: `http://localhost:8000/docs`

---

## 🐳 3. For DevOps: Docker Deployment

To run the backend isolated in a container:

```bash
# Build the Docker image
docker build -t repo-scrapper-backend ./server

# Run the container (make sure your .env file is ready)
docker run -d -p 8000:8000 --name repo-backend --env-file ./server/.env repo-scrapper-backend
```

---

## ☁️ 4. Cloud Deployment (Terraform & Azure AKS)

**Step 1: Authenticate with Azure**

```bash
az login
```

**Step 2: Provision infrastructure with Terraform**

```bash
cd terraform
terraform init
terraform plan
terraform apply -auto-approve
```

**Step 3: Deploy to Kubernetes**

```bash
az aks get-credentials --resource-group repo-scrapper-rg --name repo-scrapper-aks
kubectl apply -f k8s/
```

---

## 📄 License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).
