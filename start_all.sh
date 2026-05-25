ENV=$1

if [ "$ENV" == "core" ]; then
  docker-compose -f docker-compose-core.yml up -d --build
elif [ "$ENV" == "client" ] || [ "$ENV" == "frontend" ]; then
  docker-compose -f docker-compose-client.yml up -d --build
else
  docker-compose -f docker-compose.yml up -d --build
fi
