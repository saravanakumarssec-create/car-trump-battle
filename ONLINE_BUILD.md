# Car Trump Battle — online APK build

## 1. Deploy the server

Create a Render Web Service from the `server` directory. Build command:
`pip install -r requirements.txt`
Start command:
`python server.py`

Render accepts public WebSocket connections. Use the `wss://` URL in the app.

## 2. Put the URL in GitHub

In the GitHub repository go to Settings → Secrets and variables → Actions → New repository secret.

Name: `GAME_SERVER_URL`
Value: `wss://YOUR-SERVICE.onrender.com`

## 3. Build

Open Actions → Build Car Trump Battle APK → Run workflow.
When it finishes, open the run and download the `car-trump-battle-apk` artifact.

The workflow builds on GitHub's Ubuntu runner, not your WSL installation.
