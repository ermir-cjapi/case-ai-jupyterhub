## User Guide – JupyterHub V1 (Test Users)

### 1. Accessing JupyterHub

- Open a browser inside the corporate network.
- Navigate to: `https://jupyterhub-test.example.internal`
- Accept the certificate if it is not yet trusted.

### 2. Logging In (Local Accounts)

- Enter your **username** (provided by the admin).
- Use the **shared test password** given to you by the project team.
- After successful login, you will be redirected to the JupyterLab interface.

### 3. Starting and Stopping Notebooks

- After login, JupyterHub will start a notebook server for you automatically.
- To stop your server:
  - Click on your avatar (top-right).
  - Choose **Stop My Server**.

### 4. Working with Files

- Your home directory (`/home/jovyan`) is stored on a persistent volume.
- A shared directory is mounted at `/shared` for collaboration between testers.
- Avoid storing large datasets in the notebook image; use shared storage or external systems.

### 5. Using GPUs (If Available)

- If GPU nodes are configured, your notebook may be scheduled on a GPU node.
- Use standard libraries (e.g. PyTorch, TensorFlow) if they are installed in the image.
- Ask the admin team if you are unsure whether GPUs are available for V1.

### 6. Best Practices

- Shut down idle notebooks when not in use to free cluster resources.
- Commit important notebooks and code to Git (e.g. GitLab) instead of keeping them only in Jupyter.
- Do not store credentials or secrets directly in notebooks; use environment variables or secret management solutions.

### 7. Reporting Issues

If you encounter issues (login problems, slow performance, errors):

- Note the time, your username, and what you did.
- Share screenshots or error messages with the admin/ops team.

### 8. Using Git with Notebooks (Optional)

- If JupyterLab Git integration is enabled, you can open the **Git** sidebar to clone repositories, commit changes, and push to GitLab/GitHub directly from the notebook interface.
- A common workflow is:
  - Clone your project repository into your home directory or `/shared`.
  - Work on notebooks and scripts in that repo.
  - Commit and push regularly so your work is backed up and shareable.
- If the Git extension is not available, you can still use `git` from a terminal inside JupyterLab.


