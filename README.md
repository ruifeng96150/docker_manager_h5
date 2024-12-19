# Docker Mobile Manager

A mobile Docker management application based on Portainer API.

## Functional characteristics

- Container management (view, start, stop, delete)

- Image management

- System resource monitoring

- Responsive design, compatible with mobile devices

## Development steps

1. Cloning project
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Configure environment variables:
Create an '. env' file and set the following variables:
```
PORTAINER_URL= http://your-portainer-url:9000
PORTAINER_USERNAME=your-username
PORTAINER_PASSWORD=your-password
```

4. Running the application:
```bash
python app.py
```


## Install on Docker

```bash
# docker rm -f docker-app
docker build --build-arg BUILDKIT_INLINE_CACHE=1 -t docker-app .

docker run -d \
  -p 5000:5000 \
  -e PORTAINER_URL=http://your-portainer-url:9000 \
  -e PORTAINER_USERNAME=admin \
  -e PORTAINER_PASSWORD=admin_password \
  -e APP_USERNAME=user \
  -e APP_PASSWORD=pwd \
  -e SECRET_KEY=secret-key-here \
  -e FLASK_DEBUG=false \
  --name docker-app \
  docker-app

```


## Technology Stack

- Backend: Flask
- Frontend: HTML5, CSS3, JavaScript
- API: Portainer API



