# 🚀 LegacyLift: Agentic Migration Factory

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![Google Cloud](https://img.shields.io/badge/Google_Cloud-4285F4?logo=google-cloud&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)

**LegacyLift** is an AI-powered DevOps tool built to eliminates infrastructure toil by automatically modernizing legacy applications into production-ready Google Cloud Run and Kubernetes deployments. 

By passing a public GitHub repository, LegacyLift acts as an autonomous SRE, analyzing the codebase and utilizing Google Gemini to instantly generate optimized containerization and CI/CD artifacts.

---

## ✨ Features

* **🧠 AI Context Extraction:** Automatically scans `package.json` or `requirements.txt` to determine the technology stack.
* **🐳 Smart Containerization:** Generates highly optimized, lightweight `Dockerfile`s (e.g., Alpine/Slim images) with correct exposed ports.
* **⚙️ CI/CD Automation:** Outputs strict, ready-to-execute `cloudbuild.yaml` pipelines for Google Cloud Build.
* **☸️ Flexible Orchestration:** Dynamically generates `service.yaml` manifests for either serverless **Knative (Cloud Run)** or traditional **Kubernetes** deployments (Deployment + LoadBalancer).
* **🛡️ SRE-Focused:** Strict prompt engineering ensures outputs are raw, machine-readable configurations free of conversational LLM filler.

---

## 🏗️ Architecture Flow

1. **Ingestion:** Streamlit frontend captures the target legacy GitHub URL and temporarily clones it.
2. **Analysis:** Python backend extracts dependency manifests to map the build context.
3. **Generation:** Gemini strictly generates Infrastructure-as-Code (IaC) based on Google Cloud best practices.
4. **Validation:** Developers can locally test the generated artifacts using `docker build` before pushing to GCP.

---

## 📋 Prerequisites

Before running LegacyLift locally, ensure you have the following installed:
* Python 3.9+
* Docker Desktop
* Git
* A valid Google Gemini API Key

---

## 🚀 Installation & Setup

**1. Clone the repository**
```bash
git clone [https://github.com/karunanayak-tech/Legacy_Lift.git](https://github.com/karunanayak-tech/Legacy_Lift.git)
cd Legacy_Lift
