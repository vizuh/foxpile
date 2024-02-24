# Bot Discord
Welcome to the project

# Setup
To run the project, follow these instructions to create the .env file and configure the DISCORD_SECRET_KEY variable.

- Create a .env file in the project's root directory.

Add the key to the .env file:

```env
DISCORD_SECRET_KEY=YourSecretKeyHere
```
Replace YourSecretKeyHere with your Discord application's secret key.

Ensure not to share this key and keep it secure.

# Using Docker
To build a Docker image and run the project:

1. Execute the code:
```bash
docker build -t project-xyz .
```

2. Run de image created:
```bash
docker run --name project-xyz-container -d project-xyz
```