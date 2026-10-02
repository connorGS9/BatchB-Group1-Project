# Deploy the bank app to AWS

```
Browser ──HTTPS──▶ CloudFront ──▶ S3 bucket            (React website)
   │
   └────HTTPS──▶ API Gateway ──HTTP──▶ EC2 :8000        (FastAPI backend, Docker)
                                           └──▶ MongoDB (Docker, same server, not reachable from the internet)
```

| Piece | AWS service | Why |
|---|---|---|
| Website | S3 + CloudFront | Static files on a global CDN with HTTPS |
| Backend | EC2 (t3.micro) + Docker Compose | Same containers as on your laptop |
| HTTPS for the API | API Gateway (HTTP API) | Gives the backend an HTTPS URL, so the HTTPS website may call it |
| Database | MongoDB in Docker on the EC2 server | DocumentDB isn't allowed in the class account; port 27017 is never opened |
| Secrets | `.env` on the server (chmod 600), optional Parameter Store | Never in the code or on GitHub |

Do the steps **in order**: each one gives you a URL the next one needs. Region: **us-east-1** everywhere.
Use your name in every resource (`student-alexander-...`), because the class shares one account.

---

## Step 1: Backend on EC2

### 1a. Launch the server
EC2 → **Launch instance**
- Name: `student-alexander-bank`
- AMI: **Amazon Linux 2023** · Instance type: **t3.micro**
- Key pair: **Proceed without a key pair** (you connect in the browser)
- Network settings → **Edit** → security group `student-alexander-bank-sg` with two inbound rules:

| Type | Port | Source | Why |
|---|---|---|---|
| SSH | 22 | Custom `18.206.107.24/29` | EC2 Instance Connect (browser login) in us-east-1 |
| Custom TCP | 8000 | Anywhere `0.0.0.0/0` | API Gateway forwards requests here |

- Storage: **16 GiB** (Docker images need room)
- **Launch instance**, wait for **Running**, then copy its **Public IPv4 DNS** (`ec2-…compute-1.amazonaws.com`).

### 1b. Install Docker
Select the instance → **Connect** → **EC2 Instance Connect** → **Connect**. In that browser terminal
(if Connect fails, edit the security group's SSH rule to **Anywhere** for a moment, then set it back):
```bash
sudo dnf install -y git
git clone https://github.com/connorGS9/BatchB-Group1-Project.git
cd BatchB-Group1-Project
bash deploy/ec2-setup.sh
exit
```
Connect again (so `docker` works without sudo).

### 1c. Secrets and start
```bash
cd BatchB-Group1-Project
bash deploy/make-env.sh
docker compose up -d --build mongo backend
docker compose ps
curl http://localhost:8000/health
```
`make-env.sh` writes `.env` with random passwords (only you can read it) and prints the **API_KEY** (save it for Postman).
The last line should print `{"status":"ok","mongo":"connected"}`. The first build takes a few minutes.

> Optional, Parameter Store: if your account allows it, store the same values as SecureString parameters
> `/bank/MONGO_USER`, `/bank/MONGO_PASSWORD`, `/bank/JWT_SECRET`, `/bank/API_KEY`, `/bank/CORS_ORIGINS`,
> give the server a role with `ssm:GetParametersByPath`, and run `bash deploy/load-ssm-secrets.sh` instead of `make-env.sh`.

---

## Step 2: HTTPS URL for the backend (API Gateway)
API Gateway → **Create API** → **HTTP API** → **Build**
- **Add integration** → **HTTP** · Method **ANY** · URL `http://<Public IPv4 DNS>:8000/{proxy}`
- API name: `student-alexander-bank-api` → **Next**
- Route: Method **ANY**, path `/{proxy+}` → **Next** → stage `$default` (auto-deploy) → **Next** → **Create**
- Copy the **Invoke URL** (`https://abc123.execute-api.us-east-1.amazonaws.com`)

Test in a browser: `<Invoke URL>/health` → `"mongo":"connected"`.
Do **not** turn on CORS in API Gateway: the backend answers CORS itself (Step 4).

---

## Step 3: Website on S3 + CloudFront

### 3a. Build it (on your laptop, VS Code terminal)
```powershell
cd bank-frontend
npm install
$env:VITE_API_ORIGIN="https://abc123.execute-api.us-east-1.amazonaws.com"
npm run build
```
Use **your** Invoke URL, no slash at the end. This creates `bank-frontend/dist/`.

### 3b. Upload to S3
S3 → **Create bucket** → `student-alexander-bank-site` (keep **Block all public access** ON) → **Create**.
Open the bucket → **Upload** → drag in **everything inside** `dist` (`index.html` and the `assets` folder) → **Upload**.

### 3c. CloudFront
CloudFront → **Create distribution**
- Origin: **Amazon S3** → pick `student-alexander-bank-site`
- Origin access: **Allow private S3 bucket access to CloudFront** (recommended)
- Default root object: `index.html`
- **Create distribution**, wait until **Deployed** (5–10 min), copy the **Distribution domain name** (`d123abc.cloudfront.net`)

Then: distribution → **Error pages** → **Create custom error response**, twice:

| HTTP error code | Customize response | Response page path | HTTP response code |
|---|---|---|---|
| 403 | Yes | `/index.html` | 200 |
| 404 | Yes | `/index.html` | 200 |

This makes pages like `/adminlogin` work: S3 has no such file, so CloudFront returns the React app and React shows the page.

---

## Step 4: CORS and end-to-end test

### 4a. Allow the website to call the API
On the EC2 server:
```bash
cd BatchB-Group1-Project
sed -i 's|^CORS_ORIGINS=.*|CORS_ORIGINS=https://d123abc.cloudfront.net|' .env
docker compose up -d backend
```
Use **your** CloudFront address, with `https://` and no slash at the end.

### 4b. Test the live site
| Test | Expected |
|---|---|
| `https://d123abc.cloudfront.net` | Customer sign-in page (HTTPS padlock) |
| Sign in `john` / `password123` | John's balance and activity |
| Send $25 to ACC002 | "Sent $25.00 to ACC002" |
| `https://d123abc.cloudfront.net/adminlogin`, `admin` / `admin123` | Admin dashboard |
| `<Invoke URL>/api/v1/accounts/` with no token | `{"detail":"Not logged in"}` |
| Postman: environment `base_url` = Invoke URL, `api_key` = API_KEY from 1c, Run | All tests pass |

---

## Updating after code changes
- Backend: on the server `git pull` then `docker compose up -d --build backend`
- Website: rebuild (3a), upload `dist` again (3b), then CloudFront → **Invalidations** → **Create** → `/*`

## Cleanup (avoid charges)
1. CloudFront → distribution → **Disable**, wait, **Delete**
2. S3 → `student-alexander-bank-site` → **Empty** → **Delete**
3. API Gateway → `student-alexander-bank-api` → **Delete**
4. EC2 → instance → **Terminate**, then delete the security group

> If you **stop** and start the EC2 server, its Public DNS changes: update the API Gateway integration URL (Step 2).
