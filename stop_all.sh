ENV=$1

if [ "$ENV" == "core" ]; then
  docker-compose -f docker-compose-core.yml down
elif [ "$ENV" == "client" ] || [ "$ENV" == "frontend" ]; then
  docker-compose -f docker-compose-client.yml down
else
  docker-compose -f docker-compose.yml down
fi
