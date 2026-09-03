### Vertex AI and Gemini Setup Guide

To run the Gemini inference scripts in this repository, you must use Google Cloud's Vertex AI. This requires setting up a Google Cloud Project with your Google account and authenticating your local machine.

#### Part 1: Cloud Project Setup (This is done in your browser)

1.  Go to the Google Cloud Console at [https://console.cloud.google.com/](https://console.cloud.google.com/?authuser=1)
    
2.  Click the project dropdown at the top of the screen and select New Project.
    
3.  Name your project and write down the Project ID (for example, my-project-12345).
    
4.  Open the navigation menu in the top left, go to Billing, and link a credit card or billing account to this new project. Vertex AI will not run without an active billing account.

#### Step 2: Authenticate your Local Machine (This is done in your local terminal)

1.  Install the Google Cloud CLI. For macOS, run the following command: `brew install --cask google-cloud-sdk`. For Linux, run `curl [https://sdk.cloud.google.com](https://sdk.cloud.google.com?authuser=1)` and `bashexec -l $SHELL`

2.  Log into your Google account by running `gcloud auth login`

3.  Generate your Application Default Credentials (ADC) by running `gcloud auth application-default login`

4.  Link your terminal and credentials to your Project ID. Replace YOUR\_PROJECT\_ID with the ID you wrote down in Phase 1. Run `gcloud config set project YOUR_PROJECT_ID` and `gcloud auth application-default set-quota-project YOUR_PROJECT_ID`

5.  Enable the Vertex AI API for your project by running `gcloud services enable aiplatform.googleapis.com`

6.  Install the required Python library by running `pip install google-cloud-aiplatform`

#### Step 3: Configure the inference code file

Before running inference, you must update the repository code to use your specific Google Cloud project.

1.  Open the file located at `./inference/llm_base/interact_gemini.py`
    
2.  Change the hardcoded PROJECT\_ID to match your own. It should look like `PROJECT_ID = "YOUR_PROJECT_ID"`

#### Step 4: Run Inference

After following these steps, you should be able to run inference with Gemini models following the instructions in `./inference/README.md`