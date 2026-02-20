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

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/karunanayak-tech/Legacy_Lift.git   
cd Legacy_Lift

### 2️⃣ Configure Your Environment Variables

Create a `.env` file in the root directory and securely add your Gemini API key:

```env
# If using Option A (Docker), use:
GEMINI_API_KEY=your_api_key_here

# If using Option B (Virtual Environment), use:
GOOGLE_API_KEY=your_api_key_here


## 🛠️ Choose Your Setup Method

### 🐳 Option A: Docker (Recommended)

LegacyLift is fully containerized for a seamless developer experience.  
Spin up the application using **Docker Compose**:

#### 1️⃣ Start the Agentic Factory

```bash
docker compose up --build -d

#### 2️⃣ Access the UI

The Streamlit interface will instantly be available at:

👉 [http://localhost:8501]

#### 3️⃣ Shut Down

When you are done testing, gracefully spin down the container:

```bash
docker compose down

### 🧪 Option B: Local Virtual Environment

Use this method to manage dependencies locally and avoid path conflicts.

#### 1️⃣ Set Up a Virtual Environment

```bash
# Create the environment
python -m venv venv

# Activate it (Windows)
.\venv\Scripts\activate

# Activate it (macOS/Linux)
source venv/bin/activate

#### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt

#### 3️⃣ Launch the Application

```bash
streamlit run app.py

---

## 📖 Usage: Migrating an Application

Once the application is running via either method:

### 🔹 Input

Paste a **public GitHub repository URL** of a legacy application  
(e.g., a Flask or Node.js app) into the UI.

### 🔹 Migrate

Click the **Migrate** button.

### 🔹 Process

LegacyLift:
- Clones the repository  
- Identifies the framework  
- Utilizes **Gemini 1.5 Flash** to analyze the code  

### 🔹 Output

In under **10 seconds**, the agent generates three critical cloud-native artifacts:

### 📦 Generated Cloud-Native Artifacts

- 📄 **Dockerfile**  
  Production-grade, secure, and multi-stage.

- ⚙️ **cloudbuild.yaml**  
  Configuration for automated Google Cloud Builds.

- ☁️ **service.yaml**  
  Manifest for serverless deployment on Google Cloud Run.


