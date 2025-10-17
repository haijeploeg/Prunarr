# GitHub App Setup for Auto-Tagging

The auto-tag workflow requires a GitHub App to trigger downstream workflows. This is necessary because GitHub's `GITHUB_TOKEN` cannot trigger other workflows for security reasons.

## Why GitHub App Instead of GITHUB_TOKEN?

When using the default `GITHUB_TOKEN` to push tags or commits, GitHub **intentionally blocks** triggering of other workflows to prevent recursive workflow runs. The auto-tag workflow needs to trigger the PyPI, Docker, and Helm release workflows when it creates a tag.

**Problem:** Using `GITHUB_TOKEN` to push tags will NOT trigger:
- `docker.yml` - Docker image build and push
- `helm.yml` - Helm chart release
- `publish.yml` - PyPI package publishing

**Solutions:**
1. **GitHub App** (Recommended) - Secure, scoped to repository, no expiration
2. **Personal Access Token** (Alternative) - Less secure, has access to all repos, requires renewal

## Creating the GitHub App

### Step 1: Create GitHub App

1. Go to **Settings → Developer settings → GitHub Apps → New GitHub App**
2. Configure the app:
   - **Name**: `PrunArr Release Bot` (or any name)
   - **Homepage URL**: Your repository URL (e.g., `https://github.com/hploeg/prunarr`)
   - **Webhook**: Uncheck "Active" (not needed)
   - **Repository permissions**:
     - **Contents**: Read and write
     - **Metadata**: Read-only (automatic)
   - **Where can this GitHub App be installed?**: Only on this account
3. Click **Create GitHub App**

### Step 2: Install the App

1. After creating, click **Install App** in the left sidebar
2. Select your repository (or all repositories if preferred)
3. Click **Install**

### Step 3: Get App Credentials

1. Go to the app settings page
2. Note the **App ID** (numeric value, e.g., `123456`)
3. Scroll to **Private keys** section
4. Click **Generate a private key**
5. Download the `.pem` file (keep this secure!)

### Step 4: Add Repository Secrets

1. Go to your repository → **Settings → Secrets and variables → Actions**
2. Click **New repository secret**
3. Add two secrets:

   **Secret 1: APP_ID**
   - Name: `APP_ID`
   - Value: The numeric App ID from step 3 (e.g., `123456`)

   **Secret 2: APP_PRIVATE_KEY**
   - Name: `APP_PRIVATE_KEY`
   - Value: Full contents of the `.pem` file, including header/footer:
     ```
     -----BEGIN RSA PRIVATE KEY-----
     MIIEpAIBAAKCAQEA...
     ...
     -----END RSA PRIVATE KEY-----
     ```

## Testing the GitHub App

After setup, the auto-tag workflow will use the App token to push tags and trigger workflows.

### Test the Workflow

```bash
# 1. Update version in __init__.py
vim prunarr/__init__.py
# Change: __version__ = "1.0.1"

# 2. Commit and push to main
git add prunarr/__init__.py
git commit -m "chore: bump version to 1.0.1"
git push origin main

# 3. Watch workflow execution
gh run watch
```

### Expected Behavior

The auto-tag workflow should:
1. ✅ Successfully create tag `v1.0.1`
2. ✅ Trigger `docker.yml` workflow
3. ✅ Trigger `helm.yml` workflow
4. ✅ Trigger `publish.yml` workflow

You can verify in the Actions tab that all 4 workflows run:
- Auto Tag on Version Change
- Build and Push Docker Image
- Release Helm Chart
- Publish to PyPI

## Alternative: Personal Access Token (PAT)

If GitHub App setup is too complex, you can use a Personal Access Token instead.

### Create PAT

1. Go to **Settings → Developer settings → Personal access tokens → Fine-grained tokens**
2. Click **Generate new token**
3. Configure:
   - **Token name**: `PrunArr Auto Tag`
   - **Repository access**: Select your repository
   - **Permissions**:
     - **Contents**: Read and write
4. Click **Generate token**
5. Copy the token (you won't see it again!)

### Add Secret

1. Go to repository → **Settings → Secrets and variables → Actions**
2. Add secret:
   - Name: `PAT_TOKEN`
   - Value: Your generated token

### Update Workflow

Edit `.github/workflows/auto-tag.yml`:

```yaml
# Replace the GitHub App token step with:
- name: Checkout code
  uses: actions/checkout@v4
  with:
    fetch-depth: 0
    token: ${{ secrets.PAT_TOKEN }}
```

**Pros:**
- Simpler setup
- No app installation needed

**Cons:**
- Less secure (PAT has broader access)
- Token expires and requires manual renewal
- Shows as your personal commits instead of bot

## Troubleshooting

### Workflows Not Triggering

**Symptom**: Auto-tag workflow succeeds but Docker/Helm/PyPI workflows don't run.

**Solution**: Verify GitHub App setup:
```bash
# Check if secrets are set
gh secret list

# Should show:
# APP_ID          Updated YYYY-MM-DD
# APP_PRIVATE_KEY Updated YYYY-MM-DD
```

### Permission Denied Errors

**Symptom**: `refusing to allow a GitHub App to create or update workflow`

**Solution**: Add `workflows: write` permission to the app:
1. Go to app settings
2. Repository permissions → **Workflows**: Read and write
3. Save changes
4. Reinstall the app on your repository

### Tag Already Exists

**Symptom**: Workflow skips tag creation because tag exists.

**Solution**: Delete the existing tag:
```bash
# Delete local tag
git tag -d v1.0.1

# Delete remote tag
git push origin :refs/tags/v1.0.1
```

## Security Best Practices

1. **Use GitHub App** instead of PAT when possible
2. **Scope permissions** to minimum required (Contents: write, Metadata: read)
3. **Install on specific repository** only, not all repositories
4. **Rotate private keys** periodically
5. **Keep `.pem` file secure** - never commit to repository
6. **Use repository secrets** - never hardcode credentials

## References

- [GitHub Actions: Using GITHUB_TOKEN](https://docs.github.com/en/actions/security-guides/automatic-token-authentication#using-the-github_token-in-a-workflow)
- [Creating a GitHub App](https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps/about-creating-github-apps)
- [actions/create-github-app-token](https://github.com/actions/create-github-app-token)
