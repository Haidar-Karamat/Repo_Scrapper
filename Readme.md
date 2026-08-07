# 📦 Repo Scrapper API

![Build & Deploy Status](https://github.com/YOUR_GITHUB_USERNAME/Repo_Scrapper/actions/workflows/ci-cd.yaml/badge.svg)
![Kubernetes](https://img.shields.io/badge/Kubernetes-AKS-0078D4?logo=kubernetes&logoColor=white)
![Azure ACR](https://img.shields.io/badge/Registry-Azure_ACR-0089D6?logo=microsoftazure&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi)
![Terraform](https://img.shields.io/badge/IaC-Terraform-7B42BC?logo=terraform&logoColor=white)

An automated GitHub repository search and scraping service built with FastAPI, containerized using Docker, provisioned via Terraform, and deployed on Azure Kubernetes Service (AKS) through GitHub Actions CI/CD.

---

## 🏗 Architecture Overview

```text
  +-------------------+       +-------------------+       +--------------------+
  |  GitHub Push /    | ----> |   GitHub Actions  | ----> | Azure Container    |
  |  Pull Request     |       |   CI/CD Pipeline  |       | Registry (ACR)     |
  +-------------------+       +-------------------+       +--------------------+
                                                                     |
                                                                     v
  +-------------------+       +-------------------+       +--------------------+
  |  Client /         | <---- | Azure LoadBalancer| <---- | Azure Kubernetes   |
  |  Browser / cURL   |       | Service (Port 80) |       | Service (AKS Pods) |
  +-------------------+       +-------------------+       +--------------------+



# Clone the repository
git clone [https://github.com/YOUR_GITHUB_USERNAME/Repo_Scrapper.git](https://github.com/YOUR_GITHUB_USERNAME/Repo_Scrapper.git)
cd Repo_Scrapper

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run backend server
uvicorn server.main:app --reload --port 8000