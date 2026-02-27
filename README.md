<div align="center">
  <h1>🚀 LegacyLift</h1>
  <p><b>Intelligent, Zero-Persistence Cloud Application Modernization</b></p>
  <p><i>Lift outdated monolithic codebases into sleek, production-ready Google Kubernetes Engine (GKE) topologies using Google Generative AI.</i></p>
</div>

---

## 📖 About The Project

**LegacyLift** is a cutting-edge, AI-driven DevOps utility designed for platform engineers and developers aggressively modernizing legacy applications. 

Instead of manually analyzing outdated `requirements.txt` or `package.json` files and hand-writing Dockerfiles or Kubernetes manifests.

By simply inputting a GitHub repository URL or securely uploading an air-gapped `.zip` archive, LegacyLift analyzes your application's architecture and generates optimized, GKE-ready Dockerfiles, Deployments, Services, Ingress routes, and Horizontal Pod Autoscalers (HPAs) instantly.

### Why LegacyLift?
- **Speed**: Go from a raw Python/Node.js web application to a fully containerized K8s cluster configuration in literally one click.
- **Accuracy**: Driven by the raw context capability of `gemini-2.5-flash`, the engine understands both the application code and the specific architectural needs of Google Cloud.
- **Security**: Built under strict "Zero-Trust" and "Zero-Persistence" design principles, no source code, tokens, or credentials ever hit a physical disk or an external API unredacted.

---

## 🔒 Security Architecture 

LegacyLift is engineered for strict enterprise compliance environments where source code leakage is unacceptable.

### 1. Zero-Persistence File System (TmpFS)
Under the hood, LegacyLift NEVER saves cloned repositories or uploaded artifacts to a persistent disk. All user requests instantiate a unique Python `tempfile`.TemporaryDirectory context mapped directly to the host's RAM (`/tmp`). In milliseconds the LLM finishes context extraction, the directory is obliterated from memory. Even in the event of an Out-Of-Memory (OOM) pod crash, the data vanishes permanently.

### 2. Secure Redaction Layer (SRL)
Before any source code or dependency file context is transmitted to the Gemini API, it passes through the **Secure Redaction Layer**. High-entropy RegEx engines physically overwrite sensitive strings in-memory.
* Gemini sees: `db_uri = "<REDACTED_DB_URI>"`
* Gemini **never** sees: `db_uri = "postgresql://prod:secret@10.0.0.1"`
* *Supported Redactions: JWTs, AWS Keys, IPv4 Internals, DB Connectors, Generic Passwords.*

### 3. Archive Sanitization
Uploaded `.zip` and `.tar.gz` payloads are actively scanned for Zip Bombs (limiting extraction ratios) and Path Traversal attacks (verifying root structures) before admission to the `/tmp` workspace.

---

## ✨ Core Features

* **Multi-Ingestion Routing**: Input public/private GitHub repository URLs (using PAT scopes) or upload air-gapped archives manually.
* **Intelligent File Context**: Automatically parses Python (`requirements.txt`) and Node.js (`package.json`) architectures.
* **Interactive Artifact Editor**: An embedded UI editor allowing you to tweak the generated `Dockerfile` and `deployment.yaml` files before downloading them.
* **GKE Shell Script Generation**: Automatically drafts the exact bash commands to build, tag, push to GCR, and `kubectl apply` your configurations into Google Cloud.


---

## 🛠️ Tech Stack
* **Frontend/Backend Web Framework**: [Streamlit](https://streamlit.io/) (Python)
* **Intelligence Engine**: Google Generative AI (`gemini-2.5-flash`)
* **Source Control Integration**: GitPython
* **Containerization**: Docker Compose

---

## 🚀 Getting Started (Local Deployment)

To get a local copy of LegacyLift up and running smoothly, follow these steps.

### Prerequisites
* Docker desktop installed on your machine.
* A valid Google AI Studio API Key.

### Installation & Run

1. **Clone the repo**
   ```sh
   git clone https://github.com/your-username/LegacyLift.git
   cd LegacyLift
   ```

2. **Configure your Environment Variables**
   Create a `.env` file in the root directory and add your key:
   ```env
   GOOGLE_API_KEY="your-gemini-api-key-here"
   ```

3. **Deploy using Docker Compose**
   LegacyLift utilizes Docker Compose for hot-reloading and port mapping out-of-the-box.
   ```sh
   docker compose up --build
   ```

4. **Access the Application**
   Open your browser and navigate to:
   ```text
   http://localhost:8501
   ```

---

## 💡 Usage Guide

1. **Select Ingestion Method**: Choose between pasting a GitHub URL or uploading a compressed archive.
2. **Add Additional Components**: (Optional) Use the multi-select dropdown to ask Gemini for advanced GKE manifests like `ingress.yaml` or `hpa.yaml`.
3. **Lift Application**: Click the "Lift" button. Watch the console to see the real-time extraction, Redaction Layer sweeps, and Generation progress.
4. **Review & Edit**: Click through the tabs of generated artifacts (Dockerfiles, YAMLs). Review the code, edit inline if needed, and download the exact configurations required for your new cluster!
5. **Start Over**: Click the "Start New Deployment" button at the bottom of the page to purge the session state and lift a new app.

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.
