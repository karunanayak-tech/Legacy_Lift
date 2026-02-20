import streamlit as st

def generate_deploy_script(project_id, service_name, region="us-central1"):
    """
    Generates the 'Golden Path' gcloud commands for deployment.
    This replaces the actual API call since we have no billing.
    """
    script = f"""
    # 1. Set the Project
    gcloud config set project {project_id}
    
    # 2. Build the Container (Cloud Build)
    gcloud builds submit --tag gcr.io/{project_id}/{service_name} .
    
    # 3. Deploy to Cloud Run (Serverless)
    gcloud run deploy {service_name} \\
      --image gcr.io/{project_id}/{service_name} \\
      --platform managed \\
      --region {region} \\
      --allow-unauthenticated
      
    echo "✅ Deployment Complete! Your app is live."
    """
    return script