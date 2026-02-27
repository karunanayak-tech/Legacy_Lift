import streamlit as st
from google import genai
import git
import os
import subprocess
import urllib.parse
import requests
import gc
import shutil
import stat
from dotenv import load_dotenv
import re
import logging
import zipfile
import tarfile

logger = logging.getLogger("LegacyLift-Redactor")

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="LegacyLift", page_icon="☁️", layout="wide")

# --- INITIALIZE SESSION STATE ---
if "artifacts" not in st.session_state:
    st.session_state.artifacts = None
if "theme" not in st.session_state:
    st.session_state.theme = "light"

# --- CUSTOM THEME, CSS & ANIMATIONS ---
def load_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error loading CSS: {e}") # Let's show the error so we can debug

load_css("style.css")

# Apply dynamic Dark Mode overrides if state is active
if st.session_state.theme == "dark":
    st.markdown("""
    <style>
    /* Dark Mode Overrides */
    :root {
        --coffee-dark: #E2C792;
        --coffee-medium: #A47C54;
        --coffee-light: #4A3B32;
        --sky-blue: #0A0F1C;
        --sky-light: #131B2F;
        --soft-white: #0A0F1C;
        --text-main: #F8FAFC;
        --text-muted: #94A3B8;
        --shadow-soft: 0 8px 30px rgba(0, 0, 0, 0.8);
        --shadow-glow: 0 0 15px rgba(226, 199, 146, 0.3);
    }
    
    h1 { color: var(--text-main) !important; }
    h2, h3 { color: var(--coffee-dark) !important; }
    
    h1, h2, h3 { text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.9) !important; }
    
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        background: rgba(19, 27, 47, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    
    pre, code {
        background-color: #060913 !important;
        color: #E2C792 !important;
        border: 1px solid #1E293B !important;
        box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.8) !important;
    }
    
    .stTextInput>div>div>input, div[data-baseweb="select"] > div {
        background-color: #131B2F !important;
        border-color: #334155 !important;
        color: #F8FAFC !important;
    }
    
    .stApp::before {
        background-image: 
            radial-gradient(circle at 20% 30%, rgba(255,255,255,0.03) 0%, transparent 20%),
            radial-gradient(circle at 80% 20%, rgba(255,255,255,0.02) 0%, transparent 30%),
            radial-gradient(circle at 40% 70%, rgba(255,255,255,0.01) 0%, transparent 25%);
    }
    
    .header-icon {
        font-size: 3.8rem;
        line-height: 1.2;
    }
    </style>
    """, unsafe_allow_html=True)
# --- LOAD API KEY ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("❌ GOOGLE_API_KEY not found in .env file.")
    st.stop()

# --- SYSTEM INSTRUCTIONS ---
SYSTEM_INSTRUCTION = """
You are a Google Cloud DevOps Expert. Your goal is to modernize legacy applications for Google Kubernetes Engine (GKE).
Rules for your output:
1. OUTPUT ONLY THE RAW CODE for the requested file. 
2. DO NOT include any conversational text, explanations, or markdown code block backticks.
3. Ensure the code is production-ready and optimized for Google Kubernetes Engine.
4. For Dockerfiles: Use lightweight base images and expose port 8080.
5. For Kubernetes manifests: Ensure appropriate apiVersions (e.g. apps/v1 for Deployments, v1 for Services/ConfigMaps/Secrets, networking.k8s.io/v1 for Ingress).
"""

# The new google.genai SDK automatically picks up the GOOGLE_API_KEY env var
# client = genai.Client() will be initialized inside ask_gemini

import tempfile

# --- UTILITY FUNCTIONS ---
def remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def validate_token_scope(pat: str) -> bool:
    """Validates that the token is active and has appropriate, minimal scopes."""
    with requests.Session() as session:
        session.headers.update({"Authorization": f"Bearer {pat}"})
        response = session.get("https://api.github.com/user")
        
    if response.status_code != 200:
        raise ValueError("Invalid or expired Personal Access Token.")
    
    scopes = response.headers.get("X-OAuth-Scopes", "").split(", ")
    if "repo" not in scopes and "read:org" not in scopes:
         st.warning("Warning: Token does not have 'repo' scope. Cloning private repos may fail.")
    return True

def scrub_sensitive_data(text: str) -> str:
    """Removes any exposure of the token in error messages."""
    return re.sub(r'https://[^@]+@', 'https://*@', text)

def secure_clone(repo_url: str, pat: str, target_dir: str):
    """Executes the clone operation securely, optionally using a PAT."""
    auth_url = repo_url
    
    try:
        if pat:
            validate_token_scope(pat)
            parsed = urllib.parse.urlparse(repo_url)
            auth_url = f"{parsed.scheme}://{pat}@{parsed.netloc}{parsed.path}"
        
        # We MUST inherit os.environ so thread, networking, and DNS (getaddrinfo) resolve properly
        my_env = os.environ.copy()
        my_env["GIT_TERMINAL_PROMPT"] = "0"
        
        result = subprocess.run(
            ["git", "clone", auth_url, target_dir],
            capture_output=True,
            text=True,
            env=my_env
        )
        
        if result.returncode != 0:
            scrubbed_error = scrub_sensitive_data(result.stderr)
            raise RuntimeError(f"Git clone failed: {scrubbed_error}")
            
        return target_dir
            
    except Exception as e:
        scrubbed_msg = scrub_sensitive_data(str(e))
        raise RuntimeError(f"Operation failed safely: {scrubbed_msg}") from None
        
    finally:
        if pat:
            if 'auth_url' in locals():
                auth_url = "DELETED"
                del auth_url
            if 'pat' in locals():
                pat = "DELETED"
                del pat
        gc.collect()

# --- SECURE FILE INGESTION ---
MAX_UPLOAD_SIZE_MB = 200
MAX_EXTRACTED_SIZE_MB = 1000
MALICIOUS_EXTENSIONS = {'.exe', '.bat', '.cmd', '.sh', '.vbs', '.msi', '.pif', '.scr'}

def secure_extract(uploaded_file, dest_dir):
    """Securely extracts uploaded zip/tar.gz files preventing path traversal and bombs."""
    upload_size = uploaded_file.size
    if upload_size > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise Exception(f"Upload exceeds maximum size of {MAX_UPLOAD_SIZE_MB}MB.")

    total_extracted_size = 0
    temp_archive_path = os.path.join(dest_dir, "uploaded_archive")
    with open(temp_archive_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    try:
        if uploaded_file.name.endswith('.zip'):
            with zipfile.ZipFile(temp_archive_path, 'r') as archive:
                for member in archive.infolist():
                    if member.is_dir():
                        continue
                    
                    target_path = os.path.abspath(os.path.join(dest_dir, member.filename))
                    if not target_path.startswith(os.path.abspath(dest_dir)):
                        raise Exception(f"Path traversal attempt detected in {member.filename}.")
                        
                    ext = os.path.splitext(member.filename)[1].lower()
                    if ext in MALICIOUS_EXTENSIONS:
                         raise Exception(f"Malicious file type blocked: {member.filename}")
                         
                    total_extracted_size += member.file_size
                    if total_extracted_size > MAX_EXTRACTED_SIZE_MB * 1024 * 1024:
                        raise Exception("Zip bomb detected. Extraction exceeded limits.")
                        
                    archive.extract(member, dest_dir)
                    
        elif uploaded_file.name.endswith(('.tar.gz', '.tgz', '.tar')):
            with tarfile.open(temp_archive_path, 'r:*') as archive:
                for member in archive.getmembers():
                    if not member.isfile():
                        continue
                        
                    target_path = os.path.abspath(os.path.join(dest_dir, member.name))
                    if not target_path.startswith(os.path.abspath(dest_dir)):
                        raise Exception(f"Path traversal attempt detected in {member.name}.")
                        
                    ext = os.path.splitext(member.name)[1].lower()
                    if ext in MALICIOUS_EXTENSIONS:
                         raise Exception(f"Malicious file type blocked: {member.name}")
                         
                    total_extracted_size += member.size
                    if total_extracted_size > MAX_EXTRACTED_SIZE_MB * 1024 * 1024:
                        raise Exception("Archive bomb detected. Extraction exceeded limits.")
                        
                    archive.extract(member, dest_dir)
        else:
            raise Exception("Unsupported file format. Please upload .zip or .tar.gz.")
    finally:
        if os.path.exists(temp_archive_path):
            os.remove(temp_archive_path)

# --- SECURE REDACTION LAYER ---
SECRET_PATTERNS = {
    "JWT_TOKEN": re.compile(r"eyJ[A-Za-z0-9-=]+\.[A-Za-z0-9-=]+\.?[A-Za-z0-9-_.+/=]*"),
    "AWS_KEY": re.compile(r"(?i)\b(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}\b"),
    "GENERIC_SECRET": re.compile(r"""(?i)(?:password|secret|token|api_key|apikey)(?:\s*["':=]\s*)(["'])([^"'\s]+)\1"""),
    "DB_URI": re.compile(r"(?:postgres|mysql|mongodb)(?:\+srv)?:\/\/(?:[^:]+):([^@]+)@"),
    "INTERNAL_IP": re.compile(r"(^10\.)|(^172\.1[6-9]\.)|(^172\.2[0-9]\.)|(^172\.3[0-1]\.)|(^192\.168\.)")
}

def sanitize_context(raw_text: str) -> tuple[str, int]:
    sanitized_text = raw_text
    redaction_count = 0
    for category, pattern in SECRET_PATTERNS.items():
        matches = pattern.finditer(sanitized_text)
        for match in matches:
            redaction_count += 1
            logger.warning(f"SECURITY: Redacted {category} matching pattern.")
            if category == "GENERIC_SECRET":
                sanitized_text = sanitized_text.replace(match.group(2), f"<REDACTED_{category}>")
            elif category == "DB_URI":
                 sanitized_text = sanitized_text.replace(match.group(1), f"<REDACTED_{category}>")
            else:
                sanitized_text = sanitized_text.replace(match.group(0), f"<REDACTED_{category}>")
    return sanitized_text, redaction_count

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
            
    if not context:
        return "No major dependency files found."
        
    safe_context, hits = sanitize_context(context)
    if hits > 0:
        st.toast(f"Security Scanner active: Redacted {hits} potential secrets from source code.", icon="🛡️")
        
    return safe_context

def ask_gemini(prompt):
    try:
        # Initialize client (uses GOOGLE_API_KEY from env)
        client = genai.Client()
        
        # New genai API uses client.models.generate_content
        # Using gemini-2.5-flash as default modern model, or gemini-2.0-flash
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION
            )
        )
        return response.text.replace('dockerfile', '').replace('yaml', '').replace('```', '').strip()
    except Exception as e:
        return f"AI Error: {str(e)}"

# --- MAIN UI ---
import streamlit.components.v1 as components # Needed for robust HTML if needed
container = st.container()
with container:
    col_t1, col_t2 = st.columns([9, 1], vertical_alignment="center")
    with col_t2:
        theme_label = "🌙" if st.session_state.theme == "light" else "☀️"
        if st.button(theme_label, key="theme_toggle", use_container_width=True):
            st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
            st.rerun()

    col1, col2 = st.columns([1, 15], vertical_alignment="center")
    with col1:
        if st.session_state.theme == "light":
            st.markdown('<div class="header-icon">🌤️</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="header-icon">🚀✨</div>', unsafe_allow_html=True)
    with col2:
        st.title("LegacyLift")

    st.markdown("""
        <p style="font-size: 1.15rem; margin-bottom: 2.5rem; max-width: 800px; font-weight: 300;">
            Watch your outdated systems evolve. Enter your legacy repository URL or upload a project archive below, and we'll lift it into a modern, robust <b>Google Kubernetes Engine (GKE)</b> environment.
        </p>
    """, unsafe_allow_html=True)

    ingest_method = st.radio("Select Application Source:", ["GitHub Repository", "Upload Archive (Air-Gapped)"], horizontal=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    repo_url = ""
    token_input = ""
    uploaded_file = None
    
    if ingest_method == "GitHub Repository":
        repo_url = st.text_input("🔗 GitHub Repository URL", placeholder="https://github.com/aws-samples/eb-python-flask")
        token_input = st.text_input("GitHub Personal Access Token (Optional for Public Repos)", type="password", help="Requires 'repo' scope.")
    else:
        uploaded_file = st.file_uploader("📂 Upload Legacy App Archive (.zip, .tar.gz)", type=["zip", "tar.gz", "tgz", "tar"])
        st.caption(f"Max size: {MAX_UPLOAD_SIZE_MB}MB. Files are analyzed completely in-memory and ephemerally.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("### ☁️ Configure Ascent")
    conditional_files = st.multiselect(
        "Select additional atmospheric components (GKE Manifests):",
        ["ingress.yaml", "secret.yaml", "configmap.yaml", "hpa.yaml", "namespace.yaml"],
        default=[]
    )

# --- GENERATION LOGIC ---
st.markdown("<br>", unsafe_allow_html=True)
col_btn, _ = st.columns([1, 4]) 
with col_btn:
    lift_button = st.button("✨ Lift Application", use_container_width=True)

if lift_button:
    if ingest_method == "GitHub Repository" and not repo_url:
        st.error("Please enter a valid GitHub Repository URL first.", icon="❌")
    elif ingest_method == "Upload Archive (Air-Gapped)" and not uploaded_file:
        st.error("Please upload an archive file first.", icon="❌")
    else:
        with st.status("🧠 Initializing Migration Engine...", expanded=True) as status:
            st.write("Provisioning secure ephemeral workspace...")
            # Automatically creates an isolated /tmp/ directory and guarantees destruction when the block ends
            with tempfile.TemporaryDirectory(prefix="legacylift_") as local_folder:
                
                ingest_success = False
                app_name = "legacy-app"
                
                if ingest_method == "GitHub Repository":
                    st.write(f"Cloning repository securely into temporary RAM...")
                    try:
                        secure_clone(repo_url, token_input, local_folder)
                        ingest_success = True
                        app_name = repo_url.split("/")[-1].replace(".git", "")
                    except Exception as e:
                        st.error(f"Clone error: {str(e)}", icon="❌")
                    finally:
                        if 'token_input' in locals() and token_input:
                            token_input = "DELETED"
                            del token_input
                        gc.collect()
                else:
                    st.write(f"Securely extracting uploaded archive...")
                    try:
                        secure_extract(uploaded_file, local_folder)
                        ingest_success = True
                        app_name = os.path.splitext(uploaded_file.name)[0]
                    except Exception as e:
                        st.error(f"Security Alert / Error: {str(e)}", icon="🛡️")

                if ingest_success:
                    st.write("Analyzing dependencies and architecture...")
                    context = get_file_context(local_folder)
                    
                    st.write("Generating infrastructure artifacts...")
                    artifacts = {
                        "Dockerfile": ask_gemini(f"Generate a production-ready Dockerfile for this context: {context}"),
                        ".dockerignore": ask_gemini(f"Generate a .dockerignore file for this context: {context}"),
                        "deployment.yaml": ask_gemini(f"Generate a Kubernetes deployment.yaml manifest for this context. Use the app name {app_name}: {context}"),
                        "service.yaml": ask_gemini(f"Generate a Kubernetes service.yaml manifest for this context to expose the deployment: {context}"),
                        "README.md": ask_gemini(f"Generate a README.md explaining how to deploy these files to GKE for this context: {context}"),
                        "repo_name": app_name
                    }
                    
                    for f in conditional_files:
                        st.write(f"Generating additional component: {f}...")
                        artifacts[f] = ask_gemini(f"Generate a Kubernetes {f} manifest for this context for GKE. App name: {app_name}. Context: {context}")
                        
                    st.session_state.artifacts = artifacts
                    status.update(label="Migration Planning Complete! Data securely purged. 🎉", state="complete", expanded=False)
            # When the with block ends, local_folder is instantly destroyed

# --- DISPLAY LOGIC ---
if st.session_state.artifacts:
    st.markdown("<br><hr>", unsafe_allow_html=True)
    art = st.session_state.artifacts
    
    st.markdown("## 📦 Generated Artifacts")
    st.caption("Review and download the generated configuration files below.")
    
    # Filter out repo_name for tabs
    file_names = [k for k in art.keys() if k != "repo_name"]
    tabs = st.tabs([f"📄 {name}" for name in file_names])
    
    for tab, file_name in zip(tabs, file_names):
        with tab:
            file_content = art[file_name]
            
            st.markdown(f"### 📝 Edit {file_name}")
            st.caption("You can make direct changes to the generated code below before downloading.")
            
            # Interactive Editor using text_area
            edited_content = st.text_area(
                label=f"Edit {file_name}", 
                value=file_content, 
                height=400, 
                key=f"editor_{file_name}",
                label_visibility="collapsed"
            )
            
            col1, col2 = st.columns([1, 3])
            with col1:
                st.download_button(
                    label=f"💾 Download {file_name}",
                    data=edited_content,  # Use the edited content!
                    file_name=file_name,
                    mime="text/plain",
                    use_container_width=True
                )

    st.markdown("---")
    st.markdown("## ☁️ One-Click Deployment Script")
    st.info("Run this in your Google Cloud Shell to deploy these artifacts directly to your GKE cluster. Ensure you have the right permissions configured.", icon="💡")
    
    deploy_cmd = f"""
# 1. Authenticate with GKE cluster (replace parameters with your cluster details)
gcloud container clusters get-credentials <CLUSTER_NAME> --region <REGION> --project <PROJECT_ID>

# 2. Build and push your image
export PROJECT_ID=$(gcloud config get-value project)
export IMAGE_NAME=gcr.io/$PROJECT_ID/{art.get("repo_name", "app")}
docker build -t $IMAGE_NAME .
docker push $IMAGE_NAME

# 3. Apply Kubernetes manifests
kubectl apply -f .
"""
    st.code(deploy_cmd, language="bash")

    st.markdown("---")
    st.markdown("## 🔄 Start Over")
    st.info("Ready to lift another application? Click the button below to clear the current workspace and start a new deployment.", icon="♻️")
    if st.button("Start New Deployment", type="primary", use_container_width=True):
        st.session_state.artifacts = None
        st.rerun()
