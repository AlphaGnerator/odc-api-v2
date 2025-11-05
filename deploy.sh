#!/bin/bash
# --- Complete Deployment Script for odc-api ---

# Exit immediately if a command fails
set -e

# 1. SET VARIABLES
# This makes the script reusable and easy to read.
PROJECT_ID=$(gcloud config get-value project)
REGION=asia-south1
DB_INSTANCE_NAME="cook-postgres"
DB_HOST_PATH="/cloudsql/${PROJECT_ID}:${REGION}:${DB_INSTANCE_NAME}"

# Create a unique image name with a timestamp for versioning.
IMAGE_NAME="gcr.io/${PROJECT_ID}/odc-api:stable-$(date +%s)"
SERVICE_NAME="odc-api"

echo "--- Starting Automated Deployment ---"
echo "Project: $PROJECT_ID"
echo "Image to be built: $IMAGE_NAME"
echo "-------------------------------------"


# 2. BUILD THE CONTAINER IMAGE (This is the image creation step)
echo "Building new container image..."
# This command reads your Dockerfile, packages your code, and pushes the
# resulting container image to Google Container Registry (gcr.io).
gcloud builds submit --tag "$IMAGE_NAME" .


# 3. DEPLOY THE NEW IMAGE TO CLOUD RUN
echo "Deploying the new image to Cloud Run service: $SERVICE_NAME"
# This command tells Cloud Run to update the service using the new image
# we just built in Step 2.
gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE_NAME" \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --set-cloudsql-instances="${PROJECT_ID}:${REGION}:${DB_INSTANCE_NAME}" \
  --set-secrets=DB_PASSWORD=DB_PASSWORD:latest \
  --set-env-vars="DB_HOST=$DB_HOST_PATH"


# 4. FINAL VERIFICATION
echo "--- ✅ SUCCESS: Service Deployed and Connected ---"
# Display the URL of the deployed service
gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format='value(uri)'

echo "Deployment complete."
