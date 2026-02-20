import streamlit as st
import google.generativeai as genai
import git
import os
import shutil
import stat
from dotenv import load_dotenv

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="LegacyLift", page_icon="🚀", layout="wide")

# --- INITIALIZE SESSION STATE ---
if "artifacts" not in st.session_state:
    st.session_state.artifacts = None

# --- LOAD API KEY ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("❌ GOOGLE_API_KEY not found in .env file.")
    st.stop()

# --- SYSTEM INSTRUCTIONS ---
SYSTEM_INSTRUCTION = """
You are a Google Cloud DevOps Expert. Your goal is to modernize legacy applications for Google Cloud Run.
Rules for your output:
1. OUTPUT ONLY THE RAW CODE for the requested file. 
2. DO NOT include any conversational text, explanations, or markdown code block backticks.
3. Ensure the code is production-ready and optimized for Google Cloud.
4. For Dockerfiles: Use lightweight base images and expose port 8080.
5. For cloudbuild.yaml: Include steps to build, push, and deploy.
6. For service.yaml: Use the Knative serving.knative.dev/v1 API.
"""

genai.configure(api_key=api_key)

# --- UTILITY FUNCTIONS ---
def remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def clone_repo(repo_url):
    local_path = "./temp_legacy_app"
    if os.path.exists(local_path):
        shutil.rmtree(local_path, onerror=remove_readonly)
    try:
        git.Repo.clone_from(repo_url, local_path)
        return local_path
    except Exception as e:
        st.error(f"Git Clone Error: {e}")
        return None

def get_file_context(folder_path):
    context = ""
    req_path = os.path.join(folder_path, "requirements.txt")
    if os.path.exists(req_path):
        with open(req_path, "r") as f:
            context += f"Python Dependencies (requirements.txt):\n{f.read()}\n"
    
    pkg_path = os.path.join(folder_path, "package.json")
    if os.path.exists(pkg_path):
        with open(pkg_path, "r") as f:
            context += f"Node.js Dependencies (package.json):\n{f.read()}\n"
    return context if context else "No major dependency files found."

# --- THE AI BRAIN ---
def ask_gemini(prompt):
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        selected_model = next((m for m in available_models if '1.5-flash' in m), available_models[0])
        model = genai.GenerativeModel(
            model_name=selected_model,
            system_instruction=SYSTEM_INSTRUCTION
        )
        response = model.generate_content(prompt)
        return response.text.replace('dockerfile', '').replace('yaml', '').replace('```', '').strip()
    except Exception as e:
        return f"AI Error: {str(e)}"

# --- MAIN UI ---
st.title("🚀 LegacyLift: Agentic Migration Factory")
st.markdown("Modernize legacy apps to Google Cloud Run in seconds.")

repo_url = st.text_input("GitHub Repository URL", placeholder="https://github.com/aws-samples/eb-python-flask")

# --- GENERATION LOGIC ---
if st.button("Migrate to Cloud ☁️"):
    if not repo_url:
        st.error("Please enter a URL first.")
    else:
        with st.spinner("Analyzing Repo & Generating Clean Artifacts..."):
            local_folder = clone_repo(repo_url)
            if local_folder:
                context = get_file_context(local_folder)
                st.session_state.artifacts = {
                    "dockerfile": ask_gemini(f"Generate a production-ready Dockerfile for this context: {context}"),
                    "cloudbuild": ask_gemini(f"Generate a cloudbuild.yaml for Google Cloud Build for this context: {context}"),
                    "service_yaml": ask_gemini(f"Generate a Cloud Run service.yaml manifest for this context: {context}"),
                    "repo_name": repo_url.split("/")[-1].replace(".git", "")
                }
                

# --- DISPLAY LOGIC ---
if st.session_state.artifacts:
    art = st.session_state.artifacts
    
    st.subheader("Generated Artifacts")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("### 🐳 Dockerfile")
        st.code(art["dockerfile"], language="dockerfile")
        st.download_button(
            label="Download Dockerfile",
            data=art["dockerfile"],
            file_name="Dockerfile",
            mime="text/plain"
        )

    with c2:
        st.markdown("### 🏗️ cloudbuild.yaml")
        st.code(art["cloudbuild"], language="yaml")
        st.download_button(
            label="Download cloudbuild.yaml",
            data=art["cloudbuild"],
            file_name="cloudbuild.yaml",
            mime="text/yaml"
        )

    with c3:
        st.markdown("### ☁️ service.yaml")
        st.code(art["service_yaml"], language="yaml")
        st.download_button(
            label="Download service.yaml",
            data=art["service_yaml"],
            file_name="service.yaml",
            mime="text/yaml"
        )

    st.markdown("---")
    st.subheader("4. One-Click Deployment Script")
    st.info("Run this in your Google Cloud Shell to deploy these artifacts.")
    
    deploy_cmd = """
# 1. Build and Push to Artifact Registry
gcloud builds submit --config cloudbuild.yaml .

# 2. Deploy using the Service Manifest
gcloud run services replace service.yaml
"""
    st.code(deploy_cmd, language="bash")